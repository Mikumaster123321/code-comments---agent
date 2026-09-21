import ast
import random
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from code_maintenance import ProjectScanner, SnapshotBuilder
from project_intelligence import (
    BM25Config,
    DeterministicFakeEmbeddingProvider,
    EmbeddingFingerprintMismatchError,
    GraphExpansionConfig,
    IncrementalIndexPlan,
    IndexBuildError,
    IndexSnapshotMismatchError,
    RetrievalConfig,
    RetrievalConfigMismatchError,
    RetrievalIndex,
    RetrievalIndexIdentity,
)
from project_intelligence.corpus import CorpusBuilder


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
