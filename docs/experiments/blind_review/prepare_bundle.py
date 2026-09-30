"""Build a query-and-source-only Phase 6.2B preparation bundle offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATASET = ROOT / "docs/experiments/datasets/v1"
QUERIES = ROOT / "docs/experiments/queries/v1/queries.jsonl"
PACKET = HERE / "blank_second_judgment.jsonl"
GUIDE = HERE / "BLIND_REVIEW_README.md"
EXPECTED_QUERY_HASH = "5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba"
EXPECTED_DATASET_HASH = "164994a826fe51936d5fcb012a8d102967c33110787405fd3b0f7972efe8ade7"
EXPECTED_SELF_REVISION = "12391233daa2149ead4f451e920b2e0d8a1a6beb"
FIXTURE_DIRS = {
    "fixture-java-desk-queue": "desk-queue",
    "fixture-py-intake-queue": "intake-queue",
    "fixture-py-route-ledger": "route-ledger",
}
QUERY_KEYS = {
    "query_id", "query_set_version", "split", "language", "task_type",
    "dataset_id", "project_id", "query_text", "ground_truth_id",
    "authoring_source", "notes",
}
VISIBLE_KEYS = ("query_id", "query_text", "language", "task_type", "project_id", "split")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_relative(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid source path")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("noncanonical source path")
    path = Path(value)
    if path.is_absolute() or path.suffix not in (".py", ".java"):
        raise ValueError("source path outside the frozen source allowlist")
    if path.parts[:2] == ("docs", "thesis"):
        raise ValueError("protected thesis path is not a review source")
    return path


def _queries_and_packet() -> bytes:
    identity = json.loads((DATASET / "identity.json").read_text(encoding="utf-8"))
    if (identity["query_set_hash"] != EXPECTED_QUERY_HASH
            or identity["dataset_hash"] != EXPECTED_DATASET_HASH
            or identity["self_source_revision"] != EXPECTED_SELF_REVISION
            or identity["annotation_status"] != "drafted"):
        raise ValueError("draft identity changed; stop before preparing review material")

    rows = [json.loads(line) for line in QUERIES.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 72 or any(set(row) != QUERY_KEYS for row in rows):
        raise ValueError("frozen query schema or count changed")
    ids = [row["query_id"] for row in rows]
    if len(set(ids)) != 72:
        raise ValueError("duplicate query ID")
    rows.sort(key=lambda row: row["query_id"])
    if _digest(_canonical_bytes(rows)) != EXPECTED_QUERY_HASH:
        raise ValueError("frozen query identity mismatch")
    if Counter(row["split"] for row in rows) != {
        "english_test": 48, "english_dev": 12, "chinese_coverage": 12
    }:
        raise ValueError("query split allocation changed")

    packet = []
    for row in rows:
        visible = {key: row[key] for key in VISIBLE_KEYS}
        visible["review"] = {
            "reviewer_id": None,
            "started_at": None,
            "completed_at": None,
            "evidence": [],
            "no_relevant_source_found": None,
            "uncertainty_notes": None,
            "candidate_ambiguities": [],
            "questions_for_adjudication": [],
            "chinese_non_translation_notes": None,
            "masking_observation": None,
        }
        packet.append(visible)
    return b"".join(_canonical_bytes(row) + b"\n" for row in packet)


def _sources() -> tuple[list[dict], list[tuple[Path, bytes]]]:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    if manifest["dataset_hash"] != EXPECTED_DATASET_HASH:
        raise ValueError("dataset manifest identity mismatch")
    projects = manifest["projects"]
    if {project["project_id"] for project in projects} != {
        *FIXTURE_DIRS, "self-code-comments-agent"
    }:
        raise ValueError("source project set changed")

    catalog = []
    files = []
    for project in sorted(projects, key=lambda item: item["project_id"]):
        project_id = project["project_id"]
        revision = project["source_revision"]
        if project_id == "self-code-comments-agent":
            if project["source_kind"] != "self_repository" or revision != EXPECTED_SELF_REVISION:
                raise ValueError("self source revision changed")
        elif project["source_kind"] != "fixture" or revision != "fixture-v1":
            raise ValueError("fixture source revision changed")
        entries = project["files"]
        if len(entries) != project["file_count"]:
            raise ValueError("source file count changed")
        catalog_files = []
        for entry in sorted(entries, key=lambda item: item["relative_path"]):
            relative = _safe_relative(entry["relative_path"])
            if project_id == "self-code-comments-agent":
                raw = subprocess.check_output(
                    ["git", "show", f"{revision}:{relative.as_posix()}"], cwd=ROOT
                )
            else:
                root = DATASET / "fixtures" / FIXTURE_DIRS[project_id]
                source = root / relative
                if not source.resolve().is_relative_to(root.resolve()) or source.is_symlink():
                    raise ValueError("fixture source path escaped its root")
                raw = source.read_bytes()
            if _digest(raw) != entry["content_hash"]:
                raise ValueError("frozen source hash mismatch")
            output = Path("sources") / project_id / relative
            files.append((output, raw))
            catalog_files.append({
                "relative_path": relative.as_posix(),
                "sha256": entry["content_hash"],
            })
        catalog.append({
            "project_id": project_id,
            "source_revision": revision,
            "files": catalog_files,
        })
    if len(files) != 93 or len({path for path, _ in files}) != 93:
        raise ValueError("source bundle must contain exactly 93 unique files")
    return catalog, files


def _catalog_bytes(catalog: list[dict]) -> bytes:
    return json.dumps(
        {"projects": catalog}, ensure_ascii=False, sort_keys=True, indent=2
    ).encode("utf-8") + b"\n"


def _bundle(destination: Path) -> None:
    expected_packet = _queries_and_packet()
    if PACKET.read_bytes() != expected_packet:
        raise ValueError("blank packet differs from the frozen queries or contains filled fields")
    catalog, files = _sources()
    if destination.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("blind bundle must be outside the repository")
    if destination.exists() or not destination.parent.is_dir():
        raise ValueError("destination must be new and its parent must already exist")
    temporary = Path(tempfile.mkdtemp(prefix=".phase62b-blind-", dir=destination.parent))
    try:
        (temporary / "README.md").write_bytes(GUIDE.read_bytes())
        (temporary / "queries_for_second_judgment.jsonl").write_bytes(expected_packet)
        (temporary / "source_catalog.json").write_bytes(_catalog_bytes(catalog))
        for path, raw in files:
            target = temporary / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        temporary.rename(destination)
    except BaseException:
        shutil.rmtree(temporary)
        raise


def _verify_bundle(destination: Path) -> None:
    expected_packet = _queries_and_packet()
    if PACKET.read_bytes() != expected_packet:
        raise ValueError("tracked packet differs from the frozen queries")
    catalog, sources = _sources()
    expected = {
        Path("README.md"): GUIDE.read_bytes(),
        Path("queries_for_second_judgment.jsonl"): expected_packet,
        Path("source_catalog.json"): _catalog_bytes(catalog),
        **dict(sources),
    }
    if not destination.is_dir() or destination.is_symlink():
        raise ValueError("bundle is not an isolated directory")
    actual = {path.relative_to(destination): path for path in destination.rglob("*") if path.is_file()}
    if set(actual) != set(expected):
        raise ValueError("bundle contains missing or extra files")
    expected_dirs = {
        parent
        for relative in expected
        for parent in relative.parents
        if parent != Path(".")
    }
    actual_dirs = {
        path.relative_to(destination) for path in destination.rglob("*") if path.is_dir()
    }
    if actual_dirs != expected_dirs:
        raise ValueError("bundle contains missing or extra directories")
    if any(path.is_symlink() for path in destination.rglob("*")):
        raise ValueError("bundle contains a symlink")
    for relative, content in expected.items():
        if actual[relative].read_bytes() != content:
            raise ValueError(f"bundle content changed: {relative}")
    print(f"verified: 72 unique queries, {len(sources)} frozen source files, no extra files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-blank-packet", action="store_true")
    group.add_argument("--bundle", type=Path, metavar="NEW_DIRECTORY")
    group.add_argument("--verify-bundle", type=Path, metavar="DIRECTORY")
    args = parser.parse_args()
    if args.write_blank_packet:
        content = _queries_and_packet()
        with PACKET.open("xb") as output:
            output.write(content)
    elif args.bundle is not None:
        _bundle(args.bundle)
    else:
        _verify_bundle(args.verify_bundle)


if __name__ == "__main__":
    main()
