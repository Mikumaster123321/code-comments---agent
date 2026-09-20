import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path

import pytest

from code_maintenance import (
    ProjectScanner,
    SnapshotBuilder,
    SourceFile,
    SymbolId,
    SymbolKind,
)
from code_maintenance.adapters import PythonAdapter
from project_intelligence import (
    CorpusBuildError,
    CorpusBuilder,
    CorpusIOError,
    CorpusSnapshotMismatchError,
    DuplicateRetrievalDocumentError,
    RetrievalDocument,
)


def build_snapshot(root: Path):
    return SnapshotBuilder().build(ProjectScanner().scan(root))


def build_corpus(root: Path, snapshot=None):
    snapshot = snapshot if snapshot is not None else build_snapshot(root)
    return CorpusBuilder().build(root, snapshot)


def symbol_order_key(symbol_id):
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        symbol_id.semantic_disambiguator or "",
        symbol_id.fallback_line if symbol_id.fallback_line is not None else -1,
    )


def write_python_project(root: Path) -> str:
    source = '''\
def decorator(function):
    return function


@decorator
def top(value):
    """Return the supplied value."""
    return value


class First:
    def run(self):
        return "first"

    class Nested:
        def work(self):
            return 1


class Second:
    def run(self):
        return "second"
'''
    (root / "main.py").write_text(source, encoding="utf-8")
    return source


def test_retrieval_document_is_immutable_and_identity_aligned():
    symbol_id = SymbolId("python", "main.py", "run", SymbolKind.FUNCTION)
    document = RetrievalDocument(
        symbol_id=symbol_id,
        language="python",
        relative_path="main.py",
        qualified_name="run",
        kind=SymbolKind.FUNCTION,
        signature="run()",
        source_text="def run():\n    pass",
        documentation_text=None,
        content_hash="a" * 64,
        start_line=1,
        end_line=2,
    )

    with pytest.raises(FrozenInstanceError):
        document.source_text = "changed"
    with pytest.raises(ValueError, match="language must match"):
        replace(document, language="java")
    with pytest.raises(ValueError, match="positive integer"):
        replace(document, start_line=True)
    with pytest.raises(ValueError, match="at or after"):
        replace(document, end_line=0)


def test_python_corpus_preserves_symbols_source_ranges_signatures_and_hashes(tmp_path):
    source = write_python_project(tmp_path)
    snapshot = build_snapshot(tmp_path)

    documents = CorpusBuilder().build(tmp_path, snapshot)
    by_name = {document.qualified_name: document for document in documents}

    assert [document.symbol_id for document in documents] == sorted(
        (state.id for state in snapshot.symbols), key=symbol_order_key
    )
    assert by_name["top"].signature == "top(value)"
    assert by_name["top"].source_text.startswith("def top(value):")
    assert "@decorator" not in by_name["top"].source_text
    assert '"""Return the supplied value."""' in by_name["top"].source_text
    assert by_name["First"].kind is SymbolKind.CLASS
    assert by_name["First.run"].kind is SymbolKind.METHOD
    assert by_name["Second.run"].symbol_id != by_name["First.run"].symbol_id
    assert by_name["First.Nested.work"].source_text == (
        "        def work(self):\n            return 1"
    )
    for document in documents:
        expected_source = "\n".join(
            source.splitlines()[document.start_line - 1 : document.end_line]
        )
        assert document.source_text == expected_source
        assert document.content_hash == sha256(
            document.source_text.encode("utf-8")
        ).hexdigest()
        assert document.documentation_text is None


def test_nested_python_function_respects_existing_adapter_limit(tmp_path):
    (tmp_path / "main.py").write_text(
        "def outer():\n    def inner():\n        return 1\n    return inner()\n",
        encoding="utf-8",
    )

    documents = build_corpus(tmp_path)

    assert [document.qualified_name for document in documents] == ["outer"]
    assert "def inner():" in documents[0].source_text


def test_java_corpus_preserves_classes_methods_overloads_and_source(tmp_path):
    source = '''\
package example;

import java.util.List;

public class First {
    int find(int value) { return value; }
    String find(String value) { return value; }
}

class Second {
    void run() {}
}
'''
    (tmp_path / "First.java").write_text(source, encoding="utf-8")

    documents = build_corpus(tmp_path)
    overloads = [document for document in documents if document.qualified_name == "First.find"]

    assert {document.signature for document in overloads} == {"find(int)", "find(String)"}
    assert overloads[0].symbol_id != overloads[1].symbol_id
    assert all(document.symbol_id.semantic_disambiguator == document.signature for document in overloads)
    assert next(document for document in documents if document.qualified_name == "First").source_text.startswith(
        "public class First"
    )
    assert next(document for document in documents if document.qualified_name == "Second.run").source_text == (
        "    void run() {}"
    )
    assert all("package example" not in document.source_text for document in documents)


def test_non_ascii_source_uses_existing_utf8_policy(tmp_path):
    (tmp_path / "unicode.py").write_text(
        'def greet(name):\n    """问候。"""\n    return f"你好，{name}"\n',
        encoding="utf-8",
    )

    document = build_corpus(tmp_path)[0]

    assert "问候" in document.source_text
    assert "你好" in document.source_text
    assert document.content_hash == sha256(document.source_text.encode("utf-8")).hexdigest()


def test_empty_project_builds_empty_immutable_corpus(tmp_path):
    documents = build_corpus(tmp_path)

    assert documents == ()
    assert isinstance(documents, tuple)


def test_unsupported_files_are_validated_but_not_added_to_symbol_corpus(tmp_path):
    data = tmp_path / "notes.md"
    data.write_text("# Notes\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)

    assert CorpusBuilder().build(tmp_path, snapshot) == ()

    data.write_text("# Changed\n", encoding="utf-8")
    with pytest.raises(CorpusSnapshotMismatchError, match="file content hash differs"):
        CorpusBuilder().build(tmp_path, snapshot)


def test_repeated_builds_are_deterministic_and_preserve_symbol_ids(tmp_path):
    write_python_project(tmp_path)
    snapshot = build_snapshot(tmp_path)
    builder = CorpusBuilder()

    builds = [builder.build(tmp_path, snapshot) for _ in range(100)]

    assert all(build == builds[0] for build in builds)
    assert all(repr(build).encode("utf-8") == repr(builds[0]).encode("utf-8") for build in builds)
    assert tuple(document.symbol_id for document in builds[0]) == tuple(
        sorted((state.id for state in snapshot.symbols), key=symbol_order_key)
    )


def test_snapshot_input_order_does_not_affect_canonical_output(tmp_path):
    write_python_project(tmp_path)
    snapshot = build_snapshot(tmp_path)
    reordered = replace(
        snapshot,
        files=tuple(reversed(snapshot.files)),
        symbols=tuple(reversed(snapshot.symbols)),
    )

    assert CorpusBuilder().build(tmp_path, reordered) == CorpusBuilder().build(
        tmp_path, snapshot
    )


def test_missing_snapshot_file_fails_closed_without_partial_corpus(tmp_path):
    write_python_project(tmp_path)
    (tmp_path / "second.py").write_text("def second():\n    return 2\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    (tmp_path / "second.py").unlink()

    with pytest.raises(CorpusSnapshotMismatchError) as error:
        CorpusBuilder().build(tmp_path, snapshot)

    assert "second.py" in str(error.value)
    assert "missing" in str(error.value)


def test_changed_file_after_snapshot_fails_closed(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("def run():\n    return 1\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    source.write_text("def run():\n    return 2\n", encoding="utf-8")

    with pytest.raises(CorpusSnapshotMismatchError, match="file content hash differs"):
        CorpusBuilder().build(tmp_path, snapshot)


def test_file_added_after_snapshot_is_not_added_to_old_corpus(tmp_path):
    (tmp_path / "main.py").write_text("def old():\n    return 1\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    expected = CorpusBuilder().build(tmp_path, snapshot)
    (tmp_path / "new.py").write_text("def new():\n    return 2\n", encoding="utf-8")

    actual = CorpusBuilder().build(tmp_path, snapshot)

    assert actual == expected
    assert [document.qualified_name for document in actual] == ["old"]


def test_symbol_hash_mismatch_is_rejected_even_when_file_hash_matches(tmp_path):
    (tmp_path / "main.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    altered = replace(
        snapshot,
        symbols=(replace(snapshot.symbols[0], content_hash="0" * 64),),
    )

    with pytest.raises(CorpusSnapshotMismatchError) as error:
        CorpusBuilder().build(tmp_path, altered)

    message = str(error.value)
    assert "symbol content hash differs" in message
    assert "python:main.py:run:function" in message
    assert "return 1" not in message


def test_missing_and_unexpected_symbol_sets_are_rejected(tmp_path):
    (tmp_path / "main.py").write_text(
        "def first():\n    pass\n\ndef second():\n    pass\n", encoding="utf-8"
    )
    snapshot = build_snapshot(tmp_path)
    without_second = replace(snapshot, symbols=snapshot.symbols[:1])

    with pytest.raises(CorpusSnapshotMismatchError, match="absent from snapshot"):
        CorpusBuilder().build(tmp_path, without_second)

    missing_id = SymbolId("python", "main.py", "missing", SymbolKind.FUNCTION)
    with_missing = replace(
        snapshot,
        symbols=(replace(snapshot.symbols[0], id=missing_id), snapshot.symbols[1]),
    )
    with pytest.raises(CorpusSnapshotMismatchError, match="expected symbol is missing"):
        CorpusBuilder().build(tmp_path, with_missing)


def test_duplicate_symbol_from_adapter_fails_closed(tmp_path):
    source = "def run():\n    return 1\n"
    (tmp_path / "main.py").write_text(source, encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    symbol = PythonAdapter().parse_symbols(
        SourceFile(snapshot.project_id, "main.py", "python", source)
    )[0]

    class DuplicateAdapter:
        def parse_symbols(self, _source_file):
            return [symbol, symbol]

    with pytest.raises(DuplicateRetrievalDocumentError, match="run:function"):
        CorpusBuilder(adapters={"python": DuplicateAdapter()}).build(tmp_path, snapshot)


def test_duplicate_symbol_in_snapshot_is_rejected(tmp_path):
    (tmp_path / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    duplicate = replace(snapshot, symbols=(snapshot.symbols[0], snapshot.symbols[0]))

    with pytest.raises(DuplicateRetrievalDocumentError):
        CorpusBuilder().build(tmp_path, duplicate)


def test_project_root_must_match_snapshot_identity(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
    (second / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")

    with pytest.raises(CorpusSnapshotMismatchError, match="project identity"):
        CorpusBuilder().build(second, build_snapshot(first))


def test_path_traversal_like_snapshot_path_is_rejected_by_scan_scope(tmp_path):
    (tmp_path / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    escaped_file = replace(snapshot.files[0], relative_path="../main.py")
    escaped_id = replace(snapshot.symbols[0].id, relative_path="../main.py")
    escaped_symbol = replace(snapshot.symbols[0], id=escaped_id)
    escaped = replace(snapshot, files=(escaped_file,), symbols=(escaped_symbol,))

    with pytest.raises(CorpusSnapshotMismatchError, match="missing from current project scan"):
        CorpusBuilder().build(tmp_path, escaped)


def test_missing_project_root_is_exposed_as_stable_io_error(tmp_path):
    snapshot = build_snapshot(tmp_path)

    with pytest.raises(CorpusIOError) as error:
        CorpusBuilder().build(tmp_path / "missing", snapshot)

    assert str(error.value) == (
        "corpus source I/O failure: file='<project-root>', operation='scan', "
        "error='FileNotFoundError'"
    )


def test_parse_failure_is_atomic_and_does_not_expose_source(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("def run():\n    return 1\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)

    class FailingAdapter:
        def parse_symbols(self, _source_file):
            raise SyntaxError("secret source marker")

    with pytest.raises(CorpusBuildError) as error:
        CorpusBuilder(adapters={"python": FailingAdapter()}).build(tmp_path, snapshot)

    assert "SyntaxError" in str(error.value)
    assert "secret source marker" not in str(error.value)


def test_corpus_build_does_not_modify_project_files_or_snapshot(tmp_path):
    write_python_project(tmp_path)
    snapshot = build_snapshot(tmp_path)
    before_snapshot = snapshot.to_dict()
    before = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    CorpusBuilder().build(tmp_path, snapshot)

    after = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert snapshot.to_dict() == before_snapshot


def test_medium_project_performance_smoke_builds_all_symbols(tmp_path):
    for file_index in range(120):
        source = "\n\n".join(
            f"def function_{file_index}_{symbol_index}():\n    return {symbol_index}"
            for symbol_index in range(10)
        )
        (tmp_path / f"module_{file_index:03d}.py").write_text(
            source + "\n", encoding="utf-8"
        )
    snapshot = build_snapshot(tmp_path)

    documents = CorpusBuilder().build(tmp_path, snapshot)

    assert len(documents) == 1_200
    assert documents[0].relative_path == "module_000.py"
    assert documents[-1].relative_path == "module_119.py"


def _imports_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def test_dependency_direction_and_forbidden_import_guard():
    repository_root = Path(__file__).resolve().parents[1]
    forbidden = {
        "credits",
        "managed_access",
        "admin_operations",
        "llm_provider",
        "llm_service",
        "config",
        "openai",
        "gradio",
        "faiss",
        "chromadb",
        "sentence_transformers",
    }

    intelligence_imports = set().union(
        *(
            _imports_in(path)
            for path in (repository_root / "project_intelligence").glob("*.py")
        )
    )
    maintenance_imports = set().union(
        *(
            _imports_in(path)
            for path in (repository_root / "code_maintenance").glob("*.py")
        )
    )

    assert intelligence_imports.isdisjoint(forbidden)
    assert "project_intelligence" not in maintenance_imports


def test_phase_two_package_contains_only_implemented_minimum_files():
    package = Path(__file__).resolve().parents[1] / "project_intelligence"

    assert {path.name for path in package.iterdir() if path.is_file()} == {
        "__init__.py",
        "corpus.py",
        "domain.py",
        "lexical.py",
    }


@pytest.mark.parametrize(
    "marker",
    ["\u2028", "\u2029", "\f", "\x0b", "\x85"],
    ids=["line-separator", "paragraph-separator", "form-feed", "vertical-tab", "nel"],
)
def test_m1_python_physical_line_ranges_are_literal_and_hash_aligned(marker, tmp_path):
    source = (
        'def first():\n'
        f'    marker = "before{marker}after"\n'
        '    return marker\n'
        '\n'
        'def second():\n'
        '    return 2\n'
    )
    (tmp_path / "markers.py").write_text(source, encoding="utf-8")

    documents = build_corpus(tmp_path)
    first, second = [document for document in documents if document.qualified_name in {"first", "second"}]
    expected_first = "\n".join(source.split("\n")[0:3])
    expected_second = "\n".join(source.split("\n")[4:6])

    # These independent literal slices expose the old splitlines/AST mismatch;
    # the old implementation instead accepted its own incorrectly sliced hash.
    assert first.source_text == expected_first
    assert second.source_text == expected_second
    assert first.content_hash == sha256(expected_first.encode("utf-8")).hexdigest()
    assert second.content_hash == sha256(expected_second.encode("utf-8")).hexdigest()
    snapshot = build_snapshot(tmp_path)
    snapshot_hashes = {state.id: state.content_hash for state in snapshot.symbols}
    assert snapshot_hashes[first.symbol_id] == first.content_hash
    assert snapshot_hashes[second.symbol_id] == second.content_hash


def test_m2_zero_symbol_parse_failure_now_matches_snapshot_contract(tmp_path):
    (tmp_path / "good.py").write_text("def good():\n    return 1\n", encoding="utf-8")
    (tmp_path / "broken.py").write_text("def broken(\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)

    assert [state.id.qualified_name for state in snapshot.symbols] == ["good"]
    documents = CorpusBuilder().build(tmp_path, snapshot)

    assert [document.qualified_name for document in documents] == ["good"]


def test_m2_zero_symbol_unparseable_file_must_still_be_fresh(tmp_path):
    (tmp_path / "good.py").write_text("def good():\n    return 1\n", encoding="utf-8")
    broken = tmp_path / "broken.py"
    broken.write_text("def broken(\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    broken.write_text("def broken(\n# changed\n", encoding="utf-8")

    with pytest.raises(CorpusSnapshotMismatchError, match="file content hash differs"):
        CorpusBuilder().build(tmp_path, snapshot)


def test_m2_expected_symbol_parse_failure_still_fails_closed(tmp_path):
    (tmp_path / "good.py").write_text("def good():\n    return 1\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)

    class FailingAdapter:
        def parse_symbols(self, _source_file):
            raise SyntaxError("fixture parse failure")

    with pytest.raises(CorpusBuildError, match="parse failure"):
        CorpusBuilder(adapters={"python": FailingAdapter()}).build(tmp_path, snapshot)


def test_m2_good_files_and_multiple_unparseable_files_are_deterministic(tmp_path):
    (tmp_path / "good.py").write_text("def good():\n    return 1\n", encoding="utf-8")
    (tmp_path / "broken_a.py").write_text("def broken_a(\n", encoding="utf-8")
    (tmp_path / "broken_b.py").write_text("class broken_b(\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)

    first = CorpusBuilder().build(tmp_path, snapshot)
    second = CorpusBuilder().build(tmp_path, snapshot)

    assert [document.qualified_name for document in first] == ["good"]
    assert first == second


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"], ids=["lf", "crlf", "cr"])
def test_l1_java_source_reading_policy_is_consistent(newline, tmp_path):
    (tmp_path / "Example.java").write_bytes(
        b"class Example {" + newline + b"    void run() {}" + newline + b"}" + newline
    )
    snapshot = build_snapshot(tmp_path)

    documents = CorpusBuilder().build(tmp_path, snapshot)

    run = next(document for document in documents if document.qualified_name == "Example.run")
    assert run.source_text == "    void run() {}"


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"], ids=["lf", "crlf", "cr"])
def test_l1_python_source_reading_policy_is_consistent(newline, tmp_path):
    (tmp_path / "example.py").write_bytes(
        b"def run():" + newline + b"    return 1" + newline
    )
    snapshot = build_snapshot(tmp_path)

    run = next(document for document in CorpusBuilder().build(tmp_path, snapshot) if document.qualified_name == "run")
    assert run.source_text == "def run():\n    return 1"


def test_multiline_decorated_python_definition_keeps_ast_range(tmp_path):
    source = (
        "def decorator(function):\n"
        "    return function\n\n"
        "@decorator\n"
        "def decorated(\n"
        "    value,\n"
        "):\n"
        "    return value\n\n"
        "class Container:\n"
        "    def method(self):\n"
        "        return 1\n"
    )
    (tmp_path / "example.py").write_text(source, encoding="utf-8")

    documents = build_corpus(tmp_path)
    decorated = next(document for document in documents if document.qualified_name == "decorated")

    assert decorated.source_text == "\n".join(source.split("\n")[4:8])
    assert decorated.signature == "decorated(value)"
    assert "@decorator" not in decorated.source_text


def test_toctou_mutation_after_source_read_fails_final_freshness_check(tmp_path):
    source_path = tmp_path / "main.py"
    source_path.write_text("def run():\n    return 1\n", encoding="utf-8")
    snapshot = build_snapshot(tmp_path)
    delegate = PythonAdapter()

    class MutatingAdapter:
        def parse_symbols(self, source_file):
            source_path.write_text("def run():\n    return 2\n", encoding="utf-8")
            return delegate.parse_symbols(source_file)

    with pytest.raises(CorpusSnapshotMismatchError, match="file content hash differs"):
        CorpusBuilder(adapters={"python": MutatingAdapter()}).build(tmp_path, snapshot)
