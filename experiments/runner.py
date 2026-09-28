from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Protocol, Sequence, runtime_checkable

from code_maintenance import SymbolId
from project_intelligence import EmbeddingFingerprint

from .baselines import (
    CandidateIdentity,
    DatasetEvidenceRegistry,
    TruthMapper,
    serialize_candidate_identity,
)
from .config import BenchmarkConfig, Population, RunKind, SemanticMode
from .eligibility import (
    EligibilityError, ValidatedExecutionInputs, is_validator_issued,
    validate_formal_eligibility,
)
from .metrics import MetricSummary, MetricValues, compute_metrics, summarize_metrics
from .schemas import (
    DatasetManifest,
    GroundTruthRecord,
    QueryRecord,
    RunMetadata,
    SchemaValidationError,
    frozen_corpus_revision,
    symbol_id_to_record,
)
from .reference import ReferenceRecord
from .serialization import (
    canonical_hash,
    canonical_jsonl,
    immutable_mapping,
    normalize_relative_path,
    sha256_hex,
)


class BenchmarkRunnerError(Exception):
    pass


class FormalRunGuardError(BenchmarkRunnerError):
    pass


@dataclass(frozen=True)
class GraphProvenanceRecord:
    seed_identity: str
    relation: str
    direction: str
    hop: int
    node_identity: str

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value
            for value in (self.seed_identity, self.relation, self.direction, self.node_identity)
        ):
            raise SchemaValidationError("Graph provenance strings must be non-empty")
        if self.relation not in {"contains", "imports"}:
            raise SchemaValidationError("Graph provenance relation is invalid")
        if self.direction not in {"forward", "reverse"}:
            raise SchemaValidationError("Graph provenance direction is invalid")
        if type(self.hop) is not int or self.hop < 1:
            raise SchemaValidationError("Graph provenance hop must be positive")

    def to_record(self) -> dict:
        return {
            "seed_identity": self.seed_identity,
            "relation": self.relation,
            "direction": self.direction,
            "hop": self.hop,
            "node_identity": self.node_identity,
        }


def _score(name: str, value: float | None, *, normalized: bool = False) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaValidationError(f"{name} must be numeric or null")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise SchemaValidationError(f"{name} must be finite")
    if normalized and not 0 <= numeric <= 1:
        raise SchemaValidationError(f"{name} must be between zero and one")


@dataclass(frozen=True)
class StrategyHit:
    identity: CandidateIdentity
    relative_path: str
    rank: int
    symbol_id: SymbolId | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    raw_lexical_score: float | None = None
    raw_semantic_score: float | None = None
    normalized_lexical_score: float = 0.0
    normalized_semantic_score: float = 0.0
    graph_score: float = 0.0
    graph_provenance: tuple[GraphProvenanceRecord, ...] = ()
    final_score: float = 0.0

    def __post_init__(self) -> None:
        serialize_candidate_identity(self.identity)
        if type(self.rank) is not int or self.rank < 1:
            raise SchemaValidationError("strategy hit rank must be a positive integer")
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        if self.symbol_id is not None and not isinstance(self.symbol_id, SymbolId):
            raise SchemaValidationError("hit symbol_id must be SymbolId or null")
        if (self.start_offset is None) != (self.end_offset is None):
            raise SchemaValidationError("hit offsets must be both present or both null")
        if self.start_offset is not None and (
            type(self.start_offset) is not int
            or type(self.end_offset) is not int
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise SchemaValidationError("hit offsets are invalid")
        for name in ("raw_lexical_score", "raw_semantic_score", "final_score"):
            _score(name, getattr(self, name))
        for name in (
            "normalized_lexical_score",
            "normalized_semantic_score",
            "graph_score",
        ):
            _score(name, getattr(self, name), normalized=True)
        if type(self.graph_provenance) is not tuple or not all(
            isinstance(item, GraphProvenanceRecord) for item in self.graph_provenance
        ):
            raise SchemaValidationError("graph_provenance must be an immutable tuple")


@dataclass(frozen=True)
class StrategyResult:
    hits: tuple[StrategyHit, ...]
    degraded: bool = False
    degradation_reason: str | None = None
    token_diagnostics: tuple[Mapping[str, object], ...] = ()

    def __post_init__(self) -> None:
        if type(self.hits) is not tuple or not all(isinstance(item, StrategyHit) for item in self.hits):
            raise SchemaValidationError("strategy hits must be an immutable tuple")
        if type(self.degraded) is not bool:
            raise SchemaValidationError("degraded must be bool")
        if self.degraded != (self.degradation_reason is not None):
            raise SchemaValidationError("degraded state and reason must agree")
        if self.degradation_reason is not None and self.degradation_reason not in {
            "semantic_branch_failure", "semantic_timeout", "semantic_unavailable"
        }:
            raise SchemaValidationError("degradation_reason must be a frozen safe code")
        allowed_diagnostic_fields = {
            "identity",
            "kind",
            "untruncated_total_tokens",
            "effective_content_limit",
            "truncated",
            "dropped_token_count",
        }
        for diagnostic in self.token_diagnostics:
            if not isinstance(diagnostic, Mapping) or set(diagnostic) != allowed_diagnostic_fields:
                raise SchemaValidationError("token diagnostics must use the frozen safe fields")
            identity = diagnostic["identity"]
            if (
                not isinstance(identity, str)
                or not identity
                or not identity.startswith(("file:", "chunk:", "symbol:", "query:"))
            ):
                raise SchemaValidationError("token diagnostic identity must be a safe canonical ID")
            if diagnostic["kind"] not in {"query", "document"}:
                raise SchemaValidationError("token diagnostic kind is invalid")
            for name in (
                "untruncated_total_tokens",
                "effective_content_limit",
                "dropped_token_count",
            ):
                if type(diagnostic[name]) is not int or diagnostic[name] < 0:
                    raise SchemaValidationError(f"token diagnostic {name} is invalid")
            if type(diagnostic["truncated"]) is not bool:
                raise SchemaValidationError("token diagnostic truncated must be bool")
        object.__setattr__(
            self,
            "token_diagnostics",
            tuple(immutable_mapping(item) for item in self.token_diagnostics),
        )


@runtime_checkable
class BenchmarkStrategy(Protocol):
    @property
    def semantic_mode(self) -> SemanticMode: ...

    @property
    def index_identity(self) -> str: ...

    @property
    def embedding_fingerprint(self) -> EmbeddingFingerprint | None: ...

    def retrieve(self, query: QueryRecord, config: BenchmarkConfig) -> StrategyResult: ...


@dataclass(frozen=True)
class RankedHitRecord:
    rank: int
    candidate_identity: str
    relative_path: str
    symbol_id: SymbolId | None
    start_offset: int | None
    end_offset: int | None
    raw_lexical_score: float | None
    raw_semantic_score: float | None
    normalized_lexical_score: float
    normalized_semantic_score: float
    graph_score: float
    graph_provenance: tuple[GraphProvenanceRecord, ...]
    final_score: float
    relevance: int

    def __post_init__(self) -> None:
        if type(self.rank) is not int or self.rank < 1:
            raise SchemaValidationError("hit rank must be positive")
        if not isinstance(self.candidate_identity, str) or not self.candidate_identity:
            raise SchemaValidationError("candidate_identity must be non-empty")
        normalize_relative_path(self.relative_path)
        if type(self.relevance) is not int or self.relevance not in {0, 1, 2}:
            raise SchemaValidationError("hit relevance must be 0, 1, or 2")
        if self.symbol_id is not None and not isinstance(self.symbol_id, SymbolId):
            raise SchemaValidationError("ranked hit symbol_id must be SymbolId or null")
        if (self.start_offset is None) != (self.end_offset is None):
            raise SchemaValidationError("ranked hit offsets must both be present or null")
        if self.start_offset is not None and (
            type(self.start_offset) is not int
            or type(self.end_offset) is not int
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise SchemaValidationError("ranked hit offsets are invalid")
        for name in ("raw_lexical_score", "raw_semantic_score", "final_score"):
            _score(name, getattr(self, name))
        for name in (
            "normalized_lexical_score",
            "normalized_semantic_score",
            "graph_score",
        ):
            _score(name, getattr(self, name), normalized=True)
        if type(self.graph_provenance) is not tuple or not all(
            isinstance(item, GraphProvenanceRecord) for item in self.graph_provenance
        ):
            raise SchemaValidationError("ranked Graph provenance must be immutable")

    def to_record(self) -> dict:
        return {
            "rank": self.rank,
            "candidate_identity": self.candidate_identity,
            "relative_path": self.relative_path,
            "symbol_id": None if self.symbol_id is None else symbol_id_to_record(self.symbol_id),
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "raw_lexical_score": self.raw_lexical_score,
            "raw_semantic_score": self.raw_semantic_score,
            "normalized_lexical_score": self.normalized_lexical_score,
            "normalized_semantic_score": self.normalized_semantic_score,
            "graph_score": self.graph_score,
            "graph_provenance": [item.to_record() for item in self.graph_provenance],
            "final_score": self.final_score,
            "relevance": self.relevance,
        }


@dataclass(frozen=True)
class RawQueryResult:
    run_id: str
    experiment_id: str
    protocol_version: str
    matrix_run_id: str
    query_id: str
    split: str
    language: str
    task_type: str
    dataset_id: str
    project_id: str
    strategy: str
    retrieval_unit: str
    status: str
    failure_type: str | None
    failure_stage: str | None
    degraded: bool
    degradation_reason: str | None
    top_k: int
    retrieval_config_hash: str
    config_identity: str
    index_identity: str
    ranked_hits: tuple[RankedHitRecord, ...]
    metric_inputs: Mapping[str, int]
    metrics: MetricValues
    latency_ns: int
    embedding_fingerprint: Mapping[str, object] | None
    token_diagnostics: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        for name in (
            "run_id", "experiment_id", "protocol_version", "matrix_run_id", "query_id",
            "split", "language", "task_type", "dataset_id", "project_id", "strategy",
            "retrieval_unit", "retrieval_config_hash", "config_identity", "index_identity",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise SchemaValidationError(f"raw result {name} must be non-empty")
        if self.run_id != self.experiment_id:
            raise SchemaValidationError("experiment_id must identify the same append-only run")
        if self.status not in {"success", "failed", "invalid"}:
            raise SchemaValidationError("raw result status is invalid")
        if self.status == "success" and (self.failure_type or self.failure_stage):
            raise SchemaValidationError("successful result cannot contain failure metadata")
        if self.status != "success" and (not self.failure_type or not self.failure_stage):
            raise SchemaValidationError("failed/invalid result requires failure metadata")
        if self.status != "success" and (
            self.ranked_hits or self.metrics != MetricValues.zero()
        ):
            raise SchemaValidationError("failed/invalid result must have zero metrics and no normal hits")
        if self.config_identity != self.retrieval_config_hash:
            raise SchemaValidationError("config identity aliases must agree")
        if type(self.top_k) is not int or self.top_k <= 0:
            raise SchemaValidationError("raw result top_k must be positive")
        if type(self.ranked_hits) is not tuple or not all(
            isinstance(item, RankedHitRecord) for item in self.ranked_hits
        ):
            raise SchemaValidationError("ranked_hits must be immutable")
        if [item.rank for item in self.ranked_hits] != list(range(1, len(self.ranked_hits) + 1)):
            raise SchemaValidationError("ranked hit ranks must be contiguous")
        if len({item.candidate_identity for item in self.ranked_hits}) != len(self.ranked_hits):
            raise SchemaValidationError("ranked identities must be unique")
        if type(self.latency_ns) is not int or self.latency_ns < 0:
            raise SchemaValidationError("latency_ns must be non-negative")
        if not isinstance(self.metrics, MetricValues):
            raise SchemaValidationError("raw metrics must be MetricValues")
        if not isinstance(self.metric_inputs, Mapping) or not self.metric_inputs:
            raise SchemaValidationError("raw metric_inputs must preserve active-unit truth")
        if any(
            not isinstance(identity, str)
            or not identity
            or type(grade) is not int
            or grade not in {0, 1, 2}
            for identity, grade in self.metric_inputs.items()
        ):
            raise SchemaValidationError("raw metric_inputs are invalid")
        object.__setattr__(self, "metric_inputs", immutable_mapping(self.metric_inputs))
        if self.embedding_fingerprint is not None:
            object.__setattr__(
                self,
                "embedding_fingerprint",
                immutable_mapping(self.embedding_fingerprint),
            )
        object.__setattr__(
            self,
            "token_diagnostics",
            tuple(immutable_mapping(item) for item in self.token_diagnostics),
        )
        if type(self.degraded) is not bool or self.degraded != (
            self.degradation_reason is not None
        ):
            raise SchemaValidationError("raw degraded state and reason must agree")

    def to_record(self) -> dict:
        return {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "protocol_version": self.protocol_version,
            "matrix_run_id": self.matrix_run_id,
            "query_id": self.query_id,
            "split": self.split,
            "language": self.language,
            "task_type": self.task_type,
            "dataset_id": self.dataset_id,
            "project_id": self.project_id,
            "strategy": self.strategy,
            "retrieval_unit": self.retrieval_unit,
            "status": self.status,
            "failure_status": self.status,
            "failure_type": self.failure_type,
            "failure_stage": self.failure_stage,
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason,
            "top_k": self.top_k,
            "retrieval_config_hash": self.retrieval_config_hash,
            "config_identity": self.config_identity,
            "index_identity": self.index_identity,
            "ranked_hits": [item.to_record() for item in self.ranked_hits],
            "metric_inputs": dict(sorted(self.metric_inputs.items())),
            "metrics": self.metrics.to_record(),
            "latency_ns": self.latency_ns,
            "embedding_fingerprint": self.embedding_fingerprint,
            "token_diagnostics": list(self.token_diagnostics),
        }


@dataclass(frozen=True)
class AggregateStratum:
    dimension: str
    value: str
    summary: MetricSummary

    def __post_init__(self) -> None:
        if not isinstance(self.dimension, str) or not self.dimension:
            raise SchemaValidationError("stratum dimension must be non-empty")
        if not isinstance(self.value, str) or not self.value:
            raise SchemaValidationError("stratum value must be non-empty")
        if not isinstance(self.summary, MetricSummary):
            raise SchemaValidationError("stratum summary must be MetricSummary")

    def to_record(self) -> dict:
        return {"dimension": self.dimension, "value": self.value, **self.summary.to_record()}


@dataclass(frozen=True)
class AggregateResult:
    run_id: str
    protocol_version: str
    matrix_run_id: str
    strategy: str
    retrieval_unit: str
    run_status: str
    dataset_version: str
    dataset_hash: str
    query_set_version: str
    query_set_hash: str
    ground_truth_version: str
    ground_truth_hash: str
    config_hash: str
    code_commit: str
    embedding_fingerprint: Mapping[str, object] | None
    index_identity: str
    population_filters: Mapping[str, str]
    overall: MetricSummary
    strata: tuple[AggregateStratum, ...]
    context_diagnostic_summary_reference: str | None
    performance_artifact_reference: str | None
    raw_results_sha256: str
    aggregation_implementation_version: str
    aggregate_created_at: str

    def __post_init__(self) -> None:
        for name in (
            "run_id", "protocol_version", "matrix_run_id", "strategy", "retrieval_unit",
            "dataset_version", "query_set_version", "ground_truth_version", "code_commit",
            "index_identity", "aggregation_implementation_version", "aggregate_created_at",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise SchemaValidationError(f"aggregate {name} must be non-empty")
        for name in (
            "dataset_hash", "query_set_hash", "ground_truth_hash", "config_hash",
            "raw_results_sha256",
        ):
            value = getattr(self, name)
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise SchemaValidationError(f"aggregate {name} must be SHA-256")
        if not isinstance(self.overall, MetricSummary):
            raise SchemaValidationError("aggregate overall must be MetricSummary")
        if self.run_status not in {"success", "failed", "invalid"}:
            raise SchemaValidationError("aggregate run_status is invalid")
        expected_status = (
            "invalid" if self.overall.invalid_count else
            "failed" if self.overall.failure_count else "success"
        )
        if self.run_status != expected_status:
            raise SchemaValidationError("aggregate run_status does not match raw counts")
        if type(self.strata) is not tuple or not all(
            isinstance(item, AggregateStratum) for item in self.strata
        ):
            raise SchemaValidationError("aggregate strata must be immutable")
        if not isinstance(self.population_filters, Mapping):
            raise SchemaValidationError("population_filters must be a mapping")
        object.__setattr__(
            self, "population_filters", immutable_mapping(self.population_filters)
        )
        if self.embedding_fingerprint is not None:
            object.__setattr__(
                self,
                "embedding_fingerprint",
                immutable_mapping(self.embedding_fingerprint),
            )

    def to_record(self) -> dict:
        return {
            "run_id": self.run_id,
            "protocol_version": self.protocol_version,
            "matrix_run_id": self.matrix_run_id,
            "strategy": self.strategy,
            "retrieval_unit": self.retrieval_unit,
            "run_status": self.run_status,
            "dataset": {"version": self.dataset_version, "hash": self.dataset_hash},
            "query_set": {"version": self.query_set_version, "hash": self.query_set_hash},
            "ground_truth": {"version": self.ground_truth_version, "hash": self.ground_truth_hash},
            "config_hash": self.config_hash,
            "code_commit": self.code_commit,
            "embedding_fingerprint": self.embedding_fingerprint,
            "index_identity": self.index_identity,
            "population_filters": dict(sorted(self.population_filters.items())),
            "denominator_count": self.overall.query_count,
            "counts": {
                "success": self.overall.success_count,
                "failure": self.overall.failure_count,
                "invalid": self.overall.invalid_count,
                "degraded": self.overall.degraded_count,
            },
            "macro_metrics": self.overall.metrics.to_record(),
            "latency": {
                "median_ns": self.overall.latency_median_ns,
                "p95_ns": self.overall.latency_p95_ns,
            },
            "strata": [item.to_record() for item in self.strata],
            "context_diagnostic_summary_reference": self.context_diagnostic_summary_reference,
            "performance_artifact_reference": self.performance_artifact_reference,
            "raw_results_sha256": self.raw_results_sha256,
            "aggregation_implementation_version": self.aggregation_implementation_version,
            "aggregate_created_at": self.aggregate_created_at,
        }


@dataclass(frozen=True)
class BenchmarkRunResult:
    raw_results: tuple[RawQueryResult, ...]
    aggregate: AggregateResult


def _fingerprint_record(fingerprint: EmbeddingFingerprint | None) -> dict | None:
    if fingerprint is None:
        return None
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


class BenchmarkRunner:
    def __init__(
        self,
        *,
        allow_formal: bool = False,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        if type(allow_formal) is not bool or not callable(clock_ns):
            raise BenchmarkRunnerError("invalid runner construction")
        self._allow_formal = allow_formal
        self._clock_ns = clock_ns

    def run(
        self,
        *,
        dataset: DatasetManifest,
        queries: Iterable[QueryRecord],
        truth: Iterable[GroundTruthRecord | ReferenceRecord],
        config: BenchmarkConfig,
        strategy: BenchmarkStrategy,
        metadata: RunMetadata,
        evidence_registry: DatasetEvidenceRegistry,
        matrix_run_id: str | None = None,
        validated_inputs: ValidatedExecutionInputs | None = None,
    ) -> BenchmarkRunResult:
        query_values = tuple(sorted(tuple(queries), key=lambda item: item.query_id))
        truth_values = tuple(truth)
        if config.run_kind in {RunKind.DRY_RUN, RunKind.FORMAL}:
            if not is_validator_issued(validated_inputs):
                raise FormalRunGuardError("runtime evidence requires authoritative validated execution inputs")
            try:
                renewed = validate_formal_eligibility(
                    purpose=config.run_kind, repository_root=validated_inputs.repository_root,
                    requested_config=config, selected_reference_approval=validated_inputs.approval_identity,
                    runtime_evidence=validated_inputs.runtime_evidence,
                    code_commit=validated_inputs.code_commit,
                    dry_run_receipt=validated_inputs.dry_run_receipt_path,
                )
            except EligibilityError:
                raise FormalRunGuardError("authoritative eligibility no longer validates") from None
            if (dataset != renewed.dataset or query_values != renewed.queries or
                truth_values != renewed.reference or
                metadata.approved_reference_identity != renewed.approval_identity or
                metadata.reference_hash != renewed.reference_identity or
                metadata.execution_revision != renewed.code_commit or
                metadata.corpus_revision != frozen_corpus_revision(renewed.dataset) or
                canonical_hash(metadata.runtime.to_record()) != renewed.runtime_identity):
                raise FormalRunGuardError("execution inputs differ from validated authority")
        elif validated_inputs is not None:
            raise FormalRunGuardError("synthetic execution cannot consume formal authority")
        self._validate_inputs(
            dataset, query_values, truth_values, config, strategy, metadata, evidence_registry
        )
        if matrix_run_id is not None and matrix_run_id != config.matrix_run_id:
            raise BenchmarkRunnerError("matrix_run_id must come from the immutable config")
        truth_by_id = {item.ground_truth_id: item for item in truth_values}
        selected_queries = tuple(item for item in query_values if item.split == config.population.value)
        if not selected_queries:
            raise BenchmarkRunnerError("configured population has no queries")
        raw: list[RawQueryResult] = []
        for query in selected_queries:
            annotation = truth_by_id[query.ground_truth_id]
            candidates = evidence_registry.candidates_for(query.project_id, config.retrieval_unit)
            mapper = TruthMapper(annotation, evidence_registry.symbol_ranges_for(query.project_id))
            relevance = mapper.relevance_map(candidates)
            start = self._clock_ns()
            latency: int | None = None
            try:
                output = strategy.retrieve(query, config)
                latency = self._elapsed(start)
                for hit in output.hits:
                    evidence_registry.validate_retrieved(
                        query.project_id, config.retrieval_unit, hit.identity,
                        hit.relative_path, hit.symbol_id, hit.start_offset, hit.end_offset,
                    )
                if config.run_kind in {RunKind.DRY_RUN, RunKind.FORMAL} and config.semantic_required and output.degraded:
                    ranked = ()
                    metrics = MetricValues.zero()
                    status = "invalid"
                    failure_type = "FormalDegradedResult"
                    failure_stage = "retrieval"
                else:
                    ranked = self._ranked_records(output.hits, relevance, config.top_k)
                    metrics = compute_metrics(
                        (item.candidate_identity for item in ranked), relevance, config=config.metric
                    )
                    status = "success"
                    failure_type = None
                    failure_stage = None
            except Exception as error:
                if latency is None:
                    latency = self._elapsed(start)
                output = StrategyResult(())
                ranked = ()
                metrics = compute_metrics((), relevance, failed=True, config=config.metric)
                status = "failed"
                failure_type = type(error).__name__
                failure_stage = "retrieval"
            raw.append(
                RawQueryResult(
                    run_id=metadata.run_id,
                    experiment_id=metadata.run_id,
                    protocol_version=config.protocol_version,
                    matrix_run_id=config.matrix_run_id,
                    query_id=query.query_id,
                    split=query.split,
                    language=query.language,
                    task_type=query.task_type,
                    dataset_id=query.dataset_id,
                    project_id=query.project_id,
                    strategy=config.strategy.value,
                    retrieval_unit=config.retrieval_unit.value,
                    status=status,
                    failure_type=failure_type,
                    failure_stage=failure_stage,
                    degraded=output.degraded,
                    degradation_reason=output.degradation_reason,
                    top_k=config.top_k,
                    retrieval_config_hash=config.identity_hash,
                    config_identity=config.identity_hash,
                    index_identity=strategy.index_identity,
                    ranked_hits=ranked,
                    metric_inputs=dict(sorted(relevance.items())),
                    metrics=metrics,
                    latency_ns=latency,
                    embedding_fingerprint=_fingerprint_record(strategy.embedding_fingerprint),
                    token_diagnostics=output.token_diagnostics,
                )
            )
        raw_values = tuple(raw)
        raw_sha = sha256_hex(canonical_jsonl(item.to_record() for item in raw_values))
        strata: list[AggregateStratum] = []
        for dimension in ("task_type", "language", "dataset_id", "split"):
            values = sorted({getattr(item, dimension) for item in raw_values})
            for value in values:
                members = tuple(item for item in raw_values if getattr(item, dimension) == value)
                strata.append(AggregateStratum(dimension, value, summarize_metrics(members)))
        aggregate = AggregateResult(
            run_id=metadata.run_id,
            protocol_version=config.protocol_version,
            matrix_run_id=config.matrix_run_id,
            strategy=config.strategy.value,
            retrieval_unit=config.retrieval_unit.value,
            run_status=("invalid" if any(item.status == "invalid" for item in raw_values) else
                        "failed" if any(item.status == "failed" for item in raw_values) else "success"),
            dataset_version=config.dataset_version,
            dataset_hash=config.dataset_hash,
            query_set_version=config.query_set_version,
            query_set_hash=config.query_set_hash,
            ground_truth_version=config.ground_truth_version,
            ground_truth_hash=config.ground_truth_hash,
            config_hash=config.identity_hash,
            code_commit=metadata.execution_revision,
            embedding_fingerprint=_fingerprint_record(strategy.embedding_fingerprint),
            index_identity=strategy.index_identity,
            population_filters={
                "population": config.population.value,
                "split": config.population.value,
                "language": "all",
                "role": "primary" if config.population is Population.ENGLISH_TEST else
                        "development" if config.population is Population.ENGLISH_DEV else "coverage",
            },
            overall=summarize_metrics(raw_values),
            strata=tuple(strata),
            context_diagnostic_summary_reference=None,
            performance_artifact_reference=None,
            raw_results_sha256=raw_sha,
            aggregation_implementation_version="phase6.1-aggregate-v1",
            aggregate_created_at=metadata.ended_at,
        )
        return BenchmarkRunResult(raw_values, aggregate)

    def _elapsed(self, start: int) -> int:
        end = self._clock_ns()
        if type(start) is not int or type(end) is not int or end < start:
            raise BenchmarkRunnerError("clock must be monotonic integer nanoseconds")
        return end - start

    @staticmethod
    def _ranked_records(
        hits: Sequence[StrategyHit], relevance: Mapping[str, int], top_k: int
    ) -> tuple[RankedHitRecord, ...]:
        records: list[RankedHitRecord] = []
        seen: set[str] = set()
        ordered = sorted(hits, key=lambda item: item.rank)
        if [item.rank for item in ordered] != list(range(1, len(ordered) + 1)):
            raise BenchmarkRunnerError("strategy hit ranks must be unique and contiguous")
        for hit in ordered:
            identity = serialize_candidate_identity(hit.identity)
            if identity in seen:
                continue
            if identity not in relevance:
                raise BenchmarkRunnerError("strategy returned a candidate outside its catalog")
            seen.add(identity)
            records.append(
                RankedHitRecord(
                    rank=hit.rank,
                    candidate_identity=identity,
                    relative_path=hit.relative_path,
                    symbol_id=hit.symbol_id,
                    start_offset=hit.start_offset,
                    end_offset=hit.end_offset,
                    raw_lexical_score=hit.raw_lexical_score,
                    raw_semantic_score=hit.raw_semantic_score,
                    normalized_lexical_score=hit.normalized_lexical_score,
                    normalized_semantic_score=hit.normalized_semantic_score,
                    graph_score=hit.graph_score,
                    graph_provenance=hit.graph_provenance,
                    final_score=hit.final_score,
                    relevance=relevance[identity],
                )
            )
            if len(records) == top_k:
                break
        return tuple(records)

    @staticmethod
    def _validate_inputs(
        dataset: DatasetManifest,
        queries: Iterable[QueryRecord],
        truth: Iterable[GroundTruthRecord | ReferenceRecord],
        config: BenchmarkConfig,
        strategy: BenchmarkStrategy,
        metadata: RunMetadata,
        evidence_registry: DatasetEvidenceRegistry,
    ) -> None:
        if not isinstance(dataset, DatasetManifest) or not isinstance(config, BenchmarkConfig):
            raise BenchmarkRunnerError("dataset/config types are invalid")
        if not isinstance(metadata, RunMetadata):
            raise BenchmarkRunnerError("metadata must be RunMetadata")
        if not isinstance(evidence_registry, DatasetEvidenceRegistry):
            raise BenchmarkRunnerError("evidence_registry must be validated dataset evidence")
        if evidence_registry.manifest != dataset:
            raise BenchmarkRunnerError("evidence registry does not match dataset manifest")
        if not isinstance(strategy, BenchmarkStrategy):
            raise BenchmarkRunnerError("strategy does not implement BenchmarkStrategy")
        query_values = tuple(queries)
        truth_values = tuple(truth)
        if not query_values or not all(isinstance(item, QueryRecord) for item in query_values):
            raise BenchmarkRunnerError("queries must be a non-empty QueryRecord collection")
        truth_kind = ReferenceRecord if config.run_kind in {RunKind.DRY_RUN, RunKind.FORMAL} else GroundTruthRecord
        if not truth_values or not all(type(item) is truth_kind for item in truth_values):
            raise BenchmarkRunnerError("truth type does not match execution purpose")
        if len({item.query_id for item in query_values}) != len(query_values):
            raise BenchmarkRunnerError("query IDs must be unique")
        if len({item.ground_truth_id for item in truth_values}) != len(truth_values):
            raise BenchmarkRunnerError("ground-truth IDs must be unique")
        truth_by_id = {item.ground_truth_id: item for item in truth_values}
        projects = {item.project_id for item in dataset.projects}
        for query in query_values:
            annotation = truth_by_id.get(query.ground_truth_id)
            if annotation is None or annotation.query_id != query.query_id:
                raise BenchmarkRunnerError("query/truth linkage is invalid")
            if query.dataset_id != dataset.dataset_id or query.project_id not in projects:
                raise BenchmarkRunnerError("query does not belong to dataset manifest")
            if (annotation.dataset_id, annotation.project_id) != (
                query.dataset_id,
                query.project_id,
            ):
                raise BenchmarkRunnerError("truth does not belong to query dataset/project")
            evidence_registry.validate_truth(annotation)
        query_hash = canonical_hash([item.to_record() for item in sorted(query_values, key=lambda item: item.query_id)])
        truth_hash = (config.ground_truth_hash if truth_kind is ReferenceRecord else
                      canonical_hash([item.to_record() for item in sorted(truth_values, key=lambda item: item.query_id)]))
        versions = {item.query_set_version for item in query_values}
        truth_versions = ({config.ground_truth_version} if truth_kind is ReferenceRecord else
                          {item.ground_truth_version for item in truth_values})
        if (
            dataset.version != config.dataset_version
            or dataset.dataset_hash != config.dataset_hash
            or versions != {config.query_set_version}
            or query_hash != config.query_set_hash
            or truth_versions != {config.ground_truth_version}
            or truth_hash != config.ground_truth_hash
        ):
            raise BenchmarkRunnerError("frozen input version/hash does not match config")
        if config.semantic_mode is not strategy.semantic_mode:
            raise FormalRunGuardError("configured semantic mode does not match strategy")
        if config.embedding_fingerprint != strategy.embedding_fingerprint:
            raise FormalRunGuardError("configured embedding fingerprint does not match strategy")
        if metadata.embedding_fingerprint != _fingerprint_record(strategy.embedding_fingerprint):
            raise FormalRunGuardError("run metadata embedding fingerprint does not match strategy")
        if metadata.config_hashes != (config.identity_hash,):
            raise BenchmarkRunnerError("run metadata does not identify the exact config")
        if (
            metadata.mode != config.run_kind.value
            or metadata.split != config.population.value
            or metadata.dataset_id != dataset.dataset_id
            or metadata.dataset_version != dataset.version
            or metadata.dataset_hash != dataset.dataset_hash
            or metadata.path_manifest_hash != dataset.path_manifest_hash
            or metadata.protocol_version != config.protocol_version
            or metadata.query_set_hash != query_hash
            or metadata.ground_truth_hash != truth_hash
            or metadata.index_identity != strategy.index_identity
        ):
            raise BenchmarkRunnerError("run metadata does not match benchmark inputs")
        if config.run_kind in {RunKind.DRY_RUN, RunKind.FORMAL}:
            gate = metadata.formal_gate
            dependencies = dict(metadata.runtime.dependencies)
            if (
                (gate is not None and gate.runner_code_commit != metadata.execution_revision)
                or metadata.corpus_revision != frozen_corpus_revision(dataset)
                or metadata.dirty_state
                or metadata.runtime.python_version != "3.12.14"
                or metadata.runtime.python_implementation != "CPython"
                or dependencies.get("torch") != "2.8.0"
                or dependencies.get("transformers") != "4.56.2"
                or metadata.runtime.device != "cpu"
                or metadata.runtime.dtype != "float32"
                or not metadata.runtime.network_disabled
                or not metadata.runtime.model_local_files_only
                or (config.semantic_required and metadata.model_cache_verified is not True)
            ):
                raise FormalRunGuardError("formal gate/runtime evidence is incomplete or mismatched")
