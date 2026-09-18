# V3.0.1 Phase 1 — Credits Domain QA Report

## Review Scope

This report records the complete Phase 1 QA chain:

```text
Credits Domain implementation
-> DeepSeek independent QA
-> Phase 1.1 documentation and regression hardening
-> DeepSeek directed retest
-> Documentation Gate closure
```

Phase 1 remained offline and Provider-independent. No real API, Credential, network
LLM call, Managed Access, SQLite, Provider, LLM, or UI implementation was used.

## Initial QA

- Verdict: **PASS WITH ISSUES**;
- Critical: **0**;
- Medium: **3**;
- Blocking: **0**.

### M1 — Privileged Refund Boundary

The initial contract did not make the trusted-server/admin boundary sufficiently
explicit for `refund()` and the other privileged accounting operations.

### M2 — Idempotency Contract Precision

The initial contract required a precise distinction between the normalized lookup
identity and the payload-consistency fields, including exact note replay and separate
`USAGE`/`REFUND` namespaces.

### M3 — Future SQLite Atomicity

The Phase 2 persistence contract had to prohibit partial commit between a ledger
transaction append and its idempotency record.

## Phase 1.1 Hardening

Phase 1.1 changed documentation contracts and regression tests only. Production
Credits code remained unchanged after the Phase 1 implementation.

The hardening froze:

- `grant()`, `refund()`, and `adjust()` as privileged operations;
- low-level refund semantics and the future authorization boundary;
- idempotency identity as `(operation_type, normalized account_id, normalized
  request_id)`;
- amount and exact note as replay-consistency fields;
- independent `USAGE` and `REFUND` namespaces;
- one-transaction SQLite persistence and mandatory Phase 2 failure injection.

Sixteen collected regression cases were added. Validation returned:

- Credits: **66 passed**;
- full suite: **195 passed**;
- offline LLM-contract smoke: **6 passed**.

## Directed Retest

DeepSeek returned **PASS WITH ISSUES**:

- Critical: **0**;
- Medium: **0**;
- Blocking: **0**;
- Low: **3 non-blocking observations**;
- independent probes: **13/13 passed**.

Finding disposition:

- M1: **CLOSED — Resolved by Contract**;
- M2: **CLOSED — Resolved by Contract + Regression**;
- M3: **CLOSED FOR PHASE 1 — Phase 2 Entry Contract**.

No further Phase 1 retest is required.

## Directed-Retest Low Observations

### L1 — Future Managed Surface Guard

M1, M2, and M3 currently rely in part on frozen documentation contracts. Phase 2
should add a structural guard for the `ManagedAccessService` surface so Managed callers
cannot directly access privileged ledger operations or a ledger object. This is
non-blocking for Phase 1 and remains a Phase 2 requirement.

### L2 — Test-Baseline Placement

The previous `PROJECT_CONTEXT.md` placement could make the current V3.0.1 development
baseline appear to be the V3.0.0 release baseline. This Documentation Gate separates
the V3.0.0 released baseline of **129 passed** from the current V3.0.1 development
baseline of **195 passed**. L2 is resolved by documentation clarification.

### L3 — Missing Versioned Phase Reports

The V3.0.1 Phase 1 Development and QA reports did not yet exist at directed-retest
time. This Gate creates both version-qualified reports. **L3 is RESOLVED**.

## Deferred Low Findings

Eight existing Low findings remain explicitly deferred:

1. history object-reference hardening;
2. transaction-ID collision enforcement;
3. private-container exposure;
4. integer upper bound;
5. the global `RLock` design;
6. note normalization;
7. hostile `str` subclass behavior;
8. validation-helper duplication.

No deferred item is reported as fixed.

## Regression Evidence

Validation on the current Anaconda Python 3.13.5 host used the documented
`-p no:debugging` workaround:

```text
python -m pytest -p no:debugging tests/test_credits_domain.py
66 passed

python -m pytest -p no:debugging
195 passed

python -m pytest -p no:debugging tests/test_llm_contracts.py
6 passed
```

No real API, Credential, or network LLM request was used.

## Final QA Status

- Final Phase 1 QA: **PASS FOR PHASE 1**;
- Critical: **0**;
- Medium: **0**;
- Blocking: **0**;
- further Phase 1 retest required: **No**;
- Phase 1 Documentation Gate: **CLOSED**;
- Phase 2 implementation performed by this Gate: **No**.
