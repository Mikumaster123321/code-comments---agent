"""Independently validate prepared audit inputs against frozen Git data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from code_maintenance.adapters import JavaAdapter
from code_maintenance.domain import SourceFile
from experiments.schemas import symbol_id_to_record


DEFAULT_DIRECTORY = Path(__file__).resolve().parent
SOURCE_COMMIT = "1ed215e6a4c4505898207111bbdee720772ca461"
BASE = "docs/experiments/"
SOURCE_PREFIX = BASE + "datasets/v1/fixtures/desk-queue/"
SYMBOL_FIELDS = {
    "language", "relative_path", "qualified_name", "kind",
    "semantic_disambiguator", "fallback_line",
}
SOURCE_RE = re.compile(
    r"\[\[SOURCE_BEGIN path=([^\s\]]+) sha256=([0-9a-f]{64}) bytes=(\d+)\]\]\n"
    r"(.*?)\[\[SOURCE_END path=([^\]]+)\]\]\n",
    re.S,
)


def git_bytes(path: str) -> bytes:
    if path.startswith("/") or ".." in Path(path).parts:
        raise AssertionError(f"unsafe source path: {path}")
    return subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{path}"], cwd=ROOT)


def git_json(path: str) -> dict:
    return json.loads(git_bytes(path))


def git_rows(path: str) -> list[dict]:
    return [json.loads(row) for row in git_bytes(path).decode("utf-8").splitlines()]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_hash(value: object) -> str:
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def block(prompt: str, name: str) -> object:
    begin, end = f"[[{name}_BEGIN]]\n", f"\n[[{name}_END]]"
    assert prompt.count(begin) == prompt.count(end) == 1, name
    return json.loads(prompt.split(begin, 1)[1].split(end, 1)[0])


def symbol_span(symbol: object, text: str) -> tuple[int, int]:
    lines = text.split("\n")
    start = sum(len(line) + 1 for line in lines[:symbol.start_line - 1])
    end = start + len("\n".join(lines[symbol.start_line - 1:symbol.end_line]))
    return start, end


def validate() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    args = parser.parse_args()
    directory = args.directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_bytes())
    assert manifest["status"] == "PREPARED / NOT EXECUTED"
    assert manifest["source_commit"] == SOURCE_COMMIT
    addendum = git_bytes(BASE + "Experiment_Protocol_Addendum_D_V3_1_0.md")
    assert sha(addendum) == manifest["method_addendum_sha256"]
    identity = git_json(BASE + "datasets/v1/identity.json")
    dataset = git_json(BASE + "datasets/v1/manifest.json")
    queries = git_rows(BASE + "queries/v1/queries.jsonl")
    truths = git_rows(BASE + "ground_truth/v1/ground_truth.jsonl")
    assert canonical_hash(sorted(queries, key=lambda x: x["query_id"])) == identity["query_set_hash"]
    assert canonical_hash(sorted(truths, key=lambda x: x["query_id"])) == identity["ground_truth_hash"]
    assert dataset["dataset_hash"] == identity["dataset_hash"] == manifest["dataset_hash"]
    assert manifest["query_set_hash"] == identity["query_set_hash"]
    assert manifest["draft_truth_hash"] == identity["ground_truth_hash"]
    assert manifest["query_set_version"] == identity["query_set_version"]
    assert manifest["draft_truth_version"] == identity["ground_truth_version"]
    project = next(p for p in dataset["projects"] if p["project_id"] == "fixture-java-desk-queue")
    assert manifest["project_id"] == project["project_id"]
    assert manifest["source_revision"] == project["source_revision"] == "fixture-v1"
    assert manifest["fixture_hash"] == project["fixture_hash"]
    files = {f["relative_path"]: f for f in project["files"]}
    assert len(files) == 6
    source_bytes = {path: git_bytes(SOURCE_PREFIX + path) for path in files}
    assert all(sha(raw) == files[path]["content_hash"] for path, raw in source_bytes.items())
    fixture_rows = [
        {"path": path, "language": "java", "content_hash": sha(source_bytes[path])}
        for path in sorted(files)
    ]
    assert canonical_hash(fixture_rows) == project["fixture_hash"]
    adapter = JavaAdapter()
    symbols = {}
    for path, raw in source_bytes.items():
        text = raw.decode("utf-8")
        assert "\r" not in text
        for symbol in adapter.parse_symbols(SourceFile(project["project_id"], path, "java", text)):
            key = json.dumps(symbol_id_to_record(symbol.id), ensure_ascii=False, sort_keys=True)
            assert key not in symbols
            symbols[key] = (symbol, text)

    section = addendum.decode("utf-8").split("## 4. 12 条 English-test Evidence Audit 的预注册", 1)[1].split("## 5.", 1)[0]
    prereg_ids = re.findall(r"`(et-[a-z]{2}-(?:ja|py)-\d{2})`", section)
    groups: dict[str, list[dict]] = defaultdict(list)
    for query in queries:
        if query["split"] == "english_test":
            groups[query["task_type"]].append(query)
    expected = sorted(q["query_id"] for group in groups.values() for q in sorted(group, key=lambda x: x["query_id"])[:2])
    assert len(groups) == 6 and all(len(group) == 8 for group in groups.values())
    assert prereg_ids == expected and len(expected) == len(set(expected)) == 12
    assert set(expected) == {q["query_id"] for q in queries if q["split"] == "english_test" and q["language"] == "java"}
    assert [x["query_id"] for x in manifest["entries"]] == expected
    assert {p.name for p in (directory / "inputs").iterdir()} == {f"{qid}.txt" for qid in expected}
    assert {p.name for p in (directory / "records").iterdir()} == {f"{qid}.json" for qid in expected}
    assert not any(p.is_symlink() for p in directory.rglob("*"))
    query_by_id = {q["query_id"]: q for q in queries}
    truth_by_id = {t["ground_truth_id"]: t for t in truths}
    assert len(query_by_id) == len(queries) == 72 and len(truth_by_id) == len(truths) == 72

    total_evidence = 0
    for entry in manifest["entries"]:
        qid = entry["query_id"]
        query = query_by_id[qid]
        truth = truth_by_id[query["ground_truth_id"]]
        assert query["split"] == "english_test" and query["language"] == "java"
        assert query["project_id"] == truth["project_id"] == project["project_id"]
        assert truth["query_id"] == qid and truth["annotation_status"] == "drafted"
        assert truth["reviewed_at"] is None
        prompt_path = directory / entry["input_path"]
        assert prompt_path.parent == directory / "inputs"
        prompt_raw = prompt_path.read_bytes()
        prompt = prompt_raw.decode("utf-8")
        assert sha(prompt_raw) == entry["input_sha256"]
        assert len(prompt_raw) == entry["input_bytes"] and len(prompt) == entry["input_unicode_codepoints"]
        start = "BEGIN_PHASE62_JAVA_EVIDENCE_AUDIT_INPUT_" + qid.upper().replace("-", "_")
        end = "END_PHASE62_JAVA_EVIDENCE_AUDIT_INPUT_" + qid.upper().replace("-", "_")
        assert prompt.startswith("PREPARED / NOT EXECUTED")
        assert prompt.count(start) == 1 and prompt.endswith(end + "\n")
        assert entry["terminator"] == end
        assert prompt.count("RESPONSE_END_" + qid.upper().replace("-", "_")) == 1
        query_block = block(prompt, "QUERY_JSON")
        assert query_block == {k: query[k] for k in query_block}
        assert set(query_block) == {
            "query_id", "query_set_version", "split", "language", "task_type",
            "dataset_id", "project_id", "query_text", "ground_truth_id",
        }
        evidence_block = block(prompt, "EVIDENCE_JSON")
        assert evidence_block["ground_truth_id"] == truth["ground_truth_id"]
        assert evidence_block["ground_truth_version"] == truth["ground_truth_version"]
        assert evidence_block["annotation_status"] == "drafted"
        assert len(evidence_block["evidence"]) == len(truth["evidence"]) == entry["evidence_count"]
        for index, (included, original) in enumerate(zip(evidence_block["evidence"], truth["evidence"]), 1):
            assert included["evidence_id"] == f"E{index:02d}"
            assert included["grade"] == original["relevance"] in (1, 2)
            assert included["relative_path"] == original["relative_path"]
            assert included["rationale"] == original["rationale"]
            assert included["symbol_id"] == original["symbol_id"]
            assert set(included["symbol_id"]) == SYMBOL_FIELDS
            assert included["span"] == {k: original[k] for k in (
                "start_offset", "end_offset", "start_line", "end_line"
            )}
            key = json.dumps(original["symbol_id"], ensure_ascii=False, sort_keys=True)
            assert key in symbols
            symbol, source_text = symbols[key]
            assert (original["start_line"], original["end_line"]) == (symbol.start_line, symbol.end_line)
            assert (original["start_offset"], original["end_offset"]) == symbol_span(symbol, source_text)
            assert 0 <= original["start_offset"] < original["end_offset"] <= len(source_text)
        total_evidence += len(truth["evidence"])

        matches = list(SOURCE_RE.finditer(prompt))
        expected_paths = sorted({e["relative_path"] for e in truth["evidence"]})
        assert len(matches) == entry["source_file_count"] == len(expected_paths)
        assert [m[1] for m in matches] == expected_paths
        assert prompt.count("[[SOURCE_BEGIN") == prompt.count("[[SOURCE_END") == len(matches)
        assert [f["relative_path"] for f in entry["source_files"]] == expected_paths
        for match, file_entry in zip(matches, entry["source_files"]):
            path, stated_hash, stated_bytes, body, closing_path = match.groups()
            raw = source_bytes[path]
            assert path == closing_path == file_entry["relative_path"]
            assert body.encode("utf-8") == raw
            assert sha(raw) == stated_hash == file_entry["raw_sha256"] == files[path]["content_hash"]
            assert len(raw) == int(stated_bytes) == file_entry["raw_bytes"]
        assert all(other["query_id"] not in prompt and other["ground_truth_id"] not in prompt
                   for other in queries if other["query_id"] != qid)
        assert not any(value in prompt for value in (
            "/Users/", "/private/tmp/", "ranked_hits", "raw_results.jsonl",
            "reviewed_at", "reviewer_id", "masking_confirmed", "annotation_audit.jsonl",
        ))

        record_path = directory / entry["record_path"]
        assert record_path.parent == directory / "records"
        record_raw = record_path.read_bytes()
        assert sha(record_raw) == entry["record_sha256"]
        record = json.loads(record_raw)
        assert record["query_id"] == qid and record["input_sha256"] == entry["input_sha256"]
        assert record["status"] == "PREPARED / NOT EXECUTED"
        assert record["execution_status"] == record["overall_status"] == record["raw_reply"]["completeness"] == "NOT_EXECUTED"
        for key in ("actual_pasted_text_raw_path", "actual_pasted_text_sha256",
                    "model_display_name", "visible_version", "started_at_utc",
                    "ended_at_utc", "traework_session_id", "failure_reason",
                    "structured_transcription_sha256"):
            assert record[key] is None
        for key in ("thinking_region", "final_answer"):
            assert record[key] == {"raw_path": None, "sha256": None, "availability": "NOT_EXECUTED"}
        assert record["raw_reply"]["raw_path"] is record["raw_reply"]["sha256"] is record["raw_reply"]["completeness_notes"] is None
        for item in record["platform_fields"].values():
            assert item == {"value": None, "availability": "NOT_EXECUTED"}
        assert len(record["evidence_reviews"]) == len(truth["evidence"])
        for index, item in enumerate(record["evidence_reviews"], 1):
            assert item["evidence_id"] == f"E{index:02d}"
            assert item["status"] == "NOT_EXECUTED"
            assert item["source_behavior_or_reason"] is item["span_grade_mismatch_suspected"] is None
            original = truth["evidence"][index - 1]
            assert item["original_identity"] == {
                "relative_path": original["relative_path"],
                "symbol_id": original["symbol_id"],
                "span": {k: original[k] for k in (
                    "start_offset", "end_offset", "start_line", "end_line"
                )},
                "grade": original["relevance"],
            }
    assert total_evidence == 23
    assert Counter(x["task_type"] for x in manifest["entries"]) == {k: 2 for k in groups}
    print("PASS: 12 exact preregistered Java-test inputs, 23 evidence items, full frozen source bytes, 12 blank records")


if __name__ == "__main__":
    validate()
