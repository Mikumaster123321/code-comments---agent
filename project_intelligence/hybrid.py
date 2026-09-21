"""Deterministic and explainable lexical/semantic/graph fusion."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

from code_maintenance.domain import SymbolId
from code_maintenance.graph import GraphRelationKind

from .domain import ProjectIntelligenceError, RetrievalDocument
from .embedding import SemanticHit, SemanticRetrievalError
from .graph_expansion import (
    ExpandedContextCandidate,
    GraphExpansionProvenance,
    GraphExpansionResult,
    GraphTraversalDirection,
)
from .index import (
    EmbeddingFingerprintMismatchError,
    IndexBuildError,
    RetrievalIndex,
)
from .lexical import LexicalHit


class FusionStrategy(str, Enum):
    WEIGHTED = "weighted"
    RRF = "rrf"


class HybridRetrievalError(ProjectIntelligenceError):
    """Raised when a complete authoritative Hybrid result cannot be produced."""


class InvalidHybridConfigError(HybridRetrievalError):
    """Raised when fusion configuration is invalid."""


def symbol_id_key(symbol_id: SymbolId) -> tuple:
    """Canonical key that preserves Optional-field type distinctions."""

    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        (
            symbol_id.semantic_disambiguator is None,
            symbol_id.semantic_disambiguator or "",
        ),
        (symbol_id.fallback_line is None, symbol_id.fallback_line or 0),
    )


@dataclass(frozen=True)
class HybridConfig:
    fusion_strategy: FusionStrategy = FusionStrategy.WEIGHTED
    lexical_weight: float = 1.0
    semantic_weight: float = 1.0
    graph_weight: float = 0.25
    graph_enabled: bool = True
    top_k: int = 10
    rrf_k: int = 60

    def __post_init__(self) -> None:
        try:
            strategy = (
                self.fusion_strategy
                if isinstance(self.fusion_strategy, FusionStrategy)
                else FusionStrategy(self.fusion_strategy)
            )
        except (TypeError, ValueError) as error:
            raise InvalidHybridConfigError("unsupported fusion_strategy") from error
        object.__setattr__(self, "fusion_strategy", strategy)

        for name in ("lexical_weight", "semantic_weight", "graph_weight"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InvalidHybridConfigError(f"{name} must be a finite number")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0:
                raise InvalidHybridConfigError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, numeric)
        if self.lexical_weight == 0.0 and self.semantic_weight == 0.0:
            raise InvalidHybridConfigError(
                "at least one candidate-producing branch weight must be positive"
            )
        if type(self.graph_enabled) is not bool:
            raise InvalidHybridConfigError("graph_enabled must be a bool")
        if not self.graph_enabled and self.graph_weight != 0.0:
            raise InvalidHybridConfigError(
                "graph_weight must be zero when graph expansion is disabled"
            )
        if type(self.top_k) is not int or self.top_k <= 0:
            raise InvalidHybridConfigError("top_k must be a positive integer")
        if type(self.rrf_k) is not int or self.rrf_k <= 0:
            raise InvalidHybridConfigError("rrf_k must be a positive integer")


@dataclass(frozen=True)
class HybridHit:
    document: RetrievalDocument
    lexical_score: float | None
    lexical_rank: int | None
    semantic_score: float | None
    semantic_rank: int | None
    normalized_lexical_score: float
    normalized_semantic_score: float
    graph_score: float
    graph_provenance: tuple[GraphExpansionProvenance, ...]
    fusion_strategy: FusionStrategy
    lexical_weight: float
    semantic_weight: float
    graph_weight: float
    score: float
    rank: int

    def __post_init__(self) -> None:
        if not isinstance(self.document, RetrievalDocument):
            raise HybridRetrievalError("document must be a RetrievalDocument")
        if (self.lexical_score is None) != (self.lexical_rank is None):
            raise HybridRetrievalError("lexical score and rank must be present together")
        if (self.semantic_score is None) != (self.semantic_rank is None):
            raise HybridRetrievalError("semantic score and rank must be present together")
        for name in (
            "normalized_lexical_score",
            "normalized_semantic_score",
            "graph_score",
            "lexical_weight",
            "semantic_weight",
            "graph_weight",
            "score",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise HybridRetrievalError(f"{name} must be numeric")
            if not math.isfinite(float(value)):
                raise HybridRetrievalError(f"{name} must be finite")
        for name in (
            "normalized_lexical_score",
            "normalized_semantic_score",
            "graph_score",
        ):
            if not 0.0 <= float(getattr(self, name)) <= 1.0:
                raise HybridRetrievalError(f"{name} must be between zero and one")
        for name in ("lexical_weight", "semantic_weight", "graph_weight"):
            if float(getattr(self, name)) < 0.0:
                raise HybridRetrievalError(f"{name} must be non-negative")
        for name in ("lexical_rank", "semantic_rank", "rank"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value <= 0):
                raise HybridRetrievalError(f"{name} must be a positive integer")
        if type(self.graph_provenance) is not tuple or not all(
            isinstance(item, GraphExpansionProvenance)
            for item in self.graph_provenance
        ):
            raise HybridRetrievalError("graph_provenance must be an immutable tuple")
        if not isinstance(self.fusion_strategy, FusionStrategy):
            raise HybridRetrievalError("fusion_strategy must be a FusionStrategy")

    @property
    def symbol_id(self) -> SymbolId:
        return self.document.symbol_id

    @property
    def document_id(self) -> SymbolId:
        return self.document.symbol_id

    @property
    def final_score(self) -> float:
        return self.score


@dataclass(frozen=True)
class HybridRetrievalResult:
    hits: tuple[HybridHit, ...]
    graph_context: tuple[ExpandedContextCandidate, ...]
    degraded: bool
    degradation_reason: str | None
    failure_provenance: tuple[str, ...]
    fusion_strategy: FusionStrategy

    def __post_init__(self) -> None:
        if type(self.hits) is not tuple or not all(
            isinstance(item, HybridHit) for item in self.hits
        ):
            raise HybridRetrievalError("hits must be an immutable HybridHit tuple")
        if type(self.graph_context) is not tuple or not all(
            isinstance(item, ExpandedContextCandidate) for item in self.graph_context
        ):
            raise HybridRetrievalError(
                "graph_context must be an immutable candidate tuple"
            )
        if type(self.degraded) is not bool:
            raise HybridRetrievalError("degraded must be a bool")
        if self.degraded != (self.degradation_reason is not None):
            raise HybridRetrievalError("degraded state and reason must agree")
        if type(self.failure_provenance) is not tuple or not all(
            isinstance(item, str) and item for item in self.failure_provenance
        ):
            raise HybridRetrievalError(
                "failure_provenance must be an immutable string tuple"
            )
        if not isinstance(self.fusion_strategy, FusionStrategy):
            raise HybridRetrievalError("fusion_strategy must be a FusionStrategy")


def _validate_top_k(top_k: int) -> None:
    if type(top_k) is not int or top_k <= 0:
        raise HybridRetrievalError("top_k must be a positive integer")


def _lexical_normalization(hits: Sequence[LexicalHit]) -> dict[SymbolId, float]:
    if not hits:
        return {}
    scores = []
    for hit in hits:
        score = float(hit.score)
        if not math.isfinite(score) or score < 0.0:
            raise HybridRetrievalError("lexical scores must be finite and non-negative")
        scores.append(score)
    maximum = max(scores, default=0.0)
    if maximum == 0.0:
        return {hit.symbol_id: 0.0 for hit in hits}
    return {hit.symbol_id: float(hit.score) / maximum for hit in hits}


def _semantic_normalization(hits: Sequence[SemanticHit]) -> dict[SymbolId, float]:
    normalized: dict[SymbolId, float] = {}
    for hit in hits:
        score = float(hit.score)
        if not math.isfinite(score):
            raise HybridRetrievalError("semantic scores must be finite")
        # Exact cosine is nominally [-1, 1].  Clamp tiny floating-point drift,
        # then map that fixed interval into [0, 1].
        bounded = min(1.0, max(-1.0, score))
        normalized[hit.symbol_id] = (bounded + 1.0) / 2.0
    return normalized


def _provenance_key(provenance: GraphExpansionProvenance) -> tuple:
    seed = provenance.seed_identity
    node = provenance.node_identity
    return (
        symbol_id_key(seed) if isinstance(seed, SymbolId) else ("string", str(seed)),
        provenance.relation.value,
        provenance.direction.value,
        provenance.hop,
        symbol_id_key(node) if isinstance(node, SymbolId) else ("string", str(node)),
    )


def _candidate_key(candidate: ExpandedContextCandidate) -> tuple:
    document_key = (
        symbol_id_key(candidate.document.symbol_id)
        if candidate.document is not None
        else (candidate.node.kind.value, str(candidate.node.identity))
    )
    return (_provenance_key(candidate.provenance), document_key)


def _graph_signal(provenance: GraphExpansionProvenance) -> float:
    if type(provenance.hop) is not int or provenance.hop <= 0:
        raise HybridRetrievalError("graph provenance hop must be positive")
    relation_factor = {
        GraphRelationKind.CONTAINS: 0.75,
        GraphRelationKind.IMPORTS: 1.0,
    }.get(provenance.relation)
    direction_factor = {
        GraphTraversalDirection.FORWARD: 1.0,
        GraphTraversalDirection.REVERSE: 0.8,
    }.get(provenance.direction)
    if relation_factor is None or direction_factor is None:
        raise HybridRetrievalError("unsupported graph provenance")
    return relation_factor * direction_factor / provenance.hop


class HybridRetriever:
    """Fuse existing index branches without rebuilding or rescanning them."""

    def __init__(self, index: RetrievalIndex, config: HybridConfig | None = None) -> None:
        if not isinstance(index, RetrievalIndex):
            raise HybridRetrievalError("index must be a RetrievalIndex")
        cfg = config if config is not None else HybridConfig()
        if not isinstance(cfg, HybridConfig):
            raise InvalidHybridConfigError("config must be a HybridConfig")
        if cfg.semantic_weight > 0.0 and not index.config.embedding_enabled:
            raise InvalidHybridConfigError(
                "semantic_weight requires an embedding-enabled RetrievalIndex"
            )
        self._index = index
        self._config = cfg

    @property
    def config(self) -> HybridConfig:
        return self._config

    @property
    def index(self) -> RetrievalIndex:
        return self._index

    def retrieve(self, query: str, top_k: int | None = None) -> HybridRetrievalResult:
        if not isinstance(query, str):
            raise HybridRetrievalError("query must be a string")
        limit = self._config.top_k if top_k is None else top_k
        _validate_top_k(limit)
        if not query.strip():
            return HybridRetrievalResult(
                (), (), False, None, (), self._config.fusion_strategy
            )

        lexical_hits = (
            self._index.lexical_search(query, limit)
            if self._config.lexical_weight > 0.0
            else ()
        )
        degraded = False
        degradation_reason = None
        failure_provenance: tuple[str, ...] = ()
        if self._config.semantic_weight > 0.0:
            try:
                semantic_hits = self._index.semantic_search(query, limit)
            except (
                SemanticRetrievalError,
                IndexBuildError,
                EmbeddingFingerprintMismatchError,
            ) as error:
                if self._config.lexical_weight == 0.0:
                    raise HybridRetrievalError(
                        "semantic-only retrieval cannot degrade without a lexical branch"
                    ) from error
                semantic_hits = ()
                degraded = True
                degradation_reason = f"semantic_branch_failure:{type(error).__name__}"
                failure_provenance = (degradation_reason,)
        else:
            semantic_hits = ()

        candidate_ids = {
            *(hit.symbol_id for hit in lexical_hits),
            *(hit.symbol_id for hit in semantic_hits),
        }
        graph_result = None
        if self._config.graph_enabled and candidate_ids:
            graph_result = self._index.expand_graph(
                tuple(sorted(candidate_ids, key=symbol_id_key))
            )
        return self.fuse(
            lexical_hits,
            semantic_hits,
            self._index.documents,
            graph_result=graph_result,
            top_k=limit,
            degraded=degraded,
            degradation_reason=degradation_reason,
            failure_provenance=failure_provenance,
        )

    def fuse(
        self,
        lexical_hits: Iterable[LexicalHit],
        semantic_hits: Iterable[SemanticHit],
        documents: Iterable[RetrievalDocument],
        *,
        graph_result: GraphExpansionResult | None = None,
        top_k: int | None = None,
        degraded: bool = False,
        degradation_reason: str | None = None,
        failure_provenance: tuple[str, ...] = (),
    ) -> HybridRetrievalResult:
        limit = self._config.top_k if top_k is None else top_k
        _validate_top_k(limit)
        lexical = tuple(lexical_hits)
        semantic = tuple(semantic_hits)
        docs = tuple(documents)
        if type(degraded) is not bool:
            raise HybridRetrievalError("degraded must be a bool")
        if degraded != (degradation_reason is not None):
            raise HybridRetrievalError("degraded state and reason must agree")

        documents_by_id: dict[SymbolId, RetrievalDocument] = {}
        for document in docs:
            if not isinstance(document, RetrievalDocument):
                raise HybridRetrievalError("documents must contain RetrievalDocument values")
            if document.symbol_id in documents_by_id:
                raise HybridRetrievalError("duplicate authoritative RetrievalDocument")
            documents_by_id[document.symbol_id] = document

        lexical_by_id: dict[SymbolId, LexicalHit] = {}
        for hit in lexical:
            if not isinstance(hit, LexicalHit) or hit.symbol_id in lexical_by_id:
                raise HybridRetrievalError("lexical hits must have unique SymbolId values")
            if documents_by_id.get(hit.symbol_id) != hit.document:
                raise HybridRetrievalError("lexical hit document is not authoritative")
            lexical_by_id[hit.symbol_id] = hit
        semantic_by_id: dict[SymbolId, SemanticHit] = {}
        for hit in semantic:
            if not isinstance(hit, SemanticHit) or hit.symbol_id in semantic_by_id:
                raise HybridRetrievalError("semantic hits must have unique SymbolId values")
            document = documents_by_id.get(hit.symbol_id)
            if document is None or document.content_hash != hit.content_hash:
                raise HybridRetrievalError("semantic hit does not match an authoritative document")
            semantic_by_id[hit.symbol_id] = hit

        lexical_normalized = _lexical_normalization(lexical)
        semantic_normalized = _semantic_normalization(semantic)
        candidate_ids = set(lexical_by_id) | set(semantic_by_id)

        candidates = () if graph_result is None else tuple(graph_result.candidates)
        ordered_graph = tuple(sorted(candidates, key=_candidate_key))
        graph_by_id: dict[SymbolId, list[GraphExpansionProvenance]] = {}
        for candidate in ordered_graph:
            if not isinstance(candidate, ExpandedContextCandidate):
                raise HybridRetrievalError("graph context contains an invalid candidate")
            if candidate.document is not None:
                authoritative = documents_by_id.get(candidate.document.symbol_id)
                if authoritative != candidate.document:
                    raise HybridRetrievalError("graph document is not authoritative")
                graph_by_id.setdefault(candidate.document.symbol_id, []).append(
                    candidate.provenance
                )

        scored: list[tuple[float, SymbolId, tuple[GraphExpansionProvenance, ...], float]] = []
        for symbol_id in candidate_ids:
            provenances = tuple(
                sorted(graph_by_id.get(symbol_id, ()), key=_provenance_key)
            )
            graph_score = max((_graph_signal(item) for item in provenances), default=0.0)
            lexical_hit = lexical_by_id.get(symbol_id)
            semantic_hit = semantic_by_id.get(symbol_id)
            if self._config.fusion_strategy == FusionStrategy.WEIGHTED:
                score = math.fsum(
                    (
                        self._config.lexical_weight
                        * lexical_normalized.get(symbol_id, 0.0),
                        self._config.semantic_weight
                        * semantic_normalized.get(symbol_id, 0.0),
                        self._config.graph_weight * graph_score,
                    )
                )
            else:
                score = math.fsum(
                    (
                        0.0
                        if lexical_hit is None
                        else self._config.lexical_weight
                        / (self._config.rrf_k + lexical_hit.rank),
                        0.0
                        if semantic_hit is None
                        else self._config.semantic_weight
                        / (self._config.rrf_k + semantic_hit.rank),
                        0.0
                        if not provenances
                        else self._config.graph_weight
                        * graph_score
                        / (self._config.rrf_k + min(item.hop for item in provenances)),
                    )
                )
            if not math.isfinite(score):
                raise HybridRetrievalError("fusion score must be finite")
            scored.append((score, symbol_id, provenances, graph_score))

        scored.sort(key=lambda item: (-item[0], symbol_id_key(item[1])))
        hits = []
        for rank, (score, symbol_id, provenances, graph_score) in enumerate(
            scored[:limit], start=1
        ):
            lexical_hit = lexical_by_id.get(symbol_id)
            semantic_hit = semantic_by_id.get(symbol_id)
            hits.append(
                HybridHit(
                    document=documents_by_id[symbol_id],
                    lexical_score=None if lexical_hit is None else float(lexical_hit.score),
                    lexical_rank=None if lexical_hit is None else lexical_hit.rank,
                    semantic_score=None if semantic_hit is None else float(semantic_hit.score),
                    semantic_rank=None if semantic_hit is None else semantic_hit.rank,
                    normalized_lexical_score=lexical_normalized.get(symbol_id, 0.0),
                    normalized_semantic_score=semantic_normalized.get(symbol_id, 0.0),
                    graph_score=graph_score,
                    graph_provenance=provenances,
                    fusion_strategy=self._config.fusion_strategy,
                    lexical_weight=self._config.lexical_weight,
                    semantic_weight=self._config.semantic_weight,
                    graph_weight=self._config.graph_weight,
                    score=score,
                    rank=rank,
                )
            )
        return HybridRetrievalResult(
            hits=tuple(hits),
            graph_context=ordered_graph,
            degraded=degraded,
            degradation_reason=degradation_reason,
            failure_provenance=tuple(failure_provenance),
            fusion_strategy=self._config.fusion_strategy,
        )
