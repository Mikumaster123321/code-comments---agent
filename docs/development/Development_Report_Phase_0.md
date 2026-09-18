# V3.0.1 Phase 0 — Architecture & Scope Gate

## Background

V3.0.0 has been released and frozen. V3.0.1 targets **Managed AI Access & Credits**
while preserving the existing BYOK path.

Credits implementation could not safely begin immediately because V3.0 already has a
legacy Provider compatibility surface and task-scoped BYOK Providers. The Managed path
therefore required a frozen access, credential, package, and phase boundary first, so
that V3.0.1 would not create a third source of Provider state.

Phase 0 is documentation and architecture work only. It contains no Credits or Managed
Access business implementation.

## Phase 0.0 — Development Baseline

- development branch: `v3.0.1-dev`;
- base release: `v3.0.0`;
- V3.0.0 status: frozen;
- regression baseline: **129 passed**;
- offline LLM-contract smoke: **6 passed**;
- real Provider, credential, or network request: none.

On the current Anaconda Python 3.13.5 host, ordinary pytest reproduces the documented
debugging-plugin / `rlcompleter` segmentation fault. The approved
`python -m pytest -p no:debugging` workaround passes the full suite.

## Claude Architecture Review

The Claude architecture review allowed progression toward Phase 1 after the ADR was
frozen. Its principal decisions were the separate `BYOK` and `MANAGED` modes, the
`ManagedAccessService` boundary, an independent Credits Domain, an append-only ledger,
request idempotency, staged storage, strict package dependencies, and scope control.

The review did not authorize implementation before this Documentation Gate closed.

## Architecture Decision

The frozen decision is recorded in
[`Architecture_Decision_V3_0_1.md`](Architecture_Decision_V3_0_1.md).

## DeepSeek Architecture Consistency Review

The formal review verdict was **PASS WITH ISSUES**, with zero blocking findings:

- O-1: `LLMAccessContext` used candidate rather than frozen-contract wording;
- O-2: `PricingPolicy` phase ownership could be read as Phase 1 work;
- O-3: Provider and Managed-return prohibitions were not explicit enough;
- O-4: transaction signs and the ownership of future rounding rules were not frozen.

This Documentation Gate resolved all four observations without changing the frozen
architecture direction or any business code. No functional fix or retest was required.

## Final Frozen Contracts

- BYOK remains unchanged and independent of Credits.
- `LLMAccessMode` consists of `BYOK` and `MANAGED`.
- The future minimum `LLMAccessContext` contains `mode`, credential-free
  `model_config`, `account_id`, and `request_id`; the latter two are required for
  Managed mode and optional for BYOK.
- Credentials, clients, and Providers never belong to the access context.
- Managed callers receive only safe results and safe usage/accounting metadata.
- The Credits Domain is offline and Provider-independent.
- The ledger is append-only and authoritative; Credits are integer units.
- Transaction amounts are nonzero: grants and refunds are positive, usage is negative,
  and adjustments may be positive or negative.
- Usage charging is idempotent by `(account_id, request_id)`.
- Phase 1 provides only the Credits Domain, Repository Protocol, and in-memory storage.
- Phase 2 adds Managed Access, SQLite, and flat pricing.
- Phase 3 owns Provider/model/token pricing and the `Decimal` cost conversion rule.
- Payment is only an optional Phase 5 interface reservation.
- Package dependencies remain one-way from future `managed_access/` to `credits/` and
  existing Provider infrastructure; no reverse dependency is allowed.

## Scope

V3.0.1 does not implement real payment, a full account system, OAuth, RBAC,
multi-tenant SaaS, a production HTTP backend, RAG, Multi-Agent orchestration, a model
Router, or VS Code integration.

## Thesis Priority

V3.0.1 is an engineering-completeness enhancement. After the minimum
`ADMIN_GRANT -> Managed AI -> USAGE -> Ledger` loop is complete, thesis priority moves
to V3.1 RAG and V3.2 Multi-Agent work.

## Testing

- complete regression: **129 passed**;
- offline LLM-contract smoke: **6 passed**;
- business implementation introduced by Phase 0: none.

## Next

**Phase 1 — Credits Domain** is formally allowed after this gate, but remains **NOT
STARTED**. This report does not create or begin Phase 1.
