# V3.0.1 Phase 2 — Managed Access Foundation

## Background

V3.0.1 Phase 1 froze the Credits Domain, including integer Credits, append-only
transactions, non-negative balances, idempotent `USAGE` and `REFUND`, and the
privileged accounting boundary. Phase 2 builds the smallest safe Managed AI Access
loop on that foundation while preserving the released BYOK path.

The Phase 2 objective was to combine:

- Managed AI Access;
- SQLite Credits persistence;
- flat per-request pricing;
- a server-side Provider boundary;
- a persistent Managed request state machine.

BYOK remains frozen. It does not depend on Credits, does not enter
`ManagedAccessService`, and does not check or deduct Credits.

## Architecture

Phase 2 adds these components:

- `managed_access/domain.py`:
  - `LLMAccessMode`;
  - `LLMAccessContext`;
  - `ManagedRequest`;
  - `ManagedRequestStatus`;
  - `ManagedAccessResult`;
  - safe Managed-domain errors.
- `managed_access/service.py`:
  - `FlatPricingPolicy`;
  - the minimal `ManagedProvider` Protocol;
  - `ManagedAccessService`.
- `credits/sqlite_ledger.py`:
  - `SQLiteCreditLedger` implementing the Phase 1 `CreditLedger` contract.

The dependency direction remains:

```text
managed_access/ -> credits/
managed_access/ -> credential-free ModelConfig / server-side Provider port
```

Credits does not depend on Managed Access or Provider infrastructure. Existing BYOK,
processor, UI, and maintenance-domain architecture remains unchanged.

## Access Model

`LLMAccessMode` has exactly two values:

- `BYOK`;
- `MANAGED`.

`LLMAccessContext` is immutable and credential-free. `MANAGED` requires normalized,
non-empty `account_id` and `request_id`; those fields remain optional for `BYOK`.

Credentials never enter:

- `LLMAccessContext`;
- `ManagedRequest`;
- `ManagedAccessResult`;
- `CreditTransaction`;
- SQLite;
- logs or public exception messages;
- workspace persistence;
- UI state.

The platform Credential is owned only by the injected server-side Provider
implementation. No Credential, raw client, or Provider object is returned to callers.

## Flat Pricing and Provider Port

`FlatPricingPolicy` returns a deterministic integer Credit cost before Provider
invocation. `credits_per_request` must be a positive integer; zero, negative values,
`bool`, floats, and strings are rejected. Token pricing, real Usage Metering, currency
conversion, and commercial exchange ratios are outside Phase 2.

`ManagedProvider` exposes one small `invoke()` contract over credential-free
`ModelConfig` and prompt input. `ManagedAccessService` depends on this Protocol rather
than a real network client. All Phase 2 tests use deterministic Stub Providers.

## SQLite Credit Ledger

`SQLiteCreditLedger` uses Python's standard-library `sqlite3` module and no ORM. The
database contains:

- `credit_transactions` — append-only accounting records;
- `credit_idempotency` — the persisted identity for idempotent `USAGE` and `REFUND`;
- `managed_requests` — Managed request identity, credential-free model selection,
  reserved Credits, status, and a payload fingerprint.

It preserves the Phase 1 `InMemoryCreditLedger` semantics for:

- account and request normalization;
- integer-only Credits;
- negative-balance prevention;
- append-only authoritative history;
- history ordering and immutable returned transactions;
- operation-scoped idempotency;
- exact amount and note replay consistency;
- privileged `grant`, `refund`, and `adjust` primitives.

A fixed-seed parity regression exercises short InMemory and SQLite operation sequences.

## SQLite Atomicity

For idempotent ledger operations, the transaction append and idempotency record are
written in the same SQLite transaction:

```text
credit transaction append
+ idempotency record append
-> one commit
```

This is an all-or-nothing contract, not merely a statement that a transaction API is
used. A failure after the transaction append, after the idempotency write, or from
`commit()` itself causes an explicit rollback. A partially committed transaction
without its idempotency record, or an orphan idempotency record without its
transaction, is prohibited and covered by regression tests and independent retest.

Managed success finalization applies the same rule to three changes:

```text
USAGE append
+ USAGE idempotency record
+ managed request -> SUCCEEDED
-> one commit
```

A finalization commit failure rolls all three changes back before the request is moved
to a safe recovery state.

## Reservation Model

Phase 2 adds no new `TransactionType`. Reservations are represented by persistent
`managed_requests` state. Available balance is:

```text
available balance = ledger balance - active managed reservations
```

Reservation accounting is:

- `RESERVED`: reservation remains active;
- `FINALIZATION_FAILED`: reservation remains active;
- `FAILED`: reservation is released;
- `SUCCEEDED`: reservation is no longer active and final consumption is represented by
  the committed `USAGE` transaction.

Provider invocation occurs after the reservation transaction commits and outside any
SQLite write transaction.

## Managed Request State Machine

The allowed Phase 2 transitions are:

```text
RESERVED -> SUCCEEDED
RESERVED -> FAILED
RESERVED -> FINALIZATION_FAILED
```

`SUCCEEDED`, `FAILED`, and `FINALIZATION_FAILED` are terminal for automatic request
execution. A replay of `RESERVED` reports recovery required and never automatically
invokes the Provider. Phase 2.1 added defensive `rowcount` validation so
`RESERVED -> FINALIZATION_FAILED` must update exactly one row; illegal transitions are
not silently accepted.

## Provider Success

On Provider success, `ManagedAccessService` atomically persists the final `USAGE`, its
idempotency record, and `SUCCEEDED`. A valid replay does not call the Provider again.
Because Phase 2 does not persist the original LLM response, a successful replay returns
completion metadata with no fabricated response content.

## Provider Failure

On Provider failure:

- no `USAGE` is written;
- the request becomes terminal `FAILED`;
- its reservation is released;
- the public exception is sanitized;
- replay of the same request does not automatically invoke the Provider.

## Accounting Failure After Provider Success

If the Provider succeeds but final accounting fails, the service does not report an
ordinary Provider failure and does not retry the Provider. It records
`FINALIZATION_FAILED` when possible, retains the reservation, and requires
reconciliation. If even that recovery write is unavailable, the prior `RESERVED` state
still prevents automatic reinvocation.

## Provider-Success Crash Window

The following window is a known limitation:

```text
RESERVED committed
-> Provider produces a successful side effect
-> process stops before finalization
```

After restart, SQLite contains only `RESERVED`. The system cannot distinguish
"Provider was not invoked" from "Provider succeeded before the interruption".

The frozen safe policy is fail-closed:

- do not automatically retry the Provider;
- do not automatically release the reservation;
- do not fabricate `SUCCEEDED`;
- require manual reconciliation.

V3.0.1 does not add a distributed transaction, durable workflow engine, or
Provider-side global idempotency protocol to eliminate this window.

## Concurrency

Phase 2 uses:

- `BEGIN IMMEDIATE` for serialized SQLite write boundaries;
- process-local `RLock` protection per ledger or service object;
- SQLite uniqueness and persisted request identity;
- active-reservation balance calculation.

Regression and independent testing cover single-service and multi-service concurrency,
independent SQLite connections and locks, same-request races, same-account overspend,
and restart replay. The verified outcome is at most one Provider call, one `USAGE`, and
one charge for one logical request.

## Payload Identity

Managed idempotency uses `(normalized account_id, normalized request_id)` for lookup and
also verifies a SHA-256 fingerprint of the business payload. The fingerprint includes
the credential-free model selection, prompt, and flat Credit cost. Reuse with a
different prompt, model, or flat price raises `ManagedRequestConflictError` rather than
replaying unrelated work.

## Public Security Surface

The public `ManagedAccessService` surface is limited to:

- `invoke`;
- `get_request`;
- `close`.

It exposes no `grant`, `refund`, `adjust`, `CreditLedger`, Credential, Provider getter,
or raw client. The Phase 1 privileged accounting boundary therefore remains intact.

## Initial Validation

Phase 2 implementation completed with:

- SQLite ledger: **27 passed**;
- Managed Access: **35 passed**;
- Phase 2 new tests: **62 passed**;
- Credits regression: **66 passed**;
- BYOK Provider regression: **19 passed**;
- offline LLM-contract smoke: **6 passed**;
- full suite: **257 passed**.

No real API, Credential, Provider network call, or network LLM request was used.

## Initial DeepSeek QA

Initial independent QA returned **PASS WITH ISSUES**:

- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- independent probes: **167/167 passed**.

SQLite atomicity, restart behavior, multi-service concurrency, the state machine,
Credential security, and BYOK isolation all passed. QA requested formal repository
regressions for:

- C1: multi-service concurrency;
- C2: the Provider-success crash window;
- C3: actual `commit()` failure;
- L1: defensive `rowcount` consistency.

## Phase 2.1 Post-QA Regression Hardening

Phase 2.1 added:

- C1 multi-service concurrency regression;
- C2 Provider-success/process-interruption and restart regression;
- C3 ledger commit-boundary rollback regression;
- C3 Managed finalization commit-boundary rollback regression;
- restart terminality for `FAILED` and `FINALIZATION_FAILED`;
- flat-price payload-conflict coverage;
- fixed-seed InMemory/SQLite parity coverage.

The only production-code change was in
`ManagedAccessService._mark_finalization_failed()`: its guarded update now requires
`rowcount == 1`, matching the other controlled transition behavior. No SQLite ledger,
Credits core, BYOK, Provider, LLM, processor, or UI production code changed.

L2, L3, and L4 remain deferred:

- L2: BYOK empty `account_id` exception-type normalization;
- L3: a performance-only `managed_requests(account_id, status)` index;
- L4: an artificial upper bound for positive integer flat prices.

## Directed Retest

DeepSeek's directed retest returned **PASS**:

- C1: **CLOSED**;
- C2: **CLOSED**;
- C3: **CLOSED**;
- L1: **CLOSED**;
- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- independent probes: **186/186 passed**;
- full suite: **268 passed**.

No double charge, double Provider call, partial SQLite commit, reservation loss,
Credential leak, or BYOK regression was found. No further production fix or directed
retest is required.

## Mutation Test Evidence

A repository-external mutation campaign confirmed that formal regressions detect:

- removal of the L1 `rowcount` guard;
- a fake-success transition from `RESERVED`;
- omission of `FINALIZATION_FAILED` from active reservations;
- removal of SQLite rollback behavior.

Two existing defensive guards currently lack direct regression coverage:

- the `SUCCEEDED` update guard in `_finalize_success()`;
- the `FAILED` update guard in `_mark_provider_failed()`.

This is a Low, deferred coverage observation. Those defensive branches are not
reachable through the current normal state machine and are not classified as product
defects. They are not represented as fixed.

## Known Limitations

- SQLite deployment and locking remain single-process-oriented rather than distributed;
- automated reconciliation is not implemented;
- the original LLM response is not persisted;
- the Provider-success crash window requires manual reconciliation;
- real Usage Metering is not implemented;
- token-, model-, or Provider-based pricing is not implemented;
- Payment is not implemented;
- Admin UI is not implemented;
- a production HTTP backend is not implemented;
- L2 BYOK empty-account exception normalization remains deferred;
- L3 managed-request performance indexing remains deferred;
- L4 flat-price integer upper bounds remain deferred;
- two defensive transition guards lack direct regression coverage as noted above.

## Phase 3 Entry Contract

Phase 3 may extend flat pricing into Usage Metering and a richer `PricingPolicy`, but it
must not overturn:

- the reservation state machine;
- SQLite all-or-nothing atomicity;
- Managed request idempotency and payload identity;
- the server-side Credential boundary;
- BYOK isolation from Credits and Managed Access.

This Documentation Gate does not design Phase 3 implementation details.

## Final Status

Phase 2 implementation, initial independent QA, Phase 2.1 hardening, directed retest,
and version-qualified documentation are complete. Final Phase 2 QA status:
**PASS FOR PHASE 2**. The Phase 2 Documentation Gate is **CLOSED**. Phase 3 was not
started by this work.
