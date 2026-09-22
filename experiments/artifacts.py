from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile

from .metrics import summarize_metrics
from .runner import AggregateStratum, BenchmarkRunResult
from .schemas import RunMetadata
from .serialization import canonical_json, canonical_jsonl, normalize_relative_path, sha256_hex


class ArtifactCollisionError(FileExistsError):
    pass


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
    if (
        raw_hash != aggregate.raw_results_sha256
        or summarize_metrics(raw) != aggregate.overall
        or tuple(strata) != aggregate.strata
        or aggregate.run_status != expected_status
        or common != expected_common
        or dict(aggregate.population_filters) != expected_population
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
    output_checksums = (
        ("aggregate_results.json", sha256_hex(aggregate_content)),
        ("raw_results.jsonl", sha256_hex(raw_content)),
    )
    manifest = replace(metadata, output_checksums=output_checksums)
    manifest_content = canonical_json(manifest.to_record(), pretty=True)
    contents = {
        "aggregate_results.json": aggregate_content,
        "raw_results.jsonl": raw_content,
        "run_manifest.json": manifest_content,
    }
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
