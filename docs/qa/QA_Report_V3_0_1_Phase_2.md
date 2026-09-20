# V3.0.1 Phase 2 — Managed Access Foundation QA Report

## Review Scope

This report records the complete Phase 2 QA chain:

```text
Managed Access Foundation implementation
-> DeepSeek independent QA
-> Phase 2.1 regression hardening
-> DeepSeek directed retest
-> Documentation Gate closure
```

The reviewed scope includes SQLite ledger persistence, Managed request persistence,
flat pricing, Provider isolation, reservation accounting, request idempotency,
concurrency, restart behavior, failure atomicity, and Credential security. Testing was
offline and used Stub Providers and fake credentials only.

## Initial Implementation Baseline

Phase 2 initially completed with:

- SQLite ledger: **27 passed**;
- Managed Access: **35 passed**;
- Phase 2 new tests: **62 passed**;
- Credits regression: **66 passed**;
- BYOK Provider regression: **19 passed**;
- offline LLM-contract smoke: **6 passed**;
- full suite: **257 passed**.

## Initial Independent QA

DeepSeek returned **PASS WITH ISSUES**:

- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- independent probes: **167/167 passed**.

Independent probes passed for:

- transaction/idempotency atomicity;
- negative-balance and overspend prevention;
- restart persistence and replay;
- single-service and multi-service behavior;
- state-machine terminality;
- Credential exclusion and sanitized errors;
- BYOK isolation and regression safety.

The product architecture passed. QA requested that several already-correct high-risk
behaviors become permanent repository regressions and identified one defensive
consistency improvement.

## Initial QA Findings

### C1 — Multi-Service Concurrency Regression

Two independent `ManagedAccessService` objects, SQLite connections, and service locks
needed a formal same-request race regression. The required invariant was one Provider
call, one `USAGE`, one charge, and one logical Managed request.

### C2 — Provider-Success Crash-Window Regression

The known window between Provider success and accounting finalization needed a durable
restart regression. A persisted `RESERVED` request must fail closed after interruption,
retain its reservation, and never automatically reinvoke the Provider.

### C3 — Commit-Boundary Atomicity Regression

Existing injections covered failures before commit. QA requested deterministic tests
where `commit()` itself raises after all intended statements have executed, for both:

- ledger transaction plus idempotency persistence;
- Managed `USAGE` plus idempotency plus `SUCCEEDED` finalization.

### L1 — Defensive Rowcount Consistency

`_mark_provider_failed()` and the `SUCCEEDED` finalization update already required one
updated row. `_mark_finalization_failed()` did not check its update count and could
silently accept an illegal transition attempt.

## Phase 2.1 Regression Hardening

Phase 2.1 added permanent regressions for:

- C1 multi-service same-request concurrency;
- C2 Provider success followed by process interruption and restart;
- C3 ledger `commit()` failure rollback;
- C3 Managed finalization `commit()` failure rollback;
- terminal `FAILED` replay after restart;
- terminal `FINALIZATION_FAILED` replay after restart;
- same request ID with a changed flat price;
- fixed-seed InMemory/SQLite short-sequence parity.

L1 was fixed with one minimal production change: the guarded
`RESERVED -> FINALIZATION_FAILED` update must affect exactly one row or raise
`ManagedAccessError`. Tests verify that `SUCCEEDED`, `FAILED`, and
`FINALIZATION_FAILED` cannot be marked again.

No SQLite ledger, Credits core, BYOK, Provider, LLM, processor, or UI production code
was changed by Phase 2.1.

## Atomicity Results

The following boundaries passed deterministic failure injection:

1. failure after ledger transaction append and before idempotency persistence;
2. failure after idempotency persistence and before successful completion;
3. ledger `commit()` itself raises after both statements execute;
4. Managed finalization `commit()` raises after `USAGE`, idempotency, and `SUCCEEDED`
   update execute;
5. failure before reservation commit;
6. interruption after reservation commit and Provider success but before finalization;
7. failure before `USAGE` append;
8. failure after `USAGE` append and before idempotency persistence;
9. failure before final status commit.

No partial transaction, orphan idempotency record, partial `SUCCEEDED`, double charge,
or silent reservation loss was observed.

## Concurrency and Replay Results

Coverage includes:

- same request through one service;
- same request through two independent services;
- independent SQLite connections and `RLock` instances;
- different requests competing for one account balance;
- persisted active reservations preventing overspend;
- replay after service and connection restart;
- payload conflicts for prompt, model, and flat price.

Verified outcomes are Provider once, `USAGE` once, and charge once for one logical
request. A competing caller may observe `RESERVED` recovery-required or a completed
replay depending on timing, but cannot invoke the Provider a second time.

## Crash-Window Safety

The directed regression simulates a process interruption after a successful Provider
result but before finalization. After restart:

- state remains `RESERVED`;
- no `USAGE` exists;
- the reservation remains unavailable to other requests;
- same-request replay raises recovery-required;
- the Provider is not called again.

This is an intentional fail-closed policy requiring manual reconciliation. Phase 2
does not claim a distributed transaction, durable workflow engine, or Provider-side
global idempotency protocol.

## Credential and Public-Surface Results

Unique fake secrets were used in concurrency, crash-window, and commit-failure tests.
No secret entered a public result, request, context, exception, representation, credit
record, or SQLite file. `ManagedAccessService` exposes only `invoke`, `get_request`,
and `close`; privileged ledger operations and Provider/Credential getters remain absent.

## Directed Retest

DeepSeek returned **PASS**:

- C1: **CLOSED**;
- C2: **CLOSED**;
- C3: **CLOSED**;
- L1: **CLOSED**;
- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- independent probes: **186/186 passed**.

The directed retest found:

- double charge: **not found**;
- double Provider call: **not found**;
- partial SQLite commit: **not found**;
- reservation loss: **not found**;
- Credential leak: **not found**;
- BYOK regression: **not found**.

No further production fix or directed retest is required.

## Mutation Test Evidence

A repository-external mutation campaign confirmed that regressions detect removal of:

- the L1 `rowcount` guard;
- correct `RESERVED` success-state behavior;
- `FINALIZATION_FAILED` reservation retention;
- SQLite rollback behavior.

Two existing defensive `rowcount` guards lack direct mutation-targeted regression:

- the `SUCCEEDED` update in `_finalize_success()`;
- the `FAILED` update in `_mark_provider_failed()`.

This remains a Low, deferred coverage observation. The branches are unreachable through
the current normal state machine and are not product defects. They are not reported as
fixed.

## Deferred Low Findings

- L2: BYOK `account_id=""` remains fail-closed with the existing exception type;
- L3: the performance-only `managed_requests(account_id, status)` index remains
  deferred;
- L4: `FlatPricingPolicy` retains the positive-integer contract without an artificial
  upper bound;
- direct regression coverage for the two defensive guards noted above remains deferred.

## Final Regression Evidence

Validation on the current Anaconda Python 3.13.5 host used the documented
`-p no:debugging` workaround:

```text
python -m pytest -p no:debugging tests/test_managed_access.py
44 passed

python -m pytest -p no:debugging tests/test_sqlite_credit_ledger.py
29 passed

python -m pytest -p no:debugging tests/test_credits_domain.py
66 passed

python -m pytest -p no:debugging tests/test_provider_foundation.py
19 passed

python -m pytest -p no:debugging tests/test_llm_contracts.py
6 passed

python -m pytest -p no:debugging
268 passed
```

The historical baselines remain distinct:

- V3.0.0 released baseline: **129 passed**;
- V3.0.1 Phase 1 baseline: **195 passed**;
- current V3.0.1 Phase 2 baseline: **268 passed**.

No real API, Credential, or network LLM request was used.

## Final QA Status

- Final Phase 2 QA: **PASS FOR PHASE 2**;
- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- C1/C2/C3/L1: **CLOSED**;
- further production fix required: **No**;
- further directed retest required: **No**;
- Phase 2 Documentation Gate: **CLOSED**;
- Phase 3 implementation performed by this Gate: **No**.
