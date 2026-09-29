from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile

from .context_diagnostics import (
    CONTEXT_DIAGNOSTIC_FILENAME,
    ContextDiagnosticArtifact,
    requires_context_diagnostics,
)
from .metrics import summarize_metrics
from .runner import AggregateStratum, BenchmarkRunResult
from .schemas import RunMetadata
from .serialization import (
    canonical_hash, canonical_json, canonical_jsonl, normalize_relative_path, sha256_hex,
)
from .reference import (
    ApprovalDecisionRecord, ApprovalPrerequisiteRecord, DryRunArtifactSet,
    DryRunConfigurationSet, DryRunReceipt, DryRunReceiptV2,
    ErratumRecord, EvidenceAuditRecord, EvidenceAuditSet, Phase62ClosureRecord,
    Phase62DocumentationDecisionRecord,
    ReferenceApprovalRecord, ReferenceRecord, ResolutionRecord,
)


class ArtifactCollisionError(FileExistsError):
    pass


_LIFECYCLE_RECORD_TYPES = (
    ReferenceRecord, EvidenceAuditRecord, EvidenceAuditSet, ErratumRecord,
    ResolutionRecord, ApprovalPrerequisiteRecord, ApprovalDecisionRecord,
    ReferenceApprovalRecord, Phase62ClosureRecord, DryRunReceipt,
    DryRunReceiptV2, DryRunConfigurationSet, DryRunArtifactSet,
    Phase62DocumentationDecisionRecord,
)


def write_lifecycle_artifact(root: str | Path, record: object, raw_blobs: dict[str, bytes] | None = None) -> Path:
    """Atomically publish one immutable evidence directory, never approval authority."""
    if type(record) not in _LIFECYCLE_RECORD_TYPES:
        raise TypeError("unsupported lifecycle artifact")
    blobs = {} if raw_blobs is None else dict(raw_blobs)
    if any(type(name) is not str or "/" in normalize_relative_path(name) or
           name in {"record.json", "record.json.sha256", "checksums.sha256"} or type(payload) is not bytes
           for name, payload in blobs.items()):
        raise ValueError("raw blobs require safe one-component byte filenames")
    for payload in blobs.values():
        try:
            canonical_json({"raw_evidence": payload.decode("utf-8")})
        except UnicodeError:
            raise ValueError("raw lifecycle evidence must be UTF-8") from None
    identity = record.identity_hash
    root_path = Path(root)
    destination = root_path / identity
    root_path.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ArtifactCollisionError("append-only lifecycle artifact already exists")
    record_bytes = canonical_json(record.to_record(), pretty=True).encode("utf-8")
    contents = {"record.json": record_bytes, "record.json.sha256": (sha256_hex(record_bytes) + "\n").encode("ascii"), **blobs}
    pending = Path(tempfile.mkdtemp(prefix=f".{identity}.pending-", dir=root_path))
    try:
        for name, payload in contents.items():
            (pending / name).write_bytes(payload)
        (pending / "checksums.sha256").write_text(
            "".join(f"{sha256_hex(payload)}  {name}\n" for name, payload in sorted(contents.items())),
            encoding="utf-8", newline="\n",
        )
        pending.rename(destination)
    except Exception:
        # Incomplete staging remains hidden and cannot be mistaken for publication.
        raise
    return destination


def validate_run_result(result: BenchmarkRunResult) -> None:
    """Recompute every derived aggregate field from immutable raw evidence."""
    if not isinstance(result, BenchmarkRunResult) or not result.raw_results:
        raise ValueError("a non-empty BenchmarkRunResult is required")
    raw = result.raw_results
    aggregate = result.aggregate
    raw_hash = sha256_hex(canonical_jsonl(item.to_record() for item in raw))
    strata = []
    for dimension in ("task_type", "language", "dataset_id", "split"):
        for value in sorted({getattr(item, dimension) for item in raw}):
            members = tuple(item for item in raw if getattr(item, dimension) == value)
            strata.append(AggregateStratum(dimension, value, summarize_metrics(members)))
    expected_status = (
        "invalid" if any(item.status == "invalid" for item in raw) else
        "failed" if any(item.status == "failed" for item in raw) else "success"
    )
    common = {
        (item.run_id, item.protocol_version, item.matrix_run_id, item.strategy,
         item.retrieval_unit, item.config_identity, item.index_identity)
        for item in raw
    }
    expected_common = {
        (aggregate.run_id, aggregate.protocol_version, aggregate.matrix_run_id,
         aggregate.strategy, aggregate.retrieval_unit, aggregate.config_hash,
         aggregate.index_identity)
    }
    splits = {item.split for item in raw}
    split = next(iter(splits)) if len(splits) == 1 else None
    expected_population = {
        "population": split,
        "split": split,
        "language": "all",
        "role": (
            "primary" if split == "english_test" else
            "development" if split == "english_dev" else
            "coverage" if split == "chinese_coverage" else None
        ),
    }
    diagnostic_required = requires_context_diagnostics(aggregate.matrix_run_id)
    diagnostic = result.context_diagnostic_artifact
    diagnostic_valid = (
        diagnostic is not None
        and aggregate.context_diagnostic_summary_reference == CONTEXT_DIAGNOSTIC_FILENAME
        and diagnostic.run_id == aggregate.run_id
        and diagnostic.matrix_run_id == aggregate.matrix_run_id
        and diagnostic.config_identity == aggregate.config_hash
        and diagnostic.execution_revision == aggregate.code_commit
        and diagnostic.index_identity == aggregate.index_identity
        and tuple(item.query_id for item in diagnostic.queries)
        == tuple(item.query_id for item in raw)
        and all(
            item.retrieval_identity == canonical_hash({
                "query_id": raw_item.query_id,
                "config_identity": raw_item.config_identity,
                "index_identity": raw_item.index_identity,
                "ranked_hits": [hit.to_record() for hit in raw_item.ranked_hits],
            })
            for item, raw_item in zip(diagnostic.queries, raw)
        )
    )
    if (
        raw_hash != aggregate.raw_results_sha256
        or summarize_metrics(raw) != aggregate.overall
        or tuple(strata) != aggregate.strata
        or aggregate.run_status != expected_status
        or common != expected_common
        or dict(aggregate.population_filters) != expected_population
        or (diagnostic_required and not diagnostic_valid)
        or (not diagnostic_required and (
            diagnostic is not None or aggregate.context_diagnostic_summary_reference is not None
        ))
    ):
        raise ValueError("aggregate evidence does not recompute exactly from raw results")


def write_run_artifacts(
    root: str | Path,
    result: BenchmarkRunResult,
    metadata: RunMetadata,
) -> Path:
    """Write one new run directory without ever replacing prior evidence."""

    if not isinstance(result, BenchmarkRunResult) or not isinstance(metadata, RunMetadata):
        raise TypeError("result and metadata types are required")
    validate_run_result(result)
    if result.aggregate.run_id != metadata.run_id or any(
        item.run_id != metadata.run_id for item in result.raw_results
    ):
        raise ValueError("run IDs must agree")
    diagnostic = result.context_diagnostic_artifact
    if diagnostic is not None and (
        diagnostic.mode != metadata.mode
        or diagnostic.split != metadata.split
        or diagnostic.corpus_revision != metadata.corpus_revision
        or diagnostic.execution_revision != metadata.execution_revision
    ):
        raise ValueError("context diagnostic authority binding differs from run metadata")
    run_id = normalize_relative_path(metadata.run_id)
    if "/" in run_id:
        raise ValueError("run_id must be one safe path component")
    root_path = Path(root)
    run_path = root_path / run_id
    root_path.mkdir(parents=True, exist_ok=True)
    if run_path.exists():
        error = FileExistsError(str(run_path))
        raise ArtifactCollisionError(
            "append-only policy forbids replacing an existing run ID"
        ) from error

    raw_content = canonical_jsonl(item.to_record() for item in result.raw_results)
    aggregate_content = canonical_json(result.aggregate.to_record(), pretty=True)
    diagnostic_content = (
        canonical_json(diagnostic.to_record(), pretty=True) if diagnostic is not None else None
    )
    output_checksums = (
        ("aggregate_results.json", sha256_hex(aggregate_content)),
        ("raw_results.jsonl", sha256_hex(raw_content)),
    ) + (() if diagnostic_content is None else (
        (CONTEXT_DIAGNOSTIC_FILENAME, sha256_hex(diagnostic_content)),
    ))
    manifest = replace(metadata, output_checksums=output_checksums)
    manifest_content = canonical_json(manifest.to_record(), pretty=True)
    contents = {
        "aggregate_results.json": aggregate_content,
        "raw_results.jsonl": raw_content,
        "run_manifest.json": manifest_content,
    }
    if diagnostic_content is not None:
        contents[CONTEXT_DIAGNOSTIC_FILENAME] = diagnostic_content
    pending_path = Path(tempfile.mkdtemp(prefix=f".{run_id}.pending-", dir=root_path))
    try:
        for name, content in contents.items():
            (pending_path / name).write_text(content, encoding="utf-8", newline="\n")
        checksum_lines = "".join(
            f"{sha256_hex(content)}  {name}\n" for name, content in sorted(contents.items())
        )
        (pending_path / "checksums.sha256").write_text(
            checksum_lines, encoding="utf-8", newline="\n"
        )
        pending_path.rename(run_path)
    except Exception:
        # The hidden pending directory is retained as explicitly non-authoritative evidence.
        raise
    return run_path


def load_context_diagnostic_artifact(run_path: str | Path) -> ContextDiagnosticArtifact:
    """Reload and verify one run's bound ContextBuilder diagnostic artifact."""

    path = Path(run_path)
    aggregate = json.loads((path / "aggregate_results.json").read_bytes())
    manifest = json.loads((path / "run_manifest.json").read_bytes())
    reference = aggregate.get("context_diagnostic_summary_reference")
    if reference != CONTEXT_DIAGNOSTIC_FILENAME:
        raise ValueError("run does not bind the required context diagnostic artifact")
    diagnostic_path = path / normalize_relative_path(reference)
    payload = diagnostic_path.read_bytes()
    actual_hash = sha256_hex(payload)
    checksum_rows = {}
    for line in (path / "checksums.sha256").read_text(encoding="ascii").splitlines():
        value, name = line.split("  ", 1)
        checksum_rows[name] = value
    output_checksums = manifest.get("output_checksums")
    if (
        checksum_rows.get(reference) != actual_hash
        or not isinstance(output_checksums, dict)
        or output_checksums.get(reference) != actual_hash
    ):
        raise ValueError("context diagnostic artifact checksum does not match")
    artifact = ContextDiagnosticArtifact.from_record(json.loads(payload))
    if (
        artifact.run_id != aggregate.get("run_id")
        or artifact.matrix_run_id != aggregate.get("matrix_run_id")
        or artifact.config_identity != aggregate.get("config_hash")
        or artifact.index_identity != aggregate.get("index_identity")
        or artifact.mode != manifest.get("mode")
        or artifact.split != manifest.get("split")
        or artifact.corpus_revision != manifest.get("corpus_revision")
        or artifact.execution_revision != manifest.get("execution_revision")
    ):
        raise ValueError("context diagnostic artifact binding does not match its run")
    return artifact
