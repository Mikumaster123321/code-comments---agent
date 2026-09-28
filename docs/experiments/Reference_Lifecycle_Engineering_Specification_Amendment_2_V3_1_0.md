# V3.1.0 Reference Lifecycle Engineering Specification Amendment 2

- Version: `v1`
- Identity: `v3.1-phase62b-response-contract-failure-a2`
- Status: effective for Phase 6.2 Java Evidence execution records
- Authority: engineering clarification under Addendum D §§5–6 and Reference Lifecycle Engineering Specification v1 §3. The research method, frozen prepared inputs, Draft GT and the ten published v1 audits are unchanged.

Addendum D assigns malformed or untraceable model output to conservative `CANNOT_ASSESS`. This is an **execution outcome**, not a model verdict. A complete Final Answer that fails the frozen response parser has no adoptable per-evidence `EvidenceReview`, even if its free text resembles an allowed verdict. Do not strip prose, repair JSON, extract a code fence, infer individual verdicts, or retry for a favorable result.

`EvidenceAuditRecord` v2 is limited to this failure case. It retains the exact sent input, complete raw Final Answer, separate visible-part and platform provenance, real capture attempt number, hashes, and append-only publication. It records `evidence_reviews=[]`, `model_verdict=unavailable`, `execution_outcome=CANNOT_ASSESS`, `failure_reason=response_contract_failure`, and `overall_verdict=CANNOT_ASSESS` as the execution-level conservative outcome. The structured transcription records only those three execution fields. The loader must verify every raw hash and prove that the complete raw Final Answer fails the same strict parser used for v1. A parseable answer cannot enter this path. `provenance_status=valid` means input, session, and raw-capture provenance are valid; it does not validate the response contract.

The v1 schema, serialization, identities, and ten existing artifacts stay byte-for-byte unchanged. Count v1 structured audits and v2 execution failures separately: 12/12 executed may coexist with only 10/12 structured-valid reviews. A v2 failure cannot be counted as `SUPPORTS`, cannot create a model `CANNOT_ASSESS` verdict, and cannot silently satisfy Reference Approval. Addendum D §6 requires independent source-based resolution of both failures before approval; the present formal eligibility gate rejects unresolved v2 failures. This amendment creates no Reference Approval, Phase 6.2 Closure, or Phase 6.3 authorization.
