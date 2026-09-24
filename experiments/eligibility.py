"""Repository-backed Addendum D authority and the single execution eligibility gate."""
from __future__ import annotations

import json
import subprocess
import weakref
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .config import BenchmarkConfig, Population, RunKind, SemanticMode
from .reference import (
    ApprovalDecisionRecord, ApprovalPrerequisiteRecord, DryRunReceipt,
    EvidenceAuditRecord, EvidenceAuditSet, Phase62ClosureRecord,
    Phase62DocumentationDecisionRecord,
    PrerequisiteReference, ReferenceApprovalRecord, ReferenceRecord,
    REQUIRED_ROLES, ResolutionRecord, raw_sha256,
)
from .schemas import (
    DatasetManifest, GroundTruthRecord, QueryRecord, dataset_manifest_from_record,
    RuntimeMetadata, ground_truth_from_record, query_from_record, SchemaValidationError, _exact, _timestamp,
)
from .serialization import canonical_hash, normalize_relative_path


class EligibilityError(ValueError):
    """A stable, non-sensitive formal gate failure."""


PREREGISTERED_JAVA_IDS = tuple(sorted(
    f"et-{task}-ja-{index:02d}"
    for task in ("bl", "cf", "dq", "fl", "mt", "sl")
    for index in (1, 2)
))
METHOD_DOCUMENTS = (
    ("protocol", "Experiment_Protocol_V3_1_0.md", "v3.1-phase6-protocol-v1"),
    ("addendum_a", "Experiment_Protocol_Addendum_A_V3_1_0.md", "v1"),
    ("addendum_b", "Experiment_Protocol_Addendum_B_V3_1_0.md", "v1"),
    ("addendum_c", "Experiment_Protocol_Addendum_C_V3_1_0.md", "v1"),
    ("addendum_d", "Experiment_Protocol_Addendum_D_V3_1_0.md", "v1"),
    ("dataset_specification", "Dataset_Query_GroundTruth_Specification_V3_1_0.md", "v1"),
)
ENGINEERING_DOCUMENT = "docs/experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md"
ENGINEERING_SHA256 = "6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045"

# Frozen Engineering Specification v1 Phase 6.2B navigation lifecycle.
_CURRENT_GATE_PHASE_STATUSES = MappingProxyType({
    "6.2B.0": frozenset({"COMPLETED"}),
    "6.2B.1": frozenset({
        "ALLOWED BUT NOT STARTED", "IMPLEMENTATION IN PROGRESS",
        "IMPLEMENTED / QA PENDING", "QA PASS / DOCUMENTATION GATE PENDING",
        "COMPLETED", "CLOSED",  # CLOSED preserves the original v1 record contract.
    }),
    **{f"6.2B.{stage}": frozenset({"ALLOWED BUT NOT STARTED", "IN PROGRESS", "BLOCKED", "COMPLETED"})
       for stage in range(2, 7)},
})


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EligibilityError(code)


@dataclass(frozen=True)
class CurrentGateIndex:
    schema_version: str
    current_phase: str
    current_gate: str
    phase_status: str
    selected_reference_approval_identity: str | None
    dry_run_eligible: bool
    formal_execution_eligible: bool
    blockers: tuple[str, ...]
    next_allowed_action: str
    authoritative_documents: tuple[str, ...]
    updated_by_commit: str

    def __post_init__(self) -> None:
        if type(self.schema_version) is not str or self.schema_version != "v1" or type(self.current_phase) is not str or self.current_phase not in _CURRENT_GATE_PHASE_STATUSES:
            raise SchemaValidationError("current gate schema/phase is invalid")
        # current_gate is the overall Phase 6.2 gate; phase_status describes only the current subphase.
        if type(self.current_gate) is not str or self.current_gate not in {"OPEN", "CLOSED"} or type(self.phase_status) is not str or self.phase_status not in _CURRENT_GATE_PHASE_STATUSES[self.current_phase]:
            raise SchemaValidationError("current gate state is invalid")
        if self.selected_reference_approval_identity is not None:
            from .schemas import _sha256
            _sha256("selected approval", self.selected_reference_approval_identity)
        if type(self.dry_run_eligible) is not bool or type(self.formal_execution_eligible) is not bool:
            raise SchemaValidationError("eligibility display values must be bool")
        if type(self.blockers) is not tuple or not all(type(x) is str and x for x in self.blockers):
            raise SchemaValidationError("blockers must be immutable strings")
        if type(self.authoritative_documents) is not tuple or not self.authoritative_documents:
            raise SchemaValidationError("authoritative documents must be immutable non-empty tuple")
        for path in self.authoritative_documents: normalize_relative_path(path)
        if type(self.next_allowed_action) is not str or not self.next_allowed_action:
            raise SchemaValidationError("next action is required")
        if type(self.updated_by_commit) is not str or len(self.updated_by_commit) != 40 or any(c not in "0123456789abcdef" for c in self.updated_by_commit):
            raise SchemaValidationError("updated_by_commit must be a Git SHA-1")
        if self.current_gate == "OPEN" and (self.dry_run_eligible or self.formal_execution_eligible or self.selected_reference_approval_identity is not None):
            raise SchemaValidationError("open gate cannot advertise approval or eligibility")
        canonical_hash(self.to_record())

    def to_record(self) -> dict:
        return {"schema_version": self.schema_version, "current_phase": self.current_phase,
                "current_gate": self.current_gate, "phase_status": self.phase_status,
                "selected_reference_approval_identity": self.selected_reference_approval_identity,
                "dry_run_eligible": self.dry_run_eligible, "formal_execution_eligible": self.formal_execution_eligible,
                "blockers": list(self.blockers), "next_allowed_action": self.next_allowed_action,
                "authoritative_documents": list(self.authoritative_documents), "updated_by_commit": self.updated_by_commit}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> CurrentGateIndex:
        _exact(value, set(cls.__dataclass_fields__), "CurrentGateIndex")
        if type(value["blockers"]) is not list or type(value["authoritative_documents"]) is not list:
            raise SchemaValidationError("current gate arrays must be lists")
        return cls(**{**value, "blockers": tuple(value["blockers"]),
                      "authoritative_documents": tuple(value["authoritative_documents"])})


class RepositoryAuthority:
    """Read committed Git bytes, then recompute every referenced content identity."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        if not (self.root / ".git").exists():
            raise EligibilityError("repository_not_found")

    def raw_bytes(self, relative_path: str) -> bytes:
        try:
            normalized = normalize_relative_path(relative_path)
        except (ValueError, TypeError) as error:
            raise EligibilityError("unsafe_artifact_path") from None
        _require(normalized.startswith("docs/experiments/") and not normalized.startswith("docs/thesis/"), "artifact_outside_authority")
        target = self.root
        for component in normalized.split("/"):
            target = target / component
            _require(not target.is_symlink(), "artifact_symlink_forbidden")
        _require(target.is_file() and target.resolve().is_relative_to(self.root), "artifact_missing")
        try:
            result = subprocess.run(["git", "-C", str(self.root), "show", f"HEAD:{normalized}"],
                                    capture_output=True, check=False)
        except OSError:
            raise EligibilityError("git_authority_unavailable") from None
        _require(result.returncode == 0, "artifact_not_committed")
        content = target.read_bytes()
        _require(content == result.stdout, "artifact_worktree_mismatch")
        return content

    def raw_checksum(self, relative_path: str) -> str:
        return raw_sha256(self.raw_bytes(relative_path))

    def verify_artifact_checksum(self, path: str) -> None:
        try:
            expected = self.raw_bytes(path + ".sha256").decode("ascii").strip()
        except UnicodeError:
            raise EligibilityError("artifact_checksum_invalid") from None
        _require(len(expected) == 64 and all(c in "0123456789abcdef" for c in expected), "artifact_checksum_invalid")
        _require(self.raw_checksum(path) == expected, "artifact_checksum_mismatch")

    def verify_commit(self, commit: str) -> None:
        _require(type(commit) is str and len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), "commit_identity_invalid")
        result = subprocess.run(["git", "-C", str(self.root), "cat-file", "-e", f"{commit}^{{commit}}"],
                                capture_output=True, check=False)
        _require(result.returncode == 0, "frozen_commit_unavailable")

    def verify_execution_code(self, commit: str) -> None:
        """A declared code commit must match the tracked experiments code in use."""
        self.verify_commit(commit)
        for args in (("diff", "--quiet", "HEAD", "--", "experiments"),
                     ("diff", "--quiet", commit, "HEAD", "--", "experiments")):
            result = subprocess.run(["git", "-C", str(self.root), *args],
                                    capture_output=True, check=False)
            _require(result.returncode == 0, "execution_code_mismatch")
        untracked = subprocess.run(["git", "-C", str(self.root), "ls-files", "--others",
                                    "--exclude-standard", "--", "experiments"],
                                   capture_output=True, check=False)
        _require(untracked.returncode == 0 and not untracked.stdout, "execution_code_mismatch")

    def json_record(self, relative_path: str) -> Mapping[str, Any]:
        try:
            value = json.loads(self.raw_bytes(relative_path))
        except (UnicodeError, json.JSONDecodeError):
            raise EligibilityError("artifact_json_invalid") from None
        _require(type(value) is dict, "artifact_schema_invalid")
        return value

    def load_typed(self, path: str, kind: type, expected_identity: str | None = None):
        self.verify_artifact_checksum(path)
        try:
            record = kind.from_record(self.json_record(path))
        except EligibilityError:
            raise
        except (ValueError, TypeError, KeyError):
            raise EligibilityError("artifact_schema_invalid") from None
        if expected_identity is not None:
            _require(record.identity_hash == expected_identity, "artifact_identity_mismatch")
        return record

    def load_reference_collection(self, path: str, expected_hash: str) -> tuple[ReferenceRecord, ...]:
        self.verify_artifact_checksum(path)
        try:
            lines = self.raw_bytes(path).decode("utf-8").splitlines()
            _require(bool(lines) and all(line.strip() for line in lines), "reference_empty")
            records = tuple(ReferenceRecord.from_record(json.loads(line)) for line in lines)
        except EligibilityError:
            raise
        except (UnicodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
            raise EligibilityError("reference_schema_invalid") from None
        _require(len({x.query_id for x in records}) == len(records), "reference_duplicate_query")
        records = tuple(sorted(records, key=lambda x: x.query_id))
        _require(canonical_hash([x.identity_record() for x in records]) == expected_hash, "reference_identity_mismatch")
        return records

    def load_audit(self, path: str, expected_identity: str, prepared: Mapping[str, Any] | None = None) -> EvidenceAuditRecord:
        audit = self.load_typed(path, EvidenceAuditRecord, expected_identity)
        for capture in (audit.sent_input, audit.raw_reply, audit.independent_session_evidence, audit.context_boundary_evidence, audit.model_metadata_evidence, audit.transcription_capture):
            _require(self.raw_checksum(capture.artifact_path) == capture.raw_sha256, "audit_raw_hash_mismatch")
        _require("/executions/" in audit.sent_input.artifact_path and "/executions/" in audit.raw_reply.artifact_path,
                 "prepared_package_is_not_execution")
        for part in (audit.visible_thinking, audit.visible_final):
            if part.capture is not None:
                _require(self.raw_checksum(part.capture.artifact_path) == part.capture.raw_sha256, "audit_visible_hash_mismatch")
        platform_text = self.raw_bytes(audit.model_metadata_evidence.artifact_path).decode("utf-8", errors="replace")
        _require(audit.observed_ui_name in platform_text, "audit_model_display_unproven")
        for field in (audit.exact_revision, audit.token_usage, audit.finish_reason):
            if field.status == "available":
                _require(field.value in platform_text, "audit_model_metadata_unproven")
        _require(audit.sent_input.raw_sha256 == audit.prepared_input_hash, "audit_input_not_prepared")
        if prepared is not None:
            _require(audit.query_id == prepared["query_id"] and audit.prepared_input_hash == prepared["input_sha256"], "audit_prepared_identity_mismatch")
        if audit.reply_complete:
            _require(audit.visible_final.capture is not None, "audit_final_not_captured")
            try:
                final = json.loads(self.raw_bytes(audit.visible_final.capture.artifact_path))
            except (UnicodeError, json.JSONDecodeError):
                raise EligibilityError("audit_final_not_parseable") from None
            marker = "RESPONSE_END_" + audit.query_id.upper().replace("-", "_")
            _require(type(final) is dict and final.get("query_id") == audit.query_id and
                     final.get("end_marker") == marker and final.get("overall_status") == audit.overall_verdict,
                     "audit_final_completeness_mismatch")
            _require(final.get("evidence_reviews") == [item.to_record() for item in audit.evidence_reviews],
                     "audit_reply_reviews_mismatch")
            try:
                transcription = json.loads(self.raw_bytes(audit.transcription_capture.artifact_path))
            except (UnicodeError, json.JSONDecodeError):
                raise EligibilityError("audit_transcription_invalid") from None
            _require(transcription == [item.to_record() for item in audit.evidence_reviews],
                     "audit_transcription_mismatch")
        return audit

    def methodology_identity(self) -> str:
        documents = [{"role": role, "version": version,
                      "raw_sha256": self.raw_checksum("docs/experiments/" + name)}
                     for role, name, version in METHOD_DOCUMENTS]
        return canonical_hash({"schema_version": "v1", "documents": documents})

    def engineering_identity(self) -> str:
        checksum = self.raw_checksum(ENGINEERING_DOCUMENT)
        _require(checksum == ENGINEERING_SHA256, "engineering_specification_mismatch")
        return checksum

    def verify_frozen_checksums(self) -> None:
        lines = self.raw_bytes("docs/experiments/datasets/v1/checksums.sha256").decode("ascii").splitlines()
        _require(bool(lines), "frozen_checksums_missing")
        for line in lines:
            try:
                expected, path = line.split("  ", 1)
            except ValueError:
                raise EligibilityError("frozen_checksum_format_invalid") from None
            _require(self.raw_checksum(path) == expected, "frozen_artifact_checksum_mismatch")

    def load_current_gate(self) -> CurrentGateIndex:
        try:
            return CurrentGateIndex.from_record(self.json_record("docs/experiments/current_gate.json"))
        except EligibilityError:
            raise
        except (ValueError, TypeError, KeyError):
            raise EligibilityError("current_gate_invalid") from None

    def load_frozen_inputs(self) -> tuple[DatasetManifest, tuple[QueryRecord, ...], tuple[GroundTruthRecord, ...]]:
        base = "docs/experiments/"
        try:
            dataset = dataset_manifest_from_record(self.json_record(base + "datasets/v1/manifest.json"))
            queries = tuple(query_from_record(json.loads(line)) for line in self.raw_bytes(base + "queries/v1/queries.jsonl").decode().splitlines())
            draft = tuple(ground_truth_from_record(json.loads(line)) for line in self.raw_bytes(base + "ground_truth/v1/ground_truth.jsonl").decode().splitlines())
        except EligibilityError:
            raise
        except (ValueError, TypeError, KeyError, UnicodeError):
            raise EligibilityError("frozen_input_invalid") from None
        _require(len(queries) == 72 and len(draft) == 72 and all(x.annotation_status == "drafted" for x in draft), "draft_population_mismatch")
        return dataset, tuple(sorted(queries, key=lambda x: x.query_id)), tuple(sorted(draft, key=lambda x: x.query_id))


def validate_current_gate(authority: RepositoryAuthority, gate: CurrentGateIndex) -> None:
    """The index can veto inconsistent state but can never grant execution."""
    _require(type(gate) is CurrentGateIndex, "current_gate_invalid")
    if gate.selected_reference_approval_identity is None:
        _require(not gate.dry_run_eligible and not gate.formal_execution_eligible and gate.current_gate == "OPEN", "current_gate_conflict")
        return
    identity = gate.selected_reference_approval_identity
    path = f"docs/experiments/reference_approval/{identity}.json"
    approval = authority.load_typed(path, ReferenceApprovalRecord, identity)
    _require(approval.approval_status == "approved", "current_gate_conflict")
    _require(gate.current_gate == "CLOSED", "current_gate_conflict")
    # A selected approval alone still cannot authorize execution.


def _validate_independent_sessions(audits: tuple[EvidenceAuditRecord, ...]) -> None:
    session_hashes = [item.independent_session_evidence.raw_sha256 for item in audits]
    _require(len(session_hashes) == len(set(session_hashes)), "audit_session_not_independent")
    platform_ids = [item.platform_session_id.value for item in audits if item.platform_session_id.status == "available"]
    _require(len(platform_ids) == len(set(platform_ids)), "audit_platform_session_reused")


_ISSUED: weakref.WeakSet[ValidatedExecutionInputs] = weakref.WeakSet()


@dataclass(frozen=True, eq=False)
class ValidatedExecutionInputs:
    repository_root: Path
    purpose: RunKind
    dataset_identity: str
    query_identity: str
    reference_identity: str
    approval_identity: str
    methodology_identity: str
    engineering_identity: str
    config_identity: str
    code_commit: str
    runtime_identity: str
    runtime_evidence: RuntimeMetadata
    dry_run_receipt_path: str | None
    dataset: DatasetManifest
    queries: tuple[QueryRecord, ...]
    reference: tuple[ReferenceRecord, ...]

    def __post_init__(self) -> None:
        if self not in _ISSUED:
            raise EligibilityError("validated_inputs_must_be_issued")


def _issue(**fields) -> ValidatedExecutionInputs:
    # Construction stays module-private; runner also revalidates repository authority.
    instance = object.__new__(ValidatedExecutionInputs)
    _ISSUED.add(instance)
    try:
        instance.__init__(**fields)
    except Exception:
        _ISSUED.discard(instance)
        raise
    return instance


def is_validator_issued(value: object) -> bool:
    return type(value) is ValidatedExecutionInputs and value in _ISSUED


def validate_formal_eligibility(
    *, purpose: RunKind, repository_root: str | Path, requested_config: BenchmarkConfig,
    selected_reference_approval: str | None, runtime_evidence: RuntimeMetadata,
    code_commit: str, dry_run_receipt: str | None = None,
) -> ValidatedExecutionInputs:
    """Only this entry can issue DRY_RUN or FORMAL execution capability."""
    _require(type(purpose) is RunKind and purpose in {RunKind.DRY_RUN, RunKind.FORMAL}, "purpose_not_formal")
    _require(type(requested_config) is BenchmarkConfig, "config_invalid")
    authority = RepositoryAuthority(repository_root)
    authority.verify_frozen_checksums()
    authority.verify_commit("12391233daa2149ead4f451e920b2e0d8a1a6beb")
    gate = authority.load_current_gate()
    validate_current_gate(authority, gate)
    _require(gate.dry_run_eligible if purpose == RunKind.DRY_RUN else gate.formal_execution_eligible,
             "current_gate_conflict")
    _require(selected_reference_approval is not None and gate.selected_reference_approval_identity == selected_reference_approval, "approval_not_selected")
    approval = authority.load_typed(f"docs/experiments/reference_approval/{selected_reference_approval}.json", ReferenceApprovalRecord, selected_reference_approval)
    _require(approval.approval_status == "approved", "approval_not_approved")
    _require(approval.reference_method == "specification_anchored_with_limited_llm_evidence_audit", "approval_method_mismatch")
    dataset, queries, draft = authority.load_frozen_inputs()
    query_hash = canonical_hash([x.to_record() for x in queries])
    draft_hash = canonical_hash([x.to_record() for x in draft])
    _require(dataset.dataset_id == approval.dataset_id and dataset.version == approval.dataset_identity.version and dataset.dataset_hash == approval.dataset_identity.hash, "dataset_identity_mismatch")
    _require(len({x.query_set_version for x in queries}) == 1 and queries[0].query_set_version == approval.query_set_identity.version and query_hash == approval.query_set_identity.hash, "query_identity_mismatch")
    _require(len({x.ground_truth_version for x in draft}) == 1 and draft[0].ground_truth_version == approval.source_draft_identity.version and draft_hash == approval.source_draft_identity.hash, "source_draft_identity_mismatch")
    _require(authority.methodology_identity() == approval.methodology_identity, "methodology_identity_mismatch")
    _require(approval.engineering_identity.version == "v1" and authority.engineering_identity() == approval.engineering_identity.hash, "engineering_identity_mismatch")
    reference = authority.load_reference_collection(approval.reference_artifact_path, approval.reference_identity.hash)
    _require(len(reference) == 72 and {x.query_id for x in reference} == {x.query_id for x in queries}, "reference_population_mismatch")
    draft_by_query = {x.query_id: x for x in draft}
    for item in reference:
        source = draft_by_query[item.query_id]
        _require(item.source_draft_record_hash == canonical_hash(source.to_record()) and item.ground_truth_id == source.ground_truth_id and item.dataset_id == source.dataset_id and item.project_id == source.project_id and {canonical_hash(x.to_record()) for x in item.evidence} == {canonical_hash(x.to_record()) for x in source.evidence}, "reference_draft_derivation_mismatch")
    _require(approval.reference_identity.version == reference[0].truth_version and all(x.truth_version == reference[0].truth_version for x in reference), "reference_version_mismatch")
    prereqs = {x.role: x for x in approval.prerequisite_identities}
    _require(REQUIRED_ROLES <= prereqs.keys(), "prerequisite_missing")
    _require(all(x.identity != approval.identity_hash for x in approval.prerequisite_identities),
             "approval_identity_cycle")
    completed_times = []
    _require(prereqs["preregistration"].identity == canonical_hash({"query_ids": list(PREREGISTERED_JAVA_IDS), "query_set_hash": query_hash, "addendum_d_sha256": authority.raw_checksum("docs/experiments/Experiment_Protocol_Addendum_D_V3_1_0.md")}), "preregistration_mismatch")
    for role, item in prereqs.items():
        if role == "java_evidence_audit_set":
            audit_set = authority.load_typed(item.artifact_path, EvidenceAuditSet, item.identity)
            _require(audit_set.completeness_status == "complete" and audit_set.query_ids == PREREGISTERED_JAVA_IDS and audit_set.preregistration_identity == prereqs["preregistration"].identity, "audit_set_incomplete")
            prepared = authority.json_record("docs/experiments/evidence_audit/prepared/manifest.json")
            prepared_by_id = {x["query_id"]: x for x in prepared["entries"]}
            query_by_id = {x.query_id: x for x in queries}
            accepted_audits: list[EvidenceAuditRecord] = []
            paths = dict(audit_set.accepted_attempt_paths)
            for query_id, identity in audit_set.accepted_attempt_identities:
                audit = authority.load_audit(paths[query_id], identity, prepared_by_id[query_id])
                expected_reviews = {
                    item["evidence_id"]: canonical_hash({"query_id": query_id, "original_identity": item["original_identity"]})
                    for item in authority.json_record("docs/experiments/evidence_audit/prepared/records/" + query_id + ".json")["evidence_reviews"]
                }
                _require({x.evidence_id: x.evidence_identity for x in audit.evidence_reviews} == expected_reviews, "audit_evidence_binding_mismatch")
                _require(audit.query_id == query_id and audit.ground_truth_id == query_by_id[query_id].ground_truth_id and audit.query_identity == canonical_hash(query_by_id[query_id].to_record()) and audit.dataset_identity == dataset.dataset_hash and audit.reference_identity == approval.reference_identity.hash and audit.preregistration_identity == prereqs["preregistration"].identity and audit.provenance_status == "valid" and audit.reply_complete, "audit_provenance_invalid")
                accepted_audits.append(audit)
                completed_times.append(_timestamp("audit ended_at", audit.ended_at))
            _validate_independent_sessions(tuple(accepted_audits))
            resolution_ids = set(audit_set.resolution_identities)
            _require(resolution_ids == {item.hash for item in approval.resolution_identities} and
                     resolution_ids == {digest for audit in accepted_audits for digest in audit.resolution_identities},
                     "audit_resolution_mismatch")
            for digest in resolution_ids:
                resolution = authority.load_typed(f"docs/experiments/audits/resolutions/{digest}.json",
                                                  ResolutionRecord, digest)
                _require(resolution.status == "closed", "resolution_not_closed")
        elif role == "preregistration":
            _require(item.schema_version == "v1", "preregistration_schema_mismatch")
        else:
            prerequisite = authority.load_typed(item.artifact_path, ApprovalPrerequisiteRecord, item.identity)
            _require(prerequisite.role == role and prerequisite.status == "pass" and prerequisite.resolution_status == "closed", "prerequisite_not_passed")
            completed_times.append(_timestamp("prerequisite completed_at", prerequisite.completed_at))
            _require(authority.raw_checksum(prerequisite.output_artifact_path) == prerequisite.output_identity and authority.raw_checksum(prerequisite.provenance_artifact_path) == prerequisite.provenance_identity, "prerequisite_raw_hash_mismatch")
            if role == "final_data_qa":
                inputs = dict(prerequisite.input_identities)
                _require(inputs.get("reference") == approval.reference_identity.hash and inputs.get("java_evidence_audit_set") == prereqs["java_evidence_audit_set"].identity and inputs.get("chinese_coverage_audit") == prereqs["chinese_coverage_audit"].identity and inputs.get("methodology_review") == prereqs["methodology_review"].identity, "final_qa_inputs_mismatch")
    _require(all(_timestamp("approved_at", approval.approved_at) >= finished for finished in completed_times),
             "approval_precedes_prerequisite")
    decision = authority.load_typed(approval.decision_artifact_path, ApprovalDecisionRecord, approval.decision_identity)
    _require(decision.status == "approved" and decision.reference_identity == approval.reference_identity.hash and set(decision.prerequisite_identities) == {x.identity for x in approval.prerequisite_identities}, "approval_decision_mismatch")
    if approval.resolution_identities:
        _require("resolution_set" in prereqs and all(x.version == "v1" for x in approval.resolution_identities),
                 "resolution_set_missing")
        resolution_set = authority.load_typed(prereqs["resolution_set"].artifact_path,
                                              ApprovalPrerequisiteRecord, prereqs["resolution_set"].identity)
        bound = {digest for role, digest in resolution_set.input_identities if role.startswith("resolution:")}
        _require(bound == {x.hash for x in approval.resolution_identities}, "resolution_set_mismatch")
    closure = authority.load_typed("docs/experiments/reference_approval/phase62_closure.json", Phase62ClosureRecord)
    _require(closure.approved_reference_identity == approval.identity_hash and closure.final_data_qa_identity == prereqs["final_data_qa"].identity, "phase62_closure_mismatch")
    documentation_decision = authority.load_typed(closure.documentation_decision_artifact_path,
                                                   Phase62DocumentationDecisionRecord,
                                                   closure.documentation_decision_identity)
    _require(documentation_decision.approved_reference_identity == approval.identity_hash and documentation_decision.final_data_qa_identity == closure.final_data_qa_identity, "phase62_documentation_decision_mismatch")
    authority.verify_commit(closure.repository_commit)
    _require(requested_config.approved_reference_identity == approval.identity_hash and requested_config.dataset_hash == dataset.dataset_hash and requested_config.query_set_hash == query_hash and requested_config.ground_truth_hash == draft_hash, "config_identity_mismatch")
    _require(requested_config.run_kind == purpose and requested_config.population == (Population.ENGLISH_DEV if purpose == RunKind.DRY_RUN else Population.ENGLISH_TEST), "purpose_population_mismatch")
    _require(type(runtime_evidence) is RuntimeMetadata, "runtime_evidence_invalid")
    dependencies = dict(runtime_evidence.dependencies)
    _require(runtime_evidence.python_implementation == "CPython" and runtime_evidence.python_version == "3.12.14" and
             dependencies.get("torch") == "2.8.0" and dependencies.get("transformers") == "4.56.2" and
             runtime_evidence.device == "cpu" and runtime_evidence.dtype == "float32" and
             runtime_evidence.network_disabled and runtime_evidence.model_local_files_only,
             "runtime_contract_mismatch")
    runtime_identity = canonical_hash(runtime_evidence.to_record())
    authority.verify_execution_code(code_commit)
    if purpose == RunKind.FORMAL:
        _require(dry_run_receipt is not None, "dry_run_receipt_missing")
        receipt = authority.load_typed(dry_run_receipt, DryRunReceipt)
        _require(authority.raw_checksum(receipt.result_artifact_path) == receipt.result_checksum, "dry_run_result_hash_mismatch")
        _require(receipt.status == "pass" and receipt.approved_reference_identity == approval.identity_hash and receipt.dataset_identity == dataset.dataset_hash and receipt.query_set_identity == query_hash and receipt.reference_identity == approval.reference_identity.hash and receipt.config_identity == requested_config.experiment_family_identity and receipt.runtime_identity == runtime_identity and receipt.code_commit == code_commit, "dry_run_receipt_mismatch")
        _require(requested_config.semantic_mode != SemanticMode.FAKE_TEST, "formal_fake_model_forbidden")
    return _issue(repository_root=authority.root, purpose=purpose,
                  dataset_identity=dataset.dataset_hash, query_identity=query_hash,
                  reference_identity=approval.reference_identity.hash, approval_identity=approval.identity_hash,
                  methodology_identity=approval.methodology_identity, engineering_identity=approval.engineering_identity.hash,
                  config_identity=requested_config.identity_hash, code_commit=code_commit,
                  runtime_identity=runtime_identity, runtime_evidence=runtime_evidence,
                  dry_run_receipt_path=dry_run_receipt,
                  dataset=dataset, queries=queries, reference=reference)
