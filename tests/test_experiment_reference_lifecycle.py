"""Offline lifecycle contracts and committed Java evidence artifacts."""
from __future__ import annotations

import json
from copy import deepcopy
import os
import random
import shutil
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from code_maintenance import SymbolId, SymbolKind
from experiments import (
    ApprovalDecisionRecord, ApprovalPrerequisiteRecord, Availability, BenchmarkConfig,
    CurrentGateIndex, DatasetManifest, DryRunArtifactRef, DryRunArtifactSet,
    DryRunConfigurationSet, DryRunReceipt, DryRunReceiptV2, EligibilityError, ErratumRecord,
    EvidenceAuditRecord, EvidenceAuditSet, EvidenceRecord, EvidenceReview, FormalGateEvidence,
    GroundTruthRecord, IdentityRef, Phase62ClosureRecord, Phase62DocumentationDecisionRecord,
    Population, PrerequisiteReference,
    RawCapture, ReferenceApprovalRecord, ReferenceApprovalRequest, ReferenceRecord, RepositoryAuthority, ResolutionRecord,
    RetrievalUnit, RunKind, RuntimeMetadata, Strategy, VisiblePart, canonical_hash, canonical_json,
    derive_reference, load_ground_truth, load_queries, raw_sha256,
    validate_formal_eligibility, validate_reference_approval_readiness, write_lifecycle_artifact,
)
from experiments.reference import REFERENCE_METHOD, parse_external_evidence_response
from experiments.eligibility import _validate_source_resolution, validate_current_gate
from experiments.serialization import canonical_jsonl
from experiments.config import FROZEN_MATRIX_IDS
from experiments.execution import executable_config
from project_intelligence import LocalE5EmbeddingProvider

ROOT = Path(__file__).parents[1]
D = "a" * 64


@pytest.mark.parametrize("query_id", ("et-bl-ja-01", "et-fl-ja-02"))
def test_closed_execution_failure_resolution_checks_frozen_source(tmp_path, query_id):
    source_root = ROOT / "docs/experiments"
    root = tmp_path / "resolution-repository"
    root.mkdir()
    audit_path = None
    for candidate in (source_root / "evidence_audit/executions").glob("*/record.json"):
        if json.loads(candidate.read_text())["query_id"] == query_id:
            audit_path = candidate
            break
    assert audit_path is not None
    audit = EvidenceAuditRecord.from_record(json.loads(audit_path.read_text()))
    resolution_path = next(path for path in (source_root / "audits/resolutions").glob("*.json")
                           if json.loads(path.read_text())["target_identity"] == audit.identity_hash)
    resolution = ResolutionRecord.from_record(json.loads(resolution_path.read_text()))
    evidence_path = source_root / "audits/source_resolution" / f"{query_id}.json"
    prepared_path = source_root / "evidence_audit/prepared/records" / f"{query_id}.json"
    for path in (resolution_path, resolution_path.with_name(resolution_path.name + ".sha256"),
                 evidence_path, evidence_path.with_name(evidence_path.name + ".sha256"),
                 prepared_path):
        _write(root, path.relative_to(ROOT).as_posix(), path.read_bytes())
    evidence = json.loads(evidence_path.read_text())
    for check in evidence["checks"]:
        path = source_root / "datasets/v1/fixtures/desk-queue" / check["relative_path"]
        _write(root, path.relative_to(ROOT).as_posix(), path.read_bytes())
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Synthetic Test")
    _git(root, "config", "user.email", "synthetic@example.invalid")
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "frozen source resolution fixture")
    authority = RepositoryAuthority(root)
    prepared = json.loads(prepared_path.read_text())
    assert authority.load_typed(resolution_path.relative_to(ROOT).as_posix(),
                                ResolutionRecord, resolution.identity_hash) == resolution
    _validate_source_resolution(authority, audit, resolution, prepared)
    with pytest.raises(EligibilityError, match="audit_response_failure_requires_resolution"):
        _validate_source_resolution(authority, audit, replace(resolution, target_identity="0" * 64), prepared)
    evidence["checks"][0]["source_excerpt"] = "incorrect source"
    new_raw = (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode()
    new_hash = _write(root, evidence_path.relative_to(ROOT).as_posix(), new_raw)
    _write(root, evidence_path.relative_to(ROOT).as_posix() + ".sha256", (new_hash + "\n").encode())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "tampered source resolution")
    with pytest.raises(EligibilityError, match="audit_resolution_source_mismatch"):
        _validate_source_resolution(RepositoryAuthority(root), audit,
                                    replace(resolution, evidence_identity=new_hash), prepared)


def _git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _write(root, path, payload):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return raw_sha256(payload)


def _json(root, path, value):
    digest = _write(root, path, canonical_json(value, pretty=True).encode())
    if ("/reference/" in path or "/reference_approval/" in path or
        "/audits/" in path or "/executions/" in path):
        _write(root, path + ".sha256", (digest + "\n").encode("ascii"))
    return digest


def _capture(root, path, payload):
    return RawCapture(path, _write(root, path, payload))


def _draft():
    symbol = SymbolId("python", "src/a.py", "a", SymbolKind.FUNCTION)
    return GroundTruthRecord("gt-synthetic", "synthetic-draft-v1", "synthetic-query",
                             "synthetic-dataset", "synthetic-project",
                             (EvidenceRecord("src/a.py", symbol, 0, 4, 1, 1, 2, "synthetic rationale"),),
                             "drafted", "synthetic-author", "synthetic-reviewer", None,
                             "2026-01-01T00:00:00+00:00", None)


def _runtime():
    return RuntimeMetadata("CPython", "3.12.14", (("torch", "2.8.0"), ("transformers", "4.56.2")),
                           "synthetic-os", "synthetic-build", "synthetic-cpu", 4, 8, 16_000_000_000,
                           "synthetic", "cpu", "float32", (("OMP_NUM_THREADS", "1"),), True, True)


def _synthetic_matrix_receipt(root, config, queries, approval, dataset_hash, query_hash,
                              reference_hash, runtime, code_commit):
    runtime_hash = canonical_hash(runtime.to_record())
    template = replace(config, run_kind=RunKind.DRY_RUN, population=Population.ENGLISH_DEV,
                       embedding_fingerprint=LocalE5EmbeddingProvider(local_files_only=True).fingerprint)
    configs = tuple(executable_config(template, matrix_id) for matrix_id in FROZEN_MATRIX_IDS)
    matrix = DryRunConfigurationSet("v1", tuple(
        (item.matrix_run_id, item.experiment_family_identity, item.identity_hash)
        for item in configs))
    dev_queries = tuple(sorted((item for item in queries if item.split == "english_dev"),
                               key=lambda item: item.query_id))
    query_ids = tuple(item.query_id for item in dev_queries)
    runs = []
    for item in configs:
        run_id = "synthetic-" + item.matrix_run_id
        base = f"docs/experiments/runs/{run_id}/"
        raw_path = base + "raw_results.jsonl"
        raw = [{"run_id": run_id, "matrix_run_id": item.matrix_run_id,
                "config_identity": item.identity_hash,
                "protocol_version": config.protocol_version,
                "query_id": query.query_id, "dataset_id": query.dataset_id,
                "project_id": query.project_id, "language": query.language,
                "split": "english_dev", "status": "success", "degraded": False}
               for query in dev_queries]
        raw_hash = _write(root, raw_path, canonical_jsonl(raw).encode())
        aggregate_path = base + "aggregate_results.json"
        aggregate = {"run_id": run_id, "matrix_run_id": item.matrix_run_id,
                     "protocol_version": config.protocol_version,
                     "config_hash": item.identity_hash, "raw_results_sha256": raw_hash,
                     "query_set": {"hash": query_hash},
                     "dataset": {"hash": dataset_hash},
                     "code_commit": code_commit, "run_status": "success",
                     "population_filters": {"split": "english_dev"},
                     "denominator_count": 12,
                     "counts": {"success": 12, "failure": 0, "invalid": 0, "degraded": 0}}
        aggregate_hash = _json(root, aggregate_path, aggregate)
        manifest_path = base + "run_manifest.json"
        manifest = {"run_id": run_id,
                    "protocol": {"version": config.protocol_version},
                    "runner_code_commit": code_commit,
                    "self_repository_commit": code_commit,
                    "dirty_state": False, "environment": runtime.to_record(),
                    "approved_reference_identity": approval, "reference_hash": reference_hash,
                    "config_hashes": [item.identity_hash],
                    "query_set": {"hash": query_hash}, "dataset": {"hash": dataset_hash},
                    "output_checksums": {"raw_results.jsonl": raw_hash,
                                         "aggregate_results.json": aggregate_hash}}
        manifest_hash = _json(root, manifest_path, manifest)
        runs.append(DryRunArtifactRef(item.matrix_run_id, run_id, item.identity_hash,
                                      manifest_path, manifest_hash, aggregate_path,
                                      aggregate_hash, raw_path, raw_hash))
    artifact_set = DryRunArtifactSet("v1", approval, dataset_hash, query_hash,
                                     reference_hash, matrix.identity_hash, runtime_hash,
                                     code_commit, "dry_run", "english_dev", query_ids,
                                     tuple(runs), 204, 0, 0)
    set_path = "docs/experiments/audits/synthetic-dry-run-artifact-set.json"
    _json(root, set_path, artifact_set.to_record())
    evidence_hashes = {}
    for kind in ("determinism", "leakage"):
        path = f"docs/experiments/audits/synthetic-{kind}-evidence.json"
        evidence = {"kind": kind, "status": "pass",
                    "artifact_set_identity": artifact_set.identity_hash,
                    "configuration_set_identity": matrix.identity_hash,
                    "run_raw_sha256": [run.raw_sha256 for run in runs]}
        if kind == "leakage":
            evidence.update(english_test_count=0, chinese_count=0)
        else:
            evidence.update(comparison_scope="all_17_configurations",
                            compared_query_count=204, observed_rank_mismatches=0)
        evidence_hashes[kind] = (path, _json(root, path, evidence))
    receipt = DryRunReceiptV2("v2", "pass", approval, dataset_hash, query_hash,
                              reference_hash, matrix.identity_hash,
                              artifact_set.identity_hash, set_path, runtime_hash,
                              code_commit, config.protocol_version, "english_dev", 204,
                              *evidence_hashes["determinism"], *evidence_hashes["leakage"])
    directory = write_lifecycle_artifact(
        root / "docs/experiments/audits/dry_run_receipts", receipt)
    return (directory / "record.json").relative_to(root).as_posix()


def test_reference_derivation_identity_and_immutability():
    draft = _draft()
    first = derive_reference(draft, truth_version="synthetic-reference-v1")
    second = derive_reference(draft, truth_version="synthetic-reference-v1")
    assert first.identity_hash == second.identity_hash
    assert first.evidence == draft.evidence
    assert first.query_id == draft.query_id
    assert first.source_draft_record_hash == canonical_hash(draft.to_record())
    assert ReferenceRecord.from_record(first.to_record()) == first
    assert replace(first, evidence=(replace(first.evidence[0], relevance=1),)).identity_hash != first.identity_hash
    with pytest.raises(FrozenInstanceError):
        first.query_id = "changed"
    with pytest.raises(ValueError):
        ReferenceRecord.from_record({**first.to_record(), "reviewer_id": "fabricated"})
    with pytest.raises(ValueError):
        derive_reference(replace(draft, annotation_status="reviewed", reviewed_at="2026-01-03T00:00:00+00:00"), truth_version="v2")


def _approval(status="approved", *, approved_at="2026-02-01T00:00:00+00:00"):
    roles = ("preregistration", "java_evidence_audit_set", "chinese_coverage_audit", "methodology_review", "final_data_qa")
    prerequisites = tuple(PrerequisiteReference(role, chr(97 + i) * 64, "v1", True,
                                                   f"docs/experiments/synthetic-{role}.json") for i, role in enumerate(roles))
    return ReferenceApprovalRecord("v1", "synthetic-approval-v1", status, REFERENCE_METHOD,
                                   "synthetic-dataset", IdentityRef("v1", D), IdentityRef("v1", "b" * 64),
                                   IdentityRef("synthetic-reference-v1", "c" * 64), IdentityRef("synthetic-draft-v1", "d" * 64),
                                   "e" * 64, IdentityRef("v1", "f" * 64), "synthetic-only",
                                   prerequisites, (), "1" * 64, None, approved_at if status == "approved" else None,
                                   "docs/experiments/reference/synthetic.jsonl",
                                   "docs/experiments/audits/synthetic-decision.json")


def test_approval_projection_roles_and_timestamp_boundary():
    approval = _approval()
    assert ReferenceApprovalRecord.from_record(approval.to_record()) == approval
    assert replace(approval, approved_at="2026-02-02T00:00:00+00:00").identity_hash == approval.identity_hash
    assert replace(approval, result_namespace="synthetic-other").identity_hash != approval.identity_hash
    assert replace(approval, reference_artifact_path="docs/experiments/reference/elsewhere.jsonl").identity_hash == approval.identity_hash
    assert replace(approval, resolution_identities=(IdentityRef("v1", "0" * 64),)).identity_hash != approval.identity_hash
    assert _approval("pending").approval_status == "pending"
    assert _approval("blocked").approval_status == "blocked"
    with pytest.raises(ValueError):
        replace(approval, prerequisite_identities=approval.prerequisite_identities[:-1])
    with pytest.raises(ValueError):
        replace(approval, prerequisite_identities=approval.prerequisite_identities + approval.prerequisite_identities[:1])
    with pytest.raises(ValueError, match="identities must be unique"):
        replace(approval, prerequisite_identities=approval.prerequisite_identities[:-1] +
                (replace(approval.prerequisite_identities[-1], identity=approval.prerequisite_identities[0].identity),))
    with pytest.raises(ValueError):
        replace(approval, approval_status="pending")
    with pytest.raises(ValueError):
        ReferenceApprovalRecord.from_record({**approval.to_record(), "unknown": 1})
    with pytest.raises(ValueError):
        IdentityRef("v1", "invalid")


def test_raw_bytes_erratum_resolution_and_writer(tmp_path):
    samples = (b"a\n", b"a\r\n", "汉字\n".encode(), b"a ", b"a")
    assert len({raw_sha256(x) for x in samples}) == len(samples)
    response = b"synthetic response\r\n"
    correction = ErratumRecord("v1", raw_sha256(response), "synthetic-query", "E01",
                               "old claim", "corrected claim", D, "src/a.py:1", "synthetic source", "material", "open")
    resolution = ResolutionRecord("v1", correction.identity_hash, "source_verification", D, "closed", "synthetic verified")
    assert ErratumRecord.from_record(correction.to_record()) == correction
    assert ResolutionRecord.from_record(resolution.to_record()) == resolution
    assert raw_sha256(response) == correction.target_response_hash
    reference = derive_reference(_draft(), truth_version="synthetic-reference-v1")
    first = write_lifecycle_artifact(tmp_path, reference, {"synthetic-raw.txt": response})
    assert first.name == reference.identity_hash
    assert (first / "synthetic-raw.txt").read_bytes() == response
    with pytest.raises(FileExistsError):
        write_lifecycle_artifact(tmp_path, reference)
    assert (first / "synthetic-raw.txt").read_bytes() == response
    with pytest.raises(ValueError):
        write_lifecycle_artifact(tmp_path / "secret", reference, {"raw.txt": b"Bearer verylongsecretvalue123"})
    with pytest.raises(ValueError):
        write_lifecycle_artifact(tmp_path / "sidecar", reference, {"record.json.sha256": b"fake"})


def test_lifecycle_writer_failure_does_not_publish_partial_record(tmp_path, monkeypatch):
    reference = derive_reference(_draft(), truth_version="synthetic-reference-v1")
    original_write = Path.write_bytes

    def fail_raw_blob(path, payload):
        if path.name == "synthetic-raw.txt":
            raise OSError("synthetic write fault")
        return original_write(path, payload)

    monkeypatch.setattr(Path, "write_bytes", fail_raw_blob)
    with pytest.raises(OSError, match="synthetic write fault"):
        write_lifecycle_artifact(tmp_path, reference, {"synthetic-raw.txt": b"synthetic only"})
    assert not (tmp_path / reference.identity_hash).exists()


def test_current_gate_is_navigation_only():
    gate = CurrentGateIndex("v1", "6.2B.1", "OPEN", "IMPLEMENTED / QA PENDING", None,
                            False, False, ("reference not approved",), "independent QA",
                            ("docs/experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md",), "8f931f73bf4b0630dff5e679104fbc025132cafa")
    assert CurrentGateIndex.from_record(gate.to_record()) == gate
    with pytest.raises(ValueError):
        replace(gate, formal_execution_eligible=True)
    with pytest.raises(ValueError):
        CurrentGateIndex.from_record({**gate.to_record(), "unknown": True})


def _navigation_gate(phase="6.2B.2", status="ALLOWED BUT NOT STARTED"):
    return CurrentGateIndex("v1", phase, "OPEN", status, None, False, False,
                            ("Phase 6.2 remains open",), "Phase 6.2B.2 Evidence Capture Proof",
                            ("docs/experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md",),
                            "8f931f73bf4b0630dff5e679104fbc025132cafa")


def test_current_gate_frozen_phase_status_matrix():
    expected = {
        "6.2B.0": {"COMPLETED"},
        "6.2B.1": {"ALLOWED BUT NOT STARTED", "IMPLEMENTATION IN PROGRESS",
                   "IMPLEMENTED / QA PENDING", "QA PASS / DOCUMENTATION GATE PENDING",
                   "COMPLETED", "CLOSED"},
        **{f"6.2B.{stage}": {"ALLOWED BUT NOT STARTED", "IN PROGRESS", "BLOCKED", "COMPLETED"}
           for stage in range(2, 7)},
    }
    all_statuses = set().union(*expected.values())
    for phase, allowed in expected.items():
        for status in all_statuses:
            if status in allowed:
                gate = _navigation_gate(phase, status)
                assert CurrentGateIndex.from_record(gate.to_record()) == gate
            else:
                with pytest.raises(ValueError, match="current gate state is invalid"):
                    _navigation_gate(phase, status)


@pytest.mark.parametrize("phase", ["", "6.2B.7", "6.2C", "7.0", "V3.2", "random-phase",
                                          "6.2B.2 ", " 6.2B.2", "6.2b.2"])
def test_current_gate_rejects_unknown_phase(phase):
    with pytest.raises(ValueError, match="schema/phase is invalid"):
        _navigation_gate(phase=phase)


@pytest.mark.parametrize("status", ["", "READY", "DONE", "APPROVED", "GO", "FORMAL READY",
                                           "allowed but not started", "ALLOWED BUT NOT STARTED "])
def test_current_gate_rejects_unknown_status(status):
    with pytest.raises(ValueError, match="current gate state is invalid"):
        _navigation_gate(status=status)


def test_current_gate_navigation_strict_record_and_legacy_compatibility():
    gate = _navigation_gate()
    record = gate.to_record()
    assert gate.current_gate == "OPEN" and gate.selected_reference_approval_identity is None
    assert gate.dry_run_eligible is False and gate.formal_execution_eligible is False
    assert CurrentGateIndex.from_record(json.loads(json.dumps(record))) == gate
    assert CurrentGateIndex.from_record(dict(reversed(list(record.items())))).to_record() == record
    for field, value in (("dry_run_eligible", "false"), ("dry_run_eligible", 0),
                         ("formal_execution_eligible", "true"), ("formal_execution_eligible", 1)):
        with pytest.raises(ValueError):
            CurrentGateIndex.from_record({**record, field: value})
    for field in ("dry_run_eligible", "formal_execution_eligible"):
        with pytest.raises(ValueError):
            replace(gate, **{field: True})
    with pytest.raises(ValueError):
        CurrentGateIndex.from_record({**record, "unknown": True})
    authority = RepositoryAuthority(ROOT)
    current = authority.load_current_gate()
    assert current.schema_version == "v1"
    assert CurrentGateIndex.from_record(current.to_record()) == current
    assert validate_current_gate(authority, current) is None
    assert current.current_gate == "CLOSED"
    approval_id = current.selected_reference_approval_identity
    assert approval_id is not None
    approval = authority.load_typed(f"docs/experiments/reference_approval/{approval_id}.json", ReferenceApprovalRecord, approval_id)
    closure = authority.load_typed("docs/experiments/reference_approval/phase62_closure.json", Phase62ClosureRecord)
    assert approval.approval_status == "approved"
    assert closure.approved_reference_identity == approval.identity_hash
    assert current.dry_run_eligible is True
    assert current.formal_execution_eligible is False
    legacy = CurrentGateIndex.from_record({**record, "current_phase": "6.2B.1",
                                           "phase_status": "IMPLEMENTED / QA PENDING"})
    assert CurrentGateIndex.from_record(legacy.to_record()) == legacy


def test_next_phase_navigation_cannot_grant_formal_authority(synthetic_authority):
    root, config, approval, receipt, runtime, commit = synthetic_authority
    for path in (f"docs/experiments/reference_approval/{approval}.json",
                 "docs/experiments/reference_approval/phase62_closure.json", receipt):
        (root / path).unlink()
    gate = _navigation_gate()
    _json(root, "docs/experiments/current_gate.json", gate.to_record())
    _git(root, "add", "-A", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic navigation without authority")
    authority = RepositoryAuthority(root)
    assert authority.load_current_gate() == gate
    assert validate_current_gate(authority, gate) is None
    with pytest.raises(EligibilityError, match="current_gate_conflict"):
        _validate_fixture(synthetic_authority)
    gate_path = root / "docs/experiments/current_gate.json"
    gate_path.write_bytes(gate_path.read_bytes() + b" ")
    with pytest.raises(EligibilityError, match="artifact_worktree_mismatch"):
        authority.load_current_gate()
    forged = replace(gate, current_gate="CLOSED", phase_status="COMPLETED",
                     selected_reference_approval_identity=approval,
                     dry_run_eligible=True, formal_execution_eligible=True)
    _json(root, "docs/experiments/current_gate.json", forged.to_record())
    _git(root, "add", "docs/experiments/current_gate.json")
    _git(root, "commit", "-qm", "synthetic forged gate")
    with pytest.raises(EligibilityError, match="artifact_missing"):
        _validate_fixture(synthetic_authority)


def test_identity_is_process_and_order_independent():
    approval = _approval()
    reversed_approval = replace(approval, prerequisite_identities=tuple(reversed(approval.prerequisite_identities)))
    assert reversed_approval.identity_hash == approval.identity_hash
    generator = random.Random(6201)
    for _ in range(100):
        shuffled = list(approval.prerequisite_identities)
        generator.shuffle(shuffled)
        assert replace(approval, prerequisite_identities=tuple(shuffled)).identity_hash == approval.identity_hash
    assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})
    script = "from experiments import canonical_hash; print(canonical_hash({'b': 2, 'a': 1}))"
    hashes = []
    for seed in ("1", "7", "31"):
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(ROOT)}
        hashes.append(subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env,
                                     check=True, capture_output=True, text=True).stdout.strip())
    assert hashes == [canonical_hash({"a": 1, "b": 2})] * 3


def test_dry_run_and_formal_share_experiment_family_without_sharing_config_identity():
    formal = BenchmarkConfig(
        "v1", D, "v1", "b" * 64, "v1", "c" * 64,
        Strategy.LEXICAL, RetrievalUnit.SYMBOL, matrix_run_id="RQ1-SYMBOL",
        population=Population.ENGLISH_TEST, run_kind=RunKind.FORMAL,
        approved_reference_identity="d" * 64,
    )
    dry_run = replace(formal, population=Population.ENGLISH_DEV, run_kind=RunKind.DRY_RUN)
    assert formal.identity_hash != dry_run.identity_hash
    assert formal.experiment_family_identity == dry_run.experiment_family_identity
    assert replace(formal, approved_reference_identity="e" * 64).experiment_family_identity != formal.experiment_family_identity


@pytest.fixture
def synthetic_authority(tmp_path):
    """A separate temporary Git repository; approval version and namespace are synthetic."""
    root = tmp_path / "synthetic-repository"
    root.mkdir()
    shutil.copytree(ROOT / "docs" / "experiments", root / "docs" / "experiments")
    _git(root, "init", "-q")
    _git(root, "-c", "protocol.file.allow=always", "fetch", "-q", str(ROOT),
         "12391233daa2149ead4f451e920b2e0d8a1a6beb")
    _git(root, "config", "user.name", "Synthetic Test")
    _git(root, "config", "user.email", "synthetic@example.invalid")
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic frozen inputs")
    authority = RepositoryAuthority(root)
    dataset, queries, drafts = authority.load_frozen_inputs()
    query_hash = canonical_hash([x.to_record() for x in queries])
    draft_hash = canonical_hash([x.to_record() for x in drafts])
    reference = tuple(derive_reference(x, truth_version="synthetic-reference-v1") for x in drafts)
    reference = tuple(sorted(reference, key=lambda x: x.query_id))
    reference_hash = canonical_hash([x.identity_record() for x in reference])
    ref_path = "docs/experiments/reference/synthetic-reference-v1.jsonl"
    reference_file_hash = _write(root, ref_path, canonical_jsonl(x.to_record() for x in reference).encode())
    _write(root, ref_path + ".sha256", (reference_file_hash + "\n").encode("ascii"))
    addendum_hash = authority.raw_checksum("docs/experiments/Experiment_Protocol_Addendum_D_V3_1_0.md")
    prereg = canonical_hash({"query_ids": list(sorted(x.query_id for x in queries if x.split == "english_test" and x.language == "java")),
                             "query_set_hash": query_hash, "addendum_d_sha256": addendum_hash})
    prepared = authority.json_record("docs/experiments/evidence_audit/prepared/manifest.json")
    prepared_by_id = {x["query_id"]: x for x in prepared["entries"]}
    query_by_id = {x.query_id: x for x in queries}
    audits = []
    paths = []
    unavailable = Availability("unavailable", None, "not provided by synthetic platform")
    for query_id in sorted(prepared_by_id):
        entry = prepared_by_id[query_id]
        base = f"docs/experiments/evidence_audit/executions/synthetic-{query_id}"
        sent = _capture(root, base + "/sent.txt", authority.raw_bytes("docs/experiments/evidence_audit/prepared/" + entry["input_path"]))
        session = _capture(root, base + "/session.txt", ("synthetic independent session " + query_id).encode())
        context = _capture(root, base + "/context.txt", ("synthetic isolated context " + query_id).encode())
        model = _capture(root, base + "/model.txt", ("DeepSeek-V4-Flash synthetic UI " + query_id).encode())
        prepared_record = authority.json_record("docs/experiments/evidence_audit/prepared/records/" + query_id + ".json")
        reply_record = {"query_id": query_id, "overall_status": "SUPPORTS",
                        "evidence_reviews": [
                            {"evidence_id": item["evidence_id"], "verdict": "SUPPORTS",
                             "identity": item["original_identity"], "source_behavior": "synthetic source behavior",
                             "grade_correspondence_suspect": False, "rationale": "synthetic support"}
                            for item in prepared_record["evidence_reviews"]],
                        "scope_statement": "synthetic cited source only",
                        "end_marker": "RESPONSE_END_" + query_id.upper().replace("-", "_")}
        reply_bytes = canonical_json(reply_record).encode()
        _, reviews = parse_external_evidence_response(reply_bytes, query_id, prepared_record["evidence_reviews"])
        reply = _capture(root, base + "/reply.txt", reply_bytes)
        transcript = _capture(root, base + "/transcription.json", canonical_json([x.to_record() for x in reviews]).encode())
        audit = EvidenceAuditRecord("v1", query_id, query_by_id[query_id].ground_truth_id,
                                    1, None, dataset.dataset_hash, canonical_hash(query_by_id[query_id].to_record()),
                                    reference_hash, prereg, entry["input_sha256"], sent, reply, True, None,
                                    VisiblePart(unavailable, None), VisiblePart(Availability("available", "displayed", None), reply),
                                    unavailable, session, "synthetic-ui", context, "DeepSeek-V4-Flash",
                                    Availability("available", "DeepSeek-V4.1-Flash", None),
                                    Availability("available", "user-provided platform mapping", None),
                                    unavailable, unavailable, unavailable, model,
                                    "2026-02-01T00:00:00+00:00", "2026-02-01T00:00:01+00:00",
                                    "synthetic clock", "second", reviews, transcript.raw_sha256, transcript,
                                    "SUPPORTS", "valid", ())
        path = base + "/record.json"
        _json(root, path, audit.to_record())
        audits.append((query_id, audit.identity_hash)); paths.append((query_id, path))
    audit_set = EvidenceAuditSet("v1", prereg, tuple(q for q, _ in audits), tuple(audits),
                                 "v1", "english_test_java", (), "complete", tuple(paths))
    audit_set_path = "docs/experiments/audits/synthetic-java-set.json"
    _json(root, audit_set_path, audit_set.to_record())
    prereq_refs = [PrerequisiteReference("preregistration", prereg, "v1", True,
                                         "docs/experiments/Experiment_Protocol_Addendum_D_V3_1_0.md"),
                   PrerequisiteReference("java_evidence_audit_set", audit_set.identity_hash, "v1", True, audit_set_path)]
    other_identities = {}
    for role in ("methodology_review", "chinese_coverage_audit", "final_data_qa"):
        base = "docs/experiments/audits/synthetic-" + role
        output = _capture(root, base + "-output.txt", ("synthetic output " + role).encode())
        provenance = _capture(root, base + "-provenance.txt", ("synthetic provenance " + role).encode())
        inputs = (("reference", reference_hash),)
        if role == "chinese_coverage_audit":
            inputs += (("methodology_review", other_identities["methodology_review"]),)
        if role == "final_data_qa":
            inputs = (("reference", reference_hash), ("java_evidence_audit_set", audit_set.identity_hash),
                      ("chinese_coverage_audit", other_identities["chinese_coverage_audit"]),
                      ("methodology_review", other_identities["methodology_review"]))
        record = ApprovalPrerequisiteRecord("v1", role, "pass", inputs, output.raw_sha256,
                                            provenance.raw_sha256, "closed", output.artifact_path, provenance.artifact_path,
                                            "2026-02-01T12:00:00+00:00")
        path = base + ".json"
        _json(root, path, record.to_record())
        prereq_refs.append(PrerequisiteReference(role, record.identity_hash, "v1", True, path))
        other_identities[role] = record.identity_hash
    decision = ApprovalDecisionRecord("v1", "approved", "synthetic-test-process", "synthetic-fixture-authority",
                                      "synthetic decision", reference_hash, tuple(x.identity for x in prereq_refs))
    decision_path = "docs/experiments/audits/synthetic-decision.json"
    _json(root, decision_path, decision.to_record())
    approval = ReferenceApprovalRecord(
        "v1", "synthetic-test-v1", "approved", REFERENCE_METHOD, dataset.dataset_id,
        IdentityRef(dataset.version, dataset.dataset_hash), IdentityRef(queries[0].query_set_version, query_hash),
        IdentityRef("synthetic-reference-v1", reference_hash), IdentityRef(drafts[0].ground_truth_version, draft_hash),
        authority.methodology_identity(), IdentityRef("v1", authority.engineering_identity()),
        "synthetic-only", tuple(prereq_refs), (), decision.identity_hash, None,
        "2026-02-02T00:00:00+00:00", ref_path, decision_path,
    )
    approval_path = f"docs/experiments/reference_approval/{approval.identity_hash}.json"
    _json(root, approval_path, approval.to_record())
    documentation_decision = Phase62DocumentationDecisionRecord(
        "v1", "closed", approval.identity_hash, other_identities["final_data_qa"],
        "synthetic-test-process", "synthetic documentation closure")
    documentation_path = "docs/experiments/audits/synthetic-documentation-decision.json"
    _json(root, documentation_path, documentation_decision.to_record())
    closure = Phase62ClosureRecord("v1", "closed", approval.identity_hash,
                                   other_identities["final_data_qa"], documentation_decision.identity_hash,
                                   _git(root, "rev-parse", "HEAD"), documentation_path)
    closure_path = "docs/experiments/reference_approval/phase62_closure.json"
    _json(root, closure_path, closure.to_record())
    config = BenchmarkConfig(dataset.version, dataset.dataset_hash, queries[0].query_set_version,
                             query_hash, drafts[0].ground_truth_version, draft_hash, Strategy.LEXICAL,
                             RetrievalUnit.SYMBOL, matrix_run_id="RQ1-SYMBOL", population=Population.ENGLISH_TEST,
                             run_kind=RunKind.FORMAL, approved_reference_identity=approval.identity_hash)
    runtime_evidence = _runtime()
    runtime_identity = canonical_hash(runtime_evidence.to_record())
    code_commit = _git(root, "rev-parse", "HEAD")
    receipt_path = _synthetic_matrix_receipt(root, config, queries, approval.identity_hash,
                                             dataset.dataset_hash, query_hash, reference_hash,
                                             runtime_evidence, code_commit)
    gate = CurrentGateIndex("v1", "6.2B.1", "CLOSED", "CLOSED", approval.identity_hash,
                            True, False, (), "synthetic formal validation",
                            ("docs/experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md",),
                            code_commit)
    _json(root, "docs/experiments/current_gate.json", gate.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic approval fixture")
    return root, config, approval.identity_hash, receipt_path, runtime_evidence, code_commit


def _validate_fixture(fixture, **overrides):
    root, config, approval, receipt, runtime, commit = fixture
    return validate_formal_eligibility(
        purpose=RunKind.FORMAL, repository_root=root, requested_config=config,
        selected_reference_approval=approval, runtime_evidence=runtime,
        code_commit=commit, dry_run_receipt=receipt, **overrides,
    )


def test_synthetic_repository_authority_passes_only_with_complete_dag(synthetic_authority):
    result = _validate_fixture(synthetic_authority)
    assert result.purpose is RunKind.FORMAL
    assert result.approval_identity == synthetic_authority[2]
    assert len(result.reference) == 72
    assert len(result.queries) == 72


def test_matrix_receipt_reloads_from_committed_head_with_false_navigation_flag(synthetic_authority):
    root, _, _, receipt_path, _, _ = synthetic_authority
    authority = RepositoryAuthority(root)
    assert authority.load_current_gate().formal_execution_eligible is False
    receipt = authority.load_typed(receipt_path, DryRunReceiptV2)
    artifact_set = authority.load_typed(receipt.artifact_set_path, DryRunArtifactSet,
                                        receipt.artifact_set_identity)
    assert len(artifact_set.runs) == 17
    assert artifact_set.coverage_count == 204
    assert _validate_fixture(synthetic_authority).purpose is RunKind.FORMAL


def test_uncommitted_receipt_cannot_be_authority(synthetic_authority):
    root, config, approval, receipt_path, runtime, commit = synthetic_authority
    copied_path = "docs/experiments/audits/uncommitted-receipt.json"
    receipt = RepositoryAuthority(root).load_typed(receipt_path, DryRunReceiptV2)
    _json(root, copied_path, receipt.to_record())
    with pytest.raises(EligibilityError, match="artifact_not_committed"):
        validate_formal_eligibility(
            purpose=RunKind.FORMAL, repository_root=root, requested_config=config,
            selected_reference_approval=approval, runtime_evidence=runtime,
            code_commit=commit, dry_run_receipt=copied_path)


def test_committed_receipt_requires_content_addressed_identity(synthetic_authority):
    root, config, approval, receipt_path, runtime, commit = synthetic_authority
    copied_path = "docs/experiments/audits/dry_run_receipts/wrong-name/record.json"
    receipt = RepositoryAuthority(root).load_typed(receipt_path, DryRunReceiptV2)
    _json(root, copied_path, receipt.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic wrong receipt identity path")
    with pytest.raises(EligibilityError, match="dry_run_receipt_identity_mismatch"):
        validate_formal_eligibility(
            purpose=RunKind.FORMAL, repository_root=root, requested_config=config,
            selected_reference_approval=approval, runtime_evidence=runtime,
            code_commit=commit, dry_run_receipt=copied_path)


def test_legacy_single_config_receipt_stays_readable_but_cannot_open_formal_gate(synthetic_authority):
    root, config, approval, _, runtime, commit = synthetic_authority
    legacy = DryRunReceipt("v1", "pass", approval, config.dataset_hash,
                           config.query_set_hash, D, config.experiment_family_identity,
                           canonical_hash(runtime.to_record()), commit, D,
                           "legacy-v1", "english_dev", None,
                           "docs/experiments/audits/legacy-result.json")
    assert DryRunReceipt.from_record(legacy.to_record()) == legacy
    path = "docs/experiments/audits/legacy-receipt.json"
    _json(root, path, legacy.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic legacy receipt")
    with pytest.raises(EligibilityError, match="artifact_schema_invalid"):
        validate_formal_eligibility(
            purpose=RunKind.FORMAL, repository_root=root, requested_config=config,
            selected_reference_approval=approval, runtime_evidence=runtime,
            code_commit=commit, dry_run_receipt=path)


def test_frozen_matrix_exactness_and_canonical_identity():
    rows = tuple((matrix_id, f"{index + 1:064x}", f"{index + 101:064x}")
                 for index, matrix_id in enumerate(FROZEN_MATRIX_IDS))
    matrix = DryRunConfigurationSet("v1", rows)
    assert len(rows) == 17
    assert DryRunConfigurationSet.from_record(matrix.to_record()).identity_hash == matrix.identity_hash
    assert DryRunConfigurationSet("v1", tuple(reversed(rows))).identity_hash == matrix.identity_hash
    for invalid in (rows[:-1], rows[:-1] + (rows[0],), rows + (("EXTRA", D, D),),
                    rows[:-1] + (("UNKNOWN", D, D),)):
        with pytest.raises(ValueError):
            DryRunConfigurationSet("v1", invalid)


def test_forged_navigation_boolean_cannot_replace_receipt(synthetic_authority):
    root, config, approval, receipt_path, runtime, commit = synthetic_authority
    gate_path = "docs/experiments/current_gate.json"
    gate = RepositoryAuthority(root).load_current_gate()
    _json(root, gate_path, replace(gate, formal_execution_eligible=True).to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic navigation update")
    assert _validate_fixture(synthetic_authority).purpose is RunKind.FORMAL
    (root / receipt_path).unlink()
    _git(root, "add", "-A", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic receipt removal")
    with pytest.raises(EligibilityError, match="artifact_missing"):
        _validate_fixture(synthetic_authority)


def _rebind_synthetic_artifacts(root, receipt_path, artifact_set_record):
    receipt = RepositoryAuthority(root).load_typed(receipt_path, DryRunReceiptV2)
    _json(root, receipt.artifact_set_path, artifact_set_record)
    set_identity = canonical_hash(artifact_set_record)
    hashes = [run["raw_sha256"] for run in artifact_set_record["runs"]]
    updates = {}
    for kind in ("determinism", "leakage"):
        path = getattr(receipt, kind + "_evidence_path")
        evidence = json.loads((root / path).read_text())
        evidence["artifact_set_identity"] = set_identity
        evidence["run_raw_sha256"] = hashes
        updates[kind + "_evidence_sha256"] = _json(root, path, evidence)
    updated = replace(receipt, artifact_set_identity=set_identity, **updates)
    directory = write_lifecycle_artifact(
        root / "docs/experiments/audits/dry_run_receipts", updated)
    new_path = (directory / "record.json").relative_to(root).as_posix()
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic dry-run artifact mutation")
    return new_path


@pytest.mark.parametrize("change", ("missing", "english_test", "chinese"))
def test_formal_gate_rejects_incomplete_or_leaking_coverage(synthetic_authority, change):
    root, _, _, receipt_path, _, _ = synthetic_authority
    receipt = RepositoryAuthority(root).load_typed(receipt_path, DryRunReceiptV2)
    artifact_set_record = json.loads((root / receipt.artifact_set_path).read_text())
    run = artifact_set_record["runs"][0]
    raw = [json.loads(line) for line in (root / run["raw_path"]).read_text().splitlines()]
    if change == "missing":
        raw.pop()
    else:
        raw[0]["split"] = "english_test" if change == "english_test" else "chinese_coverage"
    run["raw_sha256"] = _write(root, run["raw_path"], canonical_jsonl(raw).encode())
    aggregate = json.loads((root / run["aggregate_path"]).read_text())
    aggregate["raw_results_sha256"] = run["raw_sha256"]
    run["aggregate_sha256"] = _json(root, run["aggregate_path"], aggregate)
    manifest = json.loads((root / run["manifest_path"]).read_text())
    manifest["output_checksums"] = {"raw_results.jsonl": run["raw_sha256"],
                                    "aggregate_results.json": run["aggregate_sha256"]}
    run["manifest_sha256"] = _json(root, run["manifest_path"], manifest)
    new_path = _rebind_synthetic_artifacts(root, receipt_path, artifact_set_record)
    with pytest.raises(EligibilityError, match="dry_run_coverage_mismatch|dry_run_raw_scope_mismatch"):
        _validate_fixture((*synthetic_authority[:3], new_path, *synthetic_authority[4:]))


@pytest.mark.parametrize("change", ("missing", "duplicate", "extra"))
def test_formal_gate_rejects_nonexact_artifact_matrix(synthetic_authority, change):
    root, _, _, receipt_path, _, _ = synthetic_authority
    receipt = RepositoryAuthority(root).load_typed(receipt_path, DryRunReceiptV2)
    artifact_set_record = json.loads((root / receipt.artifact_set_path).read_text())
    if change == "missing":
        artifact_set_record["runs"].pop()
    elif change == "duplicate":
        artifact_set_record["runs"][-1] = artifact_set_record["runs"][0]
    else:
        artifact_set_record["runs"].append(artifact_set_record["runs"][0])
    new_path = _rebind_synthetic_artifacts(root, receipt_path, artifact_set_record)
    with pytest.raises(EligibilityError, match="artifact_schema_invalid"):
        _validate_fixture((*synthetic_authority[:3], new_path, *synthetic_authority[4:]))


def test_formal_gate_requires_committed_determinism_evidence(synthetic_authority):
    root, _, _, receipt_path, _, _ = synthetic_authority
    receipt = RepositoryAuthority(root).load_typed(receipt_path, DryRunReceiptV2)
    path = receipt.determinism_evidence_path
    evidence = json.loads((root / path).read_text())
    evidence["status"] = "fail"
    new_hash = _json(root, path, evidence)
    updated = replace(receipt, determinism_evidence_sha256=new_hash)
    directory = write_lifecycle_artifact(
        root / "docs/experiments/audits/dry_run_receipts", updated)
    new_path = (directory / "record.json").relative_to(root).as_posix()
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic failed determinism")
    with pytest.raises(EligibilityError, match="dry_run_evidence_mismatch"):
        _validate_fixture((*synthetic_authority[:3], new_path, *synthetic_authority[4:]))


def test_synthetic_dry_run_eligibility_uses_dev_population_without_receipt(synthetic_authority):
    root, formal, approval, _, runtime, commit = synthetic_authority
    config = replace(formal, run_kind=RunKind.DRY_RUN, population=Population.ENGLISH_DEV)
    validated = validate_formal_eligibility(
        purpose=RunKind.DRY_RUN, repository_root=root, requested_config=config,
        selected_reference_approval=approval, runtime_evidence=runtime, code_commit=commit,
    )
    assert validated.purpose is RunKind.DRY_RUN
    assert validated.config_identity == config.identity_hash
    assert validated.dry_run_receipt_path is None


def test_dry_run_uses_closed_authority_even_when_navigation_flag_is_false(synthetic_authority):
    root, formal, approval, _, runtime, commit = synthetic_authority
    gate_path = "docs/experiments/current_gate.json"
    gate = RepositoryAuthority(root).load_current_gate()
    _json(root, gate_path, replace(gate, dry_run_eligible=False).to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic dry-run navigation update")
    dry_config = replace(formal, run_kind=RunKind.DRY_RUN,
                         population=Population.ENGLISH_DEV)
    validated = validate_formal_eligibility(
        purpose=RunKind.DRY_RUN, repository_root=root, requested_config=dry_config,
        selected_reference_approval=approval, runtime_evidence=runtime,
        code_commit=commit)
    assert validated.purpose is RunKind.DRY_RUN
    assert validated.dry_run_receipt_path is None


def _open_readiness_fixture(fixture):
    root, _, approval_id, receipt, _, _ = fixture
    authority = RepositoryAuthority(root)
    approval = authority.load_typed(f"docs/experiments/reference_approval/{approval_id}.json", ReferenceApprovalRecord)
    request = ReferenceApprovalRequest.from_approval(approval)
    closure = authority.load_typed("docs/experiments/reference_approval/phase62_closure.json", Phase62ClosureRecord)
    shutil.rmtree(root / "docs/experiments/reference_approval")
    for path in (approval.decision_artifact_path, closure.documentation_decision_artifact_path, receipt):
        (root / path).unlink()
    _json(root, "docs/experiments/current_gate.json", _navigation_gate().to_record())
    _git(root, "add", "-A", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic pre-approval stage")
    return root, request


def test_readiness_passes_without_approval_closure_or_execution_authority(synthetic_authority):
    from experiments.eligibility import is_validator_issued
    root, request = _open_readiness_fixture(synthetic_authority)
    assert ReferenceApprovalRequest.from_record(request.to_record()) == request
    assert not (root / "docs/experiments/reference_approval").exists()
    result = validate_reference_approval_readiness(repository_root=root, request=request)
    assert result is None
    assert not is_validator_issued(result)
    assert not is_validator_issued(request)
    with pytest.raises(EligibilityError, match="current_gate_conflict"):
        _validate_fixture(synthetic_authority)


@pytest.mark.parametrize("role", ("methodology_review", "chinese_coverage_audit", "final_data_qa"))
def test_readiness_missing_required_role_or_artifact_fails(synthetic_authority, role):
    root, request = _open_readiness_fixture(synthetic_authority)
    missing = replace(request, prerequisite_identities=tuple(x for x in request.prerequisite_identities if x.role != role))
    with pytest.raises(EligibilityError, match="prerequisite_missing"):
        validate_reference_approval_readiness(repository_root=root, request=missing)
    path = next(x.artifact_path for x in request.prerequisite_identities if x.role == role)
    _commit_change(root, path, remove=True)
    with pytest.raises(EligibilityError, match="artifact_missing"):
        validate_reference_approval_readiness(repository_root=root, request=request)


@pytest.mark.parametrize("field", ("dataset_identity", "query_set_identity", "source_draft_identity", "reference_identity"))
def test_readiness_rejects_wrong_candidate_identity(synthetic_authority, field):
    root, request = _open_readiness_fixture(synthetic_authority)
    request = replace(request, **{field: replace(getattr(request, field), hash="0" * 64)})
    with pytest.raises(EligibilityError, match="identity_mismatch"):
        validate_reference_approval_readiness(repository_root=root, request=request)


def test_readiness_requires_explicit_closed_resolution_bindings(synthetic_authority):
    root, request = _open_readiness_fixture(synthetic_authority)
    authority = RepositoryAuthority(root)
    audit_ref = next(x for x in request.prerequisite_identities if x.role == "java_evidence_audit_set")
    audit_set = authority.load_typed(audit_ref.artifact_path, EvidenceAuditSet)
    resolution = ResolutionRecord("v1", audit_set.accepted_attempt_identities[0][1], "source_verification", D,
                                  "open", "synthetic required finding")
    audit_set = replace(audit_set, resolution_identities=(resolution.identity_hash,))
    _json(root, audit_ref.artifact_path, audit_set.to_record())
    _json(root, f"docs/experiments/audits/resolutions/{resolution.identity_hash}.json", resolution.to_record())
    qa_ref = next(x for x in request.prerequisite_identities if x.role == "final_data_qa")
    qa = authority.load_typed(qa_ref.artifact_path, ApprovalPrerequisiteRecord)
    qa = replace(qa, input_identities=tuple(
        (role, audit_set.identity_hash if role == "java_evidence_audit_set" else digest)
        for role, digest in qa.input_identities))
    _json(root, qa_ref.artifact_path, qa.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic required resolution")
    request = replace(request, prerequisite_identities=tuple(
        replace(x, identity=audit_set.identity_hash) if x.role == audit_ref.role else
        replace(x, identity=qa.identity_hash) if x.role == qa_ref.role else x
        for x in request.prerequisite_identities))
    with pytest.raises(EligibilityError, match="audit_resolution_mismatch"):
        validate_reference_approval_readiness(repository_root=root, request=request)
    request = replace(request, resolution_identities=(IdentityRef("v1", resolution.identity_hash),))
    with pytest.raises(EligibilityError, match="resolution_not_closed"):
        validate_reference_approval_readiness(repository_root=root, request=request)


def test_readiness_rejects_closed_stage_and_uncommitted_review(synthetic_authority):
    root, _, approval_id, _, _, _ = synthetic_authority
    approval = RepositoryAuthority(root).load_typed(
        f"docs/experiments/reference_approval/{approval_id}.json", ReferenceApprovalRecord)
    with pytest.raises(EligibilityError, match="readiness_gate_conflict"):
        validate_reference_approval_readiness(repository_root=root, request=ReferenceApprovalRequest.from_approval(approval))
    root, request = _open_readiness_fixture(synthetic_authority)
    path = next(x.artifact_path for x in request.prerequisite_identities if x.role == "methodology_review")
    (root / path).write_bytes((root / path).read_bytes() + b" ")
    with pytest.raises(EligibilityError, match="artifact_worktree_mismatch"):
        validate_reference_approval_readiness(repository_root=root, request=request)


def test_missing_approval_or_receipt_fails_closed(synthetic_authority):
    root, config, approval, receipt, runtime, commit = synthetic_authority
    with pytest.raises(EligibilityError):
        validate_formal_eligibility(purpose=RunKind.FORMAL, repository_root=root,
                                    requested_config=config, selected_reference_approval=None,
                                    runtime_evidence=runtime, code_commit=commit, dry_run_receipt=receipt)
    with pytest.raises(EligibilityError, match="dry_run_receipt_missing"):
        validate_formal_eligibility(purpose=RunKind.FORMAL, repository_root=root,
                                    requested_config=config, selected_reference_approval=approval,
                                    runtime_evidence=runtime, code_commit=commit)


def test_tampered_gate_cannot_authorize(synthetic_authority):
    root, config, approval, receipt, runtime, commit = synthetic_authority
    gate_path = root / "docs/experiments/current_gate.json"
    value = json.loads(gate_path.read_text())
    value["selected_reference_approval_identity"] = "0" * 64
    gate_path.write_text(canonical_json(value, pretty=True))
    with pytest.raises(EligibilityError):
        _validate_fixture(synthetic_authority)


def test_path_escape_and_uncommitted_bytes_rejected(synthetic_authority):
    authority = RepositoryAuthority(synthetic_authority[0])
    for path in ("../secret", "/tmp/secret", "docs/thesis/private.txt"):
        with pytest.raises(EligibilityError):
            authority.raw_bytes(path)
    path = synthetic_authority[0] / "docs/experiments/reference_approval/phase62_closure.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(EligibilityError, match="artifact_worktree_mismatch"):
        _validate_fixture(synthetic_authority)


def _commit_change(root, path, *, remove=False):
    target = root / path
    if remove:
        target.unlink()
    else:
        target.write_bytes(target.read_bytes() + b" ")
    _git(root, "add", "-A", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic adversarial mutation")


@pytest.mark.parametrize("target", (
    "docs/experiments/datasets/v1/manifest.json",
    "docs/experiments/queries/v1/queries.jsonl",
    "docs/experiments/ground_truth/v1/ground_truth.jsonl",
    "docs/experiments/Experiment_Protocol_Addendum_D_V3_1_0.md",
    "docs/experiments/reference/synthetic-reference-v1.jsonl",
    "docs/experiments/audits/synthetic-chinese_coverage_audit-output.txt",
    "docs/experiments/audits/synthetic-methodology_review-output.txt",
    "docs/experiments/audits/synthetic-final_data_qa-output.txt",
    "docs/experiments/audits/synthetic-decision.json",
    "docs/experiments/audits/synthetic-dry-run-artifact-set.json",
    "docs/experiments/reference_approval/phase62_closure.json",
))
def test_committed_authority_or_raw_evidence_mutation_fails_closed(synthetic_authority, target):
    root = synthetic_authority[0]
    _commit_change(root, target)
    with pytest.raises(EligibilityError):
        _validate_fixture(synthetic_authority)


def test_audit_raw_bytes_and_prepared_separation(synthetic_authority):
    root = synthetic_authority[0]
    authority = RepositoryAuthority(root)
    path = "docs/experiments/evidence_audit/executions/synthetic-et-bl-ja-01/record.json"
    audit = authority.load_typed(path, EvidenceAuditRecord)
    assert authority.load_audit(path, audit.identity_hash).identity_hash == audit.identity_hash
    assert audit.sent_input.raw_sha256 == audit.prepared_input_hash
    assert audit.exact_revision.status == "unavailable"
    assert audit.user_provided_alias.value == "DeepSeek-V4.1-Flash"
    assert audit.observed_ui_name == "DeepSeek-V4-Flash"
    _commit_change(root, audit.raw_reply.artifact_path)
    with pytest.raises(EligibilityError, match="audit_raw_hash_mismatch"):
        RepositoryAuthority(root).load_audit(path, audit.identity_hash)


def test_response_contract_failure_is_execution_outcome_not_model_review(synthetic_authority):
    root = synthetic_authority[0]
    path = "docs/experiments/evidence_audit/executions/synthetic-et-bl-ja-01/record.json"
    original = RepositoryAuthority(root).load_typed(path, EvidenceAuditRecord)
    valid_raw = RepositoryAuthority(root).raw_bytes(original.raw_reply.artifact_path)
    raw = b'{"query_id":"et-bl-ja-01","evidence_reviews":['
    reply = _capture(root, original.raw_reply.artifact_path, raw)
    transcription = _capture(root, original.transcription_capture.artifact_path,
                             canonical_json({"model_verdict": "unavailable",
                                             "execution_outcome": "CANNOT_ASSESS",
                                             "failure_reason": "response_contract_failure"}).encode())
    failure = replace(original, schema_version="v2", raw_reply=reply,
                      visible_final=VisiblePart(original.visible_final.availability, reply),
                      evidence_reviews=(), transcription_hash=transcription.raw_sha256,
                      transcription_capture=transcription, overall_verdict="CANNOT_ASSESS",
                      model_verdict="unavailable", execution_outcome="CANNOT_ASSESS",
                      failure_reason="response_contract_failure")
    assert failure.evidence_reviews == ()
    assert EvidenceAuditRecord.from_record(failure.to_record()) == failure
    assert original.to_record().get("model_verdict") is None
    assert EvidenceAuditRecord.from_record(original.to_record()).identity_hash == original.identity_hash
    for changes in ({"model_verdict": "SUPPORTS"}, {"evidence_reviews": original.evidence_reviews},
                    {"execution_outcome": "SUPPORTS"}, {"failure_reason": None}):
        with pytest.raises(ValueError, match="v2 response failure"):
            replace(failure, **changes)
    _json(root, path, failure.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic response failure")
    authority = RepositoryAuthority(root)
    assert authority.load_audit(path, failure.identity_hash).identity_hash == failure.identity_hash
    assert authority.raw_checksum(reply.artifact_path) == raw_sha256(raw)
    _write(root, reply.artifact_path, canonical_json({"query_id": "et-bl-ja-01"}).encode())
    with pytest.raises(EligibilityError, match="artifact_worktree_mismatch"):
        RepositoryAuthority(root).load_audit(path, failure.identity_hash)
    valid_reply = original.raw_reply
    _write(root, valid_reply.artifact_path, valid_raw)
    parseable = replace(failure, raw_reply=RawCapture(valid_reply.artifact_path,
                                                      raw_sha256((root / valid_reply.artifact_path).read_bytes())),
                        visible_final=VisiblePart(failure.visible_final.availability,
                                                  RawCapture(valid_reply.artifact_path,
                                                             raw_sha256((root / valid_reply.artifact_path).read_bytes()))))
    _json(root, path, parseable.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic parseable failure claim")
    with pytest.raises(EligibilityError, match="audit_failure_response_is_valid"):
        RepositoryAuthority(root).load_audit(path, parseable.identity_hash)


def test_audit_contract_rejects_overall_alias_and_retry_errors(synthetic_authority):
    root = synthetic_authority[0]
    authority = RepositoryAuthority(root)
    path = "docs/experiments/evidence_audit/executions/synthetic-et-bl-ja-01/record.json"
    audit = authority.load_typed(path, EvidenceAuditRecord)
    with pytest.raises(ValueError, match="overall verdict"):
        replace(audit, evidence_reviews=(replace(audit.evidence_reviews[0], verdict="QUESTIONS"),))
    with pytest.raises(ValueError, match="alias"):
        replace(audit, alias_source=Availability("unavailable", None, "no mapping"))
    with pytest.raises(ValueError, match="retry"):
        replace(audit, attempt_number=2)
    retry = replace(audit, attempt_number=2, supersedes_attempt=1)
    assert retry.identity_hash != audit.identity_hash
    with pytest.raises(ValueError, match="duplicate"):
        replace(audit, evidence_reviews=audit.evidence_reviews + audit.evidence_reviews[:1])
    with pytest.raises(ValueError, match="transcription"):
        replace(audit, transcription_hash="0" * 64)
    with pytest.raises(ValueError):
        EvidenceAuditRecord.from_record({**audit.to_record(), "unknown": 1})
    with pytest.raises(ValueError):
        replace(audit, attempt_number=True)
    assert replace(audit, started_at="2026-02-01T00:00:00.100000+00:00").identity_hash == audit.identity_hash
    assert replace(audit, independent_session_evidence=replace(audit.independent_session_evidence,
                                                                raw_sha256="0" * 64)).identity_hash != audit.identity_hash
    assert replace(audit, evidence_reviews=(replace(audit.evidence_reviews[0], grade_observation="synthetic grade note"),)
                   + audit.evidence_reviews[1:]).identity_hash != audit.identity_hash


def _external_test_case():
    query_id = "et-dq-ja-01"
    prepared = json.loads((ROOT / "docs/experiments/evidence_audit/prepared/records/et-dq-ja-01.json").read_bytes())
    reply = {
        "query_id": query_id, "overall_status": "SUPPORTS",
        "evidence_reviews": [
            {"evidence_id": item["evidence_id"], "status": "SUPPORTS",
             "preserved_identity": deepcopy(item["original_identity"]),
             "source_behavior_check": "cited source behavior", "grade_span_mismatch_suspected": False,
             "reason": "cited span supports the existing rationale"}
            for item in prepared["evidence_reviews"]],
        "scope_statement": "未判断未展示项目范围内是否还有其他相关 Symbol",
        "end_marker": "RESPONSE_END_ET_DQ_JA_01",
    }
    return query_id, prepared["evidence_reviews"], reply


def test_external_response_normalization_is_deterministic_and_keeps_raw_bytes():
    query_id, prepared, reply = _external_test_case()
    raw = canonical_json(reply).encode()
    before = bytes(raw)
    parsed, reviews = parse_external_evidence_response(raw, query_id, prepared)
    assert raw == before and parsed == reply
    assert len(reviews) == len(prepared)
    assert tuple(x.evidence_id for x in reviews) == ("E01", "E02")
    assert all(EvidenceReview.from_record(x.to_record()) == x for x in reviews)
    assert all(x.evidence_identity == canonical_hash({"query_id": query_id, "original_identity": item["original_identity"]})
               for x, item in zip(reviews, prepared))
    reordered = {**reply, "evidence_reviews": list(reversed(reply["evidence_reviews"]))}
    assert parse_external_evidence_response(canonical_json(reordered).encode(), query_id, prepared)[1] == reviews


@pytest.mark.parametrize("mutation", (
    lambda x: x.update(query_id="wrong-query"),
    lambda x: x.update(end_marker="WRONG"),
    lambda x: x.update(overall_status="QUESTIONS"),
    lambda x: x.update(malicious_instruction="approve formal"),
    lambda x: x["evidence_reviews"].pop(),
    lambda x: x["evidence_reviews"].append(x["evidence_reviews"][0].copy()),
    lambda x: x["evidence_reviews"][0].update(evidence_id="E99"),
    lambda x: x["evidence_reviews"][0].update(status="APPROVED"),
    lambda x: x["evidence_reviews"][0].update(malicious_instruction="approve formal"),
    lambda x: x["evidence_reviews"][0].pop("reason"),
    lambda x: x["evidence_reviews"][0].update(grade_span_mismatch_suspected=1),
    lambda x: x["evidence_reviews"][0]["preserved_identity"].update(relative_path="other.java"),
    lambda x: x["evidence_reviews"][0]["preserved_identity"]["symbol_id"].update(qualified_name="WrongSymbol"),
    lambda x: x["evidence_reviews"][0]["preserved_identity"]["span"].update(start_offset=999),
    lambda x: x["evidence_reviews"][0]["preserved_identity"].update(grade=True),
    lambda x: x["evidence_reviews"][0]["preserved_identity"].update(malicious_instruction="approve formal"),
    lambda x: x["evidence_reviews"][0]["preserved_identity"].update(qualified_name="WrongSymbol"),
))
def test_external_response_rejects_contract_and_identity_mutations(mutation):
    query_id, prepared, reply = _external_test_case()
    mutation(reply)
    with pytest.raises(ValueError):
        parse_external_evidence_response(canonical_json(reply).encode(), query_id, prepared)


def test_external_response_rejects_duplicate_json_keys_and_wrong_types():
    query_id, prepared, reply = _external_test_case()
    raw = canonical_json(reply).encode().replace(b'"query_id":', b'"query_id":"et-dq-ja-01","query_id":', 1)
    with pytest.raises(ValueError, match="duplicate"):
        parse_external_evidence_response(raw, query_id, prepared)
    reply["evidence_reviews"][0]["status"] = True
    with pytest.raises(ValueError):
        parse_external_evidence_response(canonical_json(reply).encode(), query_id, prepared)


def test_shared_session_and_incomplete_set_fail(synthetic_authority):
    from experiments.eligibility import _validate_independent_sessions
    authority = RepositoryAuthority(synthetic_authority[0])
    a = authority.load_typed("docs/experiments/evidence_audit/executions/synthetic-et-bl-ja-01/record.json", EvidenceAuditRecord)
    b = authority.load_typed("docs/experiments/evidence_audit/executions/synthetic-et-bl-ja-02/record.json", EvidenceAuditRecord)
    with pytest.raises(EligibilityError, match="audit_session_not_independent"):
        _validate_independent_sessions((a, replace(b, independent_session_evidence=a.independent_session_evidence)))
    audit_set = authority.load_typed("docs/experiments/audits/synthetic-java-set.json", EvidenceAuditSet)
    with pytest.raises(ValueError, match="12 attempts"):
        replace(audit_set, accepted_attempt_identities=audit_set.accepted_attempt_identities[:-1],
                accepted_attempt_paths=audit_set.accepted_attempt_paths[:-1])
    with pytest.raises(ValueError, match="path cannot be reused"):
        replace(audit_set, accepted_attempt_paths=audit_set.accepted_attempt_paths[:-1] +
                ((audit_set.accepted_attempt_paths[-1][0], audit_set.accepted_attempt_paths[0][1]),))


def test_approval_status_pending_and_blocked_cannot_be_selected(synthetic_authority):
    from experiments.eligibility import validate_current_gate
    root = synthetic_authority[0]
    authority = RepositoryAuthority(root)
    old = synthetic_authority[2]
    approved = authority.load_typed(f"docs/experiments/reference_approval/{old}.json", ReferenceApprovalRecord)
    gate = authority.load_current_gate()
    for status in ("pending", "blocked"):
        candidate = replace(approved, approval_status=status, approved_at=None)
        path = f"docs/experiments/reference_approval/{candidate.identity_hash}.json"
        _json(root, path, candidate.to_record())
        _git(root, "add", "docs/experiments")
        _git(root, "commit", "-qm", "synthetic non-approved decision")
        with pytest.raises(EligibilityError, match="current_gate_conflict"):
            validate_current_gate(RepositoryAuthority(root), replace(gate, selected_reference_approval_identity=candidate.identity_hash))


def test_valid_approval_still_needs_closure_and_formal_receipt(synthetic_authority):
    root, config, approval, receipt, runtime, commit = synthetic_authority
    (root / "docs/experiments/reference_approval/phase62_closure.json").unlink()
    _git(root, "add", "-A", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic missing closure")
    with pytest.raises(EligibilityError):
        _validate_fixture(synthetic_authority)


def test_config_runtime_code_and_purpose_mismatch_rejected(synthetic_authority):
    root, config, approval, receipt, runtime, commit = synthetic_authority
    with pytest.raises(EligibilityError, match="config_identity_mismatch"):
        validate_formal_eligibility(purpose=RunKind.FORMAL, repository_root=root,
                                    requested_config=replace(config, approved_reference_identity="0" * 64),
                                    selected_reference_approval=approval, runtime_evidence=runtime,
                                    code_commit=commit, dry_run_receipt=receipt)
    with pytest.raises(EligibilityError, match="runtime_contract_mismatch"):
        validate_formal_eligibility(purpose=RunKind.FORMAL, repository_root=root,
                                    requested_config=config, selected_reference_approval=approval,
                                    runtime_evidence=replace(runtime, network_disabled=False),
                                    code_commit=commit, dry_run_receipt=receipt)
    with pytest.raises(EligibilityError, match="frozen_commit_unavailable"):
        validate_formal_eligibility(purpose=RunKind.FORMAL, repository_root=root,
                                    requested_config=config, selected_reference_approval=approval,
                                    runtime_evidence=runtime, code_commit="0" * 40,
                                    dry_run_receipt=receipt)
    with pytest.raises(EligibilityError):
        validate_formal_eligibility(purpose=RunKind.SYNTHETIC, repository_root=root,
                                    requested_config=config, selected_reference_approval=approval,
                                    runtime_evidence=runtime, code_commit=commit, dry_run_receipt=receipt)


def test_untracked_experiment_code_cannot_claim_a_committed_code_identity(synthetic_authority):
    root = synthetic_authority[0]
    _write(root, "experiments/synthetic-untracked.py", b"synthetic code mutation\n")
    with pytest.raises(EligibilityError, match="execution_code_mismatch"):
        _validate_fixture(synthetic_authority)


def test_approval_time_must_follow_completed_prerequisites(synthetic_authority):
    root, _, approval_hash, _, _, _ = synthetic_authority
    path = f"docs/experiments/reference_approval/{approval_hash}.json"
    authority = RepositoryAuthority(root)
    approval = authority.load_typed(path, ReferenceApprovalRecord)
    earlier = replace(approval, approved_at="2026-02-01T00:00:00+00:00")
    assert earlier.identity_hash == approval_hash
    _json(root, path, earlier.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic early approval")
    with pytest.raises(EligibilityError, match="approval_precedes_prerequisite"):
        _validate_fixture(synthetic_authority)


def test_frozen_data_and_prepared_packages_remain_historical():
    drafts = load_ground_truth(ROOT / "docs/experiments/ground_truth/v1/ground_truth.jsonl")
    queries = load_queries(ROOT / "docs/experiments/queries/v1/queries.jsonl")
    assert len(drafts) == len(queries) == 72
    assert {x.annotation_status for x in drafts} == {"drafted"}
    assert sum(len(x.evidence) for x in drafts) == 134
    prepared = json.loads((ROOT / "docs/experiments/evidence_audit/prepared/manifest.json").read_text())
    assert len(prepared["entries"]) == 12
    assert all(json.loads((ROOT / "docs/experiments/evidence_audit/prepared/records" / (x["query_id"] + ".json")).read_text())["execution_status"] == "NOT_EXECUTED" for x in prepared["entries"])
    authority = RepositoryAuthority(ROOT)
    closure = authority.load_typed("docs/experiments/reference_approval/phase62_closure.json", Phase62ClosureRecord)
    approval = authority.load_typed(f"docs/experiments/reference_approval/{closure.approved_reference_identity}.json", ReferenceApprovalRecord, closure.approved_reference_identity)
    assert approval.source_draft_identity.hash == canonical_hash([x.to_record() for x in sorted(drafts, key=lambda x: x.query_id)])
    assert {x.hash for x in approval.resolution_identities} == {
        "1680c6463324907a8f39e11f8a1e5b52ff79a79c71ea628078eeed9d89b8bc37",
        "ac39e3072674ef7740eb53a194c8b2cc00bca3edf73ce8529ed25344faa26b1d",
    }
    assert not authority.load_current_gate().formal_execution_eligible


def test_chinese_review_must_bind_methodology_review(synthetic_authority):
    root, request = _open_readiness_fixture(synthetic_authority)
    ref = next(x for x in request.prerequisite_identities if x.role == "chinese_coverage_audit")
    review = RepositoryAuthority(root).load_typed(ref.artifact_path, ApprovalPrerequisiteRecord)
    review = replace(review, input_identities=tuple(
        (role, "0" * 64 if role == "methodology_review" else digest)
        for role, digest in review.input_identities))
    _json(root, ref.artifact_path, review.to_record())
    _git(root, "add", "docs/experiments")
    _git(root, "commit", "-qm", "synthetic wrong methodology binding")
    request = replace(request, prerequisite_identities=tuple(
        replace(x, identity=review.identity_hash) if x.role == ref.role else x
        for x in request.prerequisite_identities))
    with pytest.raises(EligibilityError, match="chinese_methodology_binding_mismatch"):
        validate_reference_approval_readiness(repository_root=root, request=request)


@pytest.mark.parametrize("target", ("approval", "decision", "closure", "documentation"))
def test_final_eligibility_still_requires_every_downstream_artifact(synthetic_authority, target):
    root, _, identity, _, _, _ = synthetic_authority
    paths = {
        "approval": f"docs/experiments/reference_approval/{identity}.json",
        "decision": "docs/experiments/audits/synthetic-decision.json",
        "closure": "docs/experiments/reference_approval/phase62_closure.json",
        "documentation": "docs/experiments/audits/synthetic-documentation-decision.json",
    }
    _commit_change(root, paths[target], remove=True)
    with pytest.raises(EligibilityError, match="artifact_missing"):
        _validate_fixture(synthetic_authority)


def test_java_evidence_batch_reloads_from_disk_without_changing_draft_truth():
    execution_root = ROOT / "docs/experiments/evidence_audit/executions"
    reference_path = ROOT / "docs/experiments/reference/v3.1-phase6-spec-anchor-reference-v1.jsonl"
    reference_bytes = reference_path.read_bytes()
    assert reference_path.with_name(reference_path.name + ".sha256").read_text().strip() == raw_sha256(reference_bytes)
    references = [ReferenceRecord.from_record(json.loads(line)) for line in reference_bytes.splitlines()]
    assert len(references) == 72
    reference_identity = canonical_hash([item.identity_record() for item in references])
    expected_ids = {
        "et-bl-ja-01", "et-bl-ja-02", "et-cf-ja-01", "et-cf-ja-02", "et-dq-ja-01", "et-dq-ja-02",
        "et-fl-ja-01", "et-fl-ja-02", "et-mt-ja-01", "et-mt-ja-02", "et-sl-ja-01", "et-sl-ja-02",
    }
    directories = sorted(path for path in execution_root.iterdir() if path.is_dir())
    assert len(directories) == len(expected_ids) == 12
    seen = set()
    structured_count = 0
    failure_count = 0
    failure_hashes = {
        "et-bl-ja-01": "c7cbc3d12b8b4f85aeb862570972605d3afa3d2081dcff137f9e2155d7c2cd56",
        "et-fl-ja-02": "e48cbf81c06e418e24ded5f344cb8937e7afce08fc5ece1daa47e466b1730e01",
    }
    for directory in directories:
        checksums = {}
        for line in (directory / "checksums.sha256").read_text().splitlines():
            digest, name = line.split("  ", 1)
            checksums[name] = digest
        assert checksums == {path.name: raw_sha256(path.read_bytes()) for path in directory.iterdir() if path.name != "checksums.sha256"}
        record_bytes = (directory / "record.json").read_bytes()
        assert (directory / "record.json.sha256").read_text().strip() == raw_sha256(record_bytes)
        audit = EvidenceAuditRecord.from_record(json.loads(record_bytes))
        assert directory.name == audit.identity_hash
        assert audit.query_id in expected_ids - seen
        seen.add(audit.query_id)
        assert audit.reference_identity == reference_identity
        assert audit.attempt_number in {1, 2, 3, 4}
        assert audit.supersedes_attempt == (audit.attempt_number - 1 if audit.attempt_number > 1 else None)
        assert audit.raw_reply.raw_sha256 == raw_sha256((directory / "raw-reply.txt").read_bytes())
        assert audit.visible_final.capture == audit.raw_reply
        assert audit.visible_thinking.availability.status == "unavailable"
        prepared = json.loads((ROOT / "docs/experiments/evidence_audit/prepared/records" / (audit.query_id + ".json")).read_bytes())
        assert audit.prepared_input_hash == raw_sha256((directory / "sent-input.txt").read_bytes()) == prepared["input_sha256"]
        if audit.schema_version == "v2":
            failure_count += 1
            assert audit.query_id in {"et-bl-ja-01", "et-fl-ja-02"}
            assert audit.model_verdict == "unavailable"
            assert audit.execution_outcome == audit.overall_verdict == "CANNOT_ASSESS"
            assert audit.failure_reason == "response_contract_failure"
            assert audit.evidence_reviews == ()
            assert audit.raw_reply.raw_sha256 == failure_hashes[audit.query_id]
            with pytest.raises(ValueError):
                parse_external_evidence_response((directory / "raw-reply.txt").read_bytes(), audit.query_id, prepared["evidence_reviews"])
        else:
            structured_count += 1
            parsed, normalized = parse_external_evidence_response((directory / "raw-reply.txt").read_bytes(), audit.query_id, prepared["evidence_reviews"])
            assert parsed == json.loads((directory / "external-parsed-response.json").read_bytes())
            assert [item.to_record() for item in normalized] == json.loads((directory / "normalized-reviews.json").read_bytes())
            assert audit.evidence_reviews == normalized
            assert audit.overall_verdict == parsed["overall_status"] == "SUPPORTS"
        assert audit.transcription_hash == raw_sha256((directory / "transcription.json").read_bytes())
        history = json.loads((directory / "failed-attempts.json").read_bytes())
        if audit.schema_version == "v2":
            assert history["materialized_attempt_number"] == 4
            previous = history["prior_capture_attempts"]
        else:
            assert history["accepted_attempt_number"] == audit.attempt_number
            previous = history["other_capture_attempts"]
        assert {item["attempt_number"] for item in previous} >= set(range(1, audit.attempt_number))
        assert all(item["formal_audit_created"] is False for item in previous)
    assert seen == expected_ids
    assert structured_count == 10
    assert failure_count == 2
