# V3.0.1 Phase 3 — Usage Metering & PricingPolicy

## Background

V3.0.1 Phase 2 completed the first Managed Access loop with persistent reservations,
SQLite Credits, and `FlatPricingPolicy`. Its request lifecycle was deliberately small:

```text
reserve -> execute Provider -> finalize
```

Phase 3 extends that architecture with Usage Metering, token-based pricing, and
reservation-to-actual reconciliation. It does not replace the Phase 2 state machine,
introduce Payment, create a production HTTP backend, or couple BYOK to Credits.

The completed Phase 3 delivery includes both the initial implementation and Phase 3.1
Pricing Determinism & Migration Hardening.

## Architecture

Phase 3 adds or extends these Managed-side concepts:

- `UsageRecord` — immutable, Credential-free token usage;
- `ManagedProviderResponse` — safe content plus optional usage;
- `PricingContext` — the provider/model and pre-call token limits;
- `PricingPolicy` — reservation and actual-pricing contract;
- `FlatPricingPolicy` — Phase 2-compatible fixed pricing;
- `TokenPricingPolicy` — deterministic Decimal token pricing;
- `managed_usage` — Credential-free SQLite usage metadata.

The dependency and security boundaries remain:

```text
managed_access/ -> credits/
managed_access/ -> credential-free ModelConfig / server-side Provider port
```

Credits, BYOK, Provider foundation, processor, UI, and the Phase 2 Managed request
state machine were not redesigned.

## UsageRecord

`UsageRecord` is frozen and contains only:

- `provider_id`;
- `model`;
- `input_tokens`;
- `output_tokens`.

`total_tokens` is a derived property. Provider and model identifiers must be non-empty;
token counts must be non-negative integers and reject `bool`. Input-only and
output-only records are valid, while a zero-total record is rejected so missing or
meaningless metering cannot be treated as a successful token-pricing result.

`UsageRecord` contains no Credential, API key, prompt, completion, raw request, raw
response, client, or Provider object.

## ManagedProviderResponse

`ManagedProviderResponse` is the minimum safe Provider boundary for metered Managed
access. It carries:

- safe result content;
- optional `UsageRecord` metadata.

It carries no raw SDK response, Credential, raw client, or Provider object. For Phase 2
compatibility, a legacy string response remains accepted by flat-priced requests.

## PricingPolicy

The `PricingPolicy` Protocol defines:

- stable `policy_id`;
- `reserve_credits(pricing_context)`;
- `price_usage(pricing_context, usage)`.

`ManagedAccessService` depends on this contract instead of a concrete pricing class.
The versioned policy identity participates in Managed request payload identity and is
stored as Credential-free audit metadata.

## FlatPricingPolicy

`FlatPricingPolicy` preserves Phase 2 behavior:

- the request price is a positive integer known before Provider invocation;
- reserved Credits equal final Credits;
- `usage=None` remains valid;
- legacy string Provider responses remain valid;
- `credits_for(ModelConfig)` remains available for compatibility.

No existing flat-pricing state or replay semantics changed.

## TokenPricingPolicy

`TokenPricingPolicy` uses synthetic Decimal Credit rates per 1,000 tokens for input and
output usage. It rejects floats, `bool`, negative values, NaN, Infinity, and an
all-zero rate configuration.

The implementation contains no real OpenAI, DeepSeek, or other commercial price, no
RMB or USD amount, and no exchange ratio.

## Rounding

Token pricing uses Decimal intermediate arithmetic and converts the final amount to an
integer Credit count with `ROUND_CEILING`:

```text
1.0       -> 1 Credit
1.0000001 -> 2 Credits
1.9999999 -> 2 Credits
2.0       -> 2 Credits
tiny positive amount -> 1 Credit
```

Positive non-zero cost cannot disappear through rounding. A valid usage record can
still have zero final Credits when all consumed tokens use a configured zero-rate
direction; in that case usage metadata is persisted without creating an invalid
zero-amount `CreditTransaction`.

## PricingContext

`PricingContext` contains only:

- `provider_id`;
- `model`;
- `max_input_tokens`;
- `max_output_tokens`.

It is frozen and Credential-free. It contains no prompt, client, Provider, or runtime
secret.

## Reservation

Before Provider invocation, `TokenPricingPolicy.reserve_credits()` prices the declared
maximum input and output token limits. That result is the safe upper-bound reservation
for the request.

Active `RESERVED` and `FINALIZATION_FAILED` requests continue to reduce available
Credits. This preserves the Phase 2 same-account overspend protection across one or
multiple service objects and SQLite connections.

## Final Reconciliation

After Provider success, actual usage is priced and reconciled as follows:

- `actual < reserved`: write only the actual `USAGE`; release the unused reservation;
- `actual == reserved`: write the actual `USAGE` and complete normally;
- `actual > reserved`: do not charge beyond the reservation, enter
  `FINALIZATION_FAILED`, retain the reservation, and never reinvoke the Provider.

The normal path does not debit the reservation and then add a compensating refund.
Only the true final `USAGE` is appended.

## Missing or Invalid Usage

Token pricing fails closed when usage is missing, malformed, zero-total, over-limit,
or otherwise invalid after Provider success. The request enters
`FINALIZATION_FAILED`, retains its reservation, and requires manual reconciliation.
The Provider is not automatically called again.

Flat pricing remains exempt from the usage requirement because its final price is
known before execution.

## Provider and Model Integrity

Usage `provider_id` and `model` must match both the Managed model selection and the
`PricingContext`. Token counts must also remain within the declared limits. A mismatch
cannot be priced under another Provider or model and follows the same fail-closed
finalization policy.

## Usage Persistence

SQLite persists only Credential-free usage and pricing metadata:

- provider identifier;
- model identifier;
- input and output token counts;
- final integer Credits;
- policy identity and pricing limits on the Managed request.

It does not persist prompt text, completion content, raw Provider response, Credential,
API key, client, or Provider object.

On success, the following changes share one SQLite transaction:

```text
USAGE CreditTransaction
+ Credit idempotency record
+ managed_usage metadata
+ final Credits
+ Managed request -> SUCCEEDED
-> one commit
```

Failures at the usage insert, transaction append, idempotency write, success-state
update, or commit boundary leave no partial charge, orphan usage, or partial success.

## Request Fingerprint

Managed request identity remains `(normalized account_id, normalized request_id)` and
the payload fingerprint now covers all pricing-relevant inputs:

- credential-free model configuration;
- a one-way fingerprint of the prompt payload;
- pricing context and maximum token limits;
- stable policy identity/version;
- reserved Credits and flat/token mode through those fields.

The database stores only the SHA-256 payload fingerprint, not the plaintext prompt.
Changing flat/token mode, policy configuration, provider/model identity, token limits,
or prompt causes `ManagedRequestConflictError` rather than an unsafe replay.

## Schema Migration

Opening a Phase 2 database automatically adds the Phase 3 request metadata and
`managed_usage` table. Migration preserves:

- account balance;
- append-only ledger history;
- Credit idempotency records;
- Managed request identities and states;
- active reservations;
- safe replay of successful legacy flat-priced requests.

Legacy `SUCCEEDED` requests receive missing safe final-Credit metadata without
fabricating usage token counts. `INSERT OR IGNORE` fills missing metadata only and does
not overwrite an existing `managed_usage` row.

## Initial Tests

The initial Phase 3 implementation completed with:

- Phase 3 Usage/Pricing and token-flow tests: **55 passed**;
- original Managed Access regression: **44 passed**;
- SQLite ledger regression: **29 passed**;
- Credits regression: **66 passed**;
- BYOK Provider regression: **19 passed**;
- offline LLM-contract smoke: **6 passed**;
- full suite: **323 passed**.

All tests were offline and used only synthetic rates, fake credentials, and Stub
Providers.

## Initial DeepSeek QA

Initial independent QA returned **PASS WITH ISSUES**:

- Critical: **0**;
- Medium: **1**;
- Release Blocker: **0**.

M1 found that `TokenPricingPolicy._price()` depended on the ambient Decimal context.
Under low caller precision, valid prices such as `1.0000001` could be rounded before
the final ceiling step and undercharge. QA also identified the per-statement SQLite
migration autocommit window as a verified recoverable hardening recommendation.

## Phase 3.1 Pricing Determinism and Migration Hardening

Phase 3.1 resolved M1 with a local Decimal context whose precision is dynamically
sized from:

- exact Decimal coefficient digits;
- arbitrary-size integer token digits;
- exponent-alignment span;
- explicit carry safety margin.

The local context fixes `ROUND_CEILING`, exponent bounds, and clamp behavior without
modifying the process-global Decimal context. Decimal policy-identity canonicalization
also became context-independent. The original rounding contract did not change.

Phase 3.1 also placed every Phase 2-to-Phase 3 migration operation in one
`BEGIN IMMEDIATE` transaction:

- schema alterations;
- pricing-policy backfill;
- `managed_usage` creation;
- legacy usage initialization.

The transaction either commits all migration changes or rolls all of them back.

Permanent regressions added by Phase 3.1 cover:

- ambient precision and rounding changes;
- high-digit Decimal rates and large arbitrary-size token counts;
- a faithful Phase 2 schema with ledger, idempotency, and all request states;
- repeat migration/reopen idempotency;
- four migration failure points and real SQLite DDL rollback;
- preservation of existing usage metadata;
- privacy across success, failure, migration, dumps, raw database bytes, and sidecars;
- zero-cost finalization atomicity;
- Flat-to-Token and Token-to-Flat request conflicts.

After hardening, Phase 3 tests increased to **75 passed** and the full suite to
**343 passed**.

## Directed Retest

DeepSeek's directed retest returned **PASS**:

- Product Critical: **0**;
- Product Medium: **0**;
- independent probes: **137/137 passed**;
- M1: **RESOLVED**;
- previous L1-L6 observations: **CLOSED**.

Independent evidence included:

- 11 precision settings by 8 rounding modes with zero pricing drift;
- historical `1.0000001 x 1000` reproduction now always producing 2 Credits;
- no modification of the global Decimal context;
- support for a 5,001-decimal-digit integer token value;
- 9,000 reservation fuzz cases with zero upper-bound violations;
- four migration failure points with complete rollback;
- 20 migration reopens with zero drift;
- preserved legacy Phase 2 data and safe replay;
- zero-cost finalization atomicity;
- safe Flat/Token conflicts;
- zero privacy-marker occurrences across logical rows, dumps, raw database bytes, and
  SQLite sidecars.

No further production fix or directed retest is required for Phase 3.

## Frozen Phase 3 Contracts

The Phase 3 Documentation Gate freezes:

- `UsageRecord`;
- `PricingPolicy` reservation and actual-pricing methods;
- `FlatPricingPolicy` compatibility;
- `TokenPricingPolicy` and synthetic Decimal rates;
- local deterministic Decimal pricing;
- integer Credit conversion with `ROUND_CEILING`;
- token-limit reservation upper bounds;
- actual-charge reconciliation;
- `FINALIZATION_FAILED` fail-closed behavior;
- provider/model usage integrity;
- Credential-free usage persistence and privacy;
- atomic finalization;
- atomic Phase 2-to-Phase 3 migration;
- request fingerprint and stable pricing-policy identity.

Future work must preserve these contracts unless a separately reviewed architecture
decision explicitly changes them.

## Deferred Low Findings

Two directed-retest Low observations remain non-blocking and deferred:

- **L7:** `ManagedAccessService` initialization retains a structural opportunity for
  additional explicit connection-close hardening around schema-initialization failure;
- **L8:** a pre-existing malformed `managed_usage` table fails closed but has no
  proactive schema-shape validation.

Neither finding is a Product Medium, Release Blocker, or reason to reopen Phase 3.

## Known Limitations

- SQLite deployment remains single-process-oriented rather than distributed;
- automated reconciliation is not implemented;
- the Provider-success crash window still requires manual reconciliation;
- the original LLM response is not persisted;
- Payment, Admin UI, and a production HTTP backend are not implemented;
- L7 and L8 remain future hardening opportunities.

## Phase 4 Entry Contract

Phase 4 may add the Admin Operations Surface only after this Documentation Gate. It
must not weaken Credits privilege boundaries, expose platform Credentials, couple BYOK
to Managed billing, or change the frozen Phase 3 pricing and reconciliation contracts.

## Final Status

Phase 3 implementation, initial independent QA, Phase 3.1 hardening, directed retest,
and version-qualified documentation are complete. Final Phase 3 QA status is
**PASS FOR PHASE 3** with Product Critical **0** and Product Medium **0**. The Phase 3
Documentation Gate is **CLOSED**. Phase 4 was not started by this work.
