# V3.0.1 RC1.4 — Full-System Release QA

## Scope and evidence

This report records the independent DeepSeek RC1.4 Full-System Release QA evidence.
The QA run itself was read-only. This documentation gate does not add or rerun an
unreported probe, change the QA conclusion, or extend the security claims beyond the
observed surfaces.

No business code, test, README, Release Notes, version metadata, tag, or remote state
is changed by this gate. V3.0.1 remains a Release Candidate; Final Release and V3.1
have not started.

## Environment

| Item | Result |
|---|---|
| Branch | `v3.0.1-dev` |
| Gate input HEAD | `dfd0ecbce07033d51642b979f531d51d98fba2aa` |
| Version | `3.0.1-rc1` |
| Host | macOS |
| Clean venv | repository-external CPython 3.10.20 environment |
| Gate input git status | clean |
| QA mode | read-only |
| Real network LLM calls | none |
| Real Credentials | none |

The sandbox initially allowed inherited `PYTHONHOME`, `PYTHONPATH`, and
`sitecustomize` behavior to contaminate the clean virtual environment. DeepSeek
resolved this by using a repository-external isolated environment. This was a
host/sandbox environment issue, not a repository defect.

## Hard gate — 12/12 PASS

| # | Gate | Result |
|---:|---|---|
| 1 | Branch is `v3.0.1-dev` | **PASS** |
| 2 | HEAD is `dfd0ecbce07033d51642b979f531d51d98fba2aa` | **PASS** |
| 3 | Version is `3.0.1-rc1` | **PASS** |
| 4 | Git status is clean | **PASS** |
| 5 | RC1.1 is `PASS`, Release Blockers 0 | **PASS** |
| 6 | RC1.2 is `PASS WITH CLEANUP RECOMMENDED`, Release Blockers 0 | **PASS** |
| 7 | RC1.3 Product Documentation is complete | **PASS** |
| 8 | DeepSeek RC1.4 verdict is `PASS` | **PASS** |
| 9 | RC1.4 Release Blockers are 0 | **PASS** |
| 10 | RC1.4 Product Critical / Product Medium are 0 / 0 | **PASS** |
| 11 | Full clean-environment suite is `414 passed` | **PASS** |
| 12 | V3.0.1 Core Feature Freeze is `ACTIVE` | **PASS** |

Phase 0 through Phase 4 are **CLOSED**. Admin UI and optional Phase 5 Payment
Interface Reservation are **SKIPPED** for V3.0.1.

## RC1.3 commit chain

The RC1.3 documentation chain assessed by this gate was:

```text
c4ac1b5... -> dfd0ecb...
```

The second commit changed only
`docs/release/Release_Notes_V3_0_1.md` (`+2/-1`) to adjust blank-line formatting.
It did not change business code, tests, version semantics, product scope, or a
security boundary.

## Clean install and tests

| Check | Result |
|---|---|
| Clean venv | **PASS** — CPython 3.10.20 |
| Dependency install | **PASS** |
| `pip check` | **PASS** — `No broken requirements found` |
| Standard `python -m pytest` | **PASS** — `414 passed` |

The clean-environment result used the standard test command. Host and sandbox
differences are recorded in the Environment section and did not indicate a repository
dependency or product defect.

## Import and no-Credential startup

| Check | Result |
|---|---|
| Module imports | **PASS** — 24 modules |
| No-key startup | **PASS** |
| UI construction | **PASS** |
| `main` launch boundary | **PASS** |

No real Credential was used, and no real Provider or network LLM call was made.

## Legacy integration — 8/8 PASS

The full legacy integration smoke used only Stub Providers and remained offline.

| Capability | Result |
|---|---|
| Python comments | **PASS** |
| Java comments | **PASS** |
| Translation | **PASS** |
| Markdown / API documentation | **PASS** |
| Diff | **PASS** |
| Batch | **PASS** |
| Quality analysis | **PASS** |
| Pipeline | **PASS** |

## BYOK

BYOK passed without touching Credits, `ManagedAccessService`, or
`AdminCreditService`. The task-scoped Provider showed no configuration drift.
`RuntimeCredential` remained redacted and non-serializable. All validation was
offline.

## Managed end-to-end

The observed managed flow completed this real accounting loop against the temporary
QA database:

```text
Admin grant 1000
-> reserve 7
-> Provider response with actual price 2
-> USAGE -2
-> final balance 998
```

The Provider was called exactly once. The expected final row counts were:

| Table | Rows |
|---|---:|
| `credit_transactions` | 2 |
| `credit_idempotency` | 1 |
| `managed_requests` | 1 |
| `managed_usage` | 1 |
| `admin_credit_operations` | 1 |

The two Credit transactions were the Admin grant and final `USAGE` debit. The
reservation was an active managed-request state, not a separate Credit transaction;
unused reservation capacity was released without a refund row.

## Replay and restart

| Check | Result |
|---|---|
| Managed replay | **PASS** — 0 extra Provider calls, 0 extra `USAGE` rows, 0 duplicate charges |
| Admin replay | **PASS** — 0 duplicate grants |
| Restart | **PASS** — balance, history, Admin audit, managed request, and usage were preserved |

## Failure and reservation behavior

Provider failure, missing usage, usage over the declared limit, and insufficient
balance all failed closed. No case produced a partial `USAGE` write or duplicate
charge.

- Provider failure followed the terminal failure contract without a partial debit.
- Missing or over-limit usage after Provider success retained the reservation under
  the reconciliation contract and did not automatically call the Provider again.
- Insufficient balance stopped the request without a partial debit.
- Replay did not duplicate a Provider call where the persistent request state forbids
  retry.

## Admin operations

Grant, adjustment, balance, history, idempotency, and negative-balance prevention all
passed. Refund is not exposed by the Admin surface. Admin UI is not implemented in
V3.0.1.

## SQLite schema

The final business schema contained five tables:

1. `credit_transactions`
2. `credit_idempotency`
3. `managed_requests`
4. `managed_usage`
5. `admin_credit_operations`

The sensitive-column scan found **0** sensitive columns on these tables.

## Migration

| Migration path | Result |
|---|---|
| Phase 2-shaped database -> current schema | **PASS** |
| Phase 3-shaped database -> Admin schema | **PASS** |

Both paths were atomic, data-preserving, and safe to reopen. V3.0.0 had no billing
SQLite schema, so there is no V3.0.0 billing-database migration and this report does
not claim one.

## Credential security and data privacy

| Check | Result |
|---|---|
| Credential scan | **PASS** — 15 surfaces, 0 occurrences |
| Prompt persistence scan | **PASS** — 0 occurrences |
| Completion persistence scan | **PASS** — 0 occurrences |
| Workspace whitelist | **PASS** |
| Privilege boundary | **PASS** |

These results describe the tested surfaces and frozen architecture boundaries. They
are not a claim of general-purpose authentication, RBAC, enterprise IAM, or an
unbounded security guarantee.

## Product documentation and repository hygiene

| Check | Result |
|---|---|
| README | **Accurate** |
| Release Notes | **Accurate** |
| Version | `3.0.1-rc1` |
| Current status | RC1, not final |
| Repository hygiene | **PASS** |

## Final verdict

**PASS**

| Severity | Count |
|---|---:|
| Release Blockers | **0** |
| Product Critical | **0** |
| Product Medium | **0** |

No release fix is required. No directed retest is required. RC1.4 Full-System Release
QA is closed, and V3.0.1 is allowed to proceed to **RC1.5 Final Release Review**.
