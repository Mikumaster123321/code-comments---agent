from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .schemas import SchemaValidationError
from .serialization import canonical_hash


CONTEXT_DIAGNOSTIC_FILENAME = "context_diagnostics.json"
CONTEXT_DIAGNOSTIC_MATRIX_IDS = frozenset({
    "RQ4-HYBRID-NO-GRAPH",
    "RQ4-HYBRID-GRAPH",
})
_SYNTHETIC_CONTEXT_DIAGNOSTIC_MATRIX_IDS = frozenset({
    "SYNTHETIC-RQ4-HYBRID-NO-GRAPH",
    "SYNTHETIC-RQ4-HYBRID-GRAPH",
})


def requires_context_diagnostics(matrix_run_id: str) -> bool:
    return matrix_run_id in (
        CONTEXT_DIAGNOSTIC_MATRIX_IDS | _SYNTHETIC_CONTEXT_DIAGNOSTIC_MATRIX_IDS
    )


def _non_negative(name: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise SchemaValidationError(f"context diagnostic {name} must be a non-negative integer")
    return value


def _identity(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise SchemaValidationError(f"context diagnostic {name} must be SHA-256")
    return value


def _git_revision(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise SchemaValidationError(f"context diagnostic {name} must be a full Git revision")
    return value


@dataclass(frozen=True)
class ContextQueryDiagnostic:
    query_id: str
    query_input_identity: str
    retrieval_identity: str
    relevant_ground_truth_evidence_rendered: int
    relevant_ground_truth_evidence_total: int
    relevant_ranked_hits_rendered: int
    relevant_ranked_hits_total: int
    budget_used: int
    budget: int
    snippet_count: int
    context_characters: int
    package_truncated: bool
    truncated_snippet_count: int
    ranked_hits_not_rendered: int
    graph_only_rendered_snippets: int
    retained_but_unrendered_graph_provenance_count: int

    def __post_init__(self) -> None:
        if type(self.query_id) is not str or not self.query_id:
            raise SchemaValidationError("context diagnostic query_id must be non-empty")
        _identity("query_input_identity", self.query_input_identity)
        _identity("retrieval_identity", self.retrieval_identity)
        for name in (
            "relevant_ground_truth_evidence_rendered",
            "relevant_ground_truth_evidence_total",
            "relevant_ranked_hits_rendered",
            "relevant_ranked_hits_total",
            "budget_used",
            "budget",
            "snippet_count",
            "context_characters",
            "truncated_snippet_count",
            "ranked_hits_not_rendered",
            "graph_only_rendered_snippets",
            "retained_but_unrendered_graph_provenance_count",
        ):
            _non_negative(name, getattr(self, name))
        if type(self.package_truncated) is not bool:
            raise SchemaValidationError("context diagnostic package_truncated must be bool")
        if self.budget == 0 or self.budget_used > self.budget:
            raise SchemaValidationError("context diagnostic budget is invalid")
        if self.context_characters != self.budget_used:
            raise SchemaValidationError("context characters must equal budget used")
        if self.truncated_snippet_count > self.snippet_count:
            raise SchemaValidationError("truncated snippet count exceeds snippet count")
        if self.relevant_ground_truth_evidence_rendered > self.relevant_ground_truth_evidence_total:
            raise SchemaValidationError("rendered relevant evidence exceeds total relevant evidence")
        if self.relevant_ranked_hits_rendered > self.relevant_ranked_hits_total:
            raise SchemaValidationError("rendered relevant ranked hits exceed total relevant ranked hits")

    @property
    def budget_utilization_ratio(self) -> float:
        return self.budget_used / self.budget

    def to_record(self) -> dict:
        return {
            "query_id": self.query_id,
            "query_input_identity": self.query_input_identity,
            "retrieval_identity": self.retrieval_identity,
            "relevant_ground_truth_evidence_rendered": self.relevant_ground_truth_evidence_rendered,
            "relevant_ground_truth_evidence_total": self.relevant_ground_truth_evidence_total,
            "relevant_ranked_hits_rendered": self.relevant_ranked_hits_rendered,
            "relevant_ranked_hits_total": self.relevant_ranked_hits_total,
            "budget_used": self.budget_used,
            "budget": self.budget,
            "budget_utilization_ratio": self.budget_utilization_ratio,
            "snippet_count": self.snippet_count,
            "context_characters": self.context_characters,
            "package_truncated": self.package_truncated,
            "truncated_snippet_count": self.truncated_snippet_count,
            "ranked_hits_not_rendered": self.ranked_hits_not_rendered,
            "graph_only_rendered_snippets": self.graph_only_rendered_snippets,
            "retained_but_unrendered_graph_provenance_count": self.retained_but_unrendered_graph_provenance_count,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ContextQueryDiagnostic:
        expected = set(cls.__dataclass_fields__) | {"budget_utilization_ratio"}
        if not isinstance(record, Mapping) or set(record) != expected:
            raise SchemaValidationError("context query diagnostic fields are invalid")
        value = cls(**{name: record[name] for name in cls.__dataclass_fields__})
        if record["budget_utilization_ratio"] != value.budget_utilization_ratio:
            raise SchemaValidationError("context diagnostic budget utilization does not recompute")
        return value


@dataclass(frozen=True)
class ContextDiagnosticArtifact:
    mode: str
    split: str
    run_id: str
    matrix_run_id: str
    config_identity: str
    corpus_revision: str
    execution_revision: str
    index_identity: str
    queries: tuple[ContextQueryDiagnostic, ...]

    def __post_init__(self) -> None:
        if self.mode not in {"synthetic", "dry_run", "formal"}:
            raise SchemaValidationError("context diagnostic mode is invalid")
        for name in ("split", "run_id", "matrix_run_id", "index_identity"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise SchemaValidationError(f"context diagnostic {name} must be non-empty")
        _identity("config_identity", self.config_identity)
        for name in ("corpus_revision", "execution_revision"):
            _git_revision(name, getattr(self, name))
        if not requires_context_diagnostics(self.matrix_run_id):
            raise SchemaValidationError("context diagnostic is bound to a non-required config")
        if (
            (self.mode == "synthetic" and self.matrix_run_id not in _SYNTHETIC_CONTEXT_DIAGNOSTIC_MATRIX_IDS)
            or (self.mode in {"dry_run", "formal"} and self.matrix_run_id not in CONTEXT_DIAGNOSTIC_MATRIX_IDS)
        ):
            raise SchemaValidationError("context diagnostic mode and config namespace differ")
        if (
            (self.mode == "dry_run" and self.split != "english_dev")
            or (self.mode == "formal" and self.split != "english_test")
        ):
            raise SchemaValidationError("context diagnostic mode and split differ")
        if type(self.queries) is not tuple or not self.queries or not all(
            isinstance(item, ContextQueryDiagnostic) for item in self.queries
        ):
            raise SchemaValidationError("context diagnostic queries must be non-empty and immutable")
        if tuple(item.query_id for item in self.queries) != tuple(
            sorted({item.query_id for item in self.queries})
        ):
            raise SchemaValidationError("context diagnostic query IDs must be unique and sorted")

    def _summary(self) -> dict:
        query_count = len(self.queries)
        snippet_count = sum(item.snippet_count for item in self.queries)
        budget = sum(item.budget for item in self.queries)
        budget_used = sum(item.budget_used for item in self.queries)
        truncated_snippets = sum(item.truncated_snippet_count for item in self.queries)
        package_truncations = sum(item.package_truncated for item in self.queries)
        return {
            "query_count": query_count,
            "relevant_ground_truth_evidence_rendered": sum(
                item.relevant_ground_truth_evidence_rendered for item in self.queries
            ),
            "relevant_ground_truth_evidence_total": sum(
                item.relevant_ground_truth_evidence_total for item in self.queries
            ),
            "relevant_ranked_hits_rendered": sum(
                item.relevant_ranked_hits_rendered for item in self.queries
            ),
            "relevant_ranked_hits_total": sum(
                item.relevant_ranked_hits_total for item in self.queries
            ),
            "budget_used": budget_used,
            "budget": budget,
            "budget_utilization_ratio": budget_used / budget,
            "snippet_count": snippet_count,
            "context_characters": sum(item.context_characters for item in self.queries),
            "package_truncation_count": package_truncations,
            "package_truncation_rate": package_truncations / query_count,
            "snippet_truncation_count": truncated_snippets,
            "snippet_truncation_rate": truncated_snippets / snippet_count if snippet_count else 0.0,
            "ranked_hits_not_rendered": sum(item.ranked_hits_not_rendered for item in self.queries),
            "graph_only_rendered_snippets": sum(
                item.graph_only_rendered_snippets for item in self.queries
            ),
            "retained_but_unrendered_graph_provenance_count": sum(
                item.retained_but_unrendered_graph_provenance_count for item in self.queries
            ),
        }

    def identity_record(self) -> dict:
        return {
            "schema_version": "context-diagnostic-v1",
            "kind": "ContextBuilderDiagnosticArtifact",
            "mode": self.mode,
            "split": self.split,
            "run_id": self.run_id,
            "matrix_run_id": self.matrix_run_id,
            "config_identity": self.config_identity,
            "corpus_revision": self.corpus_revision,
            "execution_revision": self.execution_revision,
            "index_identity": self.index_identity,
            "summary": self._summary(),
            "queries": [item.to_record() for item in self.queries],
        }

    @property
    def identity_hash(self) -> str:
        return canonical_hash(self.identity_record())

    def to_record(self) -> dict:
        return {**self.identity_record(), "artifact_identity": self.identity_hash}

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ContextDiagnosticArtifact:
        expected = {
            "schema_version", "kind", "mode", "split", "run_id", "matrix_run_id",
            "config_identity", "corpus_revision", "execution_revision", "index_identity",
            "summary", "queries", "artifact_identity",
        }
        if not isinstance(record, Mapping) or set(record) != expected:
            raise SchemaValidationError("context diagnostic artifact fields are invalid")
        if record["schema_version"] != "context-diagnostic-v1" or record["kind"] != "ContextBuilderDiagnosticArtifact":
            raise SchemaValidationError("context diagnostic artifact schema is invalid")
        queries = record["queries"]
        if type(queries) is not list:
            raise SchemaValidationError("context diagnostic queries must be a list")
        artifact = cls(
            mode=record["mode"], split=record["split"], run_id=record["run_id"],
            matrix_run_id=record["matrix_run_id"], config_identity=record["config_identity"],
            corpus_revision=record["corpus_revision"], execution_revision=record["execution_revision"],
            index_identity=record["index_identity"],
            queries=tuple(ContextQueryDiagnostic.from_record(item) for item in queries),
        )
        if record["summary"] != artifact._summary():
            raise SchemaValidationError("context diagnostic summary does not recompute")
        if record["artifact_identity"] != artifact.identity_hash:
            raise SchemaValidationError("context diagnostic artifact identity does not match")
        return artifact
