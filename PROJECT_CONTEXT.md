# Project Context

## Project

毕业设计：《基于大语言模型与多智能体协同的软件代码智能维护系统设计与实现》。项目正从 **Code Comments Agent** 渐进演进为智能软件代码维护系统；现有 Gradio 应用必须持续可用。

## Current State

- Current Development Version: `V3.0.1`
- Current branch: `v3.0.1-dev`
- Status: `Phase 4 Documentation Gate Closed; Ready for V3.0.1 RC / Release Engineering`
- Phase 0 — Architecture & Scope Gate: completed
- Phase 0.0 — Development Baseline: completed
- Claude Phase 0 Architecture Review: completed
- V3.0.1 Architecture Decision: frozen
- Phase 0.1 — Architecture Decision Documentation: completed
- DeepSeek Phase 0 Architecture Consistency Review: `PASS WITH ISSUES`
  (Critical 0, Medium 0, Low 4, Blocking 0)
- Phase 0 Documentation Hardening: completed (O-1 through O-4 resolved)
- Phase 0 Final Documentation Gate: `CLOSED`
- V3.0.0: released / frozen
- V3.0.0 tag: annotated tag `v3.0.0` resolves to final release commit
  `2b2b0cb103264f7ac278f35c19a1dc0b02196dc8`
- Development baseline tests: `129 passed` with the documented current-host
  `python -m pytest -p no:debugging` workaround; ordinary pytest reproduces the known
  Anaconda Python 3.13.5 debugging-plugin / `rlcompleter` segmentation fault
- Offline LLM-contract smoke: `6 passed`; no real API, credential, or network LLM
  request was used
- Import smoke: core runtime and V3 modules passed; direct `ui` import remains blocked
  on this Anaconda Python 3.13.5 host by the documented `gradio` segmentation fault
- V3.0.1 Phase 1 — Credits Domain: completed
- V3.0.1 Phase 1 Initial QA: `PASS WITH ISSUES` (Critical 0, Medium 3,
  Low 10, Blocking 0)
- V3.0.1 Phase 1.1 — Credits Domain Post-QA Hardening: completed; production Credits
  behavior unchanged
- Phase 1.1 freezes the privileged-operation boundary (M1), idempotency payload
  contract (M2), and Phase 2 SQLite atomic-commit requirement (M3).
- Phase 1.1 validation: Credits `66 passed`; full suite `195 passed`; offline
  LLM-contract smoke `6 passed`. No real API, Credential, network, Provider, LLM, UI,
  SQLite, or `managed_access/` work was used.
- V3.0.1 Phase 1 DeepSeek Directed Retest: `PASS WITH ISSUES` (Critical 0,
  Medium 0, Blocking 0; 3 non-blocking Low observations; 13/13 independent probes
  passed). M1 and M2 are closed; M3 is closed for Phase 1 and frozen as a Phase 2
  entry contract. No further Phase 1 retest is required.
- V3.0.1 Phase 1 Final QA: `PASS`.
- V3.0.1 Phase 1 Documentation Gate: `CLOSED`.
- Phase 1 reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_1.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_1.md`.
- Directed-retest Low disposition: L1 remains a Phase 2 structural-guard requirement;
  L2 is resolved by separating the V3.0.0 and V3.0.1 test baselines; L3 is resolved by
  the version-qualified Development and QA reports.
- Phase 1 QA Low findings remain deferred: `history_of` object-reference hardening,
  transaction-ID collision enforcement, private-container exposure, integer upper
  bounds, the global `RLock`, note normalization, hostile `str` subclasses, and
  validation-helper duplication.
- V3.0.1 Phase 2 — Managed Access Foundation: completed. It adds frozen
  `LLMAccessMode` and credential-free `LLMAccessContext`, a small `ManagedProvider`
  port, configurable positive-integer `FlatPricingPolicy`, SQLite-backed managed
  request state, and `ManagedAccessService` orchestration.
- Phase 2 request state is `RESERVED -> SUCCEEDED` on Provider and accounting success,
  or `RESERVED -> FAILED` on a Provider failure. `FINALIZATION_FAILED` is the limited
  reconciliation state for Provider success followed by accounting failure; its active
  reservation is retained and replay never invokes the Provider again.
- Managed request identity is `(normalized account_id, normalized request_id)`. A
  SHA-256 payload fingerprint detects reuse with a different credential-free model
  selection, prompt, or flat price. `SUCCEEDED` replay returns completion metadata but
  does not fabricate or persist the original Provider response; `FAILED` is terminal.
- `SQLiteCreditLedger` implements the Phase 1 `CreditLedger` contract using the Python
  standard library. `USAGE` and `REFUND` transaction append plus idempotency identity
  are committed in one SQLite transaction. Failure injection verifies rollback both
  after transaction append and after idempotency write, with no orphan record.
- Phase 2 uses active managed reservations rather than a new `TransactionType`.
  Available Credits are derived as ledger balance minus `RESERVED` and
  `FINALIZATION_FAILED` reservations. Provider calls run outside SQLite write
  transactions. Final `USAGE` plus `SUCCEEDED` state is committed atomically.
- Platform credentials remain inside the injected server-side Provider implementation.
  They do not enter access context, managed request/result, credit transactions,
  SQLite, logs, or public service representations. The Managed service public surface
  exposes no ledger, `grant`, `refund`, or `adjust` operation.
- Phase 2 validation: SQLite ledger `27 passed`; Managed Access `35 passed`; original
  Credits regression `66 passed`; BYOK Provider regression `19 passed`; full suite
  `257 passed`; offline LLM-contract smoke `6 passed`. All Provider tests used offline
  stubs; no real API, credential, or network request was used.
- V3.0.1 Phase 2 Initial DeepSeek QA: `PASS WITH ISSUES` (Product Critical 0,
  Product Medium 0, Release Blocker 0); full suite `257 passed`; independent probes
  `167/167 passed`. The Phase 2 product architecture passed independent validation.
- V3.0.1 Phase 2.1 — Managed Access Post-QA Regression Hardening: completed. C1 adds
  deterministic multi-service concurrency coverage over independent SQLite connections
  and service locks. C2 freezes the Provider-success/process-interruption window as a
  persistent `RESERVED` state requiring manual reconciliation and forbidding automatic
  Provider retry. C3 exercises actual `commit()` failure for both ledger idempotency and
  Managed finalization boundaries.
- Phase 2.1 L1 is resolved by requiring exactly one row for
  `RESERVED -> FINALIZATION_FAILED`; illegal transitions from `SUCCEEDED`, `FAILED`, or
  `FINALIZATION_FAILED` now raise `ManagedAccessError` instead of succeeding silently.
- Phase 2.1 also freezes restart behavior for terminal `FAILED` and
  `FINALIZATION_FAILED` requests, flat-price payload conflicts, and fixed-seed
  InMemory/SQLite ledger parity as formal regressions.
- Phase 2.1 validation: SQLite ledger `29 passed`; Managed Access `44 passed`; original
  Credits regression `66 passed`; BYOK Provider regression `19 passed`; full suite
  `268 passed`; offline LLM-contract smoke `6 passed`. All tests remained offline and
  used only fake credentials and Stub Providers.
- V3.0.1 Phase 2 DeepSeek Directed Retest: `PASS` (Product Critical 0,
  Product Medium 0, Release Blocker 0; independent probes `186/186 passed`). C1
  multi-service concurrency, C2 Provider-success crash-window safety, C3 commit-boundary
  atomicity, and L1 rowcount consistency are closed. No double charge, double Provider
  call, partial SQLite commit, reservation loss, Credential leak, or BYOK regression
  was found. No further production fix or directed retest is required.
- V3.0.1 Phase 2 Final QA: `PASS`.
- V3.0.1 Phase 2 Documentation Gate: `CLOSED`.
- Phase 2 reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_2.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_2.md`. Phase 2.1 is included in the Phase 2 reports.
- V3.0.1 Phase 3 — Usage Metering + PricingPolicy: completed. It adds immutable,
  Credential-free `UsageRecord`, `PricingContext`, and `ManagedProviderResponse`
  contracts plus a minimal `PricingPolicy` Protocol for reservation quotes and actual
  usage pricing. Zero-total-token usage is rejected; input-only and output-only usage
  remain valid.
- `TokenPricingPolicy` uses synthetic `Decimal` Credit rates per 1,000 tokens and
  converts the final amount to integer Credits with `ROUND_CEILING`. Floats, `bool`,
  negative values, NaN, Infinity, and an all-zero rate configuration are rejected.
  Stable versioned policy identities participate in Managed request payload identity.
- Token-priced Managed requests require an explicit provider/model/token-limit
  `PricingContext`. The priced limits form the pre-Provider reservation upper bound.
  Actual usage must match the provider and model, remain within the declared limits,
  and price to `0 <= actual_credits <= reserved_credits`.
- Provider success with missing, malformed, mismatched, over-limit, or over-reservation
  usage transitions to `FINALIZATION_FAILED`, retains the reservation, and is never
  automatically reinvoked. Successful reconciliation records only the actual `USAGE`
  charge; unused reservation capacity is released without a compensating refund.
- Phase 3 persists Credential-free usage metadata and final Credits in `managed_usage`.
  The `USAGE` transaction, Credit idempotency record, usage metadata, final Credits,
  and `SUCCEEDED` transition share one SQLite transaction. Phase 2 databases migrate
  in place, preserve existing ledger/request data, and retain compatible flat-price
  replay behavior.
- `FlatPricingPolicy` implements the new `PricingPolicy` contract while preserving the
  Phase 2 behavior: reservation equals final Credits, usage remains optional, and
  legacy string Provider responses remain supported. BYOK, UI, processor, and Provider
  foundation files remain unchanged.
- Phase 3 validation: Usage/Pricing and Managed token flow **55 passed**; original
  Managed Access regression **44 passed**; SQLite ledger **29 passed**; Credits
  regression **66 passed**; BYOK Provider regression **19 passed**; offline
  LLM-contract smoke **6 passed**; full suite **323 passed**. All tests were offline and
  used only synthetic rates, fake credentials, and Stub Providers.
- V3.0.1 Phase 3 Initial DeepSeek QA: `PASS WITH ISSUES` (Critical 0, Medium 1,
  Release Blocker 0). M1 found that token-price arithmetic depended on the ambient
  Decimal context and could undercharge under low precision. QA also verified that the
  Phase 3 core architecture passed and identified the recoverable SQLite migration
  autocommit window for immediate hardening.
- V3.0.1 Phase 3.1 — Pricing Determinism & Migration Hardening: completed. Token
  pricing now uses a dynamically sized local Decimal context with fixed
  `ROUND_CEILING`, independent of caller precision and rounding, while policy identity
  canonicalization no longer performs context-sensitive Decimal normalization.
- Phase 3.1 places all Managed schema changes, policy-identity backfill,
  `managed_usage` creation, and legacy usage initialization inside one
  `BEGIN IMMEDIATE` transaction. Real SQLite failure injection after the first
  alteration, during backfill, before usage-table creation, and during legacy usage
  initialization proves that DDL and data changes roll back together before a normal
  reopen completes the migration.
- Phase 3.1 regression coverage includes ambient Decimal precision/rounding matrices,
  large Decimal rates and token counts, a faithful Phase 2 schema fixture, five
  idempotent migration reopens, existing usage-metadata preservation, privacy scans of
  logical rows/dumps/database sidecars, zero-cost finalization atomicity, and Flat/Token
  request-identity conflicts in both directions.
- Phase 3.1 validation: Phase 3 pricing, token-flow, and hardening tests **75 passed**;
  original Managed Access regression **44 passed**; SQLite ledger **29 passed**;
  Credits regression **66 passed**; BYOK Provider regression **19 passed**; offline
  LLM-contract smoke **6 passed**; full suite **343 passed**. No real API, Credential,
  or network LLM request was used.
- V3.0.1 Phase 3 DeepSeek Directed Retest: `PASS` (Product Critical 0, Product
  Medium 0, Release Blocker 0; independent probes `137/137 passed`). M1 ambient
  Decimal-context determinism is resolved and the previous L1-L6 observations are
  closed. Evidence includes 11 precision settings by 8 rounding modes with zero drift,
  9,000 reservation cases with zero invariant violation, four atomic-migration failure
  points with complete rollback, 20 reopens with zero drift, and zero privacy-marker
  occurrences.
- Phase 3 Final QA: `PASS FOR PHASE 3`. No further production fix or directed retest
  is required. L7 initialization connection-close structure and L8 proactive validation
  of a malformed pre-existing `managed_usage` table remain Low, non-blocking, and
  deferred for future hardening.
- Phase 3 contracts are frozen: `UsageRecord`; `PricingPolicy`; Phase 2-compatible
  `FlatPricingPolicy`; deterministic `TokenPricingPolicy`; local Decimal pricing with
  `ROUND_CEILING`; reservation upper bounds; actual reconciliation;
  `FINALIZATION_FAILED` fail-closed behavior; provider/model integrity; private usage
  persistence; atomic finalization; atomic Phase 2-to-Phase 3 migration; and request
  fingerprint/pricing-policy identity.
- V3.0.1 Phase 3 Documentation Gate: `CLOSED`. The combined Phase 3 and Phase 3.1
  reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_3.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_3.md`.
- V3.0.1 Phase 4 — Admin Operations Surface: completed. It adds a trusted
  server-side `AdminCreditService` with immutable `AdminOperationContext` and
  `AdminOperationRecord` values plus the minimal `GRANT` and `ADJUSTMENT`
  `AdminOperationType` values.
- Phase 4 administrative operation identity is `(normalized actor_id, normalized
  operation_id)`. Exact replay returns the persisted audit record without another
  Credit mutation, while any change to operation type, normalized account, amount,
  or normalized non-empty reason raises `AdminOperationConflictError`.
- Phase 4 persists normalized administrative audit metadata in
  `admin_credit_operations`. Each `ADMIN_GRANT` or `ADJUSTMENT` Credit transaction
  and its immutable admin audit row share one `BEGIN IMMEDIATE` SQLite transaction;
  failure injection and commit-failure coverage prove all-or-nothing rollback and
  safe retry.
- `AdminCreditService.balance()` and `history()` expose only an integer balance and
  immutable Credit transaction tuple. The service does not return a `CreditLedger`,
  and `ManagedAccessService` continues to expose no grant, adjust, refund, ledger, or
  Admin service capability.
- Phase 4 validation: Admin Operations **51 passed**; Phase 3 pricing/token-flow and
  hardening **75 passed**; Managed Access **44 passed**; SQLite ledger **29 passed**;
  Credits **66 passed**; BYOK Provider **19 passed**; offline LLM-contract smoke
  **6 passed**; full suite **394 passed**. No real API, Credential, Provider-network,
  or network LLM request was used.
- Phase 4 Initial DeepSeek QA: `PASS WITH ISSUES` (Critical 0, Medium 1, Low 3,
  Release Blocker 0). M-1 demonstrated that hostile `str` subclasses could bypass
  Admin actor/operation normalization and create a duplicate Grant. The Phase 4 core
  idempotency, atomicity, audit, foreign-key, concurrency, restart, migration, and
  Credential-boundary behavior passed independent validation.
- V3.0.1 Phase 4.1 — Admin Identity & Persistence Hardening: completed. The Admin
  boundary now accepts only exact built-in strings before trimming actor ID,
  operation ID, account ID, and reason, so caller-defined `strip`, equality, hash,
  string conversion, and representation behavior cannot influence Admin identity,
  replay comparison, or SQLite keys. Normal built-in whitespace normalization is
  unchanged.
- Phase 4.1 adds an Admin persistence guard for SQLite signed 64-bit Credit amounts.
  Out-of-range grants and adjustments raise `InvalidCreditAmountError` before any
  write and leave the operation identity reusable. Executable regression coverage
  also verifies `PRAGMA foreign_keys = 1` on the service connection and rejects an
  audit row whose Credit transaction does not exist.
- Phase 4.1 validation: Admin Operations **71 passed**; Phase 3 pricing/token-flow and
  hardening **75 passed**; Managed Access **44 passed**; SQLite ledger **29 passed**;
  Credits **66 passed**; BYOK Provider **19 passed**; offline LLM-contract smoke
  **6 passed**; full suite **414 passed**. All validation remained offline and used no
  real API, Credential, Provider-network, or network LLM request.
- V3.0.1 Phase 4 DeepSeek Directed Retest: `PASS` (Product Critical 0, Product
  Medium 0, Release Blocker 0; independent assertions `159 passed`; full suite
  `414 passed`). M-1 is resolved: hostile actor/operation subclasses are rejected
  before caller-defined identity behavior, with zero additional writes and zero
  hostile-method executions. Exactly-once replay, multi-service concurrency, restart,
  foreign-key enforcement, five atomic rollback boundaries, and Credential privacy
  passed independent validation. No further production fix or directed retest is
  required.
- Phase 4.1 resolves M-1 and hardens L-1 SQLite integer-range validation. L-2
  close-after-use exception wrapping remains deferred. Cumulative SQLite `SUM(amount)`
  overflow from multiple individually valid transactions remains a non-blocking member
  of the existing integer-upper-bound technical-debt family; it can make the affected
  account query fail but does not corrupt data, duplicate a Grant, break atomicity, or
  affect other accounts.
- Phase 4 contracts are frozen: `AdminOperationContext`, `AdminOperationType`,
  `AdminOperationRecord`, `AdminCreditService`, exact built-in string identity,
  `(actor_id, operation_id)` idempotency, Credit plus audit atomicity, foreign-key
  enforcement, grant/adjustment semantics, the Managed privileged boundary, refund
  non-exposure, and the Admin SQLite signed-64 amount guard.
- V3.0.1 Phase 4 Final QA: `PASS FOR PHASE 4` (Critical 0, Medium 0, Release
  Blocker 0). Phase 4 Documentation Gate: `CLOSED`. The combined Phase 4 and Phase 4.1
  reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_4.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_4.md`.
- Phase 4 does not expose `refund()`. Admin UI is `SKIPPED FOR V3.0.1` and remains a
  possible future enhancement. Optional Phase 5 Payment Interface Reservation is
  `SKIPPED FOR V3.0.1`; Payment, recharge, and `PURCHASE` remain unimplemented and may
  be reconsidered for V3.0.2 or a future commercial enhancement.
- V3.0.1 Phase 1 provides immutable `CreditAccount` and `CreditTransaction` domain
  objects, the minimal `CreditLedger` protocol, and a thread-safe
  `InMemoryCreditLedger`.
- The Phase 1 ledger is append-only and authoritative; integer Credit balances are
  derived from transaction records rather than a second authoritative balance store.
- `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT` are implemented with typed domain
  failures, failed-operation atomicity, `(account_id, request_id)` charge/refund
  idempotency, and same-account debit serialization under an `RLock`.
- Phase 1 remains fully offline and Provider-independent. It adds no Credential, LLM,
  Provider, UI, SQLite, network, pricing, or managed-access dependency.
- Phase 1 completion baseline: Credits `50 passed`; full suite `179 passed` with the documented
  current-host `python -m pytest -p no:debugging` workaround.
- Next: V3.0.1 RC / Release Engineering. RC work has not started.
- V3.0 roadmap:
  - Phase 0 — Engineering Baseline: completed
  - Phase 1 — Domain Core & Stable Symbol Identity: completed
  - Phase 2 — Processor Symbol Migration: completed
  - Phase 3.1 — Project Discovery / Project Scanner: completed
  - Phase 3.2 — Project Relationship Awareness / Project Graph: completed
  - Phase 3.2.1 — Graph Identity & Containment Hardening: completed
  - Phase 3.3 — Project Snapshot / State: completed
  - Phase 3.3.1 — Snapshot Post-QA Hardening: completed
  - V3 Core Architecture Review: frozen by the Phase 4 architecture decisions
  - Phase 4 — Project Analysis Engine: completed
  - Phase 4.0.1 — Analysis Engine Post-QA Hardening: completed
  - Phase 4 Documentation Gate: completed
  - Phase 4.1 — Provider / BYOK Foundation: completed
  - Phase 4.1.1 — Legacy Provider Atomicity Hardening: completed
  - Phase 4.1 Documentation Gate: completed
  - V3.0 RC1.1 — Release Engineering Gate: completed (`PASS WITH ISSUES`)
  - V3.0 RC1.2 — Repository Hygiene Gate: completed (`PASS WITH CLEANUP RECOMMENDED`)
  - V3.0 RC1.3 — Product Documentation & README V3: completed
  - V3.0 RC1.4 — Full-System Release QA: completed (`PASS`)
  - V3.0 RC1.5 — Claude Final Release Review: completed (`APPROVE WITH NON-BLOCKING NOTES`)
  - V3.0.0 — released
  - V3.0.1 Phase 0.0 — Development Baseline: completed
  - V3.0.1 Phase 0.1 — Architecture Decision Documentation: completed
  - V3.0.1 Phase 0 — Architecture & Scope Documentation Gate: completed
  - V3.0.1 Phase 1 — Credits Domain: completed
  - V3.0.1 Phase 1.1 — Credits Domain Post-QA Hardening: completed
  - V3.0.1 Phase 1 Documentation Gate: closed (`PASS`)
  - V3.0.1 Phase 2 — Managed Access Foundation + SQLite + flat pricing: completed
  - V3.0.1 Phase 2.1 — Managed Access Post-QA Regression Hardening: completed
  - V3.0.1 Phase 2 Documentation Gate: closed (`PASS`)
  - V3.0.1 Phase 3 — Usage Metering + token PricingPolicy: completed
  - V3.0.1 Phase 3.1 — Pricing Determinism & Migration Hardening: completed
  - V3.0.1 Phase 3 Documentation Gate: closed (`PASS`)
  - V3.0.1 Phase 4 — Admin Operations Surface: completed; Final QA `PASS FOR PHASE 4`
  - V3.0.1 Phase 4.1 — Admin Identity & Persistence Hardening: completed
  - V3.0.1 Phase 4 Documentation Gate: closed (`PASS`)
  - V3.0.1 — Managed AI Access & Credits: in development
  - V3.1 — Project Intelligence / RAG: planned
  - V3.2 — Multi-Agent: planned
  - V3.3 — Data-driven Model Router: planned
  - V3.4 — VS Code Integration + Secure Credential UI: planned
- Released product version: `3.0.0`
- V3.0.0 Final Release Gate: `PASS`
- Release Blockers: `0`
- Medium: `0`
- V3.0.0 released test baseline: `129 passed`
- Current V3.0.1 development test baseline: `414 passed`
- Current V3.0.1 Admin Operations tests: `71 passed`
- Current V3.0.1 Managed Access tests: `44 passed`
- Current V3.0.1 Phase 3 Usage/Pricing, token-flow, and hardening tests: `75 passed`
- Current V3.0.1 SQLite ledger tests: `29 passed`
- Current V3.0.1 Credits tests: `66 passed`
- Current V3.0.1 BYOK Provider tests: `19 passed`
- Current offline LLM-contract smoke: `6 passed`
- Phase 3.1 QA: `PASS` (Critical 0, Medium 0, Low observations 8; 12 independent probes passed)
- Phase 3.2: `Completed`
- Phase 3.2.1 hardening: `Completed`
- Phase 3.2 QA: `Final PASS` (initial `PASS WITH ISSUES`; D1/D2 verified in retest)
- Graph identity contract: `Preserved by Phase 3.3.1`
- Phase 3.3: `Completed`
- Phase 3.3 QA: `PASS WITH ISSUES` (Critical 0; M1/M2 resolved in Phase 3.3.1)
- Phase 3.3.1 Snapshot Post-QA Hardening: `Completed`
- Phase 3.3 DeepSeek directed retest: `PASS` (M1 PASS; M2 PASS; Golden Hash PASS)
- Phase 3.3 Final QA: `PASS` (further retest not required)
- Phase 4: `Completed`
- Phase 4 Independent QA: `PASS WITH ISSUES` (Critical 0; M1/M2 resolved in Phase 4.0.1)
- Phase 4.0.1 M1 finding validation/isolation: `Resolved`
- Phase 4.0.1 M2 recursion-depth-dependent SCC: `Resolved`
- Phase 4 DeepSeek directed retest: `PASS` (M1 PASS; M2 PASS; caller-stack independence PASS; fan-out regression PASS; determinism PASS)
- Phase 4 Final QA: `PASS` (further retest not required)
- Phase 4 tests: `32 passed`
- Offline LLM-contract smoke: `6 passed`
- Phase 4.1: `Completed`
- Phase 4.1 BYOK foundation: immutable credential-free `ModelConfig`, redacted
  runtime-only `RuntimeCredential`, read-only `ProviderRegistry`, and task-scoped
  provider/client construction over the existing Provider set
- Phase 4.1 task isolation: processor, analysis, batch, progress, preflight, retry,
  and direct LLM-service paths can use one explicitly captured provider/client without
  rereading mutable legacy active state during the task
- Phase 4.1 legacy compatibility: existing `switch_provider()`, `set_api_key()`,
  active getters, and Gradio UI remain available as a bridge that configures future
  task contexts
- Phase 4.1 security: credentials are excluded from `ModelConfig`, ordinary
  serialization, workspace persistence, provider/client representations, and sanitized
  provider error messages
- Phase 4.1 Independent QA: `PASS WITH ISSUES` (M1 directed for Phase 4.1.1)
- Phase 4.1.1: `Completed`
- Phase 4.1.1 M1 legacy Provider atomicity: `Resolved`
- Legacy Provider update contract: success atomically commits the complete active state;
  failure leaves every active scalar, client, and task-scoped provider unchanged
- Phase 4.1 tests: `19 passed`
- Phase 4.1 DeepSeek Directed Retest: `PASS`
- Phase 4.1 Final QA: `PASS` (Critical 0, Medium 0; further retest not required)
- Phase 4.1 Documentation Gate: `CLOSED`
- BYOK foundation: `Completed`; workspace persistence and `code_maintenance/` remain
  Credential/Provider-free at their respective persistence and domain boundaries
- Release metadata source: `code_maintenance.__version__ = "3.0.0"`
- Python support: minimum and recommended `3.10`; CI validates Python 3.10
- RC1.1 clean install: `PASS` in a repository-external Python 3.13.7 virtual
  environment; install, import, startup, dependency, and 129-test gates passed
- RC1.1 host note: the existing Anaconda Python 3.13.5 installation segfaults while
  importing both `gradio` and `rlcompleter`; this is isolated from the clean
  environment and is non-blocking for the release
- RC1.1 security and portability checks: `PASS`; no tracked credential, workspace,
  cache, junk file, or production/user-document local absolute path was found
- RC1.2 repository hygiene: `PASS WITH CLEANUP RECOMMENDED`; Release Blockers `0`,
  no tracked delete candidate, and no directory restructuring approved for RC1
- V3.0.0 Feature Freeze: completed
- RC1.3 product documentation: completed; README V3 now records current product
  positioning, available capabilities, BYOK boundaries, V3.0.1 planned credits,
  installation and configuration, the permanent Version History policy, Python 3.10+
  support, and the 129-test RC baseline
- RC1.3 repository hygiene: completed; the RC1.2-approved narrow coverage and local
  workspace ignore rules were added without broad JSON or archive patterns
- RC1.4 full-system release QA: completed; verdict `PASS`, Release Blockers `0`,
  Medium `0`, Low `6` (all non-blocking)
- RC1.4 test baseline: `129 passed` in both the development environment and the
  repository-external clean virtual environment
- RC1.4 clean venv: `PASS`; install and `pip check` passed with no network failure and
  no repository dependency failure
- RC1.4 gates: clean install, README command validation, no-credential startup, BYOK
  user flow, legacy feature integration, V3 Core integration, provider isolation and
  security, version consistency and history, roadmap accuracy, repository hygiene,
  directory consistency, CI, and startup smoke all `PASS`
- RC1.5 Claude Final Release Review: completed; verdict
  `APPROVE WITH NON-BLOCKING NOTES`, Release Blockers `0`
- RC1.4 QA artifact: the RC1.5 review found the RC1.4 QA report missing from the
  repository; the report was recorded as `docs/qa/QA_Report_RC1_4_Full_System_Release.md`
  to close the Release QA Documentation Gate without changing product code, tests,
  README, or version metadata
- Final Release Gate: `PASS`; V3.0.0 is released with version `3.0.0`
- Current-host validation: Anaconda Python 3.13.5 retains the known interpreter /
  pytest debugging-plugin issue; `python -m pytest -p no:debugging` passes all 129 tests
- Standard-environment evidence: RC1.4 records `python -m pytest` with `129 passed`
  under standard CPython / clean venv; the host-specific issue is not a release blocker
- Current development version: V3.0.1 — Managed AI Access & Credits (`IN DEVELOPMENT`)

## Planned Version Roadmap

### V3.0.0 — Released

V3.0.0 is the released stable Project-level Maintenance Core Foundation. It contains
the completed V3 core and BYOK foundation.

### V3.0.1 — Managed AI Access & Credits

Status: **IN DEVELOPMENT**. Phase 1 — Credits Domain, Phase 2 — Managed Access
Foundation + SQLite + flat pricing, Phase 3 — Usage Metering + PricingPolicy, Phase
3.1 hardening, Phase 4 — Admin Operations Surface, and Phase 4.1 Admin Identity &
Persistence Hardening are completed. The Phase 2
Documentation Gate is closed with Final QA `PASS`; Phase 3 Initial QA returned
`PASS WITH ISSUES`, Phase 3.1 resolved M1, the directed retest returned `PASS`, and the Phase
3 Documentation Gate is closed with Final QA `PASS FOR PHASE 3`. Phase 4 Initial QA
returned `PASS WITH ISSUES`; Phase 4.1 resolved M-1, the directed retest returned
`PASS`, and the Phase 4 Documentation Gate is closed with Final QA
`PASS FOR PHASE 4`. V3.0.1 is not part of the V3.0.0 release.

V3.0.1 is intended to preserve BYOK while optionally allowing users without their own
API configuration to use platform-managed AI access. Planned capabilities are:

- BYOK mode remains available;
- optional platform-managed AI access;
- `CreditAccount` and `CreditLedger` concepts;
- administrative credit grants;
- usage metering;
- a `PricingPolicy` abstraction;
- a reserved recharge/payment interface.

Phase 1 supports `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT`. `PURCHASE` and
payment-provider integration remain outside Phase 1 and are interface reservations
rather than mandatory V3.0.1 integrations.

The platform Provider credential must never be delivered to a client or written into
a plugin, frontend, ordinary configuration file, or client package. Managed mode must
use this server-side boundary:

`Client -> Platform Backend -> Authentication / Credit Check -> Server-side Provider Credential -> LLM Provider`

### Later Planned Versions

- V3.1 — Project Intelligence / RAG: **PLANNED**
- V3.2 — Multi-Agent: **PLANNED**
- V3.3 — Data-driven Model Router: **PLANNED**
- V3.4 — VS Code Integration + Secure Credential UI: **PLANNED**

## Current Architecture

Current domain: `Project`, `SourceFile`, `Symbol`, `SymbolId`, `AnalysisFinding`.

`PythonAdapter` and `JavaAdapter` reuse the existing parsers. `SymbolId` is:

`language + relative_path + qualified_name + kind + semantic_disambiguator`

For Java overloads, `semantic_disambiguator` uses the normalized parameter signature. `fallback_line` is collision fallback only. `content_hash` is not part of normal identity.

Processor concurrency results, errors, annotated-source backfill, Markdown document
association, and navigation anchors use `SymbolId` as their internal identity key.

`ProjectScanner` builds a read-only `ScanResult` containing the project, directories,
files, detected languages, applied ignore rules, metadata, per-file hashes, and a
deterministic aggregate project hash. It does not perform code analysis.

`ProjectGraphBuilder` builds a deterministic in-memory `ProjectGraph` from a
`ScanResult`. Graph nodes are `PROJECT`, `FILE`, `SYMBOL`, and `EXTERNAL_MODULE`;
relations are limited to `CONTAINS` and `IMPORTS`. Project, file, and symbol identities
reuse `Project.id`, `ProjectFile.relative_path`, and `SymbolId`. Python imports are
discovered with the standard AST, while Java package and import discovery remains
best-effort compatibility without a parser framework. Exact, unique local module/type
matches resolve to file nodes; all other import targets remain deterministic unresolved
external-module nodes.

Class containment is attributed with the existing symbol source ranges and the parent
class `SymbolId`, rather than treating a bare qualified class name as unique. Python
relative imports use their importer package context to produce canonical graph
identities before local resolution; imports without a reliable package context use a
deterministic unresolved-relative identity instead of a guessed module.

`SnapshotBuilder` builds an immutable in-memory `ProjectSnapshot` from a `ScanResult`
and the existing `ProjectGraph`. Snapshot file state uses normalized relative paths and
file content hashes; symbol state reuses `SymbolId` and `Symbol.content_hash`. Snapshot
content identity is a SHA-256 hash of an explicit canonical representation containing
the project identity, sorted file and symbol states, and sorted graph nodes and edges.
It excludes `created_at`, file mtimes, random values, object representations, and Python
hash values. `SnapshotDiff` compares snapshots from the same project root and reports
added, removed, changed, and unchanged files and symbols. Snapshot serialization is
limited to an in-memory `to_dict()` representation; no persistence layer exists.

`AnalysisEngine` is a deterministic service, not an Agent, over an existing
`ProjectSnapshot`. Each `AnalysisTool` is deterministic and read-only and consumes
only existing Snapshot/Graph state without reparsing source. The engine runs a small
ordered collection of tools, isolates each tool failure,
validates every returned `AnalysisFinding`, and canonically orders each tool's complete
output inside that tool's isolation boundary before final aggregation. A failed or
malformed tool produces a project-level `analysis.tool_failure` finding while the
remaining tools continue. Finding validation covers the string fields, integer line,
and optional `SymbolId` fields required by canonical ordering. Failure messages contain
only the stable tool id and exception type. The engine and tools do not scan, read
files, parse source, call adapters, use the network, or call an LLM.

Phase 4 provides `ComplexityTool`, `StructureTool`, and `DependencyTool`.
`ComplexityTool` reports direct method concentration per class from graph containment;
`StructureTool` reports per-file symbol density from snapshot symbol state; and
`DependencyTool` reports internal import cycles and high import fan-out from existing
`IMPORTS` edges. Dependency cycle detection uses deterministic iterative strongly
connected-component traversals and does not depend on Python's recursion limit. The
stable rule ids are `complexity.class_method_count`,
`structure.symbol_density`, `dependency.cycle`, `dependency.concentration`, and the
engine-owned `analysis.tool_failure`. Quality findings use `warning`; tool execution
failures use `error`.

`AnalysisFinding` scope conventions are: project-level findings use
`relative_path=""`, `line=0`, and `symbol_id=None`; file-level findings use the actual
relative path, an actual line or `0`, and `symbol_id=None`; symbol-level findings use
`Symbol.relative_path`, `Symbol.start_line`, and `Symbol.id`. Phase 4 keeps the existing
schema unchanged. Rule ids are deterministic, stable, lowercase machine-readable
dotted names.

`graph.py` owns the canonical graph node and edge ordering used by both
`ProjectGraphBuilder` and `SnapshotBuilder` through `canonicalize_graph()`; it is the
single source of truth for ProjectGraph canonical ordering. A graph built directly from
a scan is equal to the graph stored in its snapshot. Python parse boundaries skip
file-level symbol and import extraction on `SyntaxError` or `ValueError`, while
retaining the scanned file state and continuing to process other files.

`SourceFile.content_hash` hashes the entire file content. `Symbol.content_hash` hashes the
source slice returned for that symbol; neither hash is part of `SymbolId`.

## Known Debt and Boundaries

- The legacy Python parser does not extract nested functions or local classes inside functions.
- Java signature normalization is deterministic best-effort canonicalization for the
  parameter declarations currently needed by V3.0, not a complete Java compiler
  signature parser. The legacy regex parser guarantees only basic overload and
  parameter-declaration handling.
- V3.0 does not add RAG, Multi-Agent, Router, API, or VS Code integration; do not rewrite the Java parser. Migrate incrementally and keep Gradio working.
- Processor retains separate synchronous and progress-reporting pipelines; changes to
  processing stages must keep both paths behaviorally aligned.
- The legacy Java annotator is line-oriented: when several declarations share one
  physical line, their identities and documentation remain distinct, but generated
  Javadocs are inserted above the shared line rather than directly before each declaration.
- Project Scanner applies built-in rules, root `.gitignore`, and caller rules with a
  deterministic Gitignore-like subset. Nested ignore files and full Git ignore
  semantics are not implemented; symlinks are deliberately not followed.
- The Project Graph does not infer calls, references, inheritance, or wildcard/static
  import ownership. Python local resolution uses project-root module paths only; Java
  resolution requires an exact unique package/type match. Unmatched targets are
  unresolved rather than claimed to be third-party dependencies.
- Self-imports currently produce explicit self-loop `IMPORTS` edges. Star imports remain
  coarse targets such as `a.*`, and external-module nodes do not model package members.
- Python `src` layouts, `pyproject` packaging semantics, namespace-package semantics,
  installed packages, and complete import resolution remain deferred.
- Root `__init__.py` relative imports retain a narrow precision gap because the project
  root does not provide a reliable package name.
- `Project.id` depends on the resolved absolute project root path. The first Phase 3.3
  Snapshot version defaults to time-series comparison under the same project root.
- Phase 3.3 QA M3 remains deferred: case-sensitive absolute-path spelling can affect
  `Project.id`; resolving it would change the frozen project identity contract.
- Snapshot construction reads supported source files again to capture symbol content;
  Phase 3.3 QA M4 remains a known limitation because concurrent filesystem changes
  during a scan/build sequence are not made atomic.
- Phase 3.3 QA L1 remains deferred: validation of an explicitly supplied `graph=` checks
  its project node identity but does not exhaustively validate every node and edge.
- Phase 3.3 QA L2/L3 retain the current content semantics: a class symbol's content hash
  includes its method bodies, so a method-body edit can mark both method and class as
  changed.
- Low maintenance note: `graph.py` and `snapshot.py` retain duplicate
  `_symbol_id_record` and `_node_record` implementations. This remains deferred and was
  not changed by Phase 4.
- Snapshot comparison is state comparison by file and symbol identity/content hash; it
  does not provide semantic diffs, AST edit scripts, history, repositories, or storage.
- Function/method source size, cyclomatic complexity, oversized-file byte/line rules,
  and source-text style rules are deferred because `ProjectSnapshot` does not retain
  the required source ranges, file sizes, or source text. Phase 4 does not reread or
  reparse source and does not expand the frozen Snapshot contract for these metrics.
- Symbol-level Phase 4 findings that require `Symbol.start_line` are deferred for the
  same reason. The implemented class-method concentration rule is reported at file
  scope with line `0` and identifies the class in its deterministic message.
- A Phase 4 `StyleTool` is deferred because no reliable style rule can be proved from
  the current `ProjectSnapshot`, `FileState`, `SymbolState`, and `ProjectGraph` data
  without reading source text.
- Phase 4 QA Low / technical debt remains deferred: the
  `structure.symbol_density` rule id, Finding deduplication, duplicate tool-id
  enforcement, missing `tool_id` behavior, `_symbol_id_key` helper duplication, and
  `TYPE_CHECKING` import cleanup. R1 retains the hostile cross-tool `str` subclass
  final-sort edge case, and R2 retains the hostile mutable `tool_id` failure-report
  edge case. These items do not block Phase 4.1.
- Dependency semantics beyond imports, graph persistence/databases, RAG, and
  incremental graph updates remain outside the current implementation.
- Phase 4.1 provides only an in-memory runtime credential boundary. It does not provide
  Keychain, Secret Service, Vault, encryption, database persistence, or credential UI;
  secure IDE credential storage remains deferred to V3.4.
- The legacy Gradio Provider selection remains process-level state for compatibility.
  Each started task now captures an isolated provider/client, while per-session UI
  configuration state remains future work.
- Provider clients still use the existing OpenAI-compatible SDK surface. Phase 4.1 adds
  no Provider, automatic selection, fallback policy, benchmark, model scoring, or Router.
- Phase 4.1 QA Low issues remain deferred: preflight price-footer presentation (L1),
  a dedicated `TaskScopedLLMProvider` serialization guard (L2), broader `base_url`
  validation (L3), unused public Provider APIs (L4), and normalized Registry errors for
  malformed metadata instead of raw `KeyError` (L5).
- Phase 4.1 QA note N1 remains deferred: `get_models_for_provider()` reads the custom
  model name without acquiring the active-state lock.
- Phase 2 persistence and locking are single-process foundations, not distributed
  coordination. A stranded `RESERVED` request and `FINALIZATION_FAILED` request require
  reconciliation; Phase 2 intentionally provides no automatic retry or admin recovery
  workflow. The original Provider response is not persisted, so successful replay
  returns metadata only. Real Usage Metering, token pricing, Payment, Admin UI, and a
  production HTTP backend remain unimplemented.
- Phase 2 QA Low L2 remains deferred: a BYOK context with `account_id=""` continues to
  fail closed with the existing credit-domain exception type rather than a normalized
  Managed Access exception.
- Phase 2 QA Low L3 remains deferred: no
  `managed_requests(account_id, status)` performance index is added until managed
  request volume justifies it.
- Phase 2 QA Low L4 remains deferred with the Phase 1 integer-upper-bound observation:
  `FlatPricingPolicy` accepts any positive Python integer and has no artificial maximum.
- Phase 2 mutation-review coverage note remains deferred: the existing defensive
  `rowcount` guards for the `SUCCEEDED` update in `_finalize_success()` and the `FAILED`
  update in `_mark_provider_failed()` do not have direct mutation-targeted regressions.
  Their defensive branches are unreachable through the normal state machine and this
  is a Low coverage observation, not a product defect.

## Frozen Decisions

### Phase 3.3 Graph Identity Contract

- `PROJECT`, `FILE`, and `SYMBOL` identities continue to reuse `Project.id`, normalized
  relative paths, and `SymbolId`.
- Class containment uses existing symbol ranges to select the enclosing class and links
  through that class's `SymbolId`.
- Canonical Python import targets are used for both internal resolution and unresolved
  external-module identity.
- Phase 3.3 does not treat the current location-dependent `Project.id` as a portable
  cross-machine identity.

### BYOK / Credential & Provider Policy

- Official releases do not include a developer API key.
- Users configure their own Provider, Model, and Credential.
- API keys must not enter Git, ordinary configuration files, or logs.
- Phase 4.1 established the Provider/BYOK Foundation.
- `ModelConfig` is immutable ordinary configuration and remains credential-free.
- `RuntimeCredential` is runtime-only and excluded from ordinary serialization,
  workspace persistence, and non-redacted representations.
- `TaskScopedLLMProvider` is captured once per task; later legacy global switches do
  not alter an already-started task.
- Legacy Provider updates use atomic semantics: success commits the complete active
  state, while failure performs no active-state mutation.
- Workspace persistence remains credential-free, and `code_maintenance/` remains free
  of Provider, Credential, OpenAI SDK, and LLM dependencies.
- A future Router uses only providers already configured by the user.
- No secure credential store exists in Phase 4.1; the V3.4 IDE stage provides the
  secure credential-configuration UI.

### V3.0.1 Managed AI Access & Credits

- The access modes are `BYOK` and `MANAGED`. The frozen minimum contract for a future
  `LLMAccessContext` contains `mode: LLMAccessMode`, `model_config: ModelConfig`,
  `account_id`, and `request_id`. `account_id` and `request_id` are optional for BYOK
  and required for MANAGED. The context never owns a client, Provider,
  `TaskScopedLLMProvider`, `RuntimeCredential`, or any credential.
- The V3.0 BYOK architecture remains unchanged and independent of Credits: BYOK does
  not check or deduct Credits.
- Managed mode uses a process-local, backend-facing `ManagedAccessService`; V3.0.1 does
  not establish a production HTTP backend. The platform credential remains server-side
  and must not enter UI state, workspace data, ordinary configuration, credit records,
  logs, or `LLMAccessContext`.
- A Managed client or UI caller must never receive the platform `RuntimeCredential`,
  platform `TaskScopedLLMProvider`, raw Provider client, or platform API key. A future
  `ManagedAccessService` may return only safe results and safe usage/accounting metadata.
- `credits/` and `managed_access/` are new top-level peers of `code_maintenance/`.
  `managed_access/` may depend on `credits/` and existing Provider infrastructure.
  Reverse dependencies into `credits/`, dependencies from `code_maintenance/` to either
  new package, and Provider-infrastructure dependencies on `credits/` are prohibited.
- The credit ledger is append-only and authoritative. Phase 1 derives balance from the
  transaction sum, uses integer Credit units, and uses `Decimal` rather than `float` for
  real monetary values or costs.
- Every transaction amount is a nonzero integer: `ADMIN_GRANT > 0`, `USAGE < 0`,
  `REFUND > 0`, and `ADJUSTMENT` may be positive or negative but not zero.
- Phase 1 transaction types are `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT`;
  `PURCHASE` is excluded. User identity is only an opaque `account_id: str`.
- Phase 1 implements immutable `CreditAccount` and `CreditTransaction` values, the
  minimal `CreditLedger` protocol, and a thread-safe `InMemoryCreditLedger`.
- Charge and refund operations are idempotent within their operation type by
  `(account_id, request_id)`; conflicting retries fail without mutating history or the
  idempotency index. Grants and safe adjustments append new audit records.
- `grant()`, `refund()`, and `adjust()` are privileged domain operations available only
  to trusted server-side or admin-side orchestration. They must not be exposed directly
  to a client, Gradio UI, Managed caller, or ordinary user-facing API; Phase 2
  `ManagedAccessService` must not expose these methods or a ledger object.
- Phase 1 `refund()` is a low-level positive accounting primitive. Its `request_id`
  identifies the refund operation rather than an original `USAGE`, and Phase 1 does
  not reconcile usage. Any Phase 2 user-facing or Managed refund must first identify
  the original `USAGE`, authorize the refund, and prevent repeated refund against the
  same authorized usage before internally calling `CreditLedger.refund()`.
- Idempotency lookup identity is `(operation_type, normalized account_id, normalized
  request_id)` for `USAGE` and `REFUND`, which have independent namespaces. A valid
  replay must preserve amount and exact note and returns the original transaction;
  changed amount or note raises `IdempotencyConflictError`. Note is a payload
  consistency field, not a lookup key, and Phase 2 retries must preserve it.
- The in-memory ledger uses an `RLock` so idempotency checks, balance prechecks, and
  appends share one critical section. All rejected operations preserve balance,
  history, and idempotency state.
- A `USAGE` charge is idempotent by `(account_id, request_id)`. The Phase 2 charging
  contract is per-account guarded charge-after-success: precheck balance, invoke the
  Provider, and charge only after success; Provider failure is not charged.
- Phase 1 uses the minimal `CreditLedger` Protocol and in-memory implementation and defines no
  `PricingPolicy`, flat pricing, token pricing, or cost conversion. It remains completely
  offline and must not import or call LLM or Provider infrastructure. Phase 2 adds
  standard-library SQLite and flat pricing. Phase 3 adds Provider/model/token-based
  `PricingPolicy` and freezes `Decimal` cost-to-integer-Credits conversion with
  `ROUND_CEILING`.
  No ORM, distributed database, distributed transaction, or hard-coded commercial
  exchange ratio is authorized.
- Phase 2 SQLite must atomically commit the ledger transaction append and idempotency
  record in one SQLite transaction. Partial commit in either direction is prohibited,
  and Phase 2 QA must verify all-or-nothing behavior with failure injection.
- Phase 2 entry requirements are implemented: Managed clients cannot access `grant`,
  `refund`, or `adjust`; no user-facing refund is exposed; SQLite transaction append
  and idempotency-record write are atomic; and retries preserve the complete
  idempotency payload contract. Failure injection covers rollback on both sides of the
  transaction/idempotency boundary.
- Phase 4 adds the trusted server-side `AdminCreditService` as the only administrative
  Credits entrypoint in this phase. It exposes `grant`, `adjust`, `balance`, and
  immutable Credit `history`, but no public refund and no ledger object. Admin identity
  is `(normalized actor_id, normalized operation_id)` and the complete business payload
  is conflict-checked on replay.
- Phase 4.1 freezes the Admin identity boundary to exact built-in strings before
  normalization and persistence. It also rejects amounts outside SQLite's signed
  64-bit INTEGER range before opening an Admin write and formally verifies that the
  service connection enforces the Admin audit foreign key.
- The Phase 4 `admin_credit_operations` audit row and corresponding Credit transaction
  commit atomically in one SQLite transaction. `BEGIN IMMEDIATE` serializes independent
  service connections so same-operation concurrency mutates exactly once and different
  operations retain balance safety. The admin schema migrates and reopens idempotently
  without changing existing ledger, Managed request, or usage data.
- The frozen V3.0.1 sequence is Phase 0 Architecture & Scope; Phase 1 Credits Domain and
  domain grant; Phase 2 Managed Access Foundation, SQLite, and flat pricing; Phase 3
  Usage Metering and token pricing; Phase 4 Admin Operations Surface; optional Phase 5
  Payment Interface Reservation; then RC. Phases 1 through 4.1 and the Phase 4
  Documentation Gate are completed. Optional Phase 5 is skipped for V3.0.1; RC /
  Release Engineering is next and has not started.
- The timeout case where a Provider succeeded but the caller observed a timeout remains
  an explicit known limitation; V3.0.1 does not build distributed transaction machinery.
- Phase 3 extends Flat Pricing into Usage Metering and `PricingPolicy` while preserving
  the Phase 2 reservation state machine, SQLite all-or-nothing atomicity,
  Managed request idempotency and payload identity, the server-side Credential
  boundary, and BYOK isolation from Credits and Managed Access.
- V3.0.1 is an engineering-completeness enhancement. After the
  `ADMIN_GRANT -> Managed AI -> USAGE -> Ledger` loop is complete, thesis priority moves
  to V3.1 RAG and V3.2 Multi-Agent rather than commercial expansion.

### V3.0.1 Report Naming Policy

- Starting with V3.0.1, new Development and QA report filenames must include the
  version, for example `Development_Report_V3_0_1_Phase_1.md` and
  `QA_Report_V3_0_1_Phase_1.md`.
- Do not create unversioned V3.0.1 report names such as
  `Development_Report_Phase_1.md` or `QA_Report_Phase_1.md`; this avoids collisions
  with V3.0 historical phases.

## Collaboration

- Codex / GPT: primary implementation.
- Trae Work / DeepSeek: cost-effective independent QA, boundary tests, README/documentation, and small explicit assistance tasks.
- Cursor / Claude: advanced architecture reviewer and second opinion for complex refactors.
- ChatGPT: roadmap and architecture arbitration, thesis writing, and experiment design.
- The user makes final decisions and acceptance.

After each phase, update only facts that changed in **Current State**, **Test Baseline**, or **Known Debt**.
