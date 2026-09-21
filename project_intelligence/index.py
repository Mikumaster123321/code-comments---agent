"""Immutable retrieval index identity and SnapshotDiff-driven incremental indexing."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from code_maintenance.domain import SymbolId
from code_maintenance.snapshot import ProjectSnapshot, SnapshotDiff, compare_snapshots

from .domain import RetrievalDocument
from .embedding import (
    EmbeddingFingerprint,
    EmbeddingProvider,
    EmbeddingVector,
    InvalidSemanticQueryError,
    SemanticHit,
)
from .graph_expansion import (
    GraphExpansionConfig,
    GraphExpansionResult,
    GraphSnapshotMismatchError,
    expand_graph,
)
from .lexical import BM25Config, BM25Index, LexicalHit


class RetrievalIndexError(Exception):
    """Base error for index identity and update failures."""


class IndexSnapshotMismatchError(RetrievalIndexError):
    """Raised when documents or an index identity do not match a snapshot."""


class RetrievalConfigMismatchError(RetrievalIndexError):
    """Raised when update semantics differ from the existing index."""


class EmbeddingFingerprintMismatchError(RetrievalIndexError):
    """Raised when an embedding space changes and vectors cannot be reused."""


class IndexBuildError(RetrievalIndexError):
    """Raised when a provider or validation failure prevents an atomic build."""


def _symbol_id_key(symbol_id: SymbolId) -> tuple:
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        symbol_id.semantic_disambiguator or "",
        symbol_id.fallback_line if symbol_id.fallback_line is not None else -1,
    )


def _fingerprint_record(fingerprint: EmbeddingFingerprint | str | None) -> object:
    if fingerprint is None:
        return None
    if isinstance(fingerprint, str):
        return {"fingerprint_hash": fingerprint}
    if not isinstance(fingerprint, EmbeddingFingerprint):
        raise ValueError("embedding_fingerprint must be an EmbeddingFingerprint")
    return {
        "runtime_kind": fingerprint.runtime_kind,
        "model_repository": fingerprint.model_repository,
        "revision": fingerprint.revision,
        "dimension": fingerprint.dimension,
        "normalization": fingerprint.normalization,
        "similarity_metric": fingerprint.similarity_metric,
        "query_instruction": fingerprint.query_instruction,
        "document_instruction": fingerprint.document_instruction,
        "max_input_policy": fingerprint.max_input_policy,
        "fingerprint_hash": fingerprint.fingerprint_hash,
    }


@dataclass(frozen=True)
class RetrievalConfig:
    """The deterministic semantic configuration of one retrieval index."""

    retrieval_unit: str = "symbol"
    lexical_config: BM25Config = BM25Config()
    embedding_enabled: bool = False
    embedding_fingerprint: EmbeddingFingerprint | None = None
    graph_expansion_config: GraphExpansionConfig = GraphExpansionConfig()

    def __post_init__(self) -> None:
        if not isinstance(self.retrieval_unit, str) or not self.retrieval_unit:
            raise ValueError("retrieval_unit must be a non-empty string")
        if self.retrieval_unit != "symbol":
            raise ValueError("retrieval_unit must remain 'symbol' in Phase 4")
        if not isinstance(self.lexical_config, BM25Config):
            raise ValueError("lexical_config must be a BM25Config")
        if type(self.embedding_enabled) is not bool:
            raise ValueError("embedding_enabled must be a bool")
        if self.embedding_fingerprint is not None and not isinstance(
            self.embedding_fingerprint, EmbeddingFingerprint
        ):
            raise ValueError("embedding_fingerprint must be an EmbeddingFingerprint")
        if self.embedding_enabled and self.embedding_fingerprint is None:
            raise ValueError("embedding_fingerprint is required when embeddings are enabled")
        if not isinstance(self.graph_expansion_config, GraphExpansionConfig):
            raise ValueError("graph_expansion_config must be a GraphExpansionConfig")

    def to_record(self) -> dict:
        return {
            "retrieval_unit": self.retrieval_unit,
            "lexical": {
                "k1": self.lexical_config.k1,
                "b": self.lexical_config.b,
                "tokenizer_version": self.lexical_config.tokenizer_version,
            },
            "embedding_enabled": self.embedding_enabled,
            "embedding_fingerprint": _fingerprint_record(self.embedding_fingerprint),
            "graph": {
                "max_hops": self.graph_expansion_config.max_hops,
                "relations": [relation.value for relation in self.graph_expansion_config.relations],
                "max_expanded_per_seed": self.graph_expansion_config.max_expanded_per_seed,
                "max_total_context_nodes": self.graph_expansion_config.max_total_context_nodes,
            },
        }

    @property
    def identity_hash(self) -> str:
        payload = json.dumps(
            self.to_record(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    @property
    def config_hash(self) -> str:
        return self.identity_hash

    @property
    def retrieval_config_hash(self) -> str:
        return self.identity_hash


RetrievalConfigIdentity = RetrievalConfig


@dataclass(frozen=True)
class RetrievalIndexIdentity:
    project_id: str
    snapshot_content_hash: str
    retrieval_config_hash: str
    embedding_fingerprint: EmbeddingFingerprint | None = None

    def __post_init__(self) -> None:
        for field_name in ("project_id", "snapshot_content_hash", "retrieval_config_hash"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.embedding_fingerprint is not None and not isinstance(
            self.embedding_fingerprint, EmbeddingFingerprint
        ):
            raise ValueError("embedding_fingerprint must be an EmbeddingFingerprint")

    @classmethod
    def for_snapshot(
        cls,
        snapshot: ProjectSnapshot,
        config: RetrievalConfig,
    ) -> "RetrievalIndexIdentity":
        if not isinstance(snapshot, ProjectSnapshot):
            raise ValueError("snapshot must be a ProjectSnapshot")
        if not isinstance(config, RetrievalConfig):
            raise ValueError("config must be a RetrievalConfig")
        return cls(
            project_id=snapshot.project_id,
            snapshot_content_hash=snapshot.content_hash,
            retrieval_config_hash=config.identity_hash,
            embedding_fingerprint=config.embedding_fingerprint,
        )

    @property
    def identity_hash(self) -> str:
        payload = json.dumps(
            self.to_record(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_record(self) -> dict:
        return {
            "project_id": self.project_id,
            "snapshot_content_hash": self.snapshot_content_hash,
            "retrieval_config_hash": self.retrieval_config_hash,
            "embedding_fingerprint": _fingerprint_record(self.embedding_fingerprint),
        }

    @property
    def embedding_fingerprint_hash(self) -> str | None:
        return None if self.embedding_fingerprint is None else self.embedding_fingerprint.fingerprint_hash


@dataclass(frozen=True)
class IndexOperation:
    action: str
    symbol_id: SymbolId


@dataclass(frozen=True)
class IncrementalIndexPlan:
    source_snapshot_hash: str
    target_snapshot_hash: str
    added: tuple[SymbolId, ...]
    removed: tuple[SymbolId, ...]
    changed: tuple[SymbolId, ...]
    unchanged: tuple[SymbolId, ...]

    @classmethod
    def from_diff(
        cls, old: ProjectSnapshot, new: ProjectSnapshot, diff: SnapshotDiff | None = None
    ) -> "IncrementalIndexPlan":
        if old.project_id != new.project_id:
            raise IndexSnapshotMismatchError("snapshots must belong to the same project")
        expected = compare_snapshots(old, new)
        actual = diff if diff is not None else expected
        if actual != expected:
            raise IndexSnapshotMismatchError("SnapshotDiff does not match its snapshots")
        return cls(
            source_snapshot_hash=old.content_hash,
            target_snapshot_hash=new.content_hash,
            added=tuple(sorted(actual.added_symbols, key=_symbol_id_key)),
            removed=tuple(sorted(actual.removed_symbols, key=_symbol_id_key)),
            changed=tuple(sorted(actual.changed_symbols, key=_symbol_id_key)),
            unchanged=tuple(sorted(actual.unchanged_symbols, key=_symbol_id_key)),
        )

    @property
    def operations(self) -> tuple[IndexOperation, ...]:
        return tuple(
            IndexOperation(action, symbol_id)
            for action, values in (
                ("add", self.added),
                ("delete", self.removed),
                ("replace", self.changed),
                ("reuse", self.unchanged),
            )
            for symbol_id in values
        )

    @property
    def added_symbols(self) -> tuple[SymbolId, ...]:
        return self.added

    @property
    def removed_symbols(self) -> tuple[SymbolId, ...]:
        return self.removed

    @property
    def changed_symbols(self) -> tuple[SymbolId, ...]:
        return self.changed

    @property
    def unchanged_symbols(self) -> tuple[SymbolId, ...]:
        return self.unchanged

    @property
    def actions(self) -> Mapping[SymbolId, str]:
        return MappingProxyType({operation.symbol_id: operation.action for operation in self.operations})

    def action_for(self, symbol_id: SymbolId) -> str | None:
        return self.actions.get(symbol_id)


def build_incremental_plan(
    old: ProjectSnapshot, new: ProjectSnapshot, diff: SnapshotDiff | None = None
) -> IncrementalIndexPlan:
    return IncrementalIndexPlan.from_diff(old, new, diff)


@dataclass(frozen=True)
class _IndexEntry:
    document: RetrievalDocument
    vector: EmbeddingVector | None


def _text(document: RetrievalDocument) -> str:
    return document.qualified_name + "\n" + document.source_text


def _normalize_vector(vector: EmbeddingVector | Sequence[float], dimension: int) -> EmbeddingVector:
    candidate = vector if isinstance(vector, EmbeddingVector) else EmbeddingVector(vector, dimension)
    if candidate.dimension != dimension:
        raise IndexBuildError("embedding vector dimension does not match fingerprint")
    norm = math.sqrt(math.fsum(value * value for value in candidate.values))
    if not math.isfinite(norm) or norm == 0.0:
        raise IndexBuildError("embedding vector must be finite and non-zero")
    return EmbeddingVector((value / norm for value in candidate.values), dimension)


class RetrievalIndex:
    """Immutable lexical/semantic index with atomic SnapshotDiff updates."""

    def __init__(
        self,
        snapshot: ProjectSnapshot,
        documents: Sequence[RetrievalDocument],
        config: RetrievalConfig,
        entries: Sequence[_IndexEntry],
        provider: EmbeddingProvider | None,
    ) -> None:
        if not isinstance(config, RetrievalConfig):
            raise RetrievalIndexError("config must be a RetrievalConfig")
        self._validate_documents(snapshot, documents)
        canonical = tuple(sorted(documents, key=lambda item: _symbol_id_key(item.symbol_id)))
        by_id = {entry.document.symbol_id: entry for entry in entries}
        if set(by_id) != {document.symbol_id for document in canonical}:
            raise IndexBuildError("index entries do not match documents")
        for document in canonical:
            entry = by_id[document.symbol_id]
            if entry.document != document:
                raise IndexBuildError("index entry contains stale document state")
            if config.embedding_enabled:
                if entry.vector is None or entry.vector.dimension != config.embedding_fingerprint.dimension:
                    raise IndexBuildError("index entry contains an invalid semantic vector")
            elif entry.vector is not None:
                raise IndexBuildError("lexical-only index cannot contain semantic vectors")
        if config.embedding_enabled:
            if provider is None or provider.fingerprint != config.embedding_fingerprint:
                raise EmbeddingFingerprintMismatchError("provider fingerprint differs from index")
        self._snapshot = snapshot
        self._documents = canonical
        self._entries = tuple(by_id[document.symbol_id] for document in canonical)
        self._entries_by_id = MappingProxyType({entry.document.symbol_id: entry for entry in self._entries})
        self._config = config
        self._provider = provider
        self._identity = RetrievalIndexIdentity.for_snapshot(snapshot, config)
        self._lexical = BM25Index(self._documents, config.lexical_config)

    @classmethod
    def build(
        cls,
        snapshot: ProjectSnapshot,
        documents: Iterable[RetrievalDocument],
        config: RetrievalConfig | None = None,
        *,
        provider: EmbeddingProvider | None = None,
    ) -> "RetrievalIndex":
        cfg = config if config is not None else RetrievalConfig()
        if not isinstance(cfg, RetrievalConfig):
            raise RetrievalIndexError("config must be a RetrievalConfig")
        docs = tuple(documents)
        cls._validate_documents(snapshot, docs)
        ordered_docs = tuple(sorted(docs, key=lambda item: _symbol_id_key(item.symbol_id)))
        if cfg.embedding_enabled:
            if provider is None:
                raise IndexBuildError("embedding provider is required")
            try:
                fingerprint = provider.fingerprint
                if fingerprint != cfg.embedding_fingerprint:
                    raise EmbeddingFingerprintMismatchError("provider fingerprint differs from config")
                vectors = (
                    tuple(provider.embed_documents(tuple(_text(doc) for doc in ordered_docs)))
                    if ordered_docs
                    else ()
                )
                if len(vectors) != len(docs):
                    raise IndexBuildError("provider returned an unexpected vector count")
                normalized = tuple(
                    _normalize_vector(vector, fingerprint.dimension) for vector in vectors
                )
                if provider.fingerprint != fingerprint:
                    raise IndexBuildError("provider fingerprint changed during index build")
            except RetrievalIndexError:
                raise
            except Exception as error:
                raise IndexBuildError(f"embedding provider failure: {type(error).__name__}") from error
        else:
            normalized = (None,) * len(docs)
            provider = None
        entries = tuple(_IndexEntry(document, vector) for document, vector in zip(ordered_docs, normalized))
        return cls(snapshot, ordered_docs, cfg, entries, provider)

    @staticmethod
    def _validate_documents(snapshot: ProjectSnapshot, documents: Sequence[RetrievalDocument]) -> None:
        if not isinstance(snapshot, ProjectSnapshot):
            raise IndexSnapshotMismatchError("snapshot must be a ProjectSnapshot")
        expected = {state.id: state.content_hash for state in snapshot.symbols}
        actual: dict[SymbolId, str] = {}
        for document in documents:
            if not isinstance(document, RetrievalDocument):
                raise IndexBuildError("documents must contain RetrievalDocument values")
            if document.symbol_id in actual:
                raise IndexBuildError("duplicate SymbolId")
            actual[document.symbol_id] = document.content_hash
        if actual != expected:
            raise IndexSnapshotMismatchError("documents do not match target snapshot symbols/content hashes")

    @property
    def snapshot(self) -> ProjectSnapshot:
        return self._snapshot

    @property
    def documents(self) -> tuple[RetrievalDocument, ...]:
        return self._documents

    @property
    def entries(self) -> tuple[tuple[RetrievalDocument, EmbeddingVector | None], ...]:
        return tuple((entry.document, entry.vector) for entry in self._entries)

    @property
    def config(self) -> RetrievalConfig:
        return self._config

    @property
    def identity(self) -> RetrievalIndexIdentity:
        return self._identity

    @property
    def index_identity(self) -> RetrievalIndexIdentity:
        return self._identity

    @property
    def lexical_index(self) -> BM25Index:
        return self._lexical

    @property
    def vectors(self) -> tuple[EmbeddingVector, ...]:
        return tuple(entry.vector for entry in self._entries if entry.vector is not None)

    def lexical_search(self, query: str, top_k: int = 10) -> tuple[LexicalHit, ...]:
        return self._lexical.search(query, top_k)

    def semantic_search(self, query: str, top_k: int = 10) -> tuple[SemanticHit, ...]:
        if not self._config.embedding_enabled or self._provider is None:
            raise RetrievalIndexError("semantic retrieval is disabled")
        if not isinstance(query, str):
            raise InvalidSemanticQueryError("query must be a string")
        if type(top_k) is not int or top_k <= 0:
            raise InvalidSemanticQueryError("top_k must be an integer greater than zero")
        if not query.strip():
            return ()
        fingerprint = self._provider.fingerprint
        if fingerprint != self._config.embedding_fingerprint:
            raise EmbeddingFingerprintMismatchError("provider fingerprint changed")
        try:
            query_vector = _normalize_vector(
                self._provider.embed_query(query), fingerprint.dimension
            )
        except RetrievalIndexError:
            raise
        except Exception as error:
            raise IndexBuildError(f"embedding provider failure: {type(error).__name__}") from error
        scored = []
        for entry in self._entries:
            assert entry.vector is not None
            score = math.fsum(a * b for a, b in zip(query_vector.values, entry.vector.values))
            scored.append((score, entry.document))
        scored.sort(key=lambda item: (-item[0], _symbol_id_key(item[1].symbol_id)))
        return tuple(
            SemanticHit(document.symbol_id, document.content_hash, score, rank, fingerprint)
            for rank, (score, document) in enumerate(scored[:top_k], start=1)
        )

    def update(
        self,
        target_snapshot: ProjectSnapshot,
        target_documents: Iterable[RetrievalDocument],
        *,
        diff: SnapshotDiff | None = None,
        config: RetrievalConfig | None = None,
        provider: EmbeddingProvider | None = None,
    ) -> "RetrievalIndex":
        if target_snapshot.project_id != self._snapshot.project_id:
            raise IndexSnapshotMismatchError("target snapshot belongs to another project")
        if self._identity.snapshot_content_hash != self._snapshot.content_hash:
            raise IndexSnapshotMismatchError("prior index identity is stale")
        cfg = config if config is not None else self._config
        if cfg != self._config or cfg.identity_hash != self._config.identity_hash:
            raise RetrievalConfigMismatchError("retrieval config changed; rebuild is required")
        docs = tuple(target_documents)
        self._validate_documents(target_snapshot, docs)
        plan = IncrementalIndexPlan.from_diff(self._snapshot, target_snapshot, diff)
        if plan.source_snapshot_hash != self._snapshot.content_hash:
            raise IndexSnapshotMismatchError("incremental plan source does not match prior index")
        if plan.target_snapshot_hash != target_snapshot.content_hash:
            raise IndexSnapshotMismatchError("incremental plan target does not match target snapshot")

        target_by_id = {document.symbol_id: document for document in docs}
        changed_or_added = tuple(sorted((*plan.added, *plan.changed), key=_symbol_id_key))
        effective_provider = provider if provider is not None else self._provider
        if self._config.embedding_enabled:
            if effective_provider is None:
                raise IndexBuildError("embedding provider is required")
            if effective_provider.fingerprint != self._config.embedding_fingerprint:
                raise EmbeddingFingerprintMismatchError("embedding fingerprint changed; rebuild required")
            try:
                raw = tuple(
                    effective_provider.embed_documents(
                        tuple(_text(target_by_id[symbol_id]) for symbol_id in changed_or_added)
                    )
                ) if changed_or_added else ()
                if len(raw) != len(changed_or_added):
                    raise IndexBuildError("provider returned an unexpected vector count")
                new_vectors = {
                    symbol_id: _normalize_vector(vector, effective_provider.fingerprint.dimension)
                    for symbol_id, vector in zip(changed_or_added, raw)
                }
                if effective_provider.fingerprint != self._config.embedding_fingerprint:
                    raise EmbeddingFingerprintMismatchError("provider fingerprint changed during update")
            except RetrievalIndexError:
                raise
            except Exception as error:
                raise IndexBuildError(f"embedding provider failure: {type(error).__name__}") from error
        else:
            new_vectors = {}
            effective_provider = None

        entries = []
        unchanged_ids = set(plan.unchanged)
        for document in sorted(docs, key=lambda item: _symbol_id_key(item.symbol_id)):
            old_entry = self._entries_by_id.get(document.symbol_id)
            if document.symbol_id in new_vectors:
                vector = new_vectors[document.symbol_id]
            elif old_entry is not None and document.symbol_id in unchanged_ids:
                vector = old_entry.vector
            elif not self._config.embedding_enabled:
                vector = None
            else:
                raise IndexBuildError("missing vector for changed index entry")
            entries.append(_IndexEntry(document, vector))
        return RetrievalIndex(target_snapshot, docs, self._config, entries, effective_provider)

    incremental_update = update

    def expand_graph(
        self,
        seeds: Iterable[object],
        *,
        graph=None,
        config: GraphExpansionConfig | None = None,
    ) -> GraphExpansionResult:
        selected_graph = self._snapshot.graph if graph is None else graph
        return expand_graph(
            selected_graph,
            seeds,
            self._documents,
            config if config is not None else self._config.graph_expansion_config,
            expected_graph=self._snapshot.graph,
        )


IncrementalRetrievalIndex = RetrievalIndex
