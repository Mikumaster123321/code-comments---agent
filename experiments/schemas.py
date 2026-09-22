from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from code_maintenance import SymbolId, SymbolKind

from .serialization import canonical_hash, immutable_mapping, normalize_relative_path


class SchemaValidationError(ValueError):
    pass


_SPLITS = {"english_dev", "english_test", "chinese_coverage"}
_LANGUAGES = {"python", "java"}
_TASK_TYPES = {
    "symbol_lookup",
    "feature_localization",
    "dependency_questions",
    "bug_localization",
    "maintenance_tasks",
    "cross_file_understanding",
}
_SOURCE_KINDS = {"self_repository", "fixture"}
_ANNOTATION_STATUSES = {"drafted", "reviewed", "adjudicated", "frozen"}
_RUN_STATUSES = {"success", "failed", "invalid"}


def _non_empty(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaValidationError(f"{name} must be a non-empty string")
    return value


def _sha256(name: str, value: object) -> str:
    text = _non_empty(name, value)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise SchemaValidationError(f"{name} must be a lowercase SHA-256 hex digest")
    return text


def _timestamp(name: str, value: object) -> str:
    text = _non_empty(name, value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise SchemaValidationError(f"{name} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise SchemaValidationError(f"{name} must include a UTC offset")
    return text


def _exact(record: Mapping[str, Any], fields: set[str], schema: str) -> None:
    if not isinstance(record, Mapping):
        raise SchemaValidationError(f"{schema} must be an object")
    missing = fields - set(record)
    extra = set(record) - fields
    if missing or extra:
        raise SchemaValidationError(
            f"{schema} fields mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )


def symbol_id_to_record(symbol_id: SymbolId) -> dict:
    if not isinstance(symbol_id, SymbolId):
        raise SchemaValidationError("symbol_id must be a SymbolId")
    return {
        "language": symbol_id.language,
        "relative_path": symbol_id.relative_path,
        "qualified_name": symbol_id.qualified_name,
        "kind": symbol_id.kind.value,
        "semantic_disambiguator": symbol_id.semantic_disambiguator,
        "fallback_line": symbol_id.fallback_line,
    }


def symbol_id_from_record(record: Mapping[str, Any]) -> SymbolId:
    fields = {
        "language",
        "relative_path",
        "qualified_name",
        "kind",
        "semantic_disambiguator",
        "fallback_line",
    }
    _exact(record, fields, "SymbolId")
    language = _non_empty("symbol_id.language", record["language"])
    relative_path = normalize_relative_path(record["relative_path"])
    qualified_name = _non_empty("symbol_id.qualified_name", record["qualified_name"])
    try:
        kind = SymbolKind(record["kind"])
    except (TypeError, ValueError) as error:
        raise SchemaValidationError("symbol_id.kind is invalid") from error
    semantic_disambiguator = record["semantic_disambiguator"]
    if semantic_disambiguator is not None:
        _non_empty("symbol_id.semantic_disambiguator", semantic_disambiguator)
    fallback_line = record["fallback_line"]
    if fallback_line is not None and (type(fallback_line) is not int or fallback_line < 1):
        raise SchemaValidationError("symbol_id.fallback_line must be a positive integer or null")
    return SymbolId(
        language,
        relative_path,
        qualified_name,
        kind,
        semantic_disambiguator,
        fallback_line,
    )


def symbol_identity(symbol_id: SymbolId) -> str:
    from .serialization import canonical_json

    return "symbol:" + canonical_json(symbol_id_to_record(symbol_id))


@dataclass(frozen=True)
class DatasetFile:
    relative_path: str
    content_hash: str
    path_role: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        _sha256("content_hash", self.content_hash)
        if self.path_role not in {"production", "test", "fixture"}:
            raise SchemaValidationError("path_role must be production, test, or fixture")

    def to_record(self) -> dict:
        return {
            "relative_path": self.relative_path,
            "content_hash": self.content_hash,
            "path_role": self.path_role,
        }


@dataclass(frozen=True)
class DatasetProject:
    project_id: str
    version: str
    source_kind: str
    source_revision: str
    fixture_hash: str | None
    language: str
    files: tuple[DatasetFile, ...]
    file_count: int
    symbol_count: int
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _non_empty("project_id", self.project_id)
        _non_empty("project version", self.version)
        if self.source_kind not in _SOURCE_KINDS:
            raise SchemaValidationError("source_kind is invalid")
        _non_empty("source_revision", self.source_revision)
        if self.source_kind == "fixture":
            _sha256("fixture_hash", self.fixture_hash)
        elif self.fixture_hash is not None:
            raise SchemaValidationError("self_repository must not have fixture_hash")
        if self.language not in _LANGUAGES:
            raise SchemaValidationError("project language is invalid")
        if type(self.files) is not tuple or not all(isinstance(item, DatasetFile) for item in self.files):
            raise SchemaValidationError("files must be an immutable DatasetFile tuple")
        canonical = tuple(sorted(self.files, key=lambda item: item.relative_path))
        if len({item.relative_path for item in canonical}) != len(canonical):
            raise SchemaValidationError("dataset project contains duplicate file paths")
        object.__setattr__(self, "files", canonical)
        if self.file_count != len(self.files):
            raise SchemaValidationError("file_count does not match files")
        if type(self.symbol_count) is not int or self.symbol_count < 0:
            raise SchemaValidationError("symbol_count must be a non-negative integer")
        if type(self.limitations) is not tuple or not all(
            isinstance(item, str) and item for item in self.limitations
        ):
            raise SchemaValidationError("limitations must be an immutable string tuple")

    def to_record(self) -> dict:
        return {
            "project_id": self.project_id,
            "version": self.version,
            "source_kind": self.source_kind,
            "source_revision": self.source_revision,
            "fixture_hash": self.fixture_hash,
            "language": self.language,
            "files": [item.to_record() for item in self.files],
            "file_count": self.file_count,
            "symbol_count": self.symbol_count,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    version: str
    projects: tuple[DatasetProject, ...]
    dataset_hash: str | None = None

    def __post_init__(self) -> None:
        _non_empty("dataset_id", self.dataset_id)
        _non_empty("dataset version", self.version)
        if type(self.projects) is not tuple or not all(
            isinstance(item, DatasetProject) for item in self.projects
        ):
            raise SchemaValidationError("projects must be an immutable DatasetProject tuple")
        canonical = tuple(sorted(self.projects, key=lambda item: item.project_id))
        if not canonical or len({item.project_id for item in canonical}) != len(canonical):
            raise SchemaValidationError("projects must be non-empty and uniquely identified")
        object.__setattr__(self, "projects", canonical)
        expected = canonical_hash(self.identity_record())
        if self.dataset_hash is not None and self.dataset_hash != expected:
            raise SchemaValidationError("dataset_hash does not match manifest contents")
        object.__setattr__(self, "dataset_hash", expected)

    def identity_record(self) -> dict:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "projects": [item.to_record() for item in self.projects],
        }

    def to_record(self) -> dict:
        return {**self.identity_record(), "dataset_hash": self.dataset_hash}


@dataclass(frozen=True)
class QueryRecord:
    query_id: str
    query_set_version: str
    split: str
    language: str
    task_type: str
    dataset_id: str
    project_id: str
    query_text: str
    ground_truth_id: str
    authoring_source: str
    notes: str | None

    def __post_init__(self) -> None:
        for name in (
            "query_id",
            "query_set_version",
            "dataset_id",
            "project_id",
            "query_text",
            "ground_truth_id",
        ):
            _non_empty(name, getattr(self, name))
        if self.split not in _SPLITS:
            raise SchemaValidationError("query split is invalid")
        if self.language not in _LANGUAGES:
            raise SchemaValidationError("query language is invalid")
        if self.task_type not in _TASK_TYPES:
            raise SchemaValidationError("query task_type is invalid")
        if self.authoring_source not in _SOURCE_KINDS:
            raise SchemaValidationError("query authoring_source is invalid")
        if self.notes is not None and not isinstance(self.notes, str):
            raise SchemaValidationError("query notes must be a string or null")

    def to_record(self) -> dict:
        return {
            "query_id": self.query_id,
            "query_set_version": self.query_set_version,
            "split": self.split,
            "language": self.language,
            "task_type": self.task_type,
            "dataset_id": self.dataset_id,
            "project_id": self.project_id,
            "query_text": self.query_text,
            "ground_truth_id": self.ground_truth_id,
            "authoring_source": self.authoring_source,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class EvidenceRecord:
    relative_path: str
    symbol_id: SymbolId | None
    start_offset: int | None
    end_offset: int | None
    start_line: int | None
    end_line: int | None
    relevance: int
    rationale: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", normalize_relative_path(self.relative_path))
        if self.symbol_id is not None:
            if not isinstance(self.symbol_id, SymbolId):
                raise SchemaValidationError("evidence symbol_id must be a SymbolId or null")
            if self.symbol_id.relative_path != self.relative_path:
                raise SchemaValidationError("evidence path must match symbol_id")
        if (self.start_offset is None) != (self.end_offset is None):
            raise SchemaValidationError("source offsets must be both present or both null")
        if self.start_offset is not None and (
            type(self.start_offset) is not int
            or type(self.end_offset) is not int
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise SchemaValidationError("source offsets must be a non-empty end-exclusive span")
        if (self.start_line is None) != (self.end_line is None):
            raise SchemaValidationError("source lines must be both present or both null")
        if self.start_line is not None and (
            type(self.start_line) is not int
            or type(self.end_line) is not int
            or self.start_line < 1
            or self.end_line < self.start_line
        ):
            raise SchemaValidationError("source lines are invalid")
        if self.symbol_id is None and self.start_offset is None:
            raise SchemaValidationError("evidence requires a SymbolId or source span")
        if type(self.relevance) is not int or self.relevance not in {0, 1, 2}:
            raise SchemaValidationError("relevance must be 0, 1, or 2")
        _non_empty("rationale", self.rationale)

    def to_record(self) -> dict:
        return {
            "relative_path": self.relative_path,
            "symbol_id": None if self.symbol_id is None else symbol_id_to_record(self.symbol_id),
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "relevance": self.relevance,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class GroundTruthRecord:
    ground_truth_id: str
    ground_truth_version: str
    query_id: str
    dataset_id: str
    project_id: str
    evidence: tuple[EvidenceRecord, ...]
    annotation_status: str
    primary_annotator_id: str
    reviewer_id: str
    adjudicator_id: str | None
    created_at: str
    reviewed_at: str

    def __post_init__(self) -> None:
        for name in (
            "ground_truth_id",
            "ground_truth_version",
            "query_id",
            "dataset_id",
            "project_id",
            "primary_annotator_id",
            "reviewer_id",
        ):
            _non_empty(name, getattr(self, name))
        if self.annotation_status not in _ANNOTATION_STATUSES:
            raise SchemaValidationError("annotation_status is invalid")
        if self.adjudicator_id is not None:
            _non_empty("adjudicator_id", self.adjudicator_id)
        if self.annotation_status == "adjudicated" and self.adjudicator_id is None:
            raise SchemaValidationError("adjudicated truth requires adjudicator_id")
        _timestamp("created_at", self.created_at)
        _timestamp("reviewed_at", self.reviewed_at)
        if type(self.evidence) is not tuple or not all(
            isinstance(item, EvidenceRecord) for item in self.evidence
        ):
            raise SchemaValidationError("evidence must be an immutable EvidenceRecord tuple")
        if not any(item.relevance > 0 for item in self.evidence):
            raise SchemaValidationError("ground truth requires at least one relevant item")
        keys = [
            (
                item.relative_path,
                item.symbol_id,
                item.start_offset,
                item.end_offset,
            )
            for item in self.evidence
        ]
        if len(keys) != len(set(keys)):
            raise SchemaValidationError("ground truth contains duplicate evidence")
        object.__setattr__(
            self,
            "evidence",
            tuple(sorted(self.evidence, key=lambda item: (item.relative_path, item.start_offset or -1, item.end_offset or -1, str(item.symbol_id or ""), item.relevance))),
        )

    def to_record(self) -> dict:
        return {
            "ground_truth_id": self.ground_truth_id,
            "ground_truth_version": self.ground_truth_version,
            "query_id": self.query_id,
            "dataset_id": self.dataset_id,
            "project_id": self.project_id,
            "evidence": [item.to_record() for item in self.evidence],
            "annotation_status": self.annotation_status,
            "primary_annotator_id": self.primary_annotator_id,
            "reviewer_id": self.reviewer_id,
            "adjudicator_id": self.adjudicator_id,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
        }


def _dataset_file(record: Mapping[str, Any]) -> DatasetFile:
    _exact(record, {"relative_path", "content_hash", "path_role"}, "DatasetFile")
    return DatasetFile(**record)


def _dataset_project(record: Mapping[str, Any]) -> DatasetProject:
    fields = {
        "project_id", "version", "source_kind", "source_revision", "fixture_hash",
        "language", "files", "file_count", "symbol_count", "limitations",
    }
    _exact(record, fields, "DatasetProject")
    return DatasetProject(
        **{key: record[key] for key in fields - {"files", "limitations"}},
        files=tuple(_dataset_file(item) for item in record["files"]),
        limitations=tuple(record["limitations"]),
    )


def dataset_manifest_from_record(record: Mapping[str, Any]) -> DatasetManifest:
    fields = {"dataset_id", "version", "projects", "dataset_hash"}
    _exact(record, fields, "DatasetManifest")
    return DatasetManifest(
        dataset_id=record["dataset_id"],
        version=record["version"],
        projects=tuple(_dataset_project(item) for item in record["projects"]),
        dataset_hash=record["dataset_hash"],
    )


def query_from_record(record: Mapping[str, Any]) -> QueryRecord:
    fields = {
        "query_id", "query_set_version", "split", "language", "task_type",
        "dataset_id", "project_id", "query_text", "ground_truth_id",
        "authoring_source", "notes",
    }
    _exact(record, fields, "QueryRecord")
    return QueryRecord(**record)


def evidence_from_record(record: Mapping[str, Any]) -> EvidenceRecord:
    fields = {
        "relative_path", "symbol_id", "start_offset", "end_offset", "start_line",
        "end_line", "relevance", "rationale",
    }
    _exact(record, fields, "EvidenceRecord")
    return EvidenceRecord(
        **{key: record[key] for key in fields - {"symbol_id"}},
        symbol_id=(
            None if record["symbol_id"] is None else symbol_id_from_record(record["symbol_id"])
        ),
    )


def ground_truth_from_record(record: Mapping[str, Any]) -> GroundTruthRecord:
    fields = {
        "ground_truth_id", "ground_truth_version", "query_id", "dataset_id",
        "project_id", "evidence", "annotation_status", "primary_annotator_id",
        "reviewer_id", "adjudicator_id", "created_at", "reviewed_at",
    }
    _exact(record, fields, "GroundTruthRecord")
    return GroundTruthRecord(
        **{key: record[key] for key in fields - {"evidence"}},
        evidence=tuple(evidence_from_record(item) for item in record["evidence"]),
    )


def _read_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SchemaValidationError(f"cannot load JSON: {type(error).__name__}") from error


def _read_jsonl(path: str | Path) -> tuple[Mapping[str, Any], ...]:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        if any(not line.strip() for line in lines):
            raise SchemaValidationError("JSONL must not contain blank records")
        return tuple(json.loads(line) for line in lines)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SchemaValidationError(f"cannot load JSONL: {type(error).__name__}") from error


def load_dataset_manifest(path: str | Path) -> DatasetManifest:
    return dataset_manifest_from_record(_read_json(path))


def load_queries(path: str | Path) -> tuple[QueryRecord, ...]:
    queries = tuple(query_from_record(item) for item in _read_jsonl(path))
    if len({item.query_id for item in queries}) != len(queries):
        raise SchemaValidationError("query_id values must be unique")
    return tuple(sorted(queries, key=lambda item: item.query_id))


def load_ground_truth(path: str | Path) -> tuple[GroundTruthRecord, ...]:
    records = tuple(ground_truth_from_record(item) for item in _read_jsonl(path))
    if len({item.ground_truth_id for item in records}) != len(records):
        raise SchemaValidationError("ground_truth_id values must be unique")
    if len({item.query_id for item in records}) != len(records):
        raise SchemaValidationError("ground truth must have one record per query")
    return tuple(sorted(records, key=lambda item: item.query_id))


@dataclass(frozen=True)
class RuntimeMetadata:
    python_implementation: str
    python_version: str
    dependencies: tuple[tuple[str, str], ...]
    os_name: str
    os_build: str
    cpu_model: str
    physical_cores: int
    logical_cores: int
    ram_bytes: int
    power_mode: str
    device: str
    dtype: str
    thread_settings: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        for name in (
            "python_implementation", "python_version", "os_name", "os_build",
            "cpu_model", "power_mode", "device", "dtype",
        ):
            _non_empty(name, getattr(self, name))
        for name in ("physical_cores", "logical_cores", "ram_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise SchemaValidationError(f"{name} must be a positive integer")
        for name in ("dependencies", "thread_settings"):
            values = getattr(self, name)
            if type(values) is not tuple or not all(
                type(item) is tuple and len(item) == 2 and all(isinstance(part, str) and part for part in item)
                for item in values
            ):
                raise SchemaValidationError(f"{name} must contain string pairs")
            object.__setattr__(self, name, tuple(sorted(values)))

    def to_record(self) -> dict:
        return {
            "python_implementation": self.python_implementation,
            "python_version": self.python_version,
            "dependencies": dict(self.dependencies),
            "os_name": self.os_name,
            "os_build": self.os_build,
            "cpu_model": self.cpu_model,
            "physical_cores": self.physical_cores,
            "logical_cores": self.logical_cores,
            "ram_bytes": self.ram_bytes,
            "power_mode": self.power_mode,
            "device": self.device,
            "dtype": self.dtype,
            "thread_settings": dict(self.thread_settings),
        }


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    protocol_id: str
    protocol_version: str
    protocol_hash: str
    dataset_id: str
    dataset_version: str
    dataset_hash: str
    path_manifest_hash: str
    query_set_version: str
    query_set_hash: str
    ground_truth_version: str
    ground_truth_hash: str
    config_hashes: tuple[str, ...]
    self_repository_commit: str
    runner_code_commit: str
    dirty_state: bool
    embedding_fingerprint: Mapping[str, Any] | None
    model_cache_verified: bool | None
    index_identity: str
    runtime: RuntimeMetadata
    random_seed: int | None
    python_hash_seed: str
    started_at: str
    ended_at: str
    output_checksums: tuple[tuple[str, str], ...]
    operator_id: str
    independent_audit_status: str

    def __post_init__(self) -> None:
        for name in (
            "run_id", "protocol_id", "protocol_version", "dataset_id", "dataset_version",
            "query_set_version", "ground_truth_version", "self_repository_commit",
            "runner_code_commit", "index_identity", "python_hash_seed", "operator_id",
            "independent_audit_status",
        ):
            _non_empty(name, getattr(self, name))
        for name in (
            "protocol_hash", "dataset_hash", "path_manifest_hash", "query_set_hash",
            "ground_truth_hash",
        ):
            _sha256(name, getattr(self, name))
        if type(self.config_hashes) is not tuple or not self.config_hashes:
            raise SchemaValidationError("config_hashes must be a non-empty tuple")
        for value in self.config_hashes:
            _sha256("config_hash", value)
        object.__setattr__(self, "config_hashes", tuple(sorted(self.config_hashes)))
        if type(self.dirty_state) is not bool:
            raise SchemaValidationError("dirty_state must be bool")
        if self.model_cache_verified is not None and type(self.model_cache_verified) is not bool:
            raise SchemaValidationError("model_cache_verified must be bool or null")
        if self.embedding_fingerprint is not None:
            if not isinstance(self.embedding_fingerprint, Mapping):
                raise SchemaValidationError("embedding_fingerprint must be an object or null")
            object.__setattr__(
                self,
                "embedding_fingerprint",
                immutable_mapping(self.embedding_fingerprint),
            )
        if not isinstance(self.runtime, RuntimeMetadata):
            raise SchemaValidationError("runtime must be RuntimeMetadata")
        if self.random_seed is not None and type(self.random_seed) is not int:
            raise SchemaValidationError("random_seed must be int or null")
        _timestamp("started_at", self.started_at)
        _timestamp("ended_at", self.ended_at)
        if type(self.output_checksums) is not tuple:
            raise SchemaValidationError("output_checksums must be an immutable tuple")
        for path, digest in self.output_checksums:
            normalize_relative_path(path)
            _sha256("output checksum", digest)
        object.__setattr__(self, "output_checksums", tuple(sorted(self.output_checksums)))

    def deterministic_record(self) -> dict:
        return {
            "protocol": {"id": self.protocol_id, "version": self.protocol_version, "hash": self.protocol_hash},
            "dataset": {"id": self.dataset_id, "version": self.dataset_version, "hash": self.dataset_hash, "path_manifest_hash": self.path_manifest_hash},
            "query_set": {"version": self.query_set_version, "hash": self.query_set_hash},
            "ground_truth": {"version": self.ground_truth_version, "hash": self.ground_truth_hash},
            "config_hashes": list(self.config_hashes),
            "self_repository_commit": self.self_repository_commit,
            "runner_code_commit": self.runner_code_commit,
            "dirty_state": self.dirty_state,
            "embedding_fingerprint": self.embedding_fingerprint,
            "model_cache_verified": self.model_cache_verified,
            "index_identity": self.index_identity,
            "random_seed": self.random_seed,
            "python_hash_seed": self.python_hash_seed,
        }

    def to_record(self) -> dict:
        return {
            "run_id": self.run_id,
            **self.deterministic_record(),
            "environment": self.runtime.to_record(),
            "execution": {"started_at": self.started_at, "ended_at": self.ended_at},
            "output_checksums": dict(self.output_checksums),
            "operator_id": self.operator_id,
            "independent_audit_status": self.independent_audit_status,
        }
