"""Offline embedding contracts and exact semantic retrieval.

Phase 3.1 deliberately contains no model runtime.  ``EmbeddingProvider`` is a
small, independent port that can later be implemented by a real local model;
the production-safe tests use ``DeterministicFakeEmbeddingProvider`` only.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Protocol, Sequence, runtime_checkable

from code_maintenance.domain import SymbolId

from .domain import ProjectIntelligenceError, RetrievalDocument


DEFAULT_QUERY_INSTRUCTION = "query: "
DEFAULT_DOCUMENT_INSTRUCTION = "passage: "


class EmbeddingError(ProjectIntelligenceError):
    """Base error for the independent embedding boundary."""


class EmbeddingFingerprintError(EmbeddingError):
    """Raised for malformed or internally inconsistent provider identity."""


class EmbeddingVectorError(EmbeddingError):
    """Raised when an embedding vector violates the exact vector contract."""


class SemanticRetrievalError(EmbeddingError):
    """Stable error raised when semantic indexing or retrieval cannot complete."""


class InvalidSemanticQueryError(SemanticRetrievalError):
    """Raised for invalid query or ``top_k`` arguments."""


class DuplicateSemanticDocumentError(SemanticRetrievalError):
    """Raised when authoritative ``SymbolId`` identity is repeated."""

    def __init__(self, symbol_id: SymbolId) -> None:
        self.symbol_id = symbol_id
        super().__init__(f"duplicate semantic document: symbol='{symbol_id}'")


def _fingerprint_payload(
    runtime_kind: str,
    model_repository: str,
    revision: str,
    dimension: int,
    normalization: str,
    similarity_metric: str,
    query_instruction: str,
    document_instruction: str,
    max_input_policy: str,
) -> bytes:
    # A fixed ordered JSON representation avoids repr/version/platform drift.
    return json.dumps(
        [
            runtime_kind,
            model_repository,
            revision,
            dimension,
            normalization,
            similarity_metric,
            query_instruction,
            document_instruction,
            max_input_policy,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class EmbeddingFingerprint:
    """Credential-free, deterministic identity of one embedding space."""

    runtime_kind: str
    model_repository: str
    revision: str
    dimension: int
    normalization: str = "l2"
    similarity_metric: str = "cosine"
    query_instruction: str = DEFAULT_QUERY_INSTRUCTION
    document_instruction: str = DEFAULT_DOCUMENT_INSTRUCTION
    max_input_policy: str = "512-token-explicit-truncation-v1"
    fingerprint_hash: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "runtime_kind",
            "model_repository",
            "revision",
            "normalization",
            "similarity_metric",
            "query_instruction",
            "document_instruction",
            "max_input_policy",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise EmbeddingFingerprintError(f"{name} must be a non-empty string")
        if self.query_instruction != DEFAULT_QUERY_INSTRUCTION:
            raise EmbeddingFingerprintError(
                f"query_instruction must be {DEFAULT_QUERY_INSTRUCTION!r}"
            )
        if self.document_instruction != DEFAULT_DOCUMENT_INSTRUCTION:
            raise EmbeddingFingerprintError(
                f"document_instruction must be {DEFAULT_DOCUMENT_INSTRUCTION!r}"
            )
        if self.normalization != "l2":
            raise EmbeddingFingerprintError("normalization must be 'l2'")
        if self.similarity_metric != "cosine":
            raise EmbeddingFingerprintError("similarity_metric must be 'cosine'")
        if type(self.dimension) is not int or self.dimension <= 0:
            raise EmbeddingFingerprintError("dimension must be a positive integer")
        expected = sha256(
            _fingerprint_payload(
                self.runtime_kind,
                self.model_repository,
                self.revision,
                self.dimension,
                self.normalization,
                self.similarity_metric,
                self.query_instruction,
                self.document_instruction,
                self.max_input_policy,
            )
        ).hexdigest()
        if self.fingerprint_hash is not None:
            if not isinstance(self.fingerprint_hash, str) or self.fingerprint_hash != expected:
                raise EmbeddingFingerprintError("fingerprint_hash does not match identity fields")
        object.__setattr__(self, "fingerprint_hash", expected)


@dataclass(frozen=True, init=False)
class EmbeddingVector:
    """Immutable finite, exact-dimension, non-zero vector."""

    values: tuple[float, ...]
    dimension: int

    def __init__(self, values: Iterable[float], dimension: int) -> None:
        if type(dimension) is not int or dimension <= 0:
            raise EmbeddingVectorError("dimension must be a positive integer")
        try:
            raw = tuple(values)
        except TypeError as error:
            raise EmbeddingVectorError("vector must be an iterable of numbers") from error
        if len(raw) != dimension:
            raise EmbeddingVectorError("vector dimension does not match fingerprint")
        normalized: list[float] = []
        for value in raw:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise EmbeddingVectorError("vector values must be numeric and not bool")
            numeric = float(value)
            if not math.isfinite(numeric):
                raise EmbeddingVectorError("vector values must be finite")
            normalized.append(numeric)
        if not any(value != 0.0 for value in normalized):
            raise EmbeddingVectorError("zero vector is not valid for cosine similarity")
        object.__setattr__(self, "values", tuple(normalized))
        object.__setattr__(self, "dimension", dimension)

    def __iter__(self):
        return iter(self.values)

    def __len__(self) -> int:
        return self.dimension

    def __getitem__(self, index):
        return self.values[index]


@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def fingerprint(self) -> EmbeddingFingerprint: ...

    def embed_query(self, text: str) -> EmbeddingVector | Sequence[float]: ...

    def embed_documents(
        self, texts: Sequence[str]
    ) -> Sequence[EmbeddingVector | Sequence[float]]: ...


class DeterministicFakeEmbeddingProvider:
    """Stable hash-based provider for architecture tests only."""

    def __init__(
        self,
        dimension: int = 8,
        *,
        query_instruction: str = DEFAULT_QUERY_INSTRUCTION,
        document_instruction: str = DEFAULT_DOCUMENT_INSTRUCTION,
    ) -> None:
        self._fingerprint = EmbeddingFingerprint(
            runtime_kind="deterministic-fake",
            model_repository="builtin/deterministic-fake",
            revision="v1",
            dimension=dimension,
            query_instruction=query_instruction,
            document_instruction=document_instruction,
            max_input_policy="fake-provider-unbounded-v1",
        )

    @property
    def fingerprint(self) -> EmbeddingFingerprint:
        return self._fingerprint

    def _embed(self, instruction: str, text: str) -> EmbeddingVector:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        seed = (instruction + text).encode("utf-8")
        values: list[float] = []
        counter = 0
        while len(values) < self._fingerprint.dimension:
            digest = sha256(seed + counter.to_bytes(8, "big")).digest()
            for offset in range(0, len(digest), 8):
                integer = int.from_bytes(digest[offset : offset + 8], "big")
                values.append((integer / 2**63) - 1.0)
                if len(values) == self._fingerprint.dimension:
                    break
            counter += 1
        return EmbeddingVector(values, self._fingerprint.dimension)

    def embed_query(self, text: str) -> EmbeddingVector:
        return self._embed(self._fingerprint.query_instruction, text)

    def embed_documents(self, texts: Sequence[str]) -> tuple[EmbeddingVector, ...]:
        return tuple(self._embed(self._fingerprint.document_instruction, text) for text in texts)


def _symbol_id_key(symbol_id: SymbolId) -> tuple:
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        (symbol_id.semantic_disambiguator is None, symbol_id.semantic_disambiguator or ""),
        (symbol_id.fallback_line is None, symbol_id.fallback_line or 0),
    )


def _normalize_vector(vector: EmbeddingVector) -> EmbeddingVector:
    norm = math.sqrt(math.fsum(value * value for value in vector.values))
    if not math.isfinite(norm) or norm == 0.0:
        raise EmbeddingVectorError("zero vector is not valid for cosine similarity")
    return EmbeddingVector((value / norm for value in vector.values), vector.dimension)


@dataclass(frozen=True)
class SemanticHit:
    symbol_id: SymbolId
    content_hash: str
    score: float
    rank: int
    fingerprint: EmbeddingFingerprint

    @property
    def document_id(self) -> SymbolId:
        return self.symbol_id

    @property
    def fingerprint_hash(self) -> str:
        assert self.fingerprint.fingerprint_hash is not None
        return self.fingerprint.fingerprint_hash

    def __post_init__(self) -> None:
        if not isinstance(self.symbol_id, SymbolId):
            raise SemanticRetrievalError("symbol_id must be a SymbolId")
        if not isinstance(self.content_hash, str) or not self.content_hash:
            raise SemanticRetrievalError("content_hash must be a non-empty string")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise SemanticRetrievalError("score must be numeric")
        if not math.isfinite(float(self.score)):
            raise SemanticRetrievalError("score must be finite")
        if type(self.rank) is not int or self.rank < 1:
            raise SemanticRetrievalError("rank must be a positive integer")
        if not isinstance(self.fingerprint, EmbeddingFingerprint):
            raise SemanticRetrievalError("fingerprint must be an EmbeddingFingerprint")


class SemanticIndex:
    """Immutable exact in-memory semantic index over Phase 1 documents."""

    def __init__(
        self,
        documents: Sequence[RetrievalDocument] = (),
        provider: EmbeddingProvider | None = None,
    ) -> None:
        if provider is None:
            raise SemanticRetrievalError("embedding provider is required")
        try:
            corpus = tuple(documents)
        except TypeError as error:
            raise SemanticRetrievalError("documents must be iterable") from error
        for document in corpus:
            if not isinstance(document, RetrievalDocument):
                raise SemanticRetrievalError("documents must contain RetrievalDocument values")
        canonical = tuple(sorted(corpus, key=lambda item: _symbol_id_key(item.symbol_id)))
        seen: set[SymbolId] = set()
        for document in canonical:
            if document.symbol_id in seen:
                raise DuplicateSemanticDocumentError(document.symbol_id)
            seen.add(document.symbol_id)

        try:
            fingerprint = provider.fingerprint
            if not isinstance(fingerprint, EmbeddingFingerprint):
                raise EmbeddingFingerprintError("provider fingerprint is invalid")
            texts = tuple(document.qualified_name + "\n" + document.source_text for document in canonical)
            raw_vectors = tuple(provider.embed_documents(texts)) if canonical else ()
            if len(raw_vectors) != len(canonical):
                raise SemanticRetrievalError("provider returned an unexpected vector count")
            after = provider.fingerprint
            if after != fingerprint:
                raise SemanticRetrievalError("provider fingerprint changed during index build")
            validated = tuple(
                _normalize_vector(_coerce_vector(vector, fingerprint.dimension))
                for vector in raw_vectors
            )
        except SemanticRetrievalError:
            raise
        except Exception as error:
            raise SemanticRetrievalError(
                f"embedding provider failure: {type(error).__name__}"
            ) from error

        self._documents = canonical
        self._vectors = validated
        self._provider = provider
        self._fingerprint = fingerprint

    @property
    def documents(self) -> tuple[RetrievalDocument, ...]:
        return self._documents

    @property
    def vectors(self) -> tuple[EmbeddingVector, ...]:
        return self._vectors

    @property
    def fingerprint(self) -> EmbeddingFingerprint:
        return self._fingerprint

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def search(self, query: str, top_k: int = 10) -> tuple[SemanticHit, ...]:
        if not isinstance(query, str):
            raise InvalidSemanticQueryError("query must be a string")
        if type(top_k) is not int or top_k <= 0:
            raise InvalidSemanticQueryError("top_k must be an integer greater than zero")
        if not query.strip() or not self._documents:
            return ()
        try:
            if self._provider.fingerprint != self._fingerprint:
                raise SemanticRetrievalError("provider fingerprint changed after index build")
            query_vector = _normalize_vector(
                _coerce_vector(self._provider.embed_query(query), self._fingerprint.dimension)
            )
            if self._provider.fingerprint != self._fingerprint:
                raise SemanticRetrievalError("provider fingerprint changed during query")
        except SemanticRetrievalError:
            raise
        except Exception as error:
            raise SemanticRetrievalError(
                f"embedding provider failure: {type(error).__name__}"
            ) from error

        scored: list[tuple[float, RetrievalDocument]] = []
        for document, vector in zip(self._documents, self._vectors):
            score = math.fsum(a * b for a, b in zip(query_vector.values, vector.values))
            if not math.isfinite(score):
                raise SemanticRetrievalError("cosine similarity was not finite")
            scored.append((score, document))
        scored.sort(key=lambda item: (-item[0], _symbol_id_key(item[1].symbol_id)))
        return tuple(
            SemanticHit(
                symbol_id=document.symbol_id,
                content_hash=document.content_hash,
                score=score,
                rank=rank,
                fingerprint=self._fingerprint,
            )
            for rank, (score, document) in enumerate(scored[:top_k], start=1)
        )


def _coerce_vector(value: EmbeddingVector | Sequence[float], dimension: int) -> EmbeddingVector:
    if isinstance(value, EmbeddingVector):
        if value.dimension != dimension:
            raise EmbeddingVectorError("vector dimension does not match fingerprint")
        return value
    return EmbeddingVector(value, dimension)


ExactSemanticIndex = SemanticIndex
