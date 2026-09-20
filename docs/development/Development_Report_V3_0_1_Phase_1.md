# V3.0.1 Phase 1 — Credits Domain

## Background

V3.0.1 introduces optional Managed AI Access while preserving the released V3.0.0
BYOK path. A small Credits Domain was established first so accounting rules, balance
invariants, idempotency, and failure behavior could be defined independently of
Provider orchestration.

Phase 1 is deliberately offline, Provider-independent, UI-independent, and
SQLite-independent. It does not access credentials, invoke an LLM, expose a user
surface, or choose a persistence implementation. These boundaries keep the accounting
model testable and prevent the future Managed path from leaking into the existing BYOK
or maintenance domains.

## Architecture

The top-level `credits/` package contains:

- immutable `CreditAccount` and `CreditTransaction` domain values;
- the `TransactionType` enum;
- the minimal `CreditLedger` Protocol;
- the thread-safe, process-local `InMemoryCreditLedger` implementation.

The package has no dependency on Provider, LLM, UI, Managed Access, SQLite, network,
or pricing code.

## Transaction Types

Phase 1 implements exactly:

- `ADMIN_GRANT`;
- `USAGE`;
- `REFUND`;
- `ADJUSTMENT`.

`PURCHASE` is not implemented. Payment-provider integration remains outside Phase 1.

## Ledger Model

The ledger is append-only and authoritative. Balance is derived from the transaction
sum:

```text
balance = sum(account transactions)
```

There is no second authoritative balance cache.

## Credit Unit

Credits are integer units. `bool`, `float`, and `Decimal` values are rejected as
Credit amounts. Future real monetary values and Provider costs use `Decimal`; Phase 3
owns the cost-to-integer-Credits conversion and rounding contract.

## Grant

`grant()` is a privileged operation. It accepts a positive integer amount and appends
an `ADMIN_GRANT` transaction. It is intended for trusted server-side or admin-side
orchestration, not direct client access.

## Charge

`charge()` accepts a positive caller amount and records the corresponding negative
`USAGE` transaction. A charge cannot make the balance negative. Insufficient balance
raises `InsufficientCreditsError` without reserving the idempotency key or changing
ledger state.

## Refund

`refund()` is a privileged, low-level positive accounting primitive. It is not a
user-facing refund-authorization system. Its `request_id` identifies the refund
operation, not the original `USAGE`. Phase 1 performs no original-usage reconciliation.

## Adjustment

`adjust()` is privileged. It accepts a positive or negative nonzero integer, including
a negative adjustment that reaches exactly zero, but it cannot create a negative
balance.

## Idempotency

The lookup identity for idempotent operations is:

```text
(operation_type, normalized account_id, normalized request_id)
```

`USAGE` and `REFUND` have independent namespaces. A valid replay preserves the same
amount and exact note and returns the original transaction. Reuse with a different
amount or note raises `IdempotencyConflictError`. The note is a payload-consistency
field rather than part of the lookup key.

## Thread Safety

`InMemoryCreditLedger` provides single-process thread safety using one `RLock`. Within
the critical section it performs the idempotency check, balance precheck where
applicable, transaction append, and idempotency-index update. It does not claim
cross-process or distributed serialization.

## Failure Atomicity

Rejected validation, insufficient-credit, and idempotency-conflict operations produce
zero ledger state change: history, derived balance, and idempotency state remain
unchanged.

## Initial Tests

The Phase 1 implementation completed with:

- Credits tests: **50 passed**;
- full suite: **179 passed**.

Validation was offline and used the documented current-host
`python -m pytest -p no:debugging` workaround.

## Initial DeepSeek QA

The independent QA verdict was **PASS WITH ISSUES**:

- Critical: **0**;
- Medium: **3**;
- Blocking: **0**.

The Medium findings were:

- M1: the privileged refund boundary required an explicit frozen contract;
- M2: the idempotency lookup and payload-consistency contract required precision;
- M3: future SQLite transaction append and idempotency-record persistence required an
  atomicity contract.

## Phase 1.1 Hardening

Phase 1.1 hardened documentation contracts and expanded regression coverage without
changing production Credits code. Sixteen collected regression cases were added for
account and request normalization, failed-charge idempotency behavior, exact-note
payload consistency, cross-type namespaces, integer-only Credits, concurrent refund
replay, exact-zero adjustment, and the intentional low-level refund boundary.

Phase 1.1 validation completed with:

- Credits tests: **66 passed**;
- full suite: **195 passed**;
- offline LLM-contract smoke: **6 passed**.

## Directed Retest

DeepSeek's directed retest returned **PASS WITH ISSUES** with Critical **0**, Medium
**0**, Blocking **0**, and three non-blocking observations. All **13/13** independent
probes passed.

- M1: **CLOSED — Resolved by Contract**;
- M2: **CLOSED — Resolved by Contract + Regression**;
- M3: **CLOSED FOR PHASE 1 — Frozen as Phase 2 Entry Contract**.

No further Phase 1 retest is required.

## Deferred Low

The following eight Low findings remain deferred and were not represented as fixed:

1. history object-reference hardening;
2. transaction-ID collision enforcement;
3. private-container exposure;
4. integer upper bound;
5. the global `RLock` design;
6. note normalization;
7. hostile `str` subclass behavior;
8. validation-helper duplication.

## Known Limitations

- storage is in-memory only;
- thread safety is single-process only;
- no SQLite implementation exists;
- there is no Provider or Managed Access integration;
- no `PricingPolicy` exists;
- there is no Credits UI or payment integration;
- refund does not identify or reconcile an original `USAGE`.

## Phase 2 Entry Requirements

Phase 2 may begin only under these frozen requirements:

1. Managed clients cannot directly access `grant()`, `refund()`, `adjust()`, or a
   `CreditLedger` object.
2. A user-facing refund must identify the original `USAGE`, authorize the refund, and
   prevent repeated refunds against the same authorized usage before internally
   calling `CreditLedger.refund()`.
3. A SQLite ledger transaction append and its idempotency-record write must be part of
   one atomic database transaction.
4. Phase 2 QA must use failure injection to verify all-or-nothing persistence.
5. Retries must preserve normalized account identity, normalized request identity,
   amount, and exact note.

Phase 2 was not started by Phase 1 or this Documentation Gate.

## Final Status

Phase 1 implementation, independent QA, Phase 1.1 hardening, directed retest, and
documentation are complete. Final Phase 1 QA status: **PASS**. The Phase 1
Documentation Gate is **CLOSED**.
