# V3.1.0 Phase 6.2B — Reference Lifecycle Engineering Specification

- Version: **v1**
- Status: **FROZEN for Phase 6.2B.1 implementation**
- Nature: Addendum D engineering realization; **not** a research-method addendum, approval, audit execution, or Phase 6.2 closure
- Freeze input: `v3.1.0-dev` at `cc3f7f63e75875ba63b940e11e31f891424fe4e0`
- Engineering choice: **Recommended Bounded Hardening (方案 B)**

## 1. Authority, scope, and present baseline

Research-method authority is the [Experiment Protocol](Experiment_Protocol_V3_1_0.md), [Addendum A](Experiment_Protocol_Addendum_A_V3_1_0.md), [B](Experiment_Protocol_Addendum_B_V3_1_0.md), [C](Experiment_Protocol_Addendum_C_V3_1_0.md), [D](Experiment_Protocol_Addendum_D_V3_1_0.md), and [Dataset/Query/GT Specification](Dataset_Query_GroundTruth_Specification_V3_1_0.md), with each addendum controlling only its stated supersession. This document controls engineering realization only. In any conflict, the Protocol/Addenda prevail; implementation stops rather than silently changing the method. Future contract changes require v2 or a versioned amendment, never silent replacement. Chat or external-model output is not repository authority.

Addendum D replaces the old Addendum A ≥48-hour delayed blinded self-review as the *current main 72-query reference approval route*, while retaining A and the human lifecycle as history. The current route is specification-anchored reference plus the preregistered limited 12-query English-test Java evidence audit, independent methodology review, Chinese non-mechanical-translation verification, required resolutions, final independent Data QA, and a separate approval. A model audit is neither human annotation nor human IAA. The historical non-effective silver proposal remains non-effective.

At freeze: 72 Queries, 72 v1 drafted GT records and 134 evidence items exist; English test/dev/Chinese populations are 48/12/12. The 12 prepared Java packages are valid preparation, **0/12 formal audits are complete**. There is no approved reference, no Phase 6.2 closure, no Dry Run receipt, and no Formal RQ1–RQ4 result. Phase 6.2 is OPEN; Phase 6.3 is BLOCKED / NOT STARTED; V3.2 is NOT STARTED. The v1 draft canonical `ground_truth_hash` is `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87`, not an approval hash. No existing Query, GT, evidence, manifest, identity, annotation audit, checksum, or historical hash is revised by this specification.

This is bounded hardening of `experiments/`: independent contracts, trusted loader/identity, one eligibility entry, legacy-boolean deauthorization, small gate index, negative tests, and frozen-commit preflight. It is neither a lasting minimal boolean patch nor a large experiment-layer refactor. No production Retrieval, `code_maintenance/`, `project_intelligence/`, UI, providers, Credits, Managed Access, or Admin Operations restructuring is required. Existing experiment serializers, evidence registry, truth mapper, writer, and artifact directories are reused. No directory migration or V3.2/Agent/Vector DB work is authorized.

## 2. Four lifecycle objects and deterministic derivation

| Object | Authoritative meaning | Boundary |
| --- | --- | --- |
| `GroundTruthRecord` | Historical Addendum A lifecycle: `drafted`, `reviewed`, `adjudicated`, `frozen` and existing human fields | All current v1 records stay `drafted`. Never fill `reviewed_at`, `reviewer_id`, or `adjudicator_id` to represent Addendum D approval. |
| `ReferenceRecord` | Immutable specification-anchored reference **content**, deterministically derived from the v1 Draft | Neither human-reviewed GT nor approval. |
| `EvidenceAuditRecord` | One actually executed Java evidence-audit attempt | Separate from prepared package; failed attempts persist. |
| `ReferenceApprovalRecord` | Versioned decision for one exact reference and prerequisite set | Neither GT status nor a gate boolean; approval does not itself close Phase 6.2. |

`ReferenceRecord` v1 concept: `schema_version`, `reference_method=specification_anchored_with_limited_llm_evidence_audit`, `truth_version`, `ground_truth_id`, `query_id`, `dataset_id`, `project_id`, complete `evidence[]` (full SymbolId, span, grade, rationale), `source_draft_record_hash`, and `derivation_rule_version`. Keep `ground_truth_id=gt-{query_id}`; resolve its version explicitly by method/version/hash. Sort records and evidence canonically; copy Draft query binding, evidence identity, span, grade, and rationale field-for-field. Without a formally approved truth correction, derivation cannot change any of them or regenerate labels. Record hash and collection hash must be reproducible from the frozen Draft and rule. No human reviewer fields or `annotation_status=approved` belong here.

The legacy `GroundTruthRecord` hash algorithm and bytes remain historical. The new reference content gets its own version/hash. `ground_truth_hash` is never reinterpreted as `reference_hash`. Formal lineage is Approved Reference → Reference content → source Draft, retaining both source Draft and approved reference identities. Grade suggestions from DeepSeek, Claude, Grok, GPT, or Codex are `grade_observation` only. A real identity/span/grade/rationale dispute requires a separate versioned truth-correction proposal citing old truth, affected query/evidence, frozen source and reason, independent review, new truth version/hash, and invalidation/reapproval of dependents. Retrieval scores cannot decide the correction.

## 3. Evidence execution and verdict contract

One preregistered Query uses one fresh independent session. The 12 IDs and selection rule in Addendum D §4 are immutable; they happen to be all English-test Java and are not representative of Python, Chinese, or all 72. Before the other 11, one end-to-end Evidence Capture Proof must establish: prepared input → exact sent bytes → independent session → complete raw response → platform metadata/unavailable reasons → byte hashes → structured record → validation → append-only publication. If a required field cannot be captured, stop and amend the contract *before* bulk execution.

An `EvidenceAuditRecord` v1 attempt contains:

- `schema_version`, `query_id`, positive `attempt_number`, `supersedes_attempt|null`, audited dataset/query/reference identities, preregistration identity, and prepared input hash;
- sent input raw blob or immutable repository-relative reference **and raw-byte SHA-256**; raw reply blob/reference, raw-byte SHA-256, completeness, and limitations;
- separately visible thinking and final answer: each `available`/`unavailable(reason)` with raw reference/hash when available;
- session platform ID or `unavailable(reason)`, independent-session proof, UI mode, and context-boundary evidence;
- model `observed_ui_name`, `user_provided_alias`, `alias_source`, and exact revision/token usage/finish reason as actual value or `unavailable(reason)`;
- actual `started_at`/`ended_at`, source, precision and limitations; one review per complete evidence identity with verdict, frozen source location(s), reason and optional grade observation; structured transcription hash, derived overall verdict, provenance validation, and typed resolution references.

Prepared `evidence_audit/prepared/` inputs, blank records, manifest and hashes stay unchanged; execution uses a new location. Sent bytes must equal the prepared input bytes exactly. Raw means raw: do not trim, normalize line endings, reformat, or pretty-print before SHA-256. Preserve failed/incomplete attempts; retries increment attempt number, link to prior attempt, and append rather than overwrite or retain only the best. The accepted set selects only valid attempts by an explicit selection record. A response whose completeness cannot be proven cannot count as complete `SUPPORTS`; an unproven independent session cannot count toward 12/12.

Per-evidence verdict is `SUPPORTS`, `QUESTIONS`, or `CANNOT_ASSESS`. `E01`/`E02` are package-local labels and must resolve to full `(query_id, ground_truth_id, evidence identity including project/path/SymbolId/span/grade)`; cross-query reuse fails. Missing/malformed evidence, invalid transcript, source ambiguity or incomplete capture yields `CANNOT_ASSESS`. Overall verdict is computed: any `QUESTIONS` → `QUESTIONS`; else any `CANNOT_ASSESS` → `CANNOT_ASSESS`; only a complete all-`SUPPORTS` set → `SUPPORTS`. The caller cannot override it. `SUPPORTS` is limited to the supplied cited source; it does not prove all relevant evidence was found or approve a reference.

TraeWork's observed UI name in historical material is `DeepSeek-V4-Flash`; the user-supplied platform mapping is `DeepSeek-V4.1-Flash`. Store both with source, without inferring exact revision, build ID, provider internal version, or unavailable historical metadata. Addendum D's earlier candidate display name is not evidence that a particular call used a precise backend. Historical shared TraeWork replies, including apparent SUPPORTS replies, may remain pre-audit evidence but cannot be grandfathered into formal attempts or assigned invented session IDs; formal count remains 0/12.

An `EvidenceAuditSet` identity canonically binds preregistration identity, exact sorted 12-query set, expected population, each selected accepted execution identity, execution-contract version, linked errata/resolutions, and completeness status. A count of 12 alone is insufficient; 11 valid attempts remain incomplete. Time/session provenance is validated and protected by full-file raw checksums, while semantic identity excludes timestamps and host-specific session strings except where a separately declared immutable capture reference is required for provenance validation.

## 4. Raw evidence, errata, resolution, and independent prerequisites

Raw model input/reply is immutable. An append-only **erratum** binds target raw-response hash, query/evidence identity, exact original claim, correction, frozen source identity/location, verification source, impact class and resolution status; it does not edit raw evidence. A typed **resolution** records how a finding/erratum was handled (`non-material`, `re-audit`, `source verification`, `truth correction`, or documented close), with evidence and closure status. **Truth correction** alone may create a new truth version after independent review. Dependency direction is Raw Evidence → Erratum → Resolution; source Draft → corrected truth version (if approved) → derived Reference; audits/resolutions → QA/approval. No erratum directly edits truth.

For `et-bl-ja-02`, preserve the historical DeepSeek response: its claim that `closeTicket` alone calls `markClosed` conflicts with frozen source where both `DeskQueue.closeTicket` and `TicketFolder.find` call it. A future append-only erratum and independently checked resolution must cite those locations and classify impact. It neither changes Grade automatically nor rehabilitates the historical reply into a formal audit.

Chinese non-mechanical-translation review is a *separate* 12-query approval prerequisite, not a Java EvidenceAuditRecord. Freeze its rules, input population, verdict schema and identity before execution; bind its content identity in approval. It does not change grades, inspect retrieval rankings, tune Query wording, or replace Java audit, methodology review or final QA. Independent methodology review likewise requires preregistered versioned input/questions/boundaries, allowed verdicts, output identity, provenance and resolution status. Existing formal material may be cited at its actual state; no PASS is inferred from conversation. Follow `AGENTS.md` model roles if a later phase requests external review.

Final Independent Data QA binds *candidate* Reference content identity, AuditSet identity, Chinese audit identity, and methodology-review identity, never a future approval hash. It checks 72/72 population, hashes, source spans/evidence, quota, leakage, RQ1 File/Symbol/Chunk mapping, Java limitations, Addenda A/B/C/D fidelity and all prerequisites. It must explicitly PASS before approval. The dependency DAG is Draft → Reference → Audits and other reviews/resolutions → Final Data QA → Reference Approval → Phase 6.2 Closure → Dry Run → Dry Run Receipt → Formal Eligibility. Cycles such as Approval → QA → Approval are forbidden.

## 5. Approval contract and identity projection

`ReferenceApprovalRecord` v1 has `schema_version`, `approval_version`, `approval_status=pending|blocked|approved`, `reference_method`, dataset/query/reference/source-Draft/research-methodology identities, typed `prerequisite_identities`, typed `resolution_identities`, `decision_identity`, `supersedes_approval_hash|null`, and `approved_at|null`. An approval also binds the engineering realization version/hash and a distinct result namespace. Pending/blocked require `approved_at=null`; approved requires a real time no earlier than completed prerequisites. Supersession is append-only and preserves prior run-to-approval identity.

A `PrerequisiteReference` is `{role, identity, schema_version, required}` with a unique role/identity contract. Required roles are `preregistration`, `java_evidence_audit_set`, `chinese_coverage_audit`, `methodology_review`, `final_data_qa`; `resolution_set` is included when findings exist. Phase 6.2 closure is downstream and must **not** be an approval prerequisite. `decision_identity` identifies a repository-tracked, schema-valid decision statement naming decision maker/process, authority, verdict, and prerequisite-resolution basis; a model's prose alone cannot decide approval. Do not create a `ReferenceIdentity` class whose sole value is a SHA-256 string.

Freeze `identity_record()` before implementation. Its exact v1 authoritative projection is a canonical mapping of: schema and approval versions/status; reference method; dataset ID/version/hash; query-set version/hash; Reference truth version/content hash; source Draft version/hash; research-methodology identity; engineering-realization version/hash; result namespace; five required typed prerequisite references (including preregistration and audit set); sorted typed resolution references; decision identity; and prior approval hash when superseding. Approval hash = `canonical_hash(identity_record())` using the established credential-free UTF-8 sorted-key JSON serializer and stable ordering for lists. It is the **approved_reference_identity** when status is approved; it is not a hash of the entire dataclass. The approval record's `approved_at`, capture/run timestamps, local path, UI session ID, UUID, object representation and mutable display notes are outside this semantic projection, but remain covered by the full artifact **raw-byte SHA-256 checksum**. Child identities used by this projection must also exclude those provenance-only fields, preventing timestamps from leaking back indirectly. If a child contract cannot do so, version and repair it before approval. Full raw files and raw sent/reply bytes each have separately named raw-byte checksums. Never call these different hashes an unqualified “checksum.” The old v1 hash stays unchanged.

Research-methodology identity is a typed canonical manifest of version and raw-byte SHA-256 for Protocol, Addenda A–D, and Dataset Specification; engineering-realization identity separately binds this document's v1 and raw-byte SHA-256. This declares each document's role rather than blindly concatenating bytes. Any update requires explicit version/identity migration. Identities are repository-relative or content-based, host-path-independent, credential-free, deterministic under dict/input order and `PYTHONHASHSEED`, and independent of UUID and memory address. A changed authoritative field changes the corresponding hash.

## 6. Phase closure, execution eligibility, and existing components

An approved Reference is only one prerequisite of the Phase 6.2 Documentation Gate. Existing narrative QA reports, `PROJECT_CONTEXT.md`, and a future gate index cannot alone be machine-validated as the exact closed authority. Therefore Phase 6.2B.1 must define a minimal, separately published **Phase62ClosureRecord** (artifact contract, not an unnecessary general framework): status, schema/version, exact approved-reference identity, final QA identity, documentation decision identity, repository commit/authority identity, and raw-file checksum. Publish only after real closure; no artifact is created here. The validator loads and recomputes it and verifies selected approval membership. This avoids both an approval/closure identity cycle and an uncheckable text-only gate.

`validate_formal_eligibility(...)` is the only authoritative entry for `DRY_RUN` and `FORMAL`; helper checks do not become parallel gates. An explicitly separate `SYNTHETIC` test/infrastructure path is non-formal and produces no thesis-quality result. Conceptual procedure:

```text
validate_formal_eligibility(purpose, repository_state, requested_config,
                            selected_reference_approval, runtime_evidence,
                            dry_run_receipt=None):
    authority = load_accepted_repository_authority(repository_state)
    approval = authority.load_exact_approval(selected_reference_approval)
    require approval exists and status == approved and schema/version supported
    require recompute(approval.identity_record()) == selected_reference_approval
    reference = authority.load_exact_reference(approval.reference_identity)
    require recomputed dataset, query-set, reference, source-Draft,
            research-methodology and engineering-contract identities all match
    require typed preregistration and every prerequisite validates against raw evidence
    require complete 12-ID Java audit set, valid provenance and exact raw byte hashes
    require valid Chinese audit, methodology review, final Data QA PASS,
            and all required resolutions CLOSED
    closure = authority.load_phase62_closure()
    require closure CLOSED and closure references this approved_reference_identity
    require purpose allowed by the verified closure and frozen population contract
    if purpose == DRY_RUN:
        require population == english_dev (12), no English-test tuning
    elif purpose == FORMAL:
        receipt = authority.load_exact_dry_run_receipt(dry_run_receipt)
        require receipt PASS and compatible with approval, config family and runtime
        require frozen formal population, model, code and runtime contracts
    else:
        FAIL  # synthetic uses its separately marked non-formal path
    require requested config identity and runtime/code/model identities match authority
    return immutable validator-issued ValidatedExecutionInputs(...)
# Any failed requirement raises; no partial object or execution is returned.
```

A future `DryRunReceipt` binds approved-reference identity, dataset/query/reference identity, experiment/config identity, runtime/code identity, dry-run protocol version, result checksum, run/failure status, and the frozen dev population. Formal execution verifies it matches the selected approval and experiment family; a boolean cannot substitute for it. The current `FormalGateEvidence.phase_6_2_dataset_truth_frozen` and `phase_6_3_dry_run_passed` remain readable only for historical deserialization/tests/display. They have **zero authorization power**: `if legacy_boolean: allow_formal` is prohibited; if compatibility metadata contradicts repository authority, fail closed or ignore it as explicitly non-authoritative. Never add a third `reference_approved` switch.

`ValidatedExecutionInputs` is a process-local immutable validator-issued capability, not a persistent artifact or cryptographic secret. It carries validated dataset, query, reference, approval, methodology, engineering contract, config, code/runtime identities, purpose, and needed authoritative objects/paths. A caller-made lookalike cannot satisfy the runner; the formal/dry-run runner checks issuer provenance and revalidates necessary identities at entry. `BenchmarkConfig` describes strategy/unit/metrics/Hybrid/Graph/E5/population and binds the exact approved reference in its *new formal config identity*; it cannot declare approval. Existing `ground_truth_hash` stays a legacy Draft field and requires a compatible migration, not semantic renaming. `RunMetadata` records actual commit/runtime/model/device/config/reference/environment/times/output checksums and is provenance, never authority. `BenchmarkRunner` consumes only validated inputs for formal/dry-run, not arbitrary GT, metadata, approval dict or booleans. `TruthMapper` and `DatasetEvidenceRegistry` retain the existing File/Symbol/Chunk mapping and source-evidence checks. The artifact writer stays raw-first, checksum-verified, append-only and atomic; new artifact publication verifies schema, identity and cross-references, but a successful write is not eligibility or approval.

The loader accepts repository-tracked artifacts within repository-relative path boundaries, validates exact schema, recalculates canonical identity and raw checksums, and follows typed cross-references. Caller-provided dicts, local absolute paths and unchecked `current_gate.json` cannot claim approval. Formal semantic-dependent runs require the pinned real E5; fake embeddings or degraded lexical fallback cannot be reported as successful Hybrid. Failed Queries stay in the denominator; global E5 failure follows the Protocol. No RQ1–RQ4, `top_k`, metric, Hybrid/Graph config, E5 identity, File/Chunk mapping, Addendum B `5/2/2/0` and seven-document single batch, or Addendum C leakage rule changes here.

## 7. Fail-closed matrix

The validator rejects, without partial inputs: absent/non-approved/unsupported approval; mismatched approval, dataset, query, reference, source Draft, research method, engineering contract or preregistration identity; wrong/incomplete 12-ID audit set, invalid provenance/session boundary, mismatched sent/reply raw hash or incomplete reply; absent/mismatched Chinese audit or methodology review; absent/failed/mismatched final QA; open required erratum/resolution; absent/mismatched Phase 6.2 closure; disallowed purpose/population; missing/incompatible Dry Run receipt for FORMAL; runtime/code/model/config mismatch; semantic degraded fallback; legacy booleans without authority; direct drafted-GT formal input. The implementation should validate typed artifacts/status/cross-references, not persist 25 independent `*_passed` booleans. Every negative condition needs an offline regression test.

## 8. Artifact placement, navigation, CI, and compatibility

Reuse `docs/experiments/ground_truth/v1/`, `queries/v1/`, `datasets/v1/`, and `evidence_audit/prepared/` unchanged. Minimal new versioned locations, when real artifacts exist: `docs/experiments/reference/` for derived records; `evidence_audit/executions/` for attempts/raw blobs; `docs/experiments/audits/` for Chinese/methodology/final QA and resolutions; `docs/experiments/reference_approval/` for decisions/approvals/closure. Names may be refined by 6.2B.1 only if role and identity stay unambiguous; do not create synonym directories or move old artifacts. Atomic publish and append-only rules apply to executions, errata, resolutions, approvals and closure; incomplete temp artifacts are non-authoritative. Credential/secret scans precede publication. If raw evidence contains a secret, fail/quarantine with provenance; never silently redact it while calling the redaction raw. Platform session IDs may be retained only as safe auditable provenance; if sensitive or host-specific, use explained redacted/hashed provenance and exclude it from semantic identity.

Phase 6.2B.1 creates the small `docs/experiments/current_gate.json` navigation index: `schema_version`, current phase/gate/status, selected approval identity or null, derived dry-run/formal eligibility, blockers, next allowed action, authoritative documents and update commit/repository identity. It records current state only, not history; `PROJECT_CONTEXT.md` preserves history. Index changes accompany the real authority change in the same commit. The validator reloads underlying approval/closure/receipt; any index disagreement fails closed. This round freezes the index contract but does **not** create a premature index file.

The Phase 6 dataset contract needs frozen self-repository commit `12391233daa2149ead4f451e920b2e0d8a1a6beb`. Before Phase 6.2B closure, CI checkout must use `fetch-depth: 0` or an equivalent guarantee, and preflight must prove this exact object exists and is readable. Missing object fails; never fall back to HEAD. Workflow editing is a later small implementation change. Before V3.1 release push/tag, perform a separate Repository & Code Hygiene Gate for dead/temporary/duplicate files, stale docs, dependencies, model/cache/vector artifacts, outputs and Git tracking; this document does not perform that cleanup.

## 9. Migration stages and verification

1. **6.2B.0:** freeze this specification only; no actual approval/audit.
2. **6.2B.1:** implement Reference/Audit/Approval/closure contracts, identity projection, trusted loader, unified eligibility, legacy boolean deauthorization, gate index, negative tests and CI preflight. Independent QA follows. Recommended implementation agent: Codex on GPT-6 Sol High; Astra Ultra is not required.
3. **6.2B.2:** prove one preregistered Java Query's complete independent-session capture end to end before bulk audit.
4. **6.2B.3:** complete the remaining preregistered audits with append-only attempts; accept only compliant executions.
5. **6.2B.4:** freeze then execute Chinese audit and methodology review; close required errata/resolutions. Their rules cannot be backdated after results.
6. **6.2B.5:** deterministically derive the candidate 72-record Reference, then perform Final Independent Data QA on candidate and prerequisite identities.
7. **6.2B.6:** only with real PASS evidence, publish approval decision/record and subsequently separate Phase 6.2 closure. Then Phase 6.3 becomes allowed but not started. English-dev-only Dry Run and a verified receipt precede any Formal RQ run.

6.2B.1 tests cover strict schema types (including bool-as-int, unknown fields, duplicate identity, invalid hashes/status, NaN/Infinity), canonical/provenance/raw hash boundaries, input order and multiple `PYTHONHASHSEED` values, prepared-versus-executed separation, invalid/shared/incomplete attempts, append-only retry, erratum immutability, all fail-closed cases above, old-v1 readability/hash stability, and existing Phase 6.1 through Phase 1/offline-LLM/full regression. No real provider or Retriever/E5 is needed for those tests. Current Phase 6.2B.0 requires only existing offline documentation/dataset checks and full regression; it adds no production test.

No step here approves the current Draft, manufactures a review/audit/QA PASS, redoes Phase 6.2A, starts a Dry Run, or authorizes Formal RQ1–RQ4. The Phase 6.2 Gate remains OPEN after this document. Completion of this specification permits **6.2B.1 ALLOWED BUT NOT STARTED** only. Git safety: preserve user `docs/thesis/`, existing source artifacts and hashes; no push or tag in this phase.
