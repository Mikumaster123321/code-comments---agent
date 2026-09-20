# V3.0.1 Release Notes

**Status:** Release Candidate 1  
**Version:** `3.0.1-rc1`

V3.0.1 RC1 is a release candidate, not a final or stable release.

## Overview

V3.0.1 extends the LLM-assisted Software Maintenance Platform with optional Managed AI Access and Credits infrastructure. It preserves the existing project-maintenance core, Gradio workflows, and first-class BYOK path.

## Highlights

- Optional Managed AI Access with request reservation and idempotency
- Append-only Credits accounting with standard-library SQLite persistence
- Provider/model token usage metering and deterministic pricing policies
- Trusted server-side Admin grant and adjustment operations
- Platform Credential isolation and complete BYOK compatibility
- Full offline regression baseline: **414 passed**

## Architecture

The release keeps the existing dependency boundaries:

```text
BYOK: User Credential -> Task-scoped Provider -> LLM

Managed: Trusted Admin Grant -> Credits -> Managed Request -> Reservation
       -> Provider -> Usage -> Pricing -> USAGE Ledger
```

`credits/` is Provider-independent. `managed_access/` may depend on Credits and the existing Provider foundation. `code_maintenance/` remains independent of Provider, Credential, Credits, and Managed Access. This is a logical architecture, not a production network topology.

## Credits Domain

The Credits domain provides immutable accounts and transactions plus an append-only authoritative ledger. Transaction types are `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT`; balances are derived from transaction history.

`REFUND` remains a low-level accounting primitive. V3.0.1 does not expose a user refund workflow. `PURCHASE` is not implemented.

## Managed AI Access

Managed AI Access is an optional alternative to BYOK. A server-side `ManagedAccessService` coordinates request identity, reservation, Provider execution, usage validation, pricing, and final accounting. Requests use persistent states so exact replay does not repeat a completed Provider call or charge.

This release does not claim or provide a production HTTP backend.

## SQLite Persistence

Python's standard-library `sqlite3` persists:

- Credit transactions and idempotency identities
- Managed request state and active reservations
- Usage metadata and final Credits
- Trusted Admin audit records

The design is local and single-process oriented. It is not a distributed, clustered, or general multi-tenant database architecture.

## Usage Metering

Managed requests can record Provider, Model, Input Tokens, Output Tokens, and Final Credits. Billing persistence does not store Prompt, Completion, Raw Response, or Credential. Flat-price requests remain compatible with legacy string Provider responses and may omit usage metadata.

## PricingPolicy

`FlatPricingPolicy` retains fixed Credits-per-request behavior. `TokenPricingPolicy` uses synthetic `Decimal` rates per 1,000 tokens, local deterministic arithmetic, and `ROUND_CEILING` conversion to integer Credits.

Declared token limits define the reservation upper bound. Actual Provider usage is validated against Provider, Model, and limits, then reconciled to the final charge. These rates are an abstraction, not an OpenAI, DeepSeek, RMB, USD, or exchange-rate price table.

## Admin Operations

The trusted server-side `AdminCreditService` supports Grant, Adjustment, Balance, and immutable History. Admin operation identity is idempotent by normalized Actor ID and Operation ID, and the Credit transaction and Admin audit row commit atomically.

This service is not an authentication system. It assumes trusted server-side orchestration and does not include an Admin UI, Login, Password, OAuth, or RBAC.

## BYOK Compatibility

BYOK remains fully supported. Users may select their own Provider, Model, and Credential. BYOK requests do not require or deduct Credits and do not depend on Admin Operations. Task-scoped Provider isolation remains unchanged.

## Security & Privacy

- Platform Credential exists only inside trusted server-side runtime and Provider implementations.
- Platform Credential does not enter Client state, Workspace data, ordinary configuration, SQLite billing records, logs, access contexts, or public service representations.
- SQLite billing data contains no Prompt, Completion, or Raw Response.
- BYOK runtime Credential and task-scoped Provider boundaries are preserved.
- Admin operations are a trusted boundary only; Auth / RBAC is not provided.

These boundaries do not constitute enterprise IAM, zero-trust architecture, or production-grade authentication.

## Database Migration

Opening a Phase 2 database performs the Phase 2-to-Phase 3 schema migration in one `BEGIN IMMEDIATE` transaction. Existing ledger data, idempotency records, managed requests, and reservations are preserved while pricing-policy identity and usage storage are added.

The Admin schema is an additive, idempotent migration. V3.0.1 does not claim support for arbitrary future schema migrations.

## Testing

- Full repository suite: **414 passed**
- Standard clean-environment command: `python -m pytest`
- Tests are offline and do not use real API keys or make real Provider requests.
- On the documented Anaconda Python 3.13.5 host only, `python -m pytest -p no:debugging` avoids an interpreter/debugging-plugin segmentation fault.

## Known Limitations

- Local, single-process services and SQLite orientation; no distributed transaction layer
- No Admin UI, Payment, Recharge, Auth / RBAC, or production HTTP backend
- A Provider-success/process-interruption window can retain a reservation for manual reconciliation
- Low-level SQLite calls after service close may surface native SQLite exceptions
- Cumulative `SUM(amount)` can reach SQLite integer-overflow limits for an extreme account history
- Deferred Phase 3 hardening: initialization connection-close structure and proactive validation of a malformed pre-existing `managed_usage` table
- Seven RC1.2 unused import bindings remain a deferred P1 cleanup; Core Feature Freeze leaves production source unchanged

## Not Included

- Payment, Recharge, `PURCHASE`, or user-facing Refund workflow
- Admin UI, Authentication, Login, Password, OAuth, or RBAC
- Production SaaS / HTTP backend
- RAG, Multi-Agent collaboration, Multi-Model Router, or VS Code integration

## Upgrade Notes

- No separate database package or server is required; SQLite uses Python's standard library.
- Existing BYOK configuration and Gradio workflows remain available.
- Existing Phase 2 SQLite data migrates in place when opened by the V3.0.1 services; back up operational data before any upgrade as normal practice.
- Managed Credits and Admin operations have no Gradio UI in this release and are intended for trusted server-side integration.

## Roadmap

- V3.0.2 may provide a deferred commercial-infrastructure track for Admin UI, Payment interfaces, Recharge, and Auth / RBAC; all remain Planned.
- V3.1 Project Intelligence / RAG and V3.2 Controlled Multi-Agent Collaboration are the thesis-priority tracks.
- V3.3 Data-driven Multi-Model Router and V3.4 VS Code Integration remain Planned.
