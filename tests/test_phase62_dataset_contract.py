"""Offline source/identity contracts; no evaluated retriever participates in authoring."""
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timedelta
from functools import lru_cache
from itertools import combinations
import json
from pathlib import Path
import re
import subprocess

import pytest

from code_maintenance.adapters import JavaAdapter, PythonAdapter
from code_maintenance.domain import SourceFile
from code_maintenance.scanner import ProjectScanner
from code_maintenance.snapshot import SnapshotBuilder
from experiments.baselines import FileSource, build_chunk_documents, build_file_documents
from experiments.schemas import (
    load_dataset_manifest, load_ground_truth, load_queries, symbol_id_to_record,
)
from experiments.serialization import canonical_hash, normalize_lf, sha256_hex
from project_intelligence.lexical import tokenize


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/experiments"
DATA = DOCS / "datasets/v1"
FROZEN = "12391233daa2149ead4f451e920b2e0d8a1a6beb"
SELF = "self-code-comments-agent"
DATASET = "v3.1-phase6-dataset-v1"
SPEC = "Dataset_Query_GroundTruth_Specification_V3_1_0.md"
FIXTURES = {
    "fixture-py-route-ledger": "route-ledger",
    "fixture-py-intake-queue": "intake-queue",
    "fixture-java-desk-queue": "desk-queue",
}
TASKS = dict(zip(("sl", "fl", "dq", "bl", "mt", "cf"), (
    "symbol_lookup", "feature_localization", "dependency_questions",
    "bug_localization", "maintenance_tasks", "cross_file_understanding")))
DOCUMENT_HASHES = {
    "Experiment_Protocol_V3_1_0.md": "214360ac17633db7d77caec2ea2a135bf4372a773f9343b2fcb91bff8ee4e341",
    SPEC: "4e72ceb84f06df361e10a24a6ab273ed3f6eba4d3649b96177a810c6a0c30a92",
    "Experiment_Protocol_Addendum_A_V3_1_0.md": "6a09088733d18d03e04efcbfc208a00c7860fef5b00efa95acf987aebd99686b",
    "Experiment_Protocol_Addendum_B_V3_1_0.md": "34406b3dad94cf21c3422176cedd7b94221f18518b82c97e8c061e52b3972a5d",
    "Experiment_Protocol_Addendum_C_V3_1_0.md": "3a3e125b1245206ec49fe22c59cd95b625a7ec28d4c75f10dcc361770f238c79",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def authoritative_rows():
    rows = []
    section = None
    for line in (DOCS / SPEC).read_text(encoding="utf-8").splitlines():
        match = re.match(r"### 4\.(\d)", line)
        if match:
            section = int(match[1])
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not re.fullmatch(r"`(?:et|ed|zh)-[a-z]{2}-(?:py|ja)-\d{2}`", cells[0]):
            continue
        query_id = cells[0].strip("`")
        if section in (1, 3):
            project = SELF if section == 1 else "fixture-java-desk-queue"
            text, grade2, grade1 = cells[1:4]
        else:
            project = cells[1].strip("`")
            text, grade2, grade1 = cells[2:5]
        note = cells[-1].strip("`")
        rows.append(dict(query_id=query_id, project_id=project, query_text=text,
                         grade2=re.findall(r"`([^`]+)`", grade2),
                         grade1=re.findall(r"`([^`]+)`", grade1),
                         notes="graph_note=" + note if note in
                         {"contains", "imports_exact_unique"} else None))
    addendum = (DOCS / "Experiment_Protocol_Addendum_C_V3_1_0.md").read_text(encoding="utf-8")
    corrections = dict(re.findall(
        r"### 2\.\d `([^`]+)`.*?REPLACEMENT:\s*\n> ([^\n]+)", addendum, re.S))
    assert set(corrections) == {"et-bl-py-01", "et-bl-py-03", "et-mt-py-03", "et-cf-py-01"}
    for row in rows:
        row["query_text"] = corrections.get(row["query_id"], row["query_text"])
    assert len(rows) == 72
    return sorted(rows, key=lambda row: row["query_id"])


@lru_cache(maxsize=None)
def source_bytes(project):
    if project != SELF:
        base = DATA / "fixtures" / FIXTURES[project]
        return {path.relative_to(base).as_posix(): path.read_bytes()
                for path in sorted(base.rglob("*")) if path.suffix in {".py", ".java"}}
    tree = subprocess.check_output(["git", "ls-tree", "-rz", FROZEN], cwd=ROOT)
    records = {}
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        path = raw_path.decode("utf-8")
        if mode in (b"100644", b"100755") and Path(path).suffix in {".py", ".java"}:
            records[path] = subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)
    return records


def source_text(raw):
    from code_maintenance.snapshot import decode_source_bytes
    return normalize_lf(decode_source_bytes(raw))


def symbol_span(symbol, text):
    lines = text.split("\n")
    start = sum(len(line) + 1 for line in lines[:symbol.start_line - 1])
    end = start + len("\n".join(lines[symbol.start_line - 1:symbol.end_line]))
    return start, end


@lru_cache(maxsize=None)
def symbols(project):
    result = []
    for path, raw in source_bytes(project).items():
        language = "python" if path.endswith(".py") else "java"
        adapter = PythonAdapter() if language == "python" else JavaAdapter()
        result.extend(adapter.parse_symbols(SourceFile(project, path, language, source_text(raw))))
    return tuple(result)


def resolve_anchor(project, anchor):
    path, name = anchor.split("::", 1) if "::" in anchor else (None, anchor)
    candidates = [symbol for symbol in symbols(project)
                  if (symbol.qualified_name == name or symbol.id.semantic_disambiguator == name)
                  and (path is None or symbol.relative_path == path
                       or ("/" not in path and Path(symbol.relative_path).name == path))]
    assert len(candidates) == 1, (project, anchor, candidates)
    return candidates[0]


def fixture_hash(records):
    return canonical_hash([dict(path=path, language="python" if path.endswith(".py") else "java",
                                content_hash=sha256_hex(raw)) for path, raw in sorted(records.items())])


def incremental_evidence():
    snapshots = {}
    states = {}
    for state in ("base", "update"):
        base = DATA / "incremental" / state
        records = {p.relative_to(base).as_posix(): p.read_bytes() for p in sorted(base.rglob("*.py"))}
        scan = ProjectScanner().scan(base)
        scan = replace(scan, project=replace(scan.project, id="fixture-py-incremental-delta"))
        snapshots[state] = SnapshotBuilder().build(scan)
        states[state] = dict(fixture_hash=fixture_hash(records), file_count=len(records),
                             symbol_count=len(snapshots[state].symbols),
                             snapshot_hash=snapshots[state].content_hash,
                             files=[dict(relative_path=p, content_hash=sha256_hex(raw), language="python")
                                    for p, raw in records.items()])
    diff = snapshots["base"].compare(snapshots["update"])
    categories = {key: sorted(s.qualified_name for s in getattr(diff, key + "_symbols"))
                  for key in ("changed", "added", "removed", "unchanged")}
    return dict(dataset_id="v3.1-phase6-incremental-v1", project_id="fixture-py-incremental-delta",
                source_revision="fixture-v1", states=states, authoritative_diff=categories,
                direct_edit_set={"changed": ["Bin.put", "Shelf.add", "checksum"],
                                 "added": ["Bin.count", "Shelf.label"],
                                 "removed": ["Bin.remove", "Shelf.drop"]},
                enclosing_symbol_effect=["Bin", "Shelf"],
                new_embedding_documents=sorted(categories["changed"] + categories["added"]),
                future_embed_documents_batches=1, actual_embedding_calls=0)


@pytest.fixture(scope="module")
def bundle():
    return (load_dataset_manifest(DATA / "manifest.json"),
            load_queries(DOCS / "queries/v1/queries.jsonl"),
            load_ground_truth(DOCS / "ground_truth/v1/ground_truth.jsonl"),
            read_json(DATA / "authoring_audit.json"), read_json(DATA / "identity.json"))


def overlap_audit(queries, truths):
    occurrences = defaultdict(list)
    for query, truth in zip(queries, truths):
        assert query.query_id == truth.query_id
        for evidence in truth.evidence:
            key = (truth.project_id, evidence.symbol_id)
            occurrences[key].append(dict(query_id=query.query_id, split=query.split, grade=evidence.relevance))
    grade1, chinese = [], []
    for (project, symbol), items in sorted(occurrences.items(), key=lambda item: str(item[0])):
        record = dict(project_id=project, symbol_id=symbol_id_to_record(symbol), occurrences=items)
        if len(items) > 1 and any(item["grade"] == 1 for item in items):
            grade1.append(record)
        splits = {item["split"] for item in items}
        if "chinese_coverage" in splits and len(splits) > 1:
            chinese.append(record)
    return grade1, chinese


def quota_counts(queries, truths):
    counts = {task: dict(total=0, multi_relevant=0, cross_file=0) for task in TASKS.values()}
    for query, truth in zip(queries, truths):
        if query.split == "english_test":
            row = counts[query.task_type]
            relevant = [e for e in truth.evidence if e.relevance > 0]
            row["total"] += 1
            row["multi_relevant"] += len(relevant) > 1
            row["cross_file"] += len({e.relative_path for e in relevant}) > 1
    return counts


def leakage_rows(queries, truths):
    entries = []
    for query, truth in zip(queries, truths):
        for evidence in truth.evidence:
            if evidence.relevance == 2:
                simple = evidence.symbol_id.qualified_name.rsplit(".", 1)[-1]
                tokens = tokenize(simple)
                assert tokens
                exempt = query.task_type == "symbol_lookup"
                entries.append(dict(query_id=query.query_id, simple_name=simple, tokens=list(tokens),
                                    banned_identifier_token=tokens[0], lookup_exempt=exempt,
                                    failed=not exempt and tokens[0] in tokenize(query.query_text)))
    return entries


def test_population_and_authoritative_wording(bundle):
    manifest, queries, truths, audit, identity = bundle
    rows = authoritative_rows()
    assert len(queries) == len(truths) == 72
    assert [q.query_id for q in queries] == [row["query_id"] for row in rows]
    assert len({q.query_id for q in queries}) == len({t.ground_truth_id for t in truths}) == 72
    assert Counter(q.split for q in queries) == {"english_test": 48, "english_dev": 12, "chinese_coverage": 12}
    assert Counter(q.project_id for q in queries) == {SELF: 32, "fixture-py-route-ledger": 13,
        "fixture-py-intake-queue": 13, "fixture-java-desk-queue": 14}
    for split, python, java, per_task in (("english_test", 36, 12, 8), ("english_dev", 10, 2, 2),
                                          ("chinese_coverage", 12, 0, 2)):
        group = [q for q in queries if q.split == split]
        assert Counter(q.language for q in group) == Counter(python=python, java=java)
        assert Counter(q.task_type for q in group) == {task: per_task for task in TASKS.values()}
    for query, truth, row in zip(queries, truths, rows):
        assert query.query_text == row["query_text"]
        assert query.notes == row["notes"]
        assert query.project_id == truth.project_id == row["project_id"]
        assert query.ground_truth_id == truth.ground_truth_id == "gt-" + query.query_id
        assert truth.query_id == query.query_id
        assert query.dataset_id == truth.dataset_id == manifest.dataset_id == DATASET
        assert query.authoring_source == ("self_repository" if query.project_id == SELF else "fixture")
        assert query.query_set_version == "v3.1-phase6-queries-v1"
        assert truth.ground_truth_version == "v3.1-phase6-truth-v1"


@pytest.mark.parametrize("query_id", [r["query_id"] for r in authoritative_rows()])
def test_every_authoritative_evidence_matches_adapter_source(bundle, query_id):
    manifest, queries, truths, audit, identity = bundle
    truth = next(t for t in truths if t.query_id == query_id)
    row = next(r for r in authoritative_rows() if r["query_id"] == query_id)
    expected = [(resolve_anchor(truth.project_id, anchor), grade)
                for grade in (2, 1) for anchor in row["grade" + str(grade)]]
    assert len(truth.evidence) == len(expected)
    assert {(e.symbol_id, e.relevance) for e in truth.evidence} == {(s.id, g) for s, g in expected}
    assert len({e.symbol_id for e in truth.evidence}) == len(truth.evidence)
    project = next(p for p in manifest.projects if p.project_id == truth.project_id)
    for evidence in truth.evidence:
        symbol = next(s for s, grade in expected if s.id == evidence.symbol_id)
        raw = source_bytes(truth.project_id)[evidence.relative_path]
        text = source_text(raw)
        assert evidence.relative_path in {f.relative_path for f in project.files}
        assert evidence.relevance in {1, 2}
        assert (evidence.start_line, evidence.end_line) == (symbol.start_line, symbol.end_line)
        assert (evidence.start_offset, evidence.end_offset) == symbol_span(symbol, text)
        assert 0 <= evidence.start_offset < evidence.end_offset <= len(text)
        assert sha256_hex(text[evidence.start_offset:evidence.end_offset]) == symbol.content_hash
        assert (FROZEN if truth.project_id == SELF else project.fixture_hash) in evidence.rationale
        assert evidence.relative_path in evidence.rationale
        assert symbol.qualified_name in evidence.rationale
        assert f"L{symbol.start_line}-L{symbol.end_line}" in evidence.rationale
        assert f"[{evidence.start_offset},{evidence.end_offset})" in evidence.rationale
        assert "行为：" in evidence.rationale


def test_manifest_raw_bytes_and_fixtures(bundle):
    manifest, *_ = bundle
    assert manifest.version == "v1"
    assert {p.project_id for p in manifest.projects} == {SELF, *FIXTURES}
    expected_counts = {SELF: (72, 1233), "fixture-py-route-ledger": (8, 28),
                       "fixture-py-intake-queue": (7, 15), "fixture-java-desk-queue": (6, 23)}
    for project in manifest.projects:
        records = source_bytes(project.project_id)
        assert (project.file_count, project.symbol_count) == expected_counts[project.project_id]
        assert project.file_count == len(records)
        assert project.symbol_count == len(symbols(project.project_id))
        assert {f.relative_path for f in project.files} == set(records)
        assert project.source_revision == (FROZEN if project.project_id == SELF else "fixture-v1")
        assert project.fixture_hash == (None if project.project_id == SELF else fixture_hash(records))
        for file in project.files:
            assert file.content_hash == sha256_hex(records[file.relative_path])
            assert file.language == ("python" if file.relative_path.endswith(".py") else "java")
            assert file.path_role == ("test" if file.relative_path.startswith("tests/") else "production") if project.project_id == SELF else file.path_role == "fixture"


def self_statistics():
    records = source_bytes(SELF)
    source = [FileSource(path, source_text(raw)) for path, raw in records.items()]
    chunks = build_chunk_documents(source)
    all_symbols = symbols(SELF)
    spans = [(s, *symbol_span(s, source_text(records[s.relative_path]))) for s in all_symbols]
    populated = {s.relative_path for s in all_symbols}
    return dict(python_files=sum(p.endswith(".py") for p in records),
                java_files=sum(p.endswith(".java") for p in records),
                production_files=sum(not p.startswith("tests/") for p in records),
                test_files=sum(p.startswith("tests/") for p in records), symbols=len(all_symbols),
                kinds=dict(Counter(s.kind.value for s in all_symbols)),
                zero_symbol_files=sorted(set(records) - populated),
                file_documents=len(build_file_documents(source)), chunk_documents=len(chunks),
                long_symbols=sum(end - start > 1200 for s, start, end in spans),
                multi_chunk_symbols=sum(sum(c.relative_path == s.relative_path and
                    max(c.start_offset, start) < min(c.end_offset, end) for c in chunks) >= 2
                    for s, start, end in spans))


def test_self_frozen_statistics_and_scanner_filter(bundle, tmp_path):
    from io import BytesIO
    import tarfile
    archive = subprocess.check_output(["git", "archive", FROZEN], cwd=ROOT)
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        tar.extractall(tmp_path, filter="data")
    scan = ProjectScanner().scan(tmp_path)
    actual = {f.relative_path for f in scan.files if f.language in {"python", "java"}}
    assert actual == set(source_bytes(SELF))
    stats = self_statistics()
    assert stats == bundle[3]["self_repository_statistics"]
    assert (stats["python_files"], stats["java_files"], stats["production_files"], stats["test_files"]) == (72, 0, 44, 28)
    assert stats["symbols"] == 1233 and stats["kinds"] == {"class": 190, "method": 377, "function": 666}
    assert len(stats["zero_symbol_files"]) == 8
    assert (stats["file_documents"], stats["chunk_documents"], stats["long_symbols"], stats["multi_chunk_symbols"]) == (72, 857, 151, 747)


def test_draft_lifecycle_and_annotation_audit(bundle):
    _, queries, truths, audit, identity = bundle
    annotations = [json.loads(line) for line in (DOCS / "ground_truth/v1/annotation_audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [a["query_id"] for a in annotations] == [q.query_id for q in queries]
    created = datetime.fromisoformat(identity["created_at"])
    earliest = datetime.fromisoformat(identity["earliest_allowed_review_at"])
    assert earliest - created == timedelta(hours=48)
    assert created.utcoffset() == timedelta(0) and created <= datetime.now(created.tzinfo)
    for truth, annotation, query in zip(truths, annotations, queries):
        assert truth.annotation_status == annotation["annotation_status"] == "drafted"
        assert truth.primary_annotator_id == truth.reviewer_id == annotation["reviewer_id"] == "wang"
        assert truth.reviewed_at is None and truth.adjudicator_id is None
        assert truth.created_at == audit["created_at"] == identity["created_at"]
        assert annotation["initial_evidence_hash"] == canonical_hash([e.to_record() for e in truth.evidence])
        assert annotation["review_method"] == "delayed_blinded_self_review"
        assert annotation["second_annotator"] == "absent"
        for pending in ("reviewed_at", "delayed_judgment", "masking_confirmed", "ambiguity_flag", "adjudication_note"):
            assert annotation[pending] is None
        assert annotation["not_mechanical_translation"] is None
        assert annotation["translation_review_required"] == (query.split == "chinese_coverage")
    assert audit["retrieval_runs_before_freeze"] == identity["retrieval_runs_before_freeze"] == 0
    assert audit["human_IAA"] == "not_available_not_claimed"
    assert not (DOCS / "runs").exists()


def test_leakage_and_permitted_overlap_audits(bundle):
    _, queries, truths, audit, _ = bundle
    entries = leakage_rows(queries, truths)
    assert entries == audit["identifier_leakage_audit"]
    targets = [e for e in entries if not e["lookup_exempt"]]
    assert len(targets) == 60
    assert sum(len(e["tokens"]) > 1 for e in targets) == 39
    assert not any(e["failed"] for e in entries)
    grade1, chinese = overlap_audit(queries, truths)
    assert grade1 == audit["grade1_overlap_audit"]
    assert chinese == audit["chinese_english_overlap_audit"]
    grade2 = {split: {(t.project_id, e.symbol_id) for q, t in zip(queries, truths)
                     if q.split == split for e in t.evidence if e.relevance == 2}
              for split in ("english_dev", "english_test")}
    assert not grade2["english_dev"] & grade2["english_test"]
    paths = {p for project in (SELF, *FIXTURES) for p in source_bytes(project)}
    for query, truth in zip(queries, truths):
        assert not any(path in query.query_text for path in paths)
        assert "com.desk" not in query.query_text and "src/com/desk" not in query.query_text
        for evidence in truth.evidence:
            if query.task_type != "symbol_lookup":
                for value in (evidence.symbol_id.qualified_name, evidence.relative_path,
                              evidence.symbol_id.semantic_disambiguator):
                    assert not value or value not in query.query_text
            assert not any(query.query_text[i:i + 40] in evidence.rationale
                           for i in range(len(query.query_text) - 39))
        assert not re.search(r"\b(bm25|embedding|hybrid|ndcg|rrf|grade)\b", query.query_text + (query.notes or ""), re.I)
    for project in FIXTURES:
        for raw in source_bytes(project).values():
            text = source_text(raw)
            assert not re.search(r"\b(bm25|embedding|hybrid|ndcg|rrf|grade)\b", text, re.I)
            for query in queries:
                assert query.query_id not in text
                assert not any(query.query_text[i:i + 40] in text for i in range(len(query.query_text) - 39))


@pytest.mark.parametrize("simple,query,exempt,expected", [
    ("update", "the update is refused", False, True),
    ("_document", "retrieval document", False, True),
    ("normalize_payload", "normalize a payload", False, False),
    ("markClosed", "markClosed now", False, True),
    ("save", "saved item", False, False),
    ("grant", "grants credits", False, False),
    ("__post_init__", "post_init", False, True),
    ("update", "find update", True, False),
])
def test_full_identifier_rule_not_component_or_stemming(simple, query, exempt, expected):
    tokens = tokenize(simple)
    assert tokens
    assert (not exempt and tokens[0] in tokenize(query)) == expected


def test_all_pair_near_duplicates_and_quotas(bundle):
    _, queries, truths, audit, _ = bundle
    pairs = []
    for a, b in combinations(queries, 2):
        left = set(re.findall(r"[a-z0-9]{3,}", a.query_text.lower()))
        right = set(re.findall(r"[a-z0-9]{3,}", b.query_text.lower()))
        score = len(left & right) / len(left | right) if left | right else 0
        assert score <= .55, (a.query_id, b.query_id, score)
        pairs.append(score)
    assert audit["near_duplicate_audit"] == dict(pair_count=len(pairs), threshold=.55, max_jaccard=max(pairs), failures=0)
    counts = quota_counts(queries, truths)
    assert counts == audit["english_test_quotas"]
    for task, minimum_multi, minimum_cross in (("dependency_questions", 6, 5),
            ("maintenance_tasks", 6, 5), ("cross_file_understanding", 6, 5),
            ("bug_localization", 5, 3), ("feature_localization", 4, 3)):
        assert counts[task]["total"] == 8
        assert counts[task]["multi_relevant"] >= minimum_multi
        assert counts[task]["cross_file"] >= minimum_cross
    assert counts["symbol_lookup"]["multi_relevant"] <= 2


def test_incremental_production_diff_without_embedding():
    actual = incremental_evidence()
    assert read_json(DATA / "incremental/manifest.json") == actual
    assert actual["authoritative_diff"] == {
        "changed": ["Bin", "Bin.put", "Shelf", "Shelf.add", "checksum"],
        "added": ["Bin.count", "Shelf.label"], "removed": ["Bin.remove", "Shelf.drop"], "unchanged": []}
    assert {key: len(value) for key, value in actual["direct_edit_set"].items()} == {"changed": 3, "added": 2, "removed": 2}
    assert len(actual["new_embedding_documents"]) == 7
    assert actual["future_embed_documents_batches"] == 1 and actual["actual_embedding_calls"] == 0


def mapping_probes(truths):
    by_id = {truth.query_id: truth for truth in truths}
    long = next(e for e in by_id["et-fl-py-06"].evidence if e.relevance == 2)
    project = "fixture-py-intake-queue"
    chunks = build_chunk_documents([FileSource(p, source_text(raw)) for p, raw in source_bytes(project).items()])
    def hits(evidence):
        return [[c.start_offset, c.end_offset] for c in chunks
                if c.relative_path == evidence.relative_path and
                max(c.start_offset, evidence.start_offset) < min(c.end_offset, evidence.end_offset)]
    bug = by_id["et-bl-py-06"]
    last = next(e for e in bug.evidence if e.symbol_id.qualified_name.endswith(".last_record_included"))
    reason = next(e for e in bug.evidence if e.symbol_id.qualified_name.endswith(".reject_reason"))
    return dict(long_symbol_length=long.end_offset - long.start_offset,
                long_symbol_chunks=hits(long), last_record_span=[last.start_offset, last.end_offset],
                reject_reason_span=[reason.start_offset, reason.end_offset],
                last_record_chunks=hits(last), reject_reason_chunks=hits(reason),
                shared_chunks=sorted(set(map(tuple, hits(last))) & set(map(tuple, hits(reason)))),
                cross_file_paths={qid: sorted({e.relative_path for e in by_id[qid].evidence})
                                  for qid in ("et-cf-py-05", "et-dq-py-04", "et-bl-ja-02")})


def test_rq1_source_boundary_probes(bundle):
    actual = mapping_probes(bundle[2])
    assert bundle[3]["rq1_mapping_probes"] == actual
    assert 1500 <= actual["long_symbol_length"] <= 1800
    assert len(actual["long_symbol_chunks"]) >= 2
    assert actual["long_symbol_chunks"][0] == [0, 1200]
    assert actual["long_symbol_chunks"][1][0] == 1000
    assert actual["last_record_span"][0] >= 1400
    assert 0 <= actual["reject_reason_span"][0] < actual["reject_reason_span"][1] < 700
    assert actual["shared_chunks"] == []
    assert all(len(paths) >= 2 for paths in actual["cross_file_paths"].values())


@pytest.mark.parametrize("unit", ["file", "symbol", "chunk"])
def test_rq1_grades_use_authoritative_maximum(bundle, unit):
    from experiments.baselines import FileIdentity, ChunkIdentity, SymbolSourceRange, TruthMapper
    for truth in bundle[2]:
        records = source_bytes(truth.project_id)
        ranges = [SymbolSourceRange(s.id, *symbol_span(s, source_text(records[s.relative_path])))
                  for s in symbols(truth.project_id)]
        mapper = TruthMapper(truth, ranges)
        if unit == "file":
            for path in records:
                assert mapper.grade(FileIdentity(path)) == max(
                    (e.relevance for e in truth.evidence if e.relative_path == path), default=0)
        elif unit == "symbol":
            for r in ranges:
                assert mapper.grade(r.symbol_id) == max((e.relevance for e in truth.evidence
                    if e.symbol_id == r.symbol_id or (e.relative_path == r.symbol_id.relative_path
                        and r.start_offset <= e.start_offset and e.end_offset <= r.end_offset)), default=0)
        else:
            chunks = build_chunk_documents([FileSource(p, source_text(raw)) for p, raw in records.items()])
            for chunk in chunks:
                expected = max((e.relevance for e in truth.evidence if e.relative_path == chunk.relative_path
                    and max(e.start_offset, chunk.start_offset) < min(e.end_offset, chunk.end_offset)), default=0)
                assert mapper.grade(chunk.identity) == expected
    single = replace(bundle[2][0], evidence=(bundle[2][0].evidence[0],))
    e = single.evidence[0]
    assert TruthMapper(single).grade(ChunkIdentity(e.relative_path, e.end_offset, e.end_offset + 1)) == 0
    assert TruthMapper(single).grade(ChunkIdentity(e.relative_path, e.end_offset - 1, e.end_offset)) == e.relevance


def java_subsets(queries):
    return {note: [q.query_id for q in queries if q.language == "java" and q.split == "english_test"
                   and q.notes == "graph_note=" + note] for note in ("contains", "imports_exact_unique")}


def test_java_restrictions_identity_import_graph_and_subsets(bundle):
    from code_maintenance.graph import ProjectGraphBuilder, GraphNodeKind, GraphRelationKind
    project = "fixture-java-desk-queue"
    types, imports = {}, []
    for path, raw in source_bytes(project).items():
        text = source_text(raw)
        assert not re.search(r"\b(extends|implements|enum)\b|import\s+static|import\s+[^;]*\*", text)
        classes = re.findall(r"\bpublic\s+class\s+(\w+)", text)
        assert len(classes) == len(re.findall(r"\bclass\b", text)) == 1
        package = re.search(r"package\s+([\w.]+);", text)[1]
        name = package + "." + classes[0]
        assert name not in types
        types[name] = path
        imports.extend((path, name) for name in re.findall(r"import\s+([\w.]+);", text))
    assert len(types) == 6 and len(imports) == 7
    assert all(name in types for _, name in imports)
    overloaded = [s for s in symbols(project) if s.qualified_name == "DeskQueue.openTicket"]
    assert {s.id.semantic_disambiguator for s in overloaded} == {"openTicket(String,String)", "openTicket(String,String,String)"}
    assert all(s.id.fallback_line is None for s in symbols(project))
    scan = ProjectScanner().scan(DATA / "fixtures/desk-queue")
    graph = ProjectGraphBuilder().build(scan)
    edges = [e for e in graph.edges if e.relation == GraphRelationKind.IMPORTS]
    assert len(edges) == 7
    assert all(e.target.kind == GraphNodeKind.FILE for e in edges)
    assert {e.relation for e in graph.edges} == {GraphRelationKind.CONTAINS, GraphRelationKind.IMPORTS}
    actual = java_subsets(bundle[1])
    assert actual == bundle[3]["java_test_subsets"]
    assert set(actual["contains"]) == {"et-sl-ja-01", "et-sl-ja-02", "et-fl-ja-02", "et-bl-ja-01", "et-mt-ja-01"}
    assert set(actual["imports_exact_unique"]) == {"et-fl-ja-01", "et-dq-ja-01", "et-dq-ja-02", "et-bl-ja-02", "et-mt-ja-02", "et-cf-ja-01", "et-cf-ja-02"}


def test_fixture_python_behavior_and_preserved_defects(monkeypatch):
    import importlib
    import sys
    for folder in ("route-ledger", "intake-queue"):
        monkeypatch.syspath_prepend(str(DATA / "fixtures" / folder))
    # Prevent fixture bytecode artifacts from becoming part of delivery data.
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    models = importlib.import_module("route_ledger.models")
    policy = importlib.import_module("route_ledger.policy").StopPolicy()
    store = importlib.import_module("route_ledger.store").MemoryRouteStore()
    service = importlib.import_module("route_ledger.service").RouteService(store, policy)
    report = importlib.import_module("route_ledger.report").RouteReport()
    notifier = importlib.import_module("route_ledger.notify").RouteNotifier()
    with pytest.raises(ValueError):
        models.validate_entry(models.RouteEntry(""))
    entry = service.open_route("bay")
    assert policy.can_close(entry)
    service.add_stop(entry)
    assert not policy.can_close(entry) and policy.allows_skip(entry)
    with pytest.raises(ValueError):
        service.close_route(entry)
    entry.mark_closed()
    assert entry.remaining_stops() == 1 and not policy.counts_as_open(entry)
    assert report.count_open_stops([entry]) == 1  # Frozen defect, not repaired here.
    assert notifier.notify_closed(entry) == notifier.format_message(entry)
    entry.status = "skipped"
    assert not policy.counts_as_open(entry) and report.count_open_stops([entry]) == 1
    assert notifier.notify_closed(entry) is None
    replacement = models.RouteEntry("bay")
    store.save(replacement)
    assert store.load_all() == (replacement,)
    service.close_route(replacement)
    assert report.summarize(store) == {"open_stops": 0, "closed_routes": 1}
    service.reopen(replacement)
    assert replacement.status == "open"
    store.delete("bay")
    assert not store.load_all()
    env = importlib.import_module("intake_queue.envelope")
    parser = importlib.import_module("intake_queue.parser").IntakeParser()
    dispatcher = importlib.import_module("intake_queue.dispatcher").Dispatcher()
    good = env.Envelope("parcel", "body", "")
    good.checksum = env.compute_checksum(good)
    bad = env.Envelope("other", "body", "wrong")
    assert dispatcher.dispatch_ready([bad, good]) == (good,)
    assert dispatcher.queue == [good]
    assert dispatcher.audit.entries == [(bad.envelope_id, parser.reject_reason(bad))]
    assert parser.normalize_payload("first\nlast") == "first"
    assert parser.normalize_payload("first\nlast\n") == "first\nlast\n"
    assert not parser.last_record_included("last")
    for module in ("IntakeAudit.rejected_ids", "IntakeAudit.append_reason", "IntakeRules.reason_code", "Dispatcher.pending_ids"):
        assert module not in {s.qualified_name for s in symbols("fixture-py-intake-queue")}


def test_canonical_hash_chain_and_raw_checksums(bundle):
    manifest, queries, truths, audit, identity = bundle
    assert identity["dataset_hash"] == manifest.dataset_hash
    assert identity["path_manifest_hash"] == manifest.path_manifest_hash
    assert identity["query_set_hash"] == canonical_hash([q.to_record() for q in queries])
    assert identity["ground_truth_hash"] == canonical_hash([t.to_record() for t in truths])
    assert identity["self_source_revision"] == FROZEN
    assert identity["documentation_sha256"] == DOCUMENT_HASHES
    for name, digest in DOCUMENT_HASHES.items():
        assert sha256_hex((DOCS / name).read_bytes()) == digest
    assert identity["authoring_audit_sha256"] == sha256_hex((DATA / "authoring_audit.json").read_bytes())
    paths = set()
    for line in (DATA / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        assert path not in paths
        assert sha256_hex((ROOT / path).read_bytes()) == digest
        paths.add(path)
    expected = {p.relative_to(ROOT).as_posix() for base in (DATA, DOCS / "queries/v1", DOCS / "ground_truth/v1")
                for p in base.rglob("*") if p.is_file() and p.name != "checksums.sha256"
                and "__pycache__" not in p.parts}
    assert paths == expected
