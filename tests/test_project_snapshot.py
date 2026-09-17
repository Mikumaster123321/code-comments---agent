import json
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from code_maintenance import (
    GraphNodeKind,
    ProjectGraph,
    ProjectGraphBuilder,
    ProjectScanner,
    SnapshotBuilder,
)


def build_snapshot(root, **kwargs):
    return SnapshotBuilder().build(ProjectScanner().scan(root), **kwargs)


def test_repeated_unchanged_project_has_same_content_identity(tmp_path):
    (tmp_path / "main.py").write_text("def run():\n    return 1\n", encoding="utf-8")

    first = build_snapshot(tmp_path)
    second = build_snapshot(tmp_path)

    assert first.content_hash == second.content_hash
    assert first.files == second.files
    assert first.symbols == second.symbols
    assert first.graph == second.graph


def test_created_at_does_not_affect_content_hash(tmp_path):
    scan = ProjectScanner().scan(tmp_path)
    builder = SnapshotBuilder()

    first = builder.build(scan, created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
    second = builder.build(scan, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert first.created_at != second.created_at
    assert first.content_hash == second.content_hash


def test_comparison_detects_changed_and_unchanged_files(tmp_path):
    changed = tmp_path / "changed.py"
    unchanged = tmp_path / "unchanged.txt"
    changed.write_text("value = 1\n", encoding="utf-8")
    unchanged.write_text("stable\n", encoding="utf-8")
    old = build_snapshot(tmp_path)

    changed.write_text("value = 2\n", encoding="utf-8")
    new = build_snapshot(tmp_path)
    diff = old.compare(new)

    assert diff.changed_files == ("changed.py",)
    assert diff.unchanged_files == ("unchanged.txt",)
    assert diff.added_files == ()
    assert diff.removed_files == ()


def test_comparison_detects_added_file(tmp_path):
    old = build_snapshot(tmp_path)
    (tmp_path / "added.py").write_text(
        "def added():\n    return 1\n", encoding="utf-8"
    )

    diff = old.compare(build_snapshot(tmp_path))

    assert diff.added_files == ("added.py",)
    assert len(diff.added_symbols) == 1
    assert diff.added_symbols[0].relative_path == "added.py"


def test_comparison_detects_removed_file(tmp_path):
    removed = tmp_path / "removed.py"
    removed.write_text("def removed():\n    return 1\n", encoding="utf-8")
    old = build_snapshot(tmp_path)
    removed.unlink()

    diff = old.compare(build_snapshot(tmp_path))

    assert diff.removed_files == ("removed.py",)
    assert len(diff.removed_symbols) == 1
    assert diff.removed_symbols[0].relative_path == "removed.py"


def test_function_body_change_preserves_symbol_id_and_changes_symbol_state(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("def run():\n    return 1\n", encoding="utf-8")
    old = build_snapshot(tmp_path)
    source.write_text("def run():\n    return 2\n", encoding="utf-8")
    new = build_snapshot(tmp_path)

    assert old.symbols[0].id == new.symbols[0].id
    assert old.symbols[0].content_hash != new.symbols[0].content_hash
    assert old.compare(new).changed_symbols == (old.symbols[0].id,)


def test_graph_order_does_not_affect_snapshot_identity(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\n\ndef run():\n    return 1\n", encoding="utf-8"
    )
    scan = ProjectScanner().scan(tmp_path)
    graph = ProjectGraphBuilder().build(scan)
    reordered = ProjectGraph(
        nodes=tuple(reversed(graph.nodes)), edges=tuple(reversed(graph.edges))
    )
    builder = SnapshotBuilder()

    first = builder.build(scan, graph=graph)
    second = builder.build(scan, graph=reordered)

    assert first.graph == second.graph
    assert first.content_hash == second.content_hash


def test_empty_project_produces_valid_immutable_snapshot_and_dict(tmp_path):
    snapshot = build_snapshot(tmp_path)

    assert snapshot.files == ()
    assert snapshot.symbols == ()
    assert snapshot.metadata.file_count == 0
    assert snapshot.metadata.symbol_count == 0
    assert snapshot.metadata.graph_node_count == 1
    assert snapshot.to_dict()["content_hash"] == snapshot.content_hash
    with pytest.raises(FrozenInstanceError):
        snapshot.project_id = "other"


def test_comparison_rejects_different_project_identities(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()

    with pytest.raises(ValueError, match="same project"):
        build_snapshot(first_root).compare(build_snapshot(second_root))


def test_builder_rejects_graph_from_different_project(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first_scan = ProjectScanner().scan(first_root)
    second_graph = ProjectGraphBuilder().build(ProjectScanner().scan(second_root))

    with pytest.raises(ValueError, match="scanned project"):
        SnapshotBuilder().build(first_scan, graph=second_graph)


@pytest.mark.parametrize(
    "bad_source",
    [
        b"def broken():\n    return 1\x00\n",
        b"def broken(\xff):\n    return 1\n",
    ],
    ids=("nul-byte", "invalid-utf8"),
)
def test_malformed_python_does_not_abort_graph_or_snapshot(tmp_path, bad_source):
    (tmp_path / "broken.py").write_bytes(bad_source)
    (tmp_path / "healthy.py").write_text(
        "def healthy():\n    return 1\n", encoding="utf-8"
    )
    scan = ProjectScanner().scan(tmp_path)

    graph = ProjectGraphBuilder().build(scan)
    snapshot = SnapshotBuilder().build(scan)

    assert {
        node.identity for node in graph.nodes_of_kind(GraphNodeKind.FILE)
    } == {"broken.py", "healthy.py"}
    assert [
        node.label for node in graph.nodes_of_kind(GraphNodeKind.SYMBOL)
    ] == ["healthy"]
    assert [symbol.id.qualified_name for symbol in snapshot.symbols] == ["healthy"]
    assert {file.relative_path for file in snapshot.files} == {
        "broken.py",
        "healthy.py",
    }


def test_graph_builder_and_snapshot_share_canonical_graph(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\n\nclass App:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )
    scan = ProjectScanner().scan(tmp_path)
    graph = ProjectGraphBuilder().build(scan)

    snapshot = SnapshotBuilder().build(scan)

    assert graph == snapshot.graph


def test_legal_fixture_preserves_phase_3_3_content_hash(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\n\nclass App:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )
    scan = ProjectScanner().scan(tmp_path)
    scan = replace(
        scan,
        project=replace(
            scan.project,
            id="phase-3.3.1-golden-project",
            name="golden-project",
        ),
    )

    snapshot = SnapshotBuilder().build(scan)

    assert snapshot.content_hash == (
        "1c5307cc3b26d24943e585a77029b9c00b7cc13955cef3eccc8b3acb9c9d5ac3"
    )


def test_compare_snapshot_with_itself_reports_only_unchanged_state(tmp_path):
    (tmp_path / "main.py").write_text(
        "def run():\n    return 1\n", encoding="utf-8"
    )
    snapshot = build_snapshot(tmp_path)

    diff = snapshot.compare(snapshot)

    assert diff.added_files == diff.removed_files == diff.changed_files == ()
    assert diff.unchanged_files == ("main.py",)
    assert diff.added_symbols == diff.removed_symbols == diff.changed_symbols == ()
    assert diff.unchanged_symbols == (snapshot.symbols[0].id,)


def test_comparison_direction_swaps_added_and_removed_state(tmp_path):
    changed = tmp_path / "changed.py"
    removed = tmp_path / "removed.py"
    changed.write_text("def changed():\n    return 1\n", encoding="utf-8")
    removed.write_text("def removed():\n    return 1\n", encoding="utf-8")
    first = build_snapshot(tmp_path)
    changed.write_text("def changed():\n    return 2\n", encoding="utf-8")
    removed.unlink()
    (tmp_path / "added.py").write_text(
        "def added():\n    return 1\n", encoding="utf-8"
    )
    second = build_snapshot(tmp_path)

    forward = first.compare(second)
    reverse = second.compare(first)

    assert forward.added_files == reverse.removed_files == ("added.py",)
    assert forward.removed_files == reverse.added_files == ("removed.py",)
    assert forward.changed_files == reverse.changed_files == ("changed.py",)
    assert forward.added_symbols == reverse.removed_symbols
    assert forward.removed_symbols == reverse.added_symbols
    assert forward.changed_symbols == reverse.changed_symbols


def test_snapshot_copies_mutable_graph_inputs(tmp_path):
    (tmp_path / "main.py").write_text(
        "def run():\n    return 1\n", encoding="utf-8"
    )
    scan = ProjectScanner().scan(tmp_path)
    graph = ProjectGraphBuilder().build(scan)
    mutable_nodes = list(graph.nodes)
    mutable_edges = list(graph.edges)
    mutable_graph = ProjectGraph(nodes=mutable_nodes, edges=mutable_edges)

    snapshot = SnapshotBuilder().build(scan, graph=mutable_graph)
    mutable_nodes.clear()
    mutable_edges.clear()

    assert snapshot.graph == graph


def test_to_dict_is_deterministic_and_json_serializable(tmp_path):
    (tmp_path / "main.py").write_text(
        "def run():\n    return 1\n", encoding="utf-8"
    )
    scan = ProjectScanner().scan(tmp_path)
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    builder = SnapshotBuilder()

    first = builder.build(scan, created_at=created_at).to_dict()
    second = builder.build(scan, created_at=created_at).to_dict()

    assert first == second
    assert json.loads(json.dumps(first, sort_keys=True)) == first
