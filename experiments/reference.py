"""Addendum D reference lifecycle contracts; no artifact here implies approval."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Mapping

from .schemas import (
    EvidenceRecord, GroundTruthRecord, SchemaValidationError, _exact, _non_empty,
    _sha256, _timestamp, evidence_from_record,
)
from .serialization import canonical_hash, canonical_json, normalize_relative_path, sha256_hex

REFERENCE_METHOD = "specification_anchored_with_limited_llm_evidence_audit"
REQUIRED_ROLES = frozenset({
    "preregistration", "java_evidence_audit_set", "chinese_coverage_audit",
    "methodology_review", "final_data_qa",
})
ALL_ROLES = REQUIRED_ROLES | {"resolution_set"}
VERDICTS = frozenset({"SUPPORTS", "QUESTIONS", "CANNOT_ASSESS"})


def _choice(name: str, value: str, allowed: frozenset[str] | set[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise SchemaValidationError(f"{name} is invalid")


def _positive(name: str, value: int) -> None:
    if type(value) is not int or value <= 0:
        raise SchemaValidationError(f"{name} must be a positive integer")


def _safe_text(name: str, value: str) -> None:
    _non_empty(name, value)
    canonical_json({name: value})


def _path(name: str, value: str) -> None:
    normalize_relative_path(_non_empty(name, value))
    canonical_json({name: value})


def _tuple_of(name: str, value: tuple, kind: type, *, nonempty: bool = True) -> None:
    if type(value) is not tuple or (nonempty and not value) or not all(type(x) is kind for x in value):
        raise SchemaValidationError(f"{name} must be an immutable {kind.__name__} tuple")


def _sorted_unique(values: tuple, key, name: str) -> tuple:
    ordered = tuple(sorted(values, key=key))
    identities = [key(item) for item in ordered]
    if len(identities) != len(set(identities)):
        raise SchemaValidationError(f"{name} contains duplicate identity")
    return ordered


@dataclass(frozen=True)
class IdentityRef:
    """A versioned content identity, rather than an untyped digest."""
    version: str
    hash: str

    def __post_init__(self) -> None:
        _safe_text("version", self.version)
        _sha256("hash", self.hash)

    def to_record(self) -> dict:
        return {"version": self.version, "hash": self.hash}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> IdentityRef:
        _exact(value, {"version", "hash"}, "IdentityRef")
        return cls(**value)


@dataclass(frozen=True)
class ReferenceRecord:
    schema_version: str
    reference_method: str
    truth_version: str
    ground_truth_id: str
    query_id: str
    dataset_id: str
    project_id: str
    evidence: tuple[EvidenceRecord, ...]
    source_draft_record_hash: str
    derivation_rule_version: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1" or self.reference_method != REFERENCE_METHOD:
            raise SchemaValidationError("reference schema/method is unsupported")
        for name in ("truth_version", "ground_truth_id", "query_id", "dataset_id", "project_id", "derivation_rule_version"):
            _safe_text(name, getattr(self, name))
        _sha256("source_draft_record_hash", self.source_draft_record_hash)
        _tuple_of("evidence", self.evidence, EvidenceRecord)
        ordered = _sorted_unique(self.evidence, lambda x: canonical_json(x.to_record()), "reference evidence")
        if not any(item.relevance > 0 for item in ordered):
            raise SchemaValidationError("reference needs a relevant item")
        object.__setattr__(self, "evidence", ordered)

    def identity_record(self) -> dict:
        return {
            "schema_version": self.schema_version, "reference_method": self.reference_method,
            "truth_version": self.truth_version, "ground_truth_id": self.ground_truth_id,
            "query_id": self.query_id, "dataset_id": self.dataset_id, "project_id": self.project_id,
            "evidence": [item.to_record() for item in self.evidence],
            "source_draft_record_hash": self.source_draft_record_hash,
            "derivation_rule_version": self.derivation_rule_version,
        }

    @property
    def identity_hash(self) -> str:
        return canonical_hash(self.identity_record())

    def to_record(self) -> dict:
        return self.identity_record()

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> ReferenceRecord:
        fields = set(cls.__dataclass_fields__)
        _exact(value, fields, "ReferenceRecord")
        return cls(**{**value, "evidence": tuple(evidence_from_record(x) for x in value["evidence"])})


def derive_reference(draft: GroundTruthRecord, *, truth_version: str, derivation_rule_version: str = "spec-anchor-v1") -> ReferenceRecord:
    if type(draft) is not GroundTruthRecord or draft.annotation_status != "drafted":
        raise SchemaValidationError("reference derivation requires a drafted source record")
    return ReferenceRecord(
        "v1", REFERENCE_METHOD, truth_version, draft.ground_truth_id,
        draft.query_id, draft.dataset_id, draft.project_id, draft.evidence,
        canonical_hash(draft.to_record()), derivation_rule_version,
    )


@dataclass(frozen=True)
class PrerequisiteReference:
    role: str
    identity: str
    schema_version: str
    required: bool
    artifact_path: str

    def __post_init__(self) -> None:
        _choice("prerequisite role", self.role, ALL_ROLES)
        _sha256("prerequisite identity", self.identity)
        _safe_text("schema_version", self.schema_version)
        if type(self.required) is not bool or not self.required:
            raise SchemaValidationError("prerequisite must be required")
        _path("artifact_path", self.artifact_path)

    def identity_record(self) -> dict:
        return {"role": self.role, "identity": self.identity, "schema_version": self.schema_version, "required": self.required}

    def to_record(self) -> dict:
        return {**self.identity_record(), "artifact_path": self.artifact_path}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> PrerequisiteReference:
        _exact(value, set(cls.__dataclass_fields__), "PrerequisiteReference")
        return cls(**value)


@dataclass(frozen=True)
class Availability:
    status: str
    value: str | None
    reason: str | None

    def __post_init__(self) -> None:
        _choice("availability", self.status, {"available", "unavailable"})
        if self.status == "available":
            _safe_text("available value", self.value)
            if self.reason is not None:
                raise SchemaValidationError("available value cannot have unavailable reason")
        else:
            _safe_text("unavailable reason", self.reason)
            if self.value is not None:
                raise SchemaValidationError("unavailable value must be null")

    def to_record(self) -> dict:
        return {"status": self.status, "value": self.value, "reason": self.reason}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> Availability:
        _exact(value, {"status", "value", "reason"}, "Availability")
        return cls(**value)


@dataclass(frozen=True)
class RawCapture:
    artifact_path: str
    raw_sha256: str

    def __post_init__(self) -> None:
        _path("artifact_path", self.artifact_path)
        _sha256("raw_sha256", self.raw_sha256)

    def to_record(self) -> dict:
        return {"artifact_path": self.artifact_path, "raw_sha256": self.raw_sha256}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> RawCapture:
        _exact(value, {"artifact_path", "raw_sha256"}, "RawCapture")
        return cls(**value)


@dataclass(frozen=True)
class VisiblePart:
    availability: Availability
    capture: RawCapture | None

    def __post_init__(self) -> None:
        if type(self.availability) is not Availability:
            raise SchemaValidationError("visible part needs Availability")
        if self.availability.status == "available" and type(self.capture) is not RawCapture:
            raise SchemaValidationError("available visible part needs raw capture")
        if self.availability.status == "unavailable" and self.capture is not None:
            raise SchemaValidationError("unavailable visible part cannot have capture")

    def to_record(self) -> dict:
        return {"availability": self.availability.to_record(), "capture": None if self.capture is None else self.capture.to_record()}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> VisiblePart:
        _exact(value, {"availability", "capture"}, "VisiblePart")
        return cls(Availability.from_record(value["availability"]), None if value["capture"] is None else RawCapture.from_record(value["capture"]))


@dataclass(frozen=True)
class EvidenceReview:
    evidence_id: str
    evidence_identity: str
    verdict: str
    source_locations: tuple[str, ...]
    reason: str
    grade_observation: str | None

    def __post_init__(self) -> None:
        _safe_text("evidence_id", self.evidence_id)
        _sha256("evidence_identity", self.evidence_identity)
        _choice("verdict", self.verdict, VERDICTS)
        if type(self.source_locations) is not tuple or not self.source_locations:
            raise SchemaValidationError("source_locations must be non-empty tuple")
        for location in self.source_locations:
            _safe_text("source_location", location)
        _safe_text("reason", self.reason)
        if self.grade_observation is not None:
            _safe_text("grade_observation", self.grade_observation)
        canonical_json(self.to_record())

    def to_record(self) -> dict:
        return {"evidence_id": self.evidence_id, "evidence_identity": self.evidence_identity,
                "verdict": self.verdict, "source_locations": list(self.source_locations),
                "reason": self.reason, "grade_observation": self.grade_observation}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> EvidenceReview:
        _exact(value, set(cls.__dataclass_fields__), "EvidenceReview")
        return cls(**{**value, "source_locations": tuple(value["source_locations"])})


# The prepared prompt freezes the meaning of a review, not EvidenceReview's
# internal field names. Each accepted external layout has an exact field set.
_REPLY_LAYOUTS = (
    ("status", "identity", "observed_source_behavior", "grade_rationale_check", "span_grade_doubt", "span_grade_doubt_note"),
    ("verdict", "identity", "observed_behavior", "rationale_supported", "span_grade_suspected_mismatch", "span_grade_note"),
    ("verdict", "source_identity", "observed_behavior", "grade_assessment", "span_grade_concern"),
    ("status", "preserved_identity", "source_behavior_check", "grade_span_mismatch_suspected", "reason"),
    ("verdict", "identity", "source_behavior", "grade_correspondence_suspect", "rationale"),
    ("verdict", "file", "symbol_id", "span", "original_grade", "source_behavior", "rationale_supported", "span_grade_suspect", "notes"),
    ("verdict", "identity_preserved", "source_behavior_verified", "grade_support", "span_grade_correspondence_suspect", "notes"),
    ("verdict", "preserved_identity", "observed_source_behavior", "supports_grade_and_rationale", "span_grade_correspondence_doubt", "notes"),
    ("verdict", "original_identity", "source_behavior", "span_check", "grade_support", "suspected_span_grade_mismatch"),
    ("verdict", "identity", "observed_source_behavior", "grade_assessment", "span_grade_consistency_suspected"),
)
_REPLY_IDENTITY_KEYS = frozenset({"identity", "source_identity", "preserved_identity", "identity_preserved", "original_identity", "file", "symbol_id", "span", "original_grade"})
_REPLY_BOOLEAN_KEYS = frozenset({"rationale_supported", "span_grade_doubt", "span_grade_suspected_mismatch", "span_grade_concern", "grade_span_mismatch_suspected", "grade_correspondence_suspect", "span_grade_suspect", "span_grade_correspondence_doubt", "supports_grade_and_rationale", "suspected_span_grade_mismatch", "span_grade_consistency_suspected"})
_REPLY_TEXT_KEYS = frozenset({"observed_source_behavior", "grade_rationale_check", "span_grade_doubt_note", "observed_behavior", "span_grade_note", "grade_assessment", "source_behavior_check", "reason", "source_behavior", "rationale", "notes", "source_behavior_verified"})
_SYMBOL_KEYS = frozenset({"language", "kind", "qualified_name", "relative_path", "semantic_disambiguator", "fallback_line"})
_SPAN_KEYS = frozenset({"start_line", "end_line", "start_offset", "end_offset"})


def _reply_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SchemaValidationError("duplicate external response field")
        result[key] = value
    return result


def _reject_reply_constant(_: str) -> None:
    raise SchemaValidationError("non-finite response value")


def _external_identity(item: dict, original: dict) -> None:
    identity = next((item[key] for key in ("identity", "source_identity", "preserved_identity", "identity_preserved", "original_identity") if key in item), None)
    if identity is None:
        identity = {"relative_path": item["file"], "symbol_id": item["symbol_id"], "span": item["span"], "original_grade": item["original_grade"]}
    if type(identity) is not dict:
        raise SchemaValidationError("external identity must be an object")
    nested = {"relative_path", "symbol_id", "span"}
    identity_shapes = (nested, nested | {"grade"}, nested | {"original_grade"}, nested | {"claimed_grade"},
                       {"relative_path", "qualified_name", "semantic_disambiguator", "span"},
                       {"relative_path", "qualified_name", "kind", "language", "semantic_disambiguator", "span"})
    if set(identity) not in identity_shapes:
        raise SchemaValidationError("external identity fields are invalid")
    if type(identity["relative_path"]) is not str or identity["relative_path"] != original["relative_path"]:
        raise SchemaValidationError("external source path mismatch")
    span = identity["span"]
    if type(span) is not dict or set(span) != _SPAN_KEYS or any(type(x) is not int for x in span.values()) or span != original["span"]:
        raise SchemaValidationError("external span mismatch")
    symbol = identity.get("symbol_id", {key: identity[key] for key in _SYMBOL_KEYS if key in identity})
    nested_shapes = (_SYMBOL_KEYS, _SYMBOL_KEYS - {"fallback_line"}, _SYMBOL_KEYS - {"relative_path"})
    flat_shapes = ({"relative_path", "qualified_name", "semantic_disambiguator"},
                   {"relative_path", "qualified_name", "kind", "language", "semantic_disambiguator"})
    if type(symbol) is not dict or set(symbol) not in (nested_shapes if "symbol_id" in identity else flat_shapes):
        raise SchemaValidationError("external SymbolId fields are invalid")
    if any(type(value) is not type(original["symbol_id"][key]) or value != original["symbol_id"][key] for key, value in symbol.items()):
        raise SchemaValidationError("external SymbolId mismatch")
    for name in ("grade", "original_grade", "claimed_grade"):
        if name in identity and (type(identity[name]) is not int or identity[name] != original["grade"]):
            raise SchemaValidationError("external Grade identity mismatch")


def parse_external_evidence_response(raw: bytes, query_id: str, prepared_reviews: list[dict]) -> tuple[dict, tuple[EvidenceReview, ...]]:
    """Validate raw external JSON and deterministically derive canonical reviews."""
    if type(raw) is not bytes or type(query_id) is not str or type(prepared_reviews) is not list:
        raise SchemaValidationError("external response inputs are invalid")
    try:
        reply = json.loads(raw.decode("utf-8"), object_pairs_hook=_reply_object,
                           parse_constant=_reject_reply_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SchemaValidationError("external response is not UTF-8 JSON") from error
    if type(reply) is not dict or set(reply) != {"query_id", "overall_status", "evidence_reviews", "scope_statement", "end_marker"}:
        raise SchemaValidationError("external response fields are invalid")
    if reply["query_id"] != query_id or type(reply["query_id"]) is not str:
        raise SchemaValidationError("external query_id mismatch")
    _choice("external overall_status", reply["overall_status"], VERDICTS)
    _safe_text("external scope_statement", reply["scope_statement"])
    if type(reply["end_marker"]) is not str or reply["end_marker"] != "RESPONSE_END_" + query_id.upper().replace("-", "_"):
        raise SchemaValidationError("external end_marker mismatch")
    originals = {x["evidence_id"]: x["original_identity"] for x in prepared_reviews}
    if len(originals) != len(prepared_reviews) or type(reply["evidence_reviews"]) is not list:
        raise SchemaValidationError("external evidence list is invalid")
    seen = set()
    normalized = []
    for item in reply["evidence_reviews"]:
        if type(item) is not dict or type(item.get("evidence_id")) is not str or item["evidence_id"] not in originals or item["evidence_id"] in seen:
            raise SchemaValidationError("external evidence ID is missing, duplicate, or unknown")
        seen.add(item["evidence_id"])
        if not any(set(item) == {"evidence_id", *layout} for layout in _REPLY_LAYOUTS):
            raise SchemaValidationError("external evidence fields are invalid")
        verdict = item.get("verdict", item.get("status"))
        _choice("external verdict", verdict, VERDICTS)
        original = originals[item["evidence_id"]]
        _external_identity(item, original)
        for key in set(item) & _REPLY_BOOLEAN_KEYS:
            if type(item[key]) is not bool:
                raise SchemaValidationError("external boolean field is invalid")
        if verdict == "SUPPORTS" and (any(item[key] for key in set(item) & _REPLY_BOOLEAN_KEYS if key not in {"rationale_supported", "supports_grade_and_rationale"}) or
                                      any(not item[key] for key in set(item) & {"rationale_supported", "supports_grade_and_rationale"})):
            raise SchemaValidationError("external support contradicts grade doubt")
        for key in set(item) & _REPLY_TEXT_KEYS:
            _safe_text("external " + key, item[key])
        if "grade_support" in item:
            grade = item["grade_support"]
            if type(grade) is dict:
                if set(grade) != {"grade", "consistent", "reason"} or type(grade["grade"]) is not int or grade["grade"] != original["grade"] or type(grade["consistent"]) is not bool:
                    raise SchemaValidationError("external grade_support is invalid")
                _safe_text("external grade_support reason", grade["reason"])
                if verdict == "SUPPORTS" and not grade["consistent"]:
                    raise SchemaValidationError("external support contradicts grade assessment")
            else:
                _safe_text("external grade_support", grade)
        if "span_check" in item:
            check = item["span_check"]
            if type(check) is not dict or set(check) != {"span_covers_whole_line_16", "span_length_chars", "line_16_char_length_no_newline", "declaration_present_in_span", "line_number_matches_symbol", "file_ascii_so_byte_equals_char_offset", "note"} or any(type(check[x]) is not bool for x in ("span_covers_whole_line_16", "line_number_matches_symbol", "file_ascii_so_byte_equals_char_offset")) or any(type(check[x]) is not int for x in ("span_length_chars", "line_16_char_length_no_newline")):
                raise SchemaValidationError("external span_check is invalid")
            _safe_text("external span_check declaration", check["declaration_present_in_span"])
            _safe_text("external span_check note", check["note"])
        path, span = original["relative_path"], original["span"]
        reason = canonical_json({key: value for key, value in item.items() if key not in _REPLY_IDENTITY_KEYS | {"evidence_id", "verdict", "status"}})
        grade_observation = canonical_json({key: value for key, value in item.items() if "grade" in key or key == "span_check"})
        normalized.append(EvidenceReview(item["evidence_id"], canonical_hash({"query_id": query_id, "original_identity": original}),
                                         verdict, (f"{path}:L{span['start_line']}-L{span['end_line']} [{span['start_offset']},{span['end_offset']})",),
                                         reason, grade_observation))
    if seen != set(originals):
        raise SchemaValidationError("external evidence is missing")
    normalized.sort(key=lambda x: x.evidence_id)
    computed = "QUESTIONS" if any(x.verdict == "QUESTIONS" for x in normalized) else "CANNOT_ASSESS" if any(x.verdict == "CANNOT_ASSESS" for x in normalized) else "SUPPORTS"
    if reply["overall_status"] != computed:
        raise SchemaValidationError("external overall_status contradicts reviews")
    return reply, tuple(normalized)


@dataclass(frozen=True)
class EvidenceAuditRecord:
    schema_version: str
    query_id: str
    ground_truth_id: str
    attempt_number: int
    supersedes_attempt: int | None
    dataset_identity: str
    query_identity: str
    reference_identity: str
    preregistration_identity: str
    prepared_input_hash: str
    sent_input: RawCapture
    raw_reply: RawCapture
    reply_complete: bool
    reply_limitations: str | None
    visible_thinking: VisiblePart
    visible_final: VisiblePart
    platform_session_id: Availability
    independent_session_evidence: RawCapture
    ui_mode: str
    context_boundary_evidence: RawCapture
    observed_ui_name: str
    user_provided_alias: Availability
    alias_source: Availability
    exact_revision: Availability
    token_usage: Availability
    finish_reason: Availability
    model_metadata_evidence: RawCapture
    started_at: str
    ended_at: str
    timing_source: str
    timing_precision: str
    evidence_reviews: tuple[EvidenceReview, ...]
    transcription_hash: str
    transcription_capture: RawCapture
    overall_verdict: str
    provenance_status: str
    resolution_identities: tuple[str, ...]
    timing_limitations: str | None = None
    model_verdict: str | None = None
    execution_outcome: str | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version not in {"v1", "v2"}:
            raise SchemaValidationError("audit schema is unsupported")
        for name in ("query_id", "ground_truth_id", "ui_mode", "observed_ui_name", "timing_source", "timing_precision"):
            _safe_text(name, getattr(self, name))
        for name in ("independent_session_evidence", "context_boundary_evidence"):
            if type(getattr(self, name)) is not RawCapture:
                raise SchemaValidationError(f"{name} must be RawCapture")
        _positive("attempt_number", self.attempt_number)
        if self.supersedes_attempt is not None and (type(self.supersedes_attempt) is not int or self.supersedes_attempt != self.attempt_number - 1):
            raise SchemaValidationError("supersedes_attempt must name immediately preceding attempt")
        if self.attempt_number > 1 and self.supersedes_attempt is None:
            raise SchemaValidationError("retry must name preceding attempt")
        for name in ("dataset_identity", "query_identity", "reference_identity", "preregistration_identity", "prepared_input_hash", "transcription_hash"):
            _sha256(name, getattr(self, name))
        if type(self.transcription_capture) is not RawCapture or self.transcription_capture.raw_sha256 != self.transcription_hash:
            raise SchemaValidationError("transcription capture/hash mismatch")
        for name in ("sent_input", "raw_reply"):
            if type(getattr(self, name)) is not RawCapture:
                raise SchemaValidationError(f"{name} must be RawCapture")
        if type(self.reply_complete) is not bool:
            raise SchemaValidationError("reply_complete must be bool")
        if self.reply_limitations is not None:
            _safe_text("reply_limitations", self.reply_limitations)
        for name in ("visible_thinking", "visible_final"):
            if type(getattr(self, name)) is not VisiblePart:
                raise SchemaValidationError(f"{name} must be VisiblePart")
        for name in ("platform_session_id", "user_provided_alias", "alias_source", "exact_revision", "token_usage", "finish_reason"):
            if type(getattr(self, name)) is not Availability:
                raise SchemaValidationError(f"{name} must be Availability")
        if type(self.model_metadata_evidence) is not RawCapture:
            raise SchemaValidationError("model metadata requires raw platform evidence")
        if self.user_provided_alias.status != self.alias_source.status:
            raise SchemaValidationError("model alias and source availability must agree")
        if _timestamp("ended_at", self.ended_at) < _timestamp("started_at", self.started_at):
            raise SchemaValidationError("audit timing is reversed")
        if self.timing_limitations is not None:
            _safe_text("timing_limitations", self.timing_limitations)
        _tuple_of("evidence_reviews", self.evidence_reviews, EvidenceReview,
                  nonempty=self.schema_version == "v1")
        ordered = _sorted_unique(self.evidence_reviews, lambda x: x.evidence_id, "audit evidence")
        object.__setattr__(self, "evidence_reviews", ordered)
        _choice("overall_verdict", self.overall_verdict, VERDICTS)
        if self.schema_version == "v1":
            if any(value is not None for value in (self.model_verdict, self.execution_outcome, self.failure_reason)):
                raise SchemaValidationError("v1 audit cannot carry execution failure fields")
            computed = "QUESTIONS" if any(x.verdict == "QUESTIONS" for x in ordered) else "CANNOT_ASSESS" if any(x.verdict == "CANNOT_ASSESS" for x in ordered) else "SUPPORTS"
            if self.overall_verdict != computed or (not self.reply_complete and self.overall_verdict == "SUPPORTS"):
                raise SchemaValidationError("overall verdict contradicts evidence or completeness")
        elif (ordered or self.model_verdict != "unavailable" or
              self.execution_outcome != "CANNOT_ASSESS" or
              self.failure_reason != "response_contract_failure" or
              self.overall_verdict != "CANNOT_ASSESS" or not self.reply_complete):
            raise SchemaValidationError("v2 response failure must not invent model reviews")
        _choice("provenance_status", self.provenance_status, {"valid", "invalid", "incomplete"})
        if self.provenance_status == "valid" and not self.reply_complete:
            raise SchemaValidationError("valid provenance needs complete independent session")
        if type(self.resolution_identities) is not tuple:
            raise SchemaValidationError("resolution_identities must be tuple")
        for digest in self.resolution_identities:
            _sha256("resolution identity", digest)
        object.__setattr__(self, "resolution_identities", tuple(sorted(set(self.resolution_identities))))
        canonical_json(self.to_record())

    def identity_record(self) -> dict:
        result = {"schema_version": self.schema_version, "query_id": self.query_id,
                "ground_truth_id": self.ground_truth_id, "attempt_number": self.attempt_number,
                "supersedes_attempt": self.supersedes_attempt,
                "dataset_identity": self.dataset_identity, "query_identity": self.query_identity,
                "reference_identity": self.reference_identity, "preregistration_identity": self.preregistration_identity,
                "prepared_input_hash": self.prepared_input_hash, "sent_input_sha256": self.sent_input.raw_sha256,
                "raw_reply_sha256": self.raw_reply.raw_sha256, "reply_complete": self.reply_complete,
                "visible_thinking_sha256": None if self.visible_thinking.capture is None else self.visible_thinking.capture.raw_sha256,
                "visible_final_sha256": None if self.visible_final.capture is None else self.visible_final.capture.raw_sha256,
                "independent_session_sha256": self.independent_session_evidence.raw_sha256,
                "context_boundary_sha256": self.context_boundary_evidence.raw_sha256,
                "model_metadata_sha256": self.model_metadata_evidence.raw_sha256,
                "observed_ui_name": self.observed_ui_name,
                "user_provided_alias": self.user_provided_alias.to_record(),
                "alias_source": self.alias_source.to_record(),
                "exact_revision": self.exact_revision.to_record(),
                "evidence_reviews": [x.to_record() for x in self.evidence_reviews],
                "transcription_hash": self.transcription_hash, "overall_verdict": self.overall_verdict,
                "provenance_status": self.provenance_status, "resolution_identities": list(self.resolution_identities)}
        if self.schema_version == "v2":
            result.update(model_verdict=self.model_verdict, execution_outcome=self.execution_outcome,
                          failure_reason=self.failure_reason)
        return result

    @property
    def identity_hash(self) -> str:
        return canonical_hash(self.identity_record())

    def to_record(self) -> dict:
        result = {name: getattr(self, name) for name in self.__dataclass_fields__}
        for name in ("sent_input", "raw_reply", "independent_session_evidence", "context_boundary_evidence", "model_metadata_evidence", "transcription_capture", "visible_thinking", "visible_final", "platform_session_id", "user_provided_alias", "alias_source", "exact_revision", "token_usage", "finish_reason"):
            result[name] = getattr(self, name).to_record()
        result["evidence_reviews"] = [x.to_record() for x in self.evidence_reviews]
        result["resolution_identities"] = list(self.resolution_identities)
        if self.schema_version == "v1":
            for name in ("model_verdict", "execution_outcome", "failure_reason"):
                del result[name]
        return result

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> EvidenceAuditRecord:
        fields = set(cls.__dataclass_fields__)
        if value.get("schema_version") == "v1":
            fields -= {"model_verdict", "execution_outcome", "failure_reason"}
        _exact(value, fields, "EvidenceAuditRecord")
        result = dict(value)
        for name in ("sent_input", "raw_reply", "independent_session_evidence", "context_boundary_evidence", "model_metadata_evidence", "transcription_capture"):
            result[name] = RawCapture.from_record(value[name])
        for name in ("visible_thinking", "visible_final"):
            result[name] = VisiblePart.from_record(value[name])
        for name in ("platform_session_id", "user_provided_alias", "alias_source", "exact_revision", "token_usage", "finish_reason"):
            result[name] = Availability.from_record(value[name])
        result["evidence_reviews"] = tuple(EvidenceReview.from_record(x) for x in value["evidence_reviews"])
        result["resolution_identities"] = tuple(value["resolution_identities"])
        return cls(**result)


@dataclass(frozen=True)
class EvidenceAuditSet:
    schema_version: str
    preregistration_identity: str
    query_ids: tuple[str, ...]
    accepted_attempt_identities: tuple[tuple[str, str], ...]
    execution_contract_version: str
    expected_population: str
    resolution_identities: tuple[str, ...]
    completeness_status: str
    accepted_attempt_paths: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if self.schema_version != "v1":
            raise SchemaValidationError("audit set schema is unsupported")
        _sha256("preregistration_identity", self.preregistration_identity)
        _safe_text("execution_contract_version", self.execution_contract_version)
        if self.expected_population != "english_test_java":
            raise SchemaValidationError("audit population must be English-test Java")
        if type(self.query_ids) is not tuple or len(self.query_ids) != 12 or len(set(self.query_ids)) != 12:
            raise SchemaValidationError("audit set needs 12 unique query IDs")
        for query_id in self.query_ids:
            _safe_text("query_id", query_id)
        object.__setattr__(self, "query_ids", tuple(sorted(self.query_ids)))
        if type(self.accepted_attempt_identities) is not tuple:
            raise SchemaValidationError("accepted attempts must be tuple")
        for pair in self.accepted_attempt_identities:
            if type(pair) is not tuple or len(pair) != 2:
                raise SchemaValidationError("accepted attempt must pair query and hash")
            _safe_text("accepted query", pair[0]); _sha256("accepted audit identity", pair[1])
        accepted = tuple(sorted(self.accepted_attempt_identities))
        if len({q for q, _ in accepted}) != len(accepted) or not {q for q, _ in accepted} <= set(self.query_ids):
            raise SchemaValidationError("accepted audit queries are duplicate or unexpected")
        object.__setattr__(self, "accepted_attempt_identities", accepted)
        if type(self.accepted_attempt_paths) is not tuple or len(self.accepted_attempt_paths) != len(accepted) or {q for q, _ in self.accepted_attempt_paths} != {q for q, _ in accepted}:
            raise SchemaValidationError("accepted attempt paths must match accepted identities")
        for _, path in self.accepted_attempt_paths: _path("accepted attempt path", path)
        if len({path for _, path in self.accepted_attempt_paths}) != len(self.accepted_attempt_paths):
            raise SchemaValidationError("audit attempt path cannot be reused")
        object.__setattr__(self, "accepted_attempt_paths", tuple(sorted(self.accepted_attempt_paths)))
        _choice("completeness_status", self.completeness_status, {"complete", "incomplete"})
        if self.completeness_status == "complete" and len(accepted) != 12:
            raise SchemaValidationError("complete audit set needs all 12 attempts")
        if type(self.resolution_identities) is not tuple or len(set(self.resolution_identities)) != len(self.resolution_identities):
            raise SchemaValidationError("resolution identities must be unique tuple")
        for digest in self.resolution_identities: _sha256("resolution identity", digest)
        object.__setattr__(self, "resolution_identities", tuple(sorted(self.resolution_identities)))

    def identity_record(self) -> dict:
        return {"schema_version": self.schema_version, "preregistration_identity": self.preregistration_identity,
                "query_ids": list(self.query_ids), "accepted_attempt_identities": [list(x) for x in self.accepted_attempt_identities],
                "execution_contract_version": self.execution_contract_version,
                "expected_population": self.expected_population,
                "resolution_identities": list(self.resolution_identities), "completeness_status": self.completeness_status}

    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return {**self.identity_record(), "accepted_attempt_paths": [list(x) for x in self.accepted_attempt_paths]}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> EvidenceAuditSet:
        _exact(value, set(cls.__dataclass_fields__), "EvidenceAuditSet")
        return cls(**{**value, "query_ids": tuple(value["query_ids"]),
                      "accepted_attempt_identities": tuple(tuple(x) for x in value["accepted_attempt_identities"]),
                      "resolution_identities": tuple(value["resolution_identities"]),
                      "accepted_attempt_paths": tuple(tuple(x) for x in value["accepted_attempt_paths"])})


@dataclass(frozen=True)
class ErratumRecord:
    schema_version: str
    target_response_hash: str
    query_id: str
    evidence_id: str
    original_claim: str
    correction: str
    frozen_source_identity: str
    source_location: str
    verification_source: str
    impact_classification: str
    resolution_status: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1": raise SchemaValidationError("erratum schema is unsupported")
        for name in ("target_response_hash", "frozen_source_identity"):
            _sha256(name, getattr(self, name))
        for name in ("query_id", "evidence_id", "original_claim", "correction", "source_location", "verification_source", "impact_classification"):
            _safe_text(name, getattr(self, name))
        _choice("resolution_status", self.resolution_status, {"open", "closed"})

    def identity_record(self) -> dict: return self.to_record()
    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> ErratumRecord:
        _exact(value, set(cls.__dataclass_fields__), "ErratumRecord")
        return cls(**value)


@dataclass(frozen=True)
class ResolutionRecord:
    schema_version: str
    target_identity: str
    disposition: str
    evidence_identity: str
    status: str
    reason: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1": raise SchemaValidationError("resolution schema is unsupported")
        _sha256("target_identity", self.target_identity)
        _sha256("evidence_identity", self.evidence_identity)
        _choice("disposition", self.disposition, {"non_material", "re_audit", "source_verification", "truth_correction", "closed_with_explanation"})
        _choice("status", self.status, {"open", "closed"})
        _safe_text("reason", self.reason)

    def identity_record(self) -> dict: return self.to_record()
    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> ResolutionRecord:
        _exact(value, set(cls.__dataclass_fields__), "ResolutionRecord")
        return cls(**value)


@dataclass(frozen=True)
class ReferenceApprovalRecord:
    schema_version: str
    approval_version: str
    approval_status: str
    reference_method: str
    dataset_id: str
    dataset_identity: IdentityRef
    query_set_identity: IdentityRef
    reference_identity: IdentityRef
    source_draft_identity: IdentityRef
    methodology_identity: str
    engineering_identity: IdentityRef
    result_namespace: str
    prerequisite_identities: tuple[PrerequisiteReference, ...]
    resolution_identities: tuple[IdentityRef, ...]
    decision_identity: str
    supersedes_approval_hash: str | None
    approved_at: str | None
    reference_artifact_path: str
    decision_artifact_path: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1" or self.reference_method != REFERENCE_METHOD:
            raise SchemaValidationError("approval schema/method is unsupported")
        _safe_text("approval_version", self.approval_version)
        _choice("approval_status", self.approval_status, {"pending", "blocked", "approved"})
        _safe_text("dataset_id", self.dataset_id); _safe_text("result_namespace", self.result_namespace)
        for name in ("dataset_identity", "query_set_identity", "reference_identity", "source_draft_identity", "engineering_identity"):
            if type(getattr(self, name)) is not IdentityRef:
                raise SchemaValidationError(f"{name} must be IdentityRef")
        _sha256("methodology_identity", self.methodology_identity)
        _sha256("decision_identity", self.decision_identity)
        if self.supersedes_approval_hash is not None: _sha256("supersedes_approval_hash", self.supersedes_approval_hash)
        if self.approval_status == "approved":
            _timestamp("approved_at", self.approved_at)
        elif self.approved_at is not None:
            raise SchemaValidationError("pending/blocked approval cannot have approved_at")
        _path("reference_artifact_path", self.reference_artifact_path)
        _path("decision_artifact_path", self.decision_artifact_path)
        _tuple_of("prerequisite_identities", self.prerequisite_identities, PrerequisiteReference)
        ordered = _sorted_unique(self.prerequisite_identities, lambda x: x.role, "approval prerequisite roles")
        roles = {x.role for x in ordered}
        if not REQUIRED_ROLES <= roles:
            raise SchemaValidationError("approval is missing required prerequisite roles")
        if len({x.identity for x in ordered}) != len(ordered):
            raise SchemaValidationError("approval prerequisite identities must be unique")
        object.__setattr__(self, "prerequisite_identities", ordered)
        if type(self.resolution_identities) is not tuple or not all(type(x) is IdentityRef for x in self.resolution_identities) or len({x.hash for x in self.resolution_identities}) != len(self.resolution_identities):
            raise SchemaValidationError("resolution identities must be a unique tuple")
        object.__setattr__(self, "resolution_identities", tuple(sorted(self.resolution_identities, key=lambda x: x.hash)))
        canonical_json(self.to_record())

    def identity_record(self) -> dict:
        return {"schema_version": self.schema_version, "approval_version": self.approval_version,
                "approval_status": self.approval_status, "reference_method": self.reference_method,
                "dataset_id": self.dataset_id, "dataset_identity": self.dataset_identity.to_record(),
                "query_set_identity": self.query_set_identity.to_record(),
                "reference_identity": self.reference_identity.to_record(),
                "source_draft_identity": self.source_draft_identity.to_record(),
                "methodology_identity": self.methodology_identity,
                "engineering_identity": self.engineering_identity.to_record(),
                "result_namespace": self.result_namespace,
                "prerequisite_identities": [x.identity_record() for x in self.prerequisite_identities],
                "resolution_identities": [x.to_record() for x in self.resolution_identities],
                "decision_identity": self.decision_identity,
                "supersedes_approval_hash": self.supersedes_approval_hash}

    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    @property
    def approved_reference_identity(self) -> str:
        if self.approval_status != "approved": raise SchemaValidationError("reference is not approved")
        return self.identity_hash

    def to_record(self) -> dict:
        return {**self.identity_record(), "prerequisite_identities": [x.to_record() for x in self.prerequisite_identities],
                "approved_at": self.approved_at, "reference_artifact_path": self.reference_artifact_path,
                "decision_artifact_path": self.decision_artifact_path}

    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> ReferenceApprovalRecord:
        _exact(value, set(cls.__dataclass_fields__), "ReferenceApprovalRecord")
        result = dict(value)
        for name in ("dataset_identity", "query_set_identity", "reference_identity", "source_draft_identity", "engineering_identity"):
            result[name] = IdentityRef.from_record(value[name])
        result["prerequisite_identities"] = tuple(PrerequisiteReference.from_record(x) for x in value["prerequisite_identities"])
        result["resolution_identities"] = tuple(IdentityRef.from_record(x) for x in value["resolution_identities"])
        return cls(**result)


@dataclass(frozen=True)
class Phase62ClosureRecord:
    schema_version: str
    status: str
    approved_reference_identity: str
    final_data_qa_identity: str
    documentation_decision_identity: str
    repository_commit: str
    documentation_decision_artifact_path: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1" or self.status != "closed":
            raise SchemaValidationError("closure must be supported closed decision")
        for name in ("approved_reference_identity", "final_data_qa_identity", "documentation_decision_identity"):
            _sha256(name, getattr(self, name))
        _safe_text("repository_commit", self.repository_commit)
        _path("documentation_decision_artifact_path", self.documentation_decision_artifact_path)

    def identity_record(self) -> dict:
        return {name: getattr(self, name) for name in self.__dataclass_fields__ if name != "documentation_decision_artifact_path"}
    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> Phase62ClosureRecord:
        _exact(value, set(cls.__dataclass_fields__), "Phase62ClosureRecord")
        return cls(**value)


@dataclass(frozen=True)
class DryRunReceipt:
    schema_version: str
    status: str
    approved_reference_identity: str
    dataset_identity: str
    query_set_identity: str
    reference_identity: str
    config_identity: str
    runtime_identity: str
    code_commit: str
    result_checksum: str
    protocol_version: str
    population: str
    failure_status: str | None
    result_artifact_path: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1": raise SchemaValidationError("receipt schema is unsupported")
        _choice("receipt status", self.status, {"pass", "fail"})
        for name in ("approved_reference_identity", "dataset_identity", "query_set_identity", "reference_identity", "config_identity", "runtime_identity", "result_checksum"):
            _sha256(name, getattr(self, name))
        _safe_text("code_commit", self.code_commit); _safe_text("protocol_version", self.protocol_version)
        if self.population != "english_dev": raise SchemaValidationError("dry-run population must be english_dev")
        if self.status == "pass" and self.failure_status is not None: raise SchemaValidationError("pass receipt cannot have failure")
        if self.status == "fail": _safe_text("failure_status", self.failure_status)
        _path("result_artifact_path", self.result_artifact_path)

    def identity_record(self) -> dict:
        return {name: getattr(self, name) for name in self.__dataclass_fields__ if name != "result_artifact_path"}
    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> DryRunReceipt:
        _exact(value, set(cls.__dataclass_fields__), "DryRunReceipt")
        return cls(**value)


def raw_sha256(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise SchemaValidationError("raw payload must be bytes")
    return sha256_hex(payload)


@dataclass(frozen=True)
class Phase62DocumentationDecisionRecord:
    schema_version: str
    status: str
    approved_reference_identity: str
    final_data_qa_identity: str
    authority: str
    rationale: str

    def __post_init__(self) -> None:
        if self.schema_version != "v1" or self.status != "closed":
            raise SchemaValidationError("documentation decision must be closed")
        _sha256("approved_reference_identity", self.approved_reference_identity)
        _sha256("final_data_qa_identity", self.final_data_qa_identity)
        _safe_text("authority", self.authority)
        _safe_text("rationale", self.rationale)

    def identity_record(self) -> dict: return self.to_record()
    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> Phase62DocumentationDecisionRecord:
        _exact(value, set(cls.__dataclass_fields__), "Phase62DocumentationDecisionRecord")
        return cls(**value)


@dataclass(frozen=True)
class ApprovalPrerequisiteRecord:
    """Versioned non-Java review evidence; its role fixes the interpretation."""
    schema_version: str
    role: str
    status: str
    input_identities: tuple[tuple[str, str], ...]
    output_identity: str
    provenance_identity: str
    resolution_status: str
    output_artifact_path: str
    provenance_artifact_path: str
    completed_at: str | None

    def __post_init__(self) -> None:
        if self.schema_version != "v1" or self.role not in (ALL_ROLES - {"java_evidence_audit_set"}):
            raise SchemaValidationError("prerequisite schema/role is unsupported")
        _choice("prerequisite status", self.status, {"pending", "blocked", "pass"})
        _choice("resolution status", self.resolution_status, {"open", "closed"})
        if self.status == "pass":
            _timestamp("completed_at", self.completed_at)
        elif self.completed_at is not None:
            raise SchemaValidationError("incomplete prerequisite cannot have completion time")
        for name in ("output_identity", "provenance_identity"):
            _sha256(name, getattr(self, name))
        _path("output_artifact_path", self.output_artifact_path)
        _path("provenance_artifact_path", self.provenance_artifact_path)
        if type(self.input_identities) is not tuple or not self.input_identities:
            raise SchemaValidationError("input identities must be non-empty tuple")
        for role, digest in self.input_identities:
            _safe_text("input role", role); _sha256("input identity", digest)
        object.__setattr__(self, "input_identities", _sorted_unique(self.input_identities, lambda x: x[0], "prerequisite input roles"))

    def identity_record(self) -> dict:
        return {"schema_version": self.schema_version, "role": self.role, "status": self.status,
                "input_identities": [list(x) for x in self.input_identities], "output_identity": self.output_identity,
                "provenance_identity": self.provenance_identity, "resolution_status": self.resolution_status}

    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict:
        return {**self.identity_record(), "output_artifact_path": self.output_artifact_path,
                "provenance_artifact_path": self.provenance_artifact_path,
                "completed_at": self.completed_at}
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> ApprovalPrerequisiteRecord:
        _exact(value, set(cls.__dataclass_fields__), "ApprovalPrerequisiteRecord")
        return cls(**{**value, "input_identities": tuple(tuple(x) for x in value["input_identities"])})


@dataclass(frozen=True)
class ApprovalDecisionRecord:
    schema_version: str
    status: str
    decision_maker: str
    authority: str
    rationale: str
    reference_identity: str
    prerequisite_identities: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "v1": raise SchemaValidationError("decision schema is unsupported")
        _choice("decision status", self.status, {"pending", "blocked", "approved"})
        for name in ("decision_maker", "authority", "rationale"):
            _safe_text(name, getattr(self, name))
        _sha256("reference_identity", self.reference_identity)
        if type(self.prerequisite_identities) is not tuple or not self.prerequisite_identities:
            raise SchemaValidationError("decision prerequisites must be non-empty tuple")
        for digest in self.prerequisite_identities: _sha256("prerequisite identity", digest)
        object.__setattr__(self, "prerequisite_identities", tuple(sorted(set(self.prerequisite_identities))))

    def identity_record(self) -> dict:
        return {"schema_version": self.schema_version, "status": self.status,
                "decision_maker": self.decision_maker, "authority": self.authority,
                "rationale": self.rationale, "reference_identity": self.reference_identity,
                "prerequisite_identities": list(self.prerequisite_identities)}

    @property
    def identity_hash(self) -> str: return canonical_hash(self.identity_record())
    def to_record(self) -> dict: return self.identity_record()
    @classmethod
    def from_record(cls, value: Mapping[str, Any]) -> ApprovalDecisionRecord:
        _exact(value, set(cls.__dataclass_fields__), "ApprovalDecisionRecord")
        return cls(**{**value, "prerequisite_identities": tuple(value["prerequisite_identities"])})
