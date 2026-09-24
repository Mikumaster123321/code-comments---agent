"""Offline synthetic lifecycle evidence; no formal repository artifact is created."""
from __future__ import annotations

import json
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
    CurrentGateIndex, DatasetManifest, DryRunReceipt, EligibilityError, ErratumRecord,
    EvidenceAuditRecord, EvidenceAuditSet, EvidenceRecord, EvidenceReview, FormalGateEvidence,
    GroundTruthRecord, IdentityRef, Phase62ClosureRecord, Phase62DocumentationDecisionRecord,
    Population, PrerequisiteReference,
    RawCapture, ReferenceApprovalRecord, ReferenceRecord, RepositoryAuthority, ResolutionRecord,
    RetrievalUnit, RunKind, RuntimeMetadata, Strategy, VisiblePart, canonical_hash, canonical_json,
    derive_reference, load_ground_truth, load_queries, raw_sha256,
    validate_formal_eligibility, write_lifecycle_artifact,
)
from experiments.reference import REFERENCE_METHOD
from experiments.eligibility import validate_current_gate
from experiments.serialization import canonical_jsonl

ROOT = Path(__file__).parents[1]
D = "a" * 64


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
    legacy = RepositoryAuthority(ROOT).load_current_gate()
    assert legacy.schema_version == "v1"
    assert legacy.current_phase == "6.2B.1"
    assert legacy.phase_status == "IMPLEMENTED / QA PENDING"
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
        reviews = tuple(EvidenceReview(
            item["evidence_id"], canonical_hash({"query_id": query_id, "original_identity": item["original_identity"]}),
            "SUPPORTS", ("synthetic source:1",), "synthetic support", None,
        ) for item in prepared_record["evidence_reviews"])
        reply_record = {"query_id": query_id, "overall_status": "SUPPORTS",
                        "evidence_reviews": [x.to_record() for x in reviews],
                        "scope_statement": "synthetic cited source only",
                        "end_marker": "RESPONSE_END_" + query_id.upper().replace("-", "_")}
        reply = _capture(root, base + "/reply.txt", canonical_json(reply_record).encode())
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
    for role in ("chinese_coverage_audit", "methodology_review", "final_data_qa"):
        base = "docs/experiments/audits/synthetic-" + role
        output = _capture(root, base + "-output.txt", ("synthetic output " + role).encode())
        provenance = _capture(root, base + "-provenance.txt", ("synthetic provenance " + role).encode())
        inputs = (("reference", reference_hash),)
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
    result_path = "docs/experiments/audits/synthetic-dry-run-result.json"
    result_checksum = _write(root, result_path, b'{"synthetic_result":"pass"}\n')
    receipt = DryRunReceipt("v1", "pass", approval.identity_hash, dataset.dataset_hash, query_hash,
                            reference_hash, config.experiment_family_identity, runtime_identity, code_commit, D,
                            "synthetic-dry-run-v1", "english_dev", None, result_path)
    receipt = replace(receipt, result_checksum=result_checksum)
    receipt_path = "docs/experiments/audits/synthetic-dry-run-receipt.json"
    _json(root, receipt_path, receipt.to_record())
    gate = CurrentGateIndex("v1", "6.2B.1", "CLOSED", "CLOSED", approval.identity_hash,
                            True, True, (), "synthetic formal validation",
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
    "docs/experiments/audits/synthetic-dry-run-result.json",
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
    assert not (ROOT / "docs/experiments/evidence_audit/executions").exists()
    assert not (ROOT / "docs/experiments/reference_approval").exists()
