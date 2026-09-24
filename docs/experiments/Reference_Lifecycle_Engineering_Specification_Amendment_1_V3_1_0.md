# V3.1.0 Phase 6.2B.2 — Raw Reply Boundary Clarification

- Amendment ID: `v3.1-phase62b-raw-reply-boundary-a1`
- Amendment version: `v1`
- Status: **FROZEN** once committed; no EvidenceAudit execution or approval is created by this document.
- Base: [Reference Lifecycle Engineering Specification v1](Reference_Lifecycle_Engineering_Specification_V3_1_0.md), raw-byte SHA-256 `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`.
- Scope: the meaning of `raw_reply`, `visible_thinking`, `visible_final`, and `reply_complete` in base §3 when a platform displays a separate Thinking region.
- Authority: the user-approved, platform-neutral Phase 6.2B.2 method ruling. The base specification's §1 permits a versioned amendment; the original v1 bytes and [Addendum D v1](Experiment_Protocol_Addendum_D_V3_1_0.md) remain unchanged. Addendum D §5 already permits `unavailable` for Thinking that cannot be exported. In any conflict, Protocol/Addenda retain priority.

## 1. Raw reply and completeness

For an EvidenceAudit execution, `raw_reply` means the **exportable final response** that the model platform presents to the user: the final answer content that the user can export in full. Preserve its exact exported UTF-8 bytes and raw-byte SHA-256. Do not trim, normalize newlines, remove analysis-like text, reformat, or reconstruct any part before hashing. `visible_final` records the separately visible final answer and may refer to the same immutable raw capture when its bytes are exactly the complete exportable final response.

If the platform separately displays Thinking/reasoning but cannot export that region completely, its unavailable content is **not** a required component of `raw_reply` completeness. The capture must still identify the observed UI boundary, export scope, and limitation. A copied or exported text whose boundary or completeness cannot be established must not be labelled complete merely because it parses or has an end marker.

`reply_complete=true` states only that the platform's exportable final response was captured from its first character through its last character, with exact raw bytes and hash, a valid required end marker, and the frozen JSON/response contract. It does not claim that hidden platform reasoning or unexportable visible Thinking was captured. The end marker and a matching hash protect the captured bytes but do not alone prove that the UI/export scope was complete. If the final response is truncated, its boundaries cannot be established, or the required response contract fails, `reply_complete` cannot be true; the existing `CANNOT_ASSESS` and provenance rules apply.

## 2. Separately visible Thinking

Thinking is separately recorded provenance/visible-part evidence. It does not directly determine `evidence_reviews` verdicts. Use the existing `VisiblePart` and `Availability` schema without inventing a new enum value:

| Observed UI state | `visible_thinking` representation | Required provenance |
| --- | --- | --- |
| Separate Thinking is visible and completely exportable | `available` with its own exact raw capture and hash | State that the full region was exported; keep it separate from the final response. |
| Separate Thinking is visible but cannot be completely exported | `unavailable(reason)` with `capture=null` | State explicitly that the region was visible, full export was unavailable, and why. Record the visible/export boundary and any limitation without reconstructing the missing text. |
| No separate Thinking region is visible | `unavailable(reason)` with `capture=null` | State explicitly that no separate region was observed; do not describe this as an export failure. |

The second and third rows have distinct reasons despite sharing the existing `unavailable` schema value. Never record a visible-but-unexportable region as absent, attach a partial Thinking export as a complete `visible_thinking` capture, infer missing text, or synthesize it from the final answer. Hidden chain-of-thought is neither requested nor an EvidenceAudit acceptance prerequisite; screenshots, OCR, or guesses must not be used to reconstruct unexportable reasoning.

## 3. Unchanged execution gates

The audit authority remains the observable sent input, exact exportable final response, frozen source/evidence identity, independent-session and context-boundary evidence, and derived verdict contract. This clarification does not relax the base specification's exact sent-byte match, real timing and model provenance, raw hash and privacy checks, final-answer validation, append-only attempt handling, or the separation of `SUPPORTS` from execution acceptance and Reference Approval. A `visible_thinking=unavailable` record alone never establishes `reply_complete` or `provenance_status=valid`.

Future execution provenance must name this amendment ID, version, repository path, and raw-byte SHA-256 alongside the base v1 identity. A future `EvidenceAuditSet.execution_contract_version` must distinguish the amended execution contract from unamended v1; its accepted attempts still require all existing validator checks. The amendment does not itself create an accepted attempt, an AuditSet, approval, closure, Dry Run receipt, or Formal eligibility.

## 4. Phase 6.2B.2 boundary

For `et-dq-ja-01`, the user reports one fresh DeepSeek session, an exportable Final Answer, and a separate UI Thinking region whose full export is unavailable. These are provenance claims awaiting verification against the existing capture. This amendment neither validates its raw bytes nor counts it as a completed audit. Review the existing capture against this clarified contract after the amendment is frozen; do not re-call DeepSeek for this clarification.

Formal Java Evidence Audit remains **0/12**. Phase 6.2B.2 Evidence Capture Proof is **not completed**; Phase 6.2 remains **OPEN**, Reference Approval is **NOT CREATED**, and Phase 6.3 remains **BLOCKED / NOT STARTED**.
