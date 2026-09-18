# V3.0.1 Architecture Decision
## Managed AI Access & Credits

- **Status:** Frozen
- **Version:** V3.0.1
- **Phase:** Phase 0.1 — Architecture Decision Documentation
- **Scope:** Architecture and phase boundaries only; no Credits, Managed Access, Provider, or business-code implementation

## 1. Decision Summary

V3.0.1 preserves the V3.0 BYOK architecture and adds a separate, optional managed-access path. The target product flow is:

```text
ADMIN_GRANT -> Managed AI -> USAGE -> Ledger
```

The first implementation stages establish a small credit domain and a process-local, backend-facing managed-access boundary. They do not establish a production HTTP backend, payment system, full account system, or production billing platform.

## 2. LLM Access Model

The access modes are frozen as:

```text
LLMAccessMode
├── BYOK
└── MANAGED
```

The frozen minimum contract for a future `LLMAccessContext` is:

- `mode: LLMAccessMode`;
- `model_config: ModelConfig`;
- `account_id`: optional for `BYOK`, required for `MANAGED`;
- `request_id`: optional for `BYOK`, required for `MANAGED`.

Credentials are not part of `LLMAccessContext`. The context must not hold a client,
Provider, `TaskScopedLLMProvider`, or `RuntimeCredential`. Phase 0 freezes this contract
but does not implement the enum, context, or any other type.

## 3. BYOK Boundary

The V3.0 BYOK architecture remains unchanged, including:

- `ModelConfig`
- `RuntimeCredential`
- `ProviderRegistry`
- `TaskScopedLLMProvider`

BYOK does not depend on Credits, check Credits, or deduct Credits. V3.0.1 must not make the existing BYOK path conditional on the credit domain.

## 4. Managed Access Boundary

Managed mode will pass through `ManagedAccessService`, a process-local, backend-facing boundary. V3.0.1 does not create a real HTTP backend.

`ManagedAccessService` will eventually coordinate:

1. credit precheck;
2. server-side credential access;
3. Provider invocation;
4. usage accounting.

The platform credential is server-side only. It must never enter the UI, Gradio State, workspace data, ordinary configuration, credit records, logs, or `LLMAccessContext`.

In Managed mode, a client or UI caller must never receive the platform
`RuntimeCredential`, platform `TaskScopedLLMProvider`, raw Provider client, or platform
API key. A future `ManagedAccessService` may return only a safe result and safe
usage/accounting metadata; it must never return a Credential or Provider object.

## 5. Credit Domain

Phase 1 adds a top-level `credits/` package containing the domain concepts:

- `CreditAccount`
- `CreditTransaction`
- `CreditLedger`

The frozen `TransactionType` values for Phase 1 are:

- `ADMIN_GRANT`
- `USAGE`
- `REFUND`
- `ADJUSTMENT`

`PURCHASE` is not part of the Phase 1 enum.

The Phase 1 transaction amount convention is frozen as:

- `amount: int`;
- `ADMIN_GRANT`: `amount > 0`;
- `USAGE`: `amount < 0`;
- `REFUND`: `amount > 0`;
- `ADJUSTMENT`: positive or negative, but never zero;
- every transaction: `amount != 0`.

Phase 1 must provide a domain-level `grant` operation for tests and preparation of the Managed Access demonstration. An administrative UI or command wrapper is deferred to Phase 4.

## 6. Ledger and Balance

The ledger is append-only and authoritative. In Phase 1, balance is derived as:

```text
balance = sum(transactions)
```

Phase 1 must not introduce a cached authoritative balance.

Credits use integer units. Real monetary amounts and real costs use `Decimal`; `float` must not be used for real money or cost calculations.

Phase 0 does not define how a future `Decimal` cost is rounded or converted to integer
Credits. Phase 3 `PricingPolicy` must freeze that conversion and rounding rule.

## 7. Idempotency

`request_id` is the idempotency key for usage charging. A `USAGE` charge is unique by:

```text
(account_id, request_id)
```

Repeating a `request_id` for the same account must not deduct Credits more than once. Retries must preserve this rule.

## 8. Charging Contract

Phase 2 should implement **Guarded Charge-After-Success** under a per-account lock:

```text
balance precheck
-> provider invocation
-> successful result
-> USAGE charge
```

A Provider failure is not charged. This is a Phase 2 orchestration contract; Phase 1 must not implement Provider charging orchestration.

## 9. Storage

Phase 1 provides:

- a Repository Protocol;
- an in-memory implementation.

Phase 2 provides a SQLite implementation using the Python standard library `sqlite3` module.

V3.0.1 does not introduce an ORM, PostgreSQL, Redis, or a distributed database.

## 10. Pricing

Phase 1 establishes only the Credits Domain. It must not define or implement
`PricingPolicy`, `FlatPricingPolicy`, token pricing, or cost conversion.

Phase 2 owns the minimal flat-pricing behavior needed to complete the first Managed
Access call loop. Phase 3 introduces Provider-, model-, and token-based
`PricingPolicy` behavior and freezes the `Decimal` cost-to-integer-Credits conversion
and rounding rule. No commercial exchange ratio may be hard-coded into the architecture.

## 11. User Identity

Phase 1 represents user identity only as an opaque value:

```text
account_id: str
```

V3.0.1 does not implement login, passwords, OAuth, RBAC, or a multi-tenant account system.

## 12. Package and Dependency Boundaries

The new top-level package boundaries are frozen as:

```text
managed_access/ -> credits/
managed_access/ -> existing Provider infrastructure
```

The following dependencies are prohibited:

```text
credits/ -> managed_access/
credits/ -> Provider infrastructure
code_maintenance/ -> credits/
code_maintenance/ -> managed_access/
Provider infrastructure -> credits/
```

`credits/` and `managed_access/` are peers of `code_maintenance/`. Existing V3.0 files are not moved.

Phase 1 Credits Domain code **MUST NOT** import or call `llm_provider`, `llm_service`, the
Provider infrastructure in `config`, the OpenAI client, or any LLM Provider. Phase 1
must remain completely offline and Provider-independent.

## 13. Failure Model

V3.0.1 must explicitly handle or define behavior for:

- insufficient Credits;
- Provider failure;
- duplicate `request_id`;
- retry-driven duplicate charging;
- ledger or debit failure;
- Managed invocation success followed by accounting failure.

The case where a request times out but the Provider actually succeeded is a known limitation. V3.0.1 will document and contain that limitation rather than introduce a distributed transaction system.

## 14. Phase Plan

The V3.0.1 phase plan is frozen as:

1. **Phase 0 — Architecture & Scope**
2. **Phase 1 — Credits Domain + domain grant**
3. **Phase 2 — Managed Access Foundation + SQLite + flat pricing**
4. **Phase 3 — Usage Metering + token PricingPolicy**
5. **Phase 4 — Admin Operations Surface**
6. **Phase 5 — Payment Interface Reservation (optional)**
7. **RC**

Phase 5 may reserve at most a `PaymentProvider` Protocol. It must not implement Alipay, WeChat Pay, Stripe, a recharge button, or a real payment callback. Phase 5 may be skipped if Phases 1–4 already satisfy the V3.0.1 goal.

## 15. Out of Scope

The following are explicitly outside V3.0.1:

- real payment integration;
- a full account system;
- OAuth;
- RBAC;
- multi-tenant SaaS;
- a production HTTP backend;
- RAG;
- Multi-Agent orchestration;
- a model Router;
- VS Code integration;
- distributed databases;
- distributed transactions;
- a production billing platform.

## 16. Thesis Priority

V3.0.1 is an engineering-completeness enhancement, not the thesis's core algorithmic contribution. Once the `ADMIN_GRANT -> Managed AI -> USAGE -> Ledger` loop is complete, priority moves to V3.1 RAG and V3.2 Multi-Agent work. Commercial expansion must not delay the thesis core.

## 17. Consequences

- Existing BYOK behavior stays independent and backward compatible.
- Credentials remain outside both the access context and credit domain.
- The append-only ledger supplies a simple auditable source of truth.
- Idempotent usage charging and per-account serialization define the minimum correctness boundary.
- The architecture can evolve from in-memory storage to SQLite without introducing production infrastructure prematurely.
- Known ambiguity at the Provider/accounting boundary is accepted and documented for V3.0.1.
