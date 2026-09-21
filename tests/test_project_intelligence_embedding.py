import math
import random
from dataclasses import replace

import pytest

from code_maintenance.domain import SymbolId, SymbolKind
from project_intelligence import (
    DeterministicFakeEmbeddingProvider,
    DuplicateSemanticDocumentError,
    EmbeddingFingerprint,
    EmbeddingFingerprintError,
    EmbeddingVector,
    EmbeddingVectorError,
    SemanticIndex,
    SemanticRetrievalError,
)
from project_intelligence.domain import RetrievalDocument


def _doc(name: str, source: str, line: int = 1) -> RetrievalDocument:
    symbol_id = SymbolId("python", f"{name}.py", name, SymbolKind.FUNCTION, fallback_line=line)
    return RetrievalDocument(
        symbol_id=symbol_id,
        language="python",
        relative_path=f"{name}.py",
        qualified_name=name,
        kind=SymbolKind.FUNCTION,
        signature=None,
        source_text=source,
        documentation_text=None,
        content_hash=f"hash-{name}",
        start_line=line,
        end_line=line,
    )


def test_fingerprint_is_deterministic_and_sensitive_to_every_identity_field():
    fingerprint = EmbeddingFingerprint("fake", "repo", "rev", 3)
    assert fingerprint.fingerprint_hash == EmbeddingFingerprint("fake", "repo", "rev", 3).fingerprint_hash
    for field in (
        "runtime_kind",
        "model_repository",
        "revision",
        "dimension",
        "normalization",
        "similarity_metric",
        "query_instruction",
        "document_instruction",
        "max_input_policy",
    ):
        value = getattr(fingerprint, field)
        if field in {
            "normalization",
            "similarity_metric",
            "query_instruction",
            "document_instruction",
        }:
            with pytest.raises(EmbeddingFingerprintError):
                replace(fingerprint, fingerprint_hash=None, **{field: value + "-changed"})
            continue
        changed = replace(
            fingerprint,
            fingerprint_hash=None,
            **{field: value + "-changed" if isinstance(value, str) else value + 1},
        )
        assert changed.fingerprint_hash != fingerprint.fingerprint_hash


def test_fingerprint_rejects_bool_dimension_and_hash_mismatch():
    with pytest.raises(EmbeddingFingerprintError):
        EmbeddingFingerprint("fake", "repo", "rev", True)
    with pytest.raises(EmbeddingFingerprintError):
        EmbeddingFingerprint("fake", "repo", "rev", 3, fingerprint_hash="bad")
    with pytest.raises(EmbeddingFingerprintError):
        EmbeddingFingerprint("fake", "repo", "rev", 3, normalization="unit")


def test_vector_contract_is_finite_exact_dimension_nonzero_and_immutable():
    vector = EmbeddingVector((1, 2, 3), 3)
    assert vector.values == (1.0, 2.0, 3.0)
    with pytest.raises(EmbeddingVectorError):
        EmbeddingVector((1, 2), 3)
    with pytest.raises(EmbeddingVectorError):
        EmbeddingVector((0, 0), 2)
    with pytest.raises(EmbeddingVectorError):
        EmbeddingVector((math.nan, 1), 2)
    with pytest.raises(EmbeddingVectorError):
        EmbeddingVector((math.inf, 1), 2)
    with pytest.raises(EmbeddingVectorError):
        EmbeddingVector((True, 1), 2)
    with pytest.raises((AttributeError, TypeError)):
        vector.values = (4.0, 5.0, 6.0)


def test_fake_provider_is_deterministic_and_separates_query_document_paths():
    provider = DeterministicFakeEmbeddingProvider(dimension=4)
    assert provider.embed_query("same").values == provider.embed_query("same").values
    assert provider.embed_query("same").values != provider.embed_query("different").values
    assert provider.embed_query("same").values != provider.embed_documents(("same",))[0].values
    assert provider.embed_documents(("a", "b"))[0].values == provider.embed_documents(("a", "b"))[0].values


def test_semantic_index_uses_fair_document_text_and_exact_search():
    provider = DeterministicFakeEmbeddingProvider(dimension=4)
    index = SemanticIndex((_doc("a", "alpha"), _doc("b", "beta")), provider)
    assert index.document_count == 2
    assert index.documents == tuple(sorted(index.documents, key=lambda d: str(d.symbol_id)))
    hits = index.search("alpha", top_k=1)
    assert len(hits) == 1
    assert hits[0].rank == 1
    assert math.isfinite(hits[0].score)
    assert hits[0].fingerprint == provider.fingerprint
    assert index.search(" ") == ()
    with pytest.raises(SemanticRetrievalError):
        index.search("alpha", top_k=True)


def test_empty_corpus_and_duplicate_identity_fail_closed():
    provider = DeterministicFakeEmbeddingProvider(dimension=3)
    empty = SemanticIndex((), provider)
    assert empty.search("anything") == ()
    duplicate = _doc("same", "x")
    with pytest.raises(DuplicateSemanticDocumentError):
        SemanticIndex((duplicate, duplicate), provider)


def test_index_is_order_independent_and_ties_use_symbol_id():
    provider = DeterministicFakeEmbeddingProvider(dimension=5)
    docs = (_doc("z", "same"), _doc("a", "same"), _doc("m", "same"))
    first = SemanticIndex(docs, provider).search("same")
    second = SemanticIndex(tuple(reversed(docs)), provider).search("same")
    assert [(hit.symbol_id, hit.rank, hit.score) for hit in first] == [
        (hit.symbol_id, hit.rank, hit.score) for hit in second
    ]


def test_repeated_searches_and_one_hundred_corpus_permutations_are_identical():
    provider = DeterministicFakeEmbeddingProvider(dimension=5)
    docs = tuple(_doc(name, name) for name in ("a", "b", "c", "d"))
    expected = SemanticIndex(docs, provider).search("a")
    for _ in range(100):
        assert SemanticIndex(tuple(random.Random(_).sample(docs, len(docs))), provider).search("a") == expected
    stable = SemanticIndex(docs, provider)
    for _ in range(100):
        assert stable.search("a") == expected


class _FailingProvider(DeterministicFakeEmbeddingProvider):
    def embed_documents(self, texts):
        raise RuntimeError("source should not appear")


class _BadCountProvider(DeterministicFakeEmbeddingProvider):
    def embed_documents(self, texts):
        return ()


class _BadVectorProvider(DeterministicFakeEmbeddingProvider):
    def embed_documents(self, texts):
        return ((0.0,) * self.fingerprint.dimension for _ in texts)


class _BadDimensionProvider(DeterministicFakeEmbeddingProvider):
    def embed_documents(self, texts):
        return ((0.0, 1.0) for _ in texts)


class _DriftingProvider(DeterministicFakeEmbeddingProvider):
    @property
    def fingerprint(self):
        value = super().fingerprint
        if getattr(self, "_drift", False):
            return replace(value, revision="drifted", fingerprint_hash=None)
        return value

    def embed_documents(self, texts):
        self._drift = True
        return super().embed_documents(texts)


def test_provider_failure_invalid_vector_count_and_vector_are_stable_errors():
    for provider in (
        _FailingProvider(),
        _BadCountProvider(),
        _BadVectorProvider(),
        _BadDimensionProvider(),
    ):
        with pytest.raises(SemanticRetrievalError) as error:
            SemanticIndex((_doc("a", "x"),), provider)
        assert "source should not appear" not in str(error.value)


def test_fingerprint_drift_aborts_atomic_build_and_query():
    with pytest.raises(SemanticRetrievalError, match="fingerprint"):
        SemanticIndex((_doc("a", "x"),), _DriftingProvider())
    provider = DeterministicFakeEmbeddingProvider(dimension=3)
    index = SemanticIndex((_doc("a", "x"),), provider)
    provider._fingerprint = replace(provider.fingerprint, revision="drifted", fingerprint_hash=None)
    with pytest.raises(SemanticRetrievalError, match="fingerprint"):
        index.search("x")


def test_cosine_oracle_with_controlled_provider():
    class OracleProvider:
        fingerprint = EmbeddingFingerprint("oracle", "test", "1", 2)

        def embed_documents(self, texts):
            return ((1.0, 0.0), (-1.0, 0.0))

        def embed_query(self, text):
            return (1.0, 0.0)

    hits = SemanticIndex((_doc("positive", "x"), _doc("negative", "y")), OracleProvider()).search("q")
    assert hits[0].score == pytest.approx(1.0)
    assert hits[1].score == pytest.approx(-1.0)


def test_index_does_not_mutate_corpus_documents():
    documents = (_doc("a", "x"), _doc("b", "y"))
    snapshot = tuple(documents)
    SemanticIndex(documents, DeterministicFakeEmbeddingProvider())
    assert documents == snapshot
