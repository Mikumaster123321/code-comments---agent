from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from project_intelligence import (
    DEFAULT_DOCUMENT_INSTRUCTION,
    DEFAULT_QUERY_INSTRUCTION,
    EmbeddingFingerprint,
)

from .serialization import canonical_hash, is_absolute_host_path


PROTOCOL_VERSION = "v3.1-phase6-protocol-v1"
E5_REPOSITORY = "intfloat/multilingual-e5-base"
E5_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"
E5_DIMENSION = 768
TOKEN_POLICY = "512-token-explicit-truncation-v1"


class ConfigValidationError(ValueError):
    pass


class RetrievalUnit(str, Enum):
    FILE = "file"
    SYMBOL = "symbol"
    CHUNK = "chunk"


class Strategy(str, Enum):
    LEXICAL = "lexical"
    EMBEDDING = "embedding"
    WEIGHTED = "weighted"
    RRF = "rrf"


class RunKind(str, Enum):
    SYNTHETIC = "synthetic"
    FORMAL = "formal"


class SemanticMode(str, Enum):
    NONE = "none"
    FAKE_TEST = "fake_test"
    REAL_E5 = "real_e5"


@dataclass(frozen=True)
class MetricConfig:
    recall_k: tuple[int, ...] = (1, 5, 10)
    mrr_cutoff: int = 10
    ndcg_k: int = 5
    precision_k: int = 5
    hit_rate_k: int = 5

    def __post_init__(self) -> None:
        if self.recall_k != (1, 5, 10):
            raise ConfigValidationError("recall_k must remain (1, 5, 10)")
        for name in ("mrr_cutoff", "ndcg_k", "precision_k", "hit_rate_k"):
            if getattr(self, name) != {"mrr_cutoff": 10}.get(name, 5):
                raise ConfigValidationError(f"{name} does not match the frozen protocol")

    def to_record(self) -> dict:
        return {
            "recall_k": list(self.recall_k),
            "mrr_cutoff": self.mrr_cutoff,
            "ndcg_k": self.ndcg_k,
            "precision_k": self.precision_k,
            "hit_rate_k": self.hit_rate_k,
        }


@dataclass(frozen=True)
class HybridExperimentConfig:
    lexical_weight: float = 1.0
    semantic_weight: float = 0.0
    graph_weight: float = 0.0
    rrf_k: int = 60

    def __post_init__(self) -> None:
        for name in ("lexical_weight", "semantic_weight", "graph_weight"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ConfigValidationError(f"{name} must be a finite number")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0:
                raise ConfigValidationError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, numeric)
        if self.lexical_weight not in {0.0, 1.0} or self.semantic_weight not in {0.0, 1.0}:
            raise ConfigValidationError("Lexical/Semantic weights must remain 0.0 or 1.0")
        if self.graph_weight not in {0.0, 0.25}:
            raise ConfigValidationError("Graph weight must remain 0.0 or 0.25")
        if self.rrf_k != 60:
            raise ConfigValidationError("rrf_k must remain 60")

    def to_record(self) -> dict:
        return {
            "lexical_weight": self.lexical_weight,
            "semantic_weight": self.semantic_weight,
            "graph_weight": self.graph_weight,
            "rrf_k": self.rrf_k,
        }


@dataclass(frozen=True)
class GraphExperimentConfig:
    enabled: bool = False
    max_hops: int = 1
    relations: tuple[str, ...] = ("contains", "imports")
    directions: tuple[str, ...] = ("forward", "reverse")
    signals: tuple[tuple[str, str], ...] = (
        ("contains", "forward"),
        ("contains", "reverse"),
        ("imports", "forward"),
        ("imports", "reverse"),
    )
    max_expanded_per_seed: int = 5
    max_total_context_nodes: int = 30
    contains_factor: float = 0.75
    imports_factor: float = 1.0
    forward_factor: float = 1.0
    reverse_factor: float = 0.8

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ConfigValidationError("graph enabled must be bool")
        expected = (1, ("contains", "imports"), ("forward", "reverse"), 5, 30)
        actual = (
            self.max_hops,
            self.relations,
            self.directions,
            self.max_expanded_per_seed,
            self.max_total_context_nodes,
        )
        if actual != expected:
            raise ConfigValidationError("Graph configuration differs from the protocol")
        allowed_signals = {
            ("contains", "forward"),
            ("contains", "reverse"),
            ("imports", "forward"),
            ("imports", "reverse"),
        }
        if (
            type(self.signals) is not tuple
            or not self.signals
            or any(type(item) is not tuple or item not in allowed_signals for item in self.signals)
            or len(set(self.signals)) != len(self.signals)
        ):
            raise ConfigValidationError("Graph signals must be unique frozen relation/direction pairs")
        canonical_signals = tuple(sorted(self.signals))
        if len(canonical_signals) not in {1, 4}:
            raise ConfigValidationError("Graph signals must be all four pairs or one RQ3 ablation pair")
        object.__setattr__(self, "signals", canonical_signals)
        if (
            self.contains_factor,
            self.imports_factor,
            self.forward_factor,
            self.reverse_factor,
        ) != (0.75, 1.0, 1.0, 0.8):
            raise ConfigValidationError("Graph score factors differ from the protocol")

    def to_record(self) -> dict:
        return {
            "enabled": self.enabled,
            "max_hops": self.max_hops,
            "relations": list(self.relations),
            "directions": list(self.directions),
            "signals": [list(item) for item in self.signals],
            "max_expanded_per_seed": self.max_expanded_per_seed,
            "max_total_context_nodes": self.max_total_context_nodes,
            "score_factors": {
                "contains": self.contains_factor,
                "imports": self.imports_factor,
                "forward": self.forward_factor,
                "reverse": self.reverse_factor,
            },
        }


@dataclass(frozen=True)
class FileExperimentConfig:
    identity: str = "relative_path"
    text_layout: str = "relative_path_newline_full_source"

    def __post_init__(self) -> None:
        if (self.identity, self.text_layout) != (
            "relative_path",
            "relative_path_newline_full_source",
        ):
            raise ConfigValidationError("File baseline configuration is frozen")

    def to_record(self) -> dict:
        return {"identity": self.identity, "text_layout": self.text_layout}


@dataclass(frozen=True)
class ChunkExperimentConfig:
    size: int = 1200
    overlap: int = 200
    stride: int = 1000
    boundary: str = "unicode_codepoint"

    def __post_init__(self) -> None:
        if (self.size, self.overlap, self.stride, self.boundary) != (
            1200,
            200,
            1000,
            "unicode_codepoint",
        ):
            raise ConfigValidationError("Chunk baseline configuration is frozen")

    def to_record(self) -> dict:
        return {
            "size": self.size,
            "overlap": self.overlap,
            "stride": self.stride,
            "boundary": self.boundary,
        }


def _embedding_record(fingerprint: EmbeddingFingerprint | None) -> dict | None:
    if fingerprint is None:
        return None
    if not isinstance(fingerprint, EmbeddingFingerprint):
        raise ConfigValidationError("embedding_fingerprint must be an EmbeddingFingerprint")
    if is_absolute_host_path(fingerprint.model_repository):
        raise ConfigValidationError("embedding identity must not contain an absolute path")
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
class BenchmarkConfig:
    dataset_version: str
    dataset_hash: str
    query_set_version: str
    query_set_hash: str
    ground_truth_version: str
    ground_truth_hash: str
    strategy: Strategy
    retrieval_unit: RetrievalUnit
    run_kind: RunKind = RunKind.SYNTHETIC
    semantic_mode: SemanticMode = SemanticMode.NONE
    top_k: int = 10
    metric: MetricConfig = MetricConfig()
    hybrid: HybridExperimentConfig = HybridExperimentConfig()
    graph: GraphExperimentConfig = GraphExperimentConfig()
    embedding_fingerprint: EmbeddingFingerprint | None = None
    file: FileExperimentConfig = FileExperimentConfig()
    chunk: ChunkExperimentConfig = ChunkExperimentConfig()
    protocol_version: str = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        for name in (
            "dataset_version",
            "dataset_hash",
            "query_set_version",
            "query_set_hash",
            "ground_truth_version",
            "ground_truth_hash",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ConfigValidationError(f"{name} must be a non-empty string")
            if is_absolute_host_path(value):
                raise ConfigValidationError(f"{name} must not contain an absolute path")
        for name, enum_type in (
            ("strategy", Strategy),
            ("retrieval_unit", RetrievalUnit),
            ("run_kind", RunKind),
            ("semantic_mode", SemanticMode),
        ):
            value = getattr(self, name)
            if not isinstance(value, enum_type):
                try:
                    object.__setattr__(self, name, enum_type(value))
                except (TypeError, ValueError) as error:
                    raise ConfigValidationError(f"invalid {name}") from error
        if self.protocol_version != PROTOCOL_VERSION:
            raise ConfigValidationError("protocol_version is not the frozen protocol")
        if self.top_k != 10:
            raise ConfigValidationError("top_k must remain 10")
        semantic_required = self.strategy in {
            Strategy.EMBEDDING,
            Strategy.WEIGHTED,
            Strategy.RRF,
        } and self.hybrid.semantic_weight > 0
        if semantic_required and self.semantic_mode is SemanticMode.NONE:
            raise ConfigValidationError("semantic strategy requires an explicit semantic mode")
        if not semantic_required and self.semantic_mode is not SemanticMode.NONE:
            raise ConfigValidationError("semantic mode is not applicable to this strategy")
        if semantic_required and self.embedding_fingerprint is None:
            raise ConfigValidationError("semantic strategy requires an embedding fingerprint")
        weights = (
            self.hybrid.lexical_weight,
            self.hybrid.semantic_weight,
            self.hybrid.graph_weight,
        )
        expected_weights = {
            Strategy.LEXICAL: (1.0, 0.0, 0.0),
            Strategy.EMBEDDING: (0.0, 1.0, 0.0),
        }.get(self.strategy)
        if self.strategy in {Strategy.WEIGHTED, Strategy.RRF}:
            expected_weights = (1.0, 1.0, 0.25 if self.graph.enabled else 0.0)
        if weights != expected_weights:
            raise ConfigValidationError("strategy weights do not match the frozen experiment matrix")
        if self.graph.enabled != (self.hybrid.graph_weight == 0.25):
            raise ConfigValidationError("Graph enabled state and frozen Graph weight must agree")
        if self.run_kind is RunKind.FORMAL:
            self.validate_formal_semantics()

    @property
    def semantic_required(self) -> bool:
        return self.semantic_mode is not SemanticMode.NONE

    def validate_formal_semantics(self) -> None:
        if not self.semantic_required:
            return
        if self.semantic_mode is not SemanticMode.REAL_E5:
            raise ConfigValidationError("formal semantic runs require real E5, never fake mode")
        fingerprint = self.embedding_fingerprint
        if fingerprint is None:
            raise ConfigValidationError("formal semantic runs require an E5 fingerprint")
        expected = (
            E5_REPOSITORY,
            E5_REVISION,
            E5_DIMENSION,
            "l2",
            "cosine",
            DEFAULT_QUERY_INSTRUCTION,
            DEFAULT_DOCUMENT_INSTRUCTION,
            TOKEN_POLICY,
        )
        actual = (
            fingerprint.model_repository,
            fingerprint.revision,
            fingerprint.dimension,
            fingerprint.normalization,
            fingerprint.similarity_metric,
            fingerprint.query_instruction,
            fingerprint.document_instruction,
            fingerprint.max_input_policy,
        )
        if actual != expected or fingerprint.runtime_kind != "transformers-torch":
            raise ConfigValidationError("formal semantic fingerprint is not the frozen real E5")

    def to_record(self) -> dict:
        return {
            "protocol_version": self.protocol_version,
            "dataset": {"version": self.dataset_version, "hash": self.dataset_hash},
            "query_set": {
                "version": self.query_set_version,
                "hash": self.query_set_hash,
            },
            "ground_truth": {
                "version": self.ground_truth_version,
                "hash": self.ground_truth_hash,
            },
            "strategy": self.strategy.value,
            "retrieval_unit": self.retrieval_unit.value,
            "run_kind": self.run_kind.value,
            "semantic_mode": self.semantic_mode.value,
            "top_k": self.top_k,
            "metric": self.metric.to_record(),
            "hybrid": self.hybrid.to_record(),
            "graph": self.graph.to_record(),
            "embedding_fingerprint": _embedding_record(self.embedding_fingerprint),
            "file": self.file.to_record(),
            "chunk": self.chunk.to_record(),
        }

    @property
    def identity_hash(self) -> str:
        return canonical_hash(self.to_record())

    @property
    def config_hash(self) -> str:
        return self.identity_hash
