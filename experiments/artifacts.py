from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .runner import BenchmarkRunResult
from .schemas import RunMetadata
from .serialization import canonical_json, canonical_jsonl, normalize_relative_path, sha256_hex


class ArtifactCollisionError(FileExistsError):
    pass


def write_run_artifacts(
    root: str | Path,
    result: BenchmarkRunResult,
    metadata: RunMetadata,
) -> Path:
    """Write one new run directory without ever replacing prior evidence."""

    if not isinstance(result, BenchmarkRunResult) or not isinstance(metadata, RunMetadata):
        raise TypeError("result and metadata types are required")
    if result.aggregate.run_id != metadata.run_id or any(
        item.run_id != metadata.run_id for item in result.raw_results
    ):
        raise ValueError("run IDs must agree")
    run_id = normalize_relative_path(metadata.run_id)
    if "/" in run_id:
        raise ValueError("run_id must be one safe path component")
    root_path = Path(root)
    run_path = root_path / run_id
    try:
        run_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
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
    try:
        for name, content in contents.items():
            (run_path / name).write_text(content, encoding="utf-8", newline="\n")
        checksum_lines = "".join(
            f"{sha256_hex(content)}  {name}\n" for name, content in sorted(contents.items())
        )
        (run_path / "checksums.sha256").write_text(
            checksum_lines, encoding="utf-8", newline="\n"
        )
    except Exception:
        # Preserve a partial directory as failure evidence; append-only policy still applies.
        raise
    return run_path
