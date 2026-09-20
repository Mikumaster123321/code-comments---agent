# V3.0.1 Phase 3 — Usage Metering & PricingPolicy QA Report

## Review Scope

This report records the complete Phase 3 QA chain:

```text
Phase 3 Usage Metering and PricingPolicy implementation
-> DeepSeek independent QA
-> Phase 3.1 Pricing Determinism & Migration Hardening
-> DeepSeek directed retest
-> Documentation Gate closure
```

The reviewed scope includes Usage Metering, flat and token pricing, Decimal-to-integer
Credit conversion, reservation upper bounds, actual-charge reconciliation, usage
identity and persistence, request fingerprinting, SQLite finalization atomicity,
Phase 2-to-Phase 3 migration, replay, concurrency, privacy, and BYOK isolation.

## Initial Implementation Baseline

The initial Phase 3 implementation completed with:

- Phase 3 Usage/Pricing and token-flow tests: **55 passed**;
- original Managed Access regression: **44 passed**;
- SQLite ledger regression: **29 passed**;
- Credits regression: **66 passed**;
- BYOK Provider regression: **19 passed**;
- offline LLM-contract smoke: **6 passed**;
- full suite: **323 passed**.

Testing used synthetic Decimal rates, fake credentials, and Stub Providers. It made no
real API, Credential, Provider-network, or network LLM request.

## Initial Independent QA

DeepSeek returned **PASS WITH ISSUES**:

- Critical: **0**;
- Medium: **1**;
- Release Blocker: **0**.

The core Phase 3 architecture passed. Usage privacy, reconciliation, fail-closed
behavior, reservation safety, request identity, legacy compatibility, and the Managed
state machine were accepted. One Product Medium required hardening before closure.

## Initial QA Finding

### M1 — Ambient Decimal Context Determinism

`TokenPricingPolicy._price()` performed Decimal multiplication, addition, and division
under the caller's ambient Decimal context. Low precision could round a value before
the explicit `ROUND_CEILING` conversion. The historical reproduction was:

```text
rate-derived amount: 1.0000001
usage scale: 1,000 tokens
expected: 2 Credits
low ambient precision before hardening: possible undercharge
```

The global Decimal context could therefore influence billing output for identical
policy, pricing context, and usage inputs.

### Migration Atomicity Recommendation

Independent QA also verified that a real Phase 2 database migrated successfully and
that interrupted partial migrations were recoverable on reopen. However, the migration
used per-statement autocommit and exposed an intermediate window where an alteration
could be committed before its backfill or usage-table initialization. This was accepted
as an immediate hardening recommendation rather than a separate Product Medium.

## Phase 3.1 Hardening

Phase 3.1 made two bounded production changes.

First, token pricing now runs inside a local Decimal context with dynamically computed
precision. The precision accounts for Decimal coefficient digits, arbitrary-size token
digits, exponent alignment, and carry margin. Local rounding remains
`ROUND_CEILING`; exponent bounds and clamp are explicit. No global Decimal setting is
modified. Policy identity canonicalization is also independent of ambient context.

Second, the complete Managed schema migration now executes under one
`BEGIN IMMEDIATE` transaction. Schema alterations, pricing-policy backfill,
`managed_usage` creation, and legacy metadata initialization commit or roll back as one
unit.

Phase 3.1 added permanent regressions for:

- ambient precision and rounding independence;
- rounding-boundary compatibility;
- high-digit Decimal rates and very large integer tokens;
- faithful Phase 2 schema migration;
- ledger, idempotency, state, replay, and reservation preservation;
- repeat-reopen migration idempotency;
- four migration failure boundaries and DDL rollback;
- existing usage-row preservation under `INSERT OR IGNORE`;
- privacy across success and failure paths;
- zero-cost finalization atomicity;
- bidirectional Flat/Token request conflicts.

The resulting repository baseline became Phase 3 **75 passed** and full suite
**343 passed**.

## Decimal Determinism Evidence

The directed retest exercised:

- **11** precision settings;
- **8** rounding modes;
- identical reservation and usage-pricing inputs;
- zero observed result drift.

The historical `1.0000001 x 1000` case now always produces **2 Credits**. The global
Decimal context remains unchanged after pricing. A **5,001-decimal-digit** integer token
value is supported without float conversion or dependence on Python's integer-to-string
digit limit.

M1 status: **RESOLVED**.

## Rounding Compatibility

The frozen conversion remains Decimal plus `ROUND_CEILING` to integer Credits. Directed
and repository tests preserve:

```text
1.0       -> 1
1.0000001 -> 2
1.9999999 -> 2
2.0       -> 2
tiny positive -> 1
```

No commercial pricing value or currency exchange ratio was introduced.

## Reservation Evidence

Independent fuzzing exercised **9,000** reservation cases. Observed violations of the
normal-finalization invariant were **0**:

```text
0 <= actual_credits <= reserved_credits
```

Usage exceeding provider/model limits or a pricing-policy reservation fails closed.
The service does not overcharge, create a negative balance, or reinvoke the Provider.

## Migration Atomicity Evidence

The final migration boundary is:

```text
BEGIN IMMEDIATE
-> schema alterations
-> pricing-policy backfill
-> managed_usage creation
-> legacy usage initialization
-> COMMIT or ROLLBACK
```

Real SQLite failure injection covered four points:

1. after the first schema alteration;
2. during backfill;
3. before `managed_usage` creation;
4. during legacy usage initialization.

Every injected failure produced complete rollback to the intact Phase 2 schema and
data. A subsequent normal reopen completed migration successfully.

## Migration Idempotency and Legacy Preservation

The directed retest reopened the migrated database **20 times** with zero drift.
Repository regression performs five repeated reopens as a permanent smoke boundary.

Verified preserved data includes:

- `ADMIN_GRANT` and `USAGE` ledger history;
- account balance;
- Credit idempotency;
- `SUCCEEDED`, `FAILED`, and `RESERVED` Managed requests;
- active reservation availability;
- successful legacy flat-price replay;
- existing `managed_usage` rows.

`INSERT OR IGNORE` adds only missing legacy metadata and does not overwrite or fabricate
an existing usage record.

## Finalization Atomicity

The `USAGE` transaction, Credit idempotency record, usage metadata, final Credits, and
`SUCCEEDED` transition remain one SQLite transaction. Failure injection covers usage
metadata writes, transaction append, idempotency, success-state update, and commit.

Zero-cost finalization received dedicated coverage: when usage metadata is inserted but
the success update or commit fails, no orphan usage remains, the request becomes
`FINALIZATION_FAILED`, the reservation remains active, and the Provider is not called
again.

## Flat and Token Conflict Safety

Reusing one `(account_id, request_id)` first with Flat pricing and then Token pricing
raises `ManagedRequestConflictError`. The reverse Token-to-Flat order behaves the same.
The second Provider is never invoked and no duplicate charge is written.

## Privacy Evidence

Unique prompt, completion, and secret markers were exercised across:

- successful token pricing;
- missing usage;
- model mismatch;
- actual price above reservation;
- finalization failure;
- Phase 2 migration and replay.

The retest scanned:

- logical SQLite rows;
- SQLite dumps;
- raw database bytes;
- `-journal`, `-wal`, and `-shm` sidecars when present.

Marker occurrences were **0**. SQLite retains only the payload fingerprint, safe
provider/model identity, token counts, Credits, and policy metadata. It does not retain
plaintext prompt, completion, raw response, Credential, or API key.

## Directed Retest

DeepSeek returned **PASS**:

- Product Critical: **0**;
- Product Medium: **0**;
- independent probes: **137/137 passed**;
- M1: **RESOLVED**;
- previous L1-L6: **CLOSED**.

The retest found no Decimal drift, reservation-bound violation, partial migration,
reopen drift, privacy marker, duplicate Provider invocation, duplicate charge, orphan
usage metadata, Credential leak, or BYOK regression.

No further production fix is required. No further directed retest is required.

## Deferred Low Findings

Two current Low observations remain non-blocking:

### L7 — Initialization Connection-Close Structure

`ManagedAccessService` initialization retains a structural opportunity for additional
explicit connection-close hardening around schema-initialization failure. The observed
behavior remains fail-closed. This is future hardening only.

### L8 — Proactive managed_usage Schema Validation

A pre-existing malformed `managed_usage` table fails closed, but initialization does
not proactively validate the table's complete schema shape before use. This is future
hardening only.

L7 and L8 are not Product Medium findings, Release Blockers, or reasons to delay the
Phase 3 Documentation Gate.

## Frozen Contracts

The final QA result freezes:

- `UsageRecord` and Credential-free usage structure;
- `PricingPolicy.policy_id`, `reserve_credits()`, and `price_usage()`;
- Phase 2-compatible `FlatPricingPolicy`;
- deterministic `TokenPricingPolicy`;
- local Decimal pricing and `ROUND_CEILING`;
- pre-call reservation upper bounds;
- actual-charge reconciliation;
- `FINALIZATION_FAILED` fail-closed behavior;
- provider/model integrity;
- private usage persistence;
- atomic finalization;
- atomic Phase 2-to-Phase 3 migration;
- request fingerprint and pricing identity.

## Final Regression Evidence

Validation on the current Anaconda Python 3.13.5 host used the documented
`-p no:debugging` workaround:

```text
python -m pytest -p no:debugging \
  tests/test_usage_pricing.py \
  tests/test_managed_token_pricing.py \
  tests/test_phase3_hardening.py
75 passed

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
343 passed
```

The historical baselines remain distinct:

- initial Phase 3 baseline: **323 passed**;
- final Phase 3.1 and Documentation Gate baseline: **343 passed**.

No real API, Credential, or network LLM request was used.

## Final QA Status

- Final Phase 3 QA: **PASS FOR PHASE 3**;
- Product Critical: **0**;
- Product Medium: **0**;
- Release Blocker: **0**;
- M1: **RESOLVED**;
- previous L1-L6: **CLOSED**;
- current L7/L8: **deferred, non-blocking**;
- further production fix required: **No**;
- further directed retest required: **No**;
- Phase 3 Documentation Gate: **CLOSED**;
- Phase 4 implementation performed by this Gate: **No**.
