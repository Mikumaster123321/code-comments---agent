import ast
import random
import time
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from code_maintenance import (
    FileState,
    GraphNode,
    GraphNodeKind,
    GraphRelationKind,
    ProjectGraph,
    ProjectScanner,
    ProjectSnapshot,
    SnapshotBuilder,
    SnapshotMetadata,
    SymbolId,
    SymbolKind,
    SymbolState,
)
from project_intelligence import (
    BM25Config,
    DeterministicFakeEmbeddingProvider,
    EmbeddingFingerprintMismatchError,
    GraphExpansionConfig,
    GraphTraversalDirection,
    IncrementalIndexPlan,
    IndexBuildError,
    IndexSnapshotMismatchError,
    RetrievalConfig,
    RetrievalConfigMismatchError,
    RetrievalDocument,
    RetrievalIndex,
    RetrievalIndexIdentity,
)
from project_intelligence.corpus import CorpusBuilder
import project_intelligence.index as index_module


class SpyProvider(DeterministicFakeEmbeddingProvider):
    def __init__(self):
        super().__init__(dimension=8)
        self.calls = []

    def embed_documents(self, texts):
        self.calls.extend(texts)
        return super().embed_documents(texts)


def state(root):
    snapshot = SnapshotBuilder().build(ProjectScanner().scan(root))
    documents = CorpusBuilder().build(root, snapshot)
    return snapshot, documents


def test_identity_and_config_are_deterministic_and_path_free(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    snapshot, documents = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    first = RetrievalIndexIdentity.for_snapshot(snapshot, config)
    second = RetrievalIndexIdentity.for_snapshot(snapshot, config)
    assert first == second
    assert first.identity_hash == second.identity_hash
    assert str(tmp_path) not in repr(first)
    assert documents[0].content_hash == snapshot.symbols[0].content_hash


def test_identity_is_immutable_and_sensitive_to_every_authoritative_field(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    snapshot, _ = state(tmp_path)
    base = RetrievalIndexIdentity.for_snapshot(snapshot, RetrievalConfig())
    variants = (
        replace(base, project_id="other"),
        replace(base, snapshot_content_hash="other"),
        replace(base, retrieval_config_hash="other"),
    )
    assert len({base.identity_hash, *(item.identity_hash for item in variants)}) == 4
    with pytest.raises(FrozenInstanceError):
        base.project_id = "mutated"


def test_config_hash_covers_lexical_embedding_and_graph_semantics():
    provider = SpyProvider()
    configs = (
        RetrievalConfig(),
        RetrievalConfig(lexical_config=BM25Config(k1=1.2)),
        RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint),
        RetrievalConfig(graph_expansion_config=GraphExpansionConfig(max_hops=2)),
    )
    assert len({config.identity_hash for config in configs}) == len(configs)


def test_plan_maps_snapshot_diff_to_stable_operations(tmp_path):
    path = tmp_path / "a.py"
    path.write_text("def alpha():\n    return 1\n", encoding="utf-8")
    old, _ = state(tmp_path)
    path.write_text("def alpha():\n    return 2\n\ndef beta():\n    return 3\n", encoding="utf-8")
    new, _ = state(tmp_path)
    plan = IncrementalIndexPlan.from_diff(old, new)
    assert len(plan.changed) == 1
    assert len(plan.added) == 1
    assert [operation.action for operation in plan.operations] == ["add", "replace"]


def test_incremental_update_reuses_unchanged_and_matches_full_rebuild(tmp_path):
    first_path = tmp_path / "first.py"
    second_path = tmp_path / "second.py"
    first_path.write_text("def first():\n    return 1\n", encoding="utf-8")
    second_path.write_text("def second():\n    return 2\n", encoding="utf-8")
    old, old_docs = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    old_index = RetrievalIndex.build(old, old_docs, config, provider=provider)
    assert len(provider.calls) == 2

    first_path.write_text("def first():\n    return 9\n", encoding="utf-8")
    (tmp_path / "third.py").write_text("def third():\n    return 3\n", encoding="utf-8")
    second_path.unlink()
    new, new_docs = state(tmp_path)
    updated = old_index.update(new, new_docs)
    assert len(provider.calls) == 4  # one changed + one added; unchanged was reused

    rebuild_provider = SpyProvider()
    rebuilt = RetrievalIndex.build(new, new_docs, config, provider=rebuild_provider)
    assert updated.documents == rebuilt.documents
    assert updated.identity == rebuilt.identity
    assert updated.lexical_search("return", 10) == rebuilt.lexical_search("return", 10)
    assert updated.semantic_search("return", 10) == rebuilt.semantic_search("return", 10)


def test_fingerprint_and_config_changes_fail_closed(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    snapshot, docs = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    index = RetrievalIndex.build(snapshot, docs, config, provider=provider)
    changed = RetrievalConfig(lexical_config=BM25Config(k1=1.2))
    with pytest.raises(RetrievalConfigMismatchError):
        index.update(snapshot, docs, config=changed)
    other_provider = DeterministicFakeEmbeddingProvider(dimension=9)
    with pytest.raises(EmbeddingFingerprintMismatchError):
        index.update(snapshot, docs, provider=other_provider)


def test_old_index_remains_usable_after_failed_update(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    snapshot, docs = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    index = RetrievalIndex.build(snapshot, docs, config, provider=provider)
    bad = replace(docs[0], content_hash="0" * 64)
    with pytest.raises(Exception):
        index.update(snapshot, (bad,))
    assert index.documents == docs
    assert index.semantic_search("alpha")


def test_snapshot_mismatch_duplicate_and_stale_diff_fail_closed(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    first, documents = state(tmp_path)
    with pytest.raises(IndexBuildError, match="duplicate"):
        RetrievalIndex.build(first, (*documents, documents[0]))
    (tmp_path / "a.py").write_text("def alpha():\n    return 2\n", encoding="utf-8")
    second, second_documents = state(tmp_path)
    index = RetrievalIndex.build(first, documents)
    with pytest.raises(IndexSnapshotMismatchError):
        index.update(second, documents)
    empty_diff = first.compare(first)
    with pytest.raises(IndexSnapshotMismatchError, match="SnapshotDiff"):
        index.update(second, second_documents, diff=empty_diff)


def test_provider_failure_is_atomic(tmp_path):
    class FailingProvider(SpyProvider):
        def embed_documents(self, texts):
            raise RuntimeError("secret provider detail")

    path = tmp_path / "a.py"
    path.write_text("def alpha():\n    return 1\n", encoding="utf-8")
    first, documents = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    index = RetrievalIndex.build(first, documents, config, provider=provider)
    path.write_text("def alpha():\n    return 2\n", encoding="utf-8")
    second, second_documents = state(tmp_path)
    with pytest.raises(IndexBuildError, match="RuntimeError"):
        index.update(second, second_documents, provider=FailingProvider())
    assert index.snapshot == first
    assert index.documents == documents


def test_lexical_only_build_and_update_never_require_provider(tmp_path):
    path = tmp_path / "a.py"
    path.write_text("def alpha():\n    return 1\n", encoding="utf-8")
    first, documents = state(tmp_path)
    index = RetrievalIndex.build(first, documents)
    path.write_text("def alpha():\n    return 2\n", encoding="utf-8")
    second, second_documents = state(tmp_path)
    updated = index.update(second, second_documents)
    assert updated.lexical_search("alpha")
    assert updated.vectors == ()


def test_build_is_independent_of_100_document_input_permutations(tmp_path):
    (tmp_path / "many.py").write_text(
        "\n\n".join(f"def fn_{number}():\n    return {number}" for number in range(12)) + "\n",
        encoding="utf-8",
    )
    snapshot, documents = state(tmp_path)
    expected = RetrievalIndex.build(snapshot, documents).documents
    randomizer = random.Random(310)
    for _ in range(100):
        shuffled = list(documents)
        randomizer.shuffle(shuffled)
        assert RetrievalIndex.build(snapshot, shuffled).documents == expected


def test_embedding_call_accounting_for_100_symbol_fixture(tmp_path):
    values = {f"fn_{number}": number for number in range(100)}

    def write_values():
        (tmp_path / "many.py").write_text(
            "\n\n".join(
                f"def {name}():\n    return {value}" for name, value in sorted(values.items())
            )
            + "\n",
            encoding="utf-8",
        )

    write_values()
    first, documents = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    index = RetrievalIndex.build(first, documents, config, provider=provider)
    assert len(provider.calls) == 100
    for number in range(5):
        values[f"fn_{number}"] += 1000
    del values["fn_5"]
    del values["fn_6"]
    values.update({"new_a": 1, "new_b": 2, "new_c": 3})
    write_values()
    second, second_documents = state(tmp_path)
    index.update(second, second_documents)
    assert len(provider.calls) == 108


def test_phase_four_production_modules_keep_dependency_boundary():
    allowed_roots = {
        "__future__",
        "code_maintenance",
        "dataclasses",
        "enum",
        "hashlib",
        "json",
        "math",
        "pathlib",
        "types",
        "typing",
    }
    for filename in ("index.py", "graph_expansion.py"):
        source = (Path(__file__).parents[1] / "project_intelligence" / filename).read_text()
        tree = ast.parse(source)
        roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        roots.update(
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
        )
        assert roots <= allowed_roots


def _synthetic_symbol_id(index):
    return SymbolId("python", f"pkg/mod_{index // 100}.py", f"fn_{index}", SymbolKind.FUNCTION)


def _synthetic_document(symbol_id, content_hash, payload):
    return RetrievalDocument(
        symbol_id=symbol_id,
        language=symbol_id.language,
        relative_path=symbol_id.relative_path,
        qualified_name=symbol_id.qualified_name,
        kind=symbol_id.kind,
        signature=None,
        source_text=f"def {symbol_id.qualified_name}(): return {payload}",
        documentation_text=None,
        content_hash=content_hash,
        start_line=1,
        end_line=1,
    )


def synthetic_state(count, revision="r1", *, changed=(), removed=(), extra=()):
    """Build a synthetic snapshot/document pair without touching the file system.

    Only the ``changed``/``removed``/``extra`` indices move between revisions, so
    every other symbol keeps an identical ``content_hash`` and ``source_text``.
    """
    changed = set(changed)
    removed = set(removed)
    indices = sorted(set(range(count)) - removed) + sorted(extra)
    symbols = []
    documents = []
    for index in indices:
        symbol_id = _synthetic_symbol_id(index)
        marker = "changed" if index in changed else "stable"
        content_hash = f"hash-{marker}-{index}"
        symbols.append(SymbolState(symbol_id, content_hash))
        documents.append(_synthetic_document(symbol_id, content_hash, f"value_{marker}_{index}"))
    hashes_by_path = {}
    for symbol in symbols:
        hashes_by_path.setdefault(symbol.id.relative_path, []).append(symbol.content_hash)
    files = tuple(
        FileState(path, "python", "|".join(sorted(hashes)))
        for path, hashes in sorted(hashes_by_path.items())
    )
    snapshot = ProjectSnapshot(
        project_id="synthetic-project",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        files=files,
        symbols=tuple(symbols),
        graph=ProjectGraph((), ()),
        content_hash=f"synthetic-snapshot-{revision}",
        metadata=SnapshotMetadata(
            file_count=len(files),
            symbol_count=len(symbols),
            graph_node_count=0,
            graph_edge_count=0,
        ),
    )
    return snapshot, tuple(documents)


def _entries_by_symbol_id(index):
    return {document.symbol_id: vector for document, vector in index.entries}


class _CountingTuple(tuple):
    """Tuple that records how often membership is tested against it."""

    def __new__(cls, values):
        instance = super().__new__(cls, values)
        instance.contains_calls = 0
        return instance

    def __contains__(self, item):
        self.contains_calls += 1
        return super().__contains__(item)


class _RecordingPlanFactory:
    """Plan factory that hands ``update`` a countable ``unchanged`` tuple."""

    last_unchanged = None

    @classmethod
    def from_diff(cls, old, new, diff=None):
        plan = IncrementalIndexPlan.from_diff(old, new, diff)
        counting = _CountingTuple(plan.unchanged)
        cls.last_unchanged = counting
        return IncrementalIndexPlan(
            source_snapshot_hash=plan.source_snapshot_hash,
            target_snapshot_hash=plan.target_snapshot_hash,
            added=plan.added,
            removed=plan.removed,
            changed=plan.changed,
            unchanged=counting,
        )


def test_incremental_plan_keeps_public_immutable_tuple_contract(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    snapshot, _ = state(tmp_path)
    plan = IncrementalIndexPlan.from_diff(snapshot, snapshot)
    for name in ("added", "removed", "changed", "unchanged"):
        assert type(getattr(plan, name)) is tuple
    assert plan.unchanged_symbols is plan.unchanged
    with pytest.raises(FrozenInstanceError):
        plan.unchanged = ()


def test_update_looks_up_unchanged_symbols_without_per_document_tuple_scan(monkeypatch):
    snapshot, documents = synthetic_state(600)
    index = RetrievalIndex.build(snapshot, documents)
    monkeypatch.setattr(index_module, "IncrementalIndexPlan", _RecordingPlanFactory)
    _RecordingPlanFactory.last_unchanged = None
    updated = index.update(snapshot, documents)
    counting = _RecordingPlanFactory.last_unchanged
    assert isinstance(counting, tuple)
    assert len(counting) == 600
    assert counting.contains_calls == 0
    assert len(updated.documents) == len(documents)
    assert {item.symbol_id for item in updated.documents} == {
        item.symbol_id for item in documents
    }
    assert updated is not index


def test_large_incremental_update_matches_full_rebuild_and_reuses_vectors():
    count = 5000
    changed = (1, 2, 3)
    removed = (10, 11)
    extra = (count, count + 1)
    old_snapshot, old_documents = synthetic_state(count)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    old_index = RetrievalIndex.build(old_snapshot, old_documents, config, provider=provider)
    assert len(provider.calls) == count

    new_snapshot, new_documents = synthetic_state(
        count, "r2", changed=changed, removed=removed, extra=extra
    )
    updated = old_index.update(new_snapshot, new_documents)
    assert len(new_documents) == count
    # only changed + added symbols are embedded; unchanged and removed never are
    assert len(provider.calls) == count + len(changed) + len(extra)

    rebuild_provider = SpyProvider()
    rebuilt = RetrievalIndex.build(new_snapshot, new_documents, config, provider=rebuild_provider)
    assert updated.identity == rebuilt.identity
    assert updated.documents == rebuilt.documents
    assert [item.content_hash for item in updated.documents] == [
        item.content_hash for item in rebuilt.documents
    ]
    assert updated.entries == rebuilt.entries
    assert updated.vectors == rebuilt.vectors
    assert updated.lexical_search("return stable", 20) == rebuilt.lexical_search("return stable", 20)
    assert updated.semantic_search("return stable", 20) == rebuilt.semantic_search("return stable", 20)

    old_vectors = _entries_by_symbol_id(old_index)
    new_vectors = _entries_by_symbol_id(updated)
    rebuilt_vectors = _entries_by_symbol_id(rebuilt)
    for index in (0, 4, 100, count - 1):
        symbol_id = _synthetic_symbol_id(index)
        assert new_vectors[symbol_id] is old_vectors[symbol_id]
    for index in changed:
        symbol_id = _synthetic_symbol_id(index)
        assert new_vectors[symbol_id] is not old_vectors[symbol_id]
        assert new_vectors[symbol_id] == rebuilt_vectors[symbol_id]
    for index in removed:
        assert _synthetic_symbol_id(index) not in new_vectors


def test_large_incremental_update_performance_smoke():
    count = 5000
    snapshot, documents = synthetic_state(count)
    index = RetrievalIndex.build(snapshot, documents)

    start = time.perf_counter()
    index.update(snapshot, documents)
    incremental_seconds = time.perf_counter() - start

    start = time.perf_counter()
    RetrievalIndex.build(snapshot, documents)
    rebuild_seconds = time.perf_counter() - start

    # No absolute millisecond gate: an unchanged-only incremental update must stay
    # in the same order of magnitude as a full rebuild instead of degrading ~O(N^2).
    assert incremental_seconds < max(rebuild_seconds * 5, 1.5)


def test_structural_nodes_are_context_only_and_consume_expansion_budget(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    snapshot, documents = state(tmp_path)
    index = RetrievalIndex.build(snapshot, documents)

    result = index.expand_graph([documents[0].symbol_id])
    file_candidates = [item for item in result.candidates if item.node.kind == GraphNodeKind.FILE]
    assert file_candidates
    assert file_candidates[0].document is None
    assert file_candidates[0].provenance.relation is GraphRelationKind.CONTAINS
    assert file_candidates[0].provenance.direction is GraphTraversalDirection.REVERSE

    deeper = index.expand_graph(
        [documents[0].symbol_id], config=GraphExpansionConfig(max_hops=2)
    )
    project_candidates = [
        item for item in deeper.candidates if item.node.kind == GraphNodeKind.PROJECT
    ]
    assert project_candidates
    assert project_candidates[0].document is None
    assert len(deeper.candidates) <= 30

    file_seed = GraphNode(
        GraphNodeKind.FILE, documents[0].relative_path, documents[0].relative_path
    )
    from_file = index.expand_graph([file_seed])
    project_from_file = [
        item for item in from_file.candidates if item.node.kind == GraphNodeKind.PROJECT
    ]
    assert project_from_file
    assert project_from_file[0].document is None
    assert project_from_file[0].provenance.direction is GraphTraversalDirection.REVERSE


def test_graph_expansion_does_not_change_lexical_or_semantic_scores(tmp_path):
    (tmp_path / "a.py").write_text(
        "def alpha():\n    return 1\n\ndef beta():\n    return alpha()\n", encoding="utf-8"
    )
    (tmp_path / "b.py").write_text("def gamma():\n    return 2\n", encoding="utf-8")
    snapshot, documents = state(tmp_path)
    provider = SpyProvider()
    config = RetrievalConfig(embedding_enabled=True, embedding_fingerprint=provider.fingerprint)
    index = RetrievalIndex.build(snapshot, documents, config, provider=provider)
    lexical_before = index.lexical_search("return", 10)
    semantic_before = index.semantic_search("return", 10)
    assert lexical_before and semantic_before

    assert index.expand_graph([documents[0].symbol_id]).candidates

    assert index.lexical_search("return", 10) == lexical_before
    assert index.semantic_search("return", 10) == semantic_before
    assert index.documents == documents
    assert index.snapshot == snapshot
