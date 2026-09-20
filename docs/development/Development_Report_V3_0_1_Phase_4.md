# V3.0.1 Phase 4 — Admin Operations Surface

## Objective

Phase 4 establishes a trusted server-side boundary for administrative Credit
operations. It provides persistent, auditable grants and adjustments without exposing
the underlying ledger through the Managed Access surface.

This phase does not implement an authentication system, RBAC, an Admin Web dashboard,
or a Payment backend. The completed delivery includes both the initial Phase 4
implementation and Phase 4.1 Admin Identity & Persistence Hardening.

## Package

The implementation is contained in `admin_operations/`:

- `domain.py` defines the immutable Admin domain values and typed failures;
- `service.py` defines the trusted SQLite-backed `AdminCreditService`.

The package depends on the existing Credits domain and SQLite ledger internals. It does
not change the Credits protocol, Provider foundation, Managed request state machine,
processor, or UI.

## AdminOperationContext

`AdminOperationContext` is immutable and contains:

- `actor_id`;
- `operation_id`;
- `reason`.

Accepted built-in strings are trimmed and validated as non-empty. The context is
Credential-free and contains no API key, password, authentication token, Provider,
client, or runtime authorization object.

## AdminOperationType

The Phase 4 operation types are deliberately minimal:

- `GRANT`;
- `ADJUSTMENT`.

`REFUND` is not exposed by the Admin service. `PURCHASE` and all Payment operations are
not implemented.

## AdminOperationRecord

`AdminOperationRecord` is immutable and auditable. It records:

- actor identifier;
- operation identifier;
- operation type;
- account identifier;
- integer amount;
- reason;
- corresponding Credit transaction identifier;
- creation timestamp.

The audit record contains business and identity metadata only. It does not contain a
Credential, raw connection, ledger object, Provider object, or authentication secret.

## AdminCreditService

The public service surface is:

- `grant()`;
- `adjust()`;
- `balance()`;
- `history()`;
- `close()`.

It does not publicly expose a ledger, `refund()`, Credential, or raw SQLite connection.
The service is intended to be instantiated and controlled by trusted server-side code.

## Idempotency

Administrative operation identity is:

```text
(normalized actor_id, normalized operation_id)
```

An exact retry with the same operation type, normalized account, amount, and normalized
reason returns the persisted `AdminOperationRecord` without another Credit mutation.

Reusing the identity with a different operation type, account, amount, or reason raises
`AdminOperationConflictError`. The database primary key enforces the same identity
across restarts and independent service connections.

## Atomicity

Each mutation writes:

```text
CreditTransaction
+ AdminOperationRecord
-> one BEGIN IMMEDIATE SQLite transaction
```

The transaction commits both rows or rolls both back. `BEGIN IMMEDIATE` serializes
competing writers across independent connections. Failure injection before and after
the Credit insert, before and after the Admin audit insert, and at commit verifies that
no partial Credit or orphan audit record survives.

## Foreign Key

SQLite foreign-key enforcement is enabled on the service connection. Every Admin audit
row references its Credit transaction through:

```text
FOREIGN KEY (credit_transaction_id)
REFERENCES credit_transactions(transaction_id)
ON DELETE RESTRICT
```

Regression coverage verifies both `PRAGMA foreign_keys = 1` and actual rejection of an
audit row that references a missing Credit transaction.

## Grant

`grant()` accepts a positive non-zero integer and appends an `ADMIN_GRANT` Credit
transaction. Invalid, zero, negative, Boolean, non-integer, or SQLite-out-of-range
amounts fail before persistence.

## Adjustment

`adjust()` accepts a positive or negative non-zero integer. A negative adjustment may
reduce the balance to exactly zero but cannot make it negative. Successful adjustments
append an `ADJUSTMENT` Credit transaction.

## Read Operations

`balance()` returns the derived integer balance. `history()` returns an immutable tuple
of Credit transactions in ledger order. Neither read operation creates an Admin audit
record or mutates the ledger.

## Privileged Boundary

`ManagedAccessService` cannot access or expose:

- `grant`;
- `adjust`;
- `refund`;
- a Credit ledger;
- an Admin service.

The existing Managed client boundary therefore remains unable to perform privileged
Credit operations.

## Initial Tests

The initial Phase 4 implementation completed with:

- Admin Operations: **51 passed**;
- Phase 3 pricing, token-flow, and hardening: **75 passed**;
- Managed Access: **44 passed**;
- SQLite ledger: **29 passed**;
- Credits: **66 passed**;
- BYOK Provider: **19 passed**;
- offline LLM-contract smoke: **6 passed**;
- full suite: **394 passed**.

All testing was offline and made no real API, Credential, Provider-network, or network
LLM request.

## Initial DeepSeek QA

Independent QA returned **PASS WITH ISSUES**:

- Critical: **0**;
- Medium: **1**;
- Low: **3**;
- Release Blocker: **0**.

The core atomicity, foreign-key, restart, concurrency, migration, and Credential
boundaries passed. M-1 found a real identity defect: a hostile `str` subclass could
override normalization behavior and persist a second actor or operation identity,
producing a duplicate Grant.

## Phase 4.1 Admin Identity & Persistence Hardening

Phase 4.1 changed the Admin boundary to accept only exact built-in `str` objects before
trimming or validation. A `str` subclass is rejected before caller-defined `strip`,
comparison, hash, string conversion, representation, or SQLite adaptation can
participate in Admin identity.

The same local defensive rule covers `account_id` and `reason`. The Credits domain was
not modified. Normal built-in string normalization remains unchanged:

```text
" admin "  -> "admin"
"admin"    -> "admin"
"\tadmin\n" -> "admin"
```

## Admin SQLite Integer Range

Phase 4.1 adds a persistence constraint at the Admin service boundary:

```text
-(2**63) <= amount <= 2**63 - 1
```

`2**63 - 1` is accepted when business semantics permit it. `2**63` and values below
`-(2**63)` raise `InvalidCreditAmountError` before a SQLite write, avoiding a raw
`OverflowError` or SQLite range error. A failed range check writes no identity or audit
state, so the same operation can be retried with a legal amount.

This guard is an Admin SQLite persistence constraint. It does not redefine the entire
Credits mathematical domain.

## Phase 4.1 Validation

The hardened baseline is:

- Admin Operations: **71 passed**;
- Phase 3 pricing, token-flow, and hardening: **75 passed**;
- Managed Access: **44 passed**;
- SQLite ledger: **29 passed**;
- Credits: **66 passed**;
- BYOK Provider: **19 passed**;
- offline LLM-contract smoke: **6 passed**;
- full suite: **414 passed**.

The current host requires `-p no:debugging` because its Anaconda Python 3.13.5 pytest
debugging plugin reproducibly segfaults while importing `rlcompleter`. This documented
host issue is unrelated to the product tests.

## Directed Retest

DeepSeek directed retest returned **PASS**:

- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- independent assertions: **159 passed**;
- full suite: **414 passed**;
- M-1: **RESOLVED**.

The historical hostile-string defect reproduced the balance progression
`7 -> 14 -> 21`. On the fixed version, hostile actor and operation values are rejected
with zero additional writes, and their hostile methods execute zero times.

The retest also confirmed exactly-once behavior for 1,000 replays, independent-service
concurrency, and restart replay; actual foreign-key enforcement; rollback at all five
mutation/commit failure boundaries; and zero Credential leakage.

## Deferred Low Findings

Two Low technical-debt items remain non-blocking:

1. Calling the service after `close()` may expose `sqlite3.ProgrammingError` rather
   than a service-specific lifecycle exception.
2. Although each Admin amount is signed-64 guarded, multiple individually valid
   transactions can make SQLite `SUM(amount)` overflow for one account. The affected
   account's balance or adjustment query can fail, but no data corruption, duplicate
   Grant, or atomicity violation occurs and other accounts remain unaffected.

These items do not require a Phase 4 production change or another directed retest.

## Admin UI Decision

Admin UI is **SKIPPED FOR V3.0.1**. `AdminCreditService` provides the trusted
server-side boundary required by this version, while a complete UI, authentication,
and RBAC system is outside the V3.0.1 scope. Admin UI remains a possible future
enhancement; it is not rejected permanently.

## Phase 5 Decision

Optional Phase 5 Payment Interface Reservation is **SKIPPED FOR V3.0.1**. This version
does not implement `PaymentProvider`, `PURCHASE`, recharge, Alipay, WeChat Pay, or
Stripe. Payment can be reconsidered for V3.0.2 or a future commercial enhancement.

## Frozen Contracts

Documentation Gate closure freezes:

- `AdminOperationContext`;
- `AdminOperationType`;
- `AdminOperationRecord`;
- `AdminCreditService`;
- the exact built-in string identity boundary;
- `(actor_id, operation_id)` idempotency;
- Credit plus Admin audit atomicity;
- executable foreign-key enforcement;
- grant and adjustment semantics;
- the Managed privileged-operation boundary;
- refund non-exposure;
- the Admin SQLite signed-64 amount guard.

Phase 4 and Phase 4.1 are complete. No further production fix or directed retest is
required for the Phase 4 gate.
