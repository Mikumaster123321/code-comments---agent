# V3.0.1 RC1.2 — Repository Hygiene Audit

## Gate Result

**Verdict: PASS WITH CLEANUP RECOMMENDED**

Release Blockers: **0**.

V3.0.1 remains a Release Candidate. Core Feature Freeze remains **ACTIVE**. This
audit does not authorize a tag, push, package migration, source cleanup, README
change, Release Notes, or RC1.3 implementation.

## Hard Gate

| Item | Result |
|---|---|
| Branch | `v3.0.1-dev` |
| Gate input HEAD | `2d7d888a8f212ddcbd9704df6ada9afcf1fb7785` |
| Version | `code_maintenance.__version__ == "3.0.1-rc1"` |
| Initial Git status | Clean |
| RC1.1 | `PASS` |
| Release Blockers | `0` |
| Core Feature Freeze | `ACTIVE` |
| Expected test baseline | `414 passed` |
| Observed full suite | `414 passed` |

Plain `python -m pytest` reproduced the documented Anaconda Python 3.13.5
`pytest` debugging-plugin / `rlcompleter` segmentation fault before collection.
The approved host workaround, `python -m pytest -p no:debugging`, collected and
passed all 414 tests in 1.39 seconds. No real Provider, Credential, API, or network
LLM request was used.

## Audit Method and Scope

The audit was read-only until this report and `PROJECT_CONTEXT.md` were updated. It
used the tracked-file inventory, ignored/untracked status, import and reference
searches, Python AST import-load checks, package exports, Git blob identities,
runtime entry chains, test collection, documentation naming, ignore checks, and
sanitized credential/path pattern scans. No production source, tests, README,
release notes, public API, file placement, or history was changed.

## Root Directory Inventory

| Category | Root contents | Assessment |
|---|---|---|
| Runtime / Entry | `main.py`, `ui.py`, `processor.py`, `i18n.py`, `llm_service.py`, `llm_provider.py` | ACCEPTABLE |
| Configuration | `config.py`, `.env.example`, `.gitignore`, `pytest.ini`, `requirements.txt` | GOOD |
| Legacy Language Layer | `Py/`, `Java/` | KEEP |
| V3 Core | `code_maintenance/` | GOOD |
| V3.0.1 Credits / Managed / Admin | `credits/`, `managed_access/`, `admin_operations/` | GOOD |
| Tests | `tests/` | GOOD |
| Documentation | `README.md`, `docs/` | ACCEPTABLE |
| AI Collaboration | `AGENTS.md`, `CLAUDE.md`, `PROJECT_CONTEXT.md` | ACCEPTABLE |
| CI | `.github/workflows/pytest.yml` | GOOD |
| Generated / Ignored | `.DS_Store`, `.pytest_cache/`, root and package `__pycache__/` trees | GOOD: ignored and untracked |
| Repository Internals | `.git/` | EXPECTED |

There are 88 tracked files. The root remains a deliberately flat compatibility
layout around the Gradio runtime plus peer domain packages. Its contents reflect
real runtime, test, documentation, collaboration, and release-engineering roles;
root file count alone is not evidence for restructuring.

## Root Python Modules

| Path | Current purpose and evidence | Decision |
|---|---|---|
| `main.py` | Executable entry; imports `create_ui` and `CUSTOM_CSS`, launches Gradio | KEEP |
| `ui.py` | Gradio composition; imports Processor operations, i18n, and Provider configuration | KEEP |
| `processor.py` | Production orchestration for single/batch processing, analysis, progress, diff, workspace, and adapters; called by UI and tests | KEEP |
| `config.py` | Legacy-compatible Provider configuration and task-scoped Provider capture; used by UI, Processor, LLM service, and Provider tests | KEEP |
| `i18n.py` | Runtime translations and language helpers; used by UI, Processor, and LLM service | KEEP |
| `llm_service.py` | LLM generation, cleaning, retry, ping, and cost estimation; used by Processor and offline contract tests | KEEP |
| `llm_provider.py` | Credential-free model configuration, runtime Credential boundary, registry, and task-scoped Provider; used by configuration and Managed Access | KEEP |

No obsolete copy or dead root module was proved. Core Feature Freeze therefore
rules out a root-to-package migration.

The AST/reference audit did identify seven unused import bindings:

- `ui.py`: `process_code`, `process_batch_files`;
- `processor.py`: `io`, `sys`, `math`;
- `llm_service.py`: `LANG_CODE`;
- `managed_access/service.py`: `FlatPricingPolicy`, `InvalidFlatPricingError`.

Each appears only at its import site and has no runtime effect. This is a **P1 RC
cleanup recommendation**, not a release blocker. The imports were not removed in
this gate because source modification is outside the allowed RC1.2 change set.

## Legacy Python and Java Layers

`Py/` and `Java/` are production dependencies, not historical garbage:

- `processor.py` directly uses the Python parser, annotator, analyzer, Java parser,
  and Java annotator;
- `code_maintenance/adapters.py` reuses both legacy parsers;
- graph and snapshot construction consume those V3 adapters;
- dedicated parser and adapter regression tests cover both languages;
- `Java/java_annotator.py` reuses the Java parser's comment/string masker.

Both directories are **KEEP**. The presence of `code_maintenance/` does not replace
them.

## `code_maintenance/` Assessment

The package has six focused implementation modules: domain values, legacy adapters,
project scanning, graph construction, snapshot/diff state, and deterministic
analysis. Dependencies flow inward from graph/snapshot/analysis to domain and
adapters without Credits, Managed Access, Admin, Provider, Credential, network, or
LLM imports.

The known duplicate canonical helpers remain **P2 technical debt**:

- `_symbol_id_record` in `graph.py` and `snapshot.py`;
- `_node_record` in `graph.py` and `snapshot.py`;
- `_symbol_id_key` in `analysis.py` and `snapshot.py`.

They protect frozen identity, hashing, and ordering contracts. They are a future
merge candidate, not an RC refactor. No dead public API or redundant source file was
proved.

## `credits/` Assessment

Responsibilities are clear:

- `domain.py`: immutable Credit domain values, transaction types, normalization,
  validation, and typed failures;
- `ledger.py`: minimal `CreditLedger` Protocol and thread-safe in-memory backend;
- `sqlite_ledger.py`: persistent append-only SQLite backend with atomic idempotency;
- `__init__.py`: deliberate public contract exports.

`InMemoryCreditLedger` and `SQLiteCreditLedger` are intentional parallel backends,
not duplicate garbage. The package imports only the standard library and its own
domain; it does not depend on Managed Access, Admin Operations, Provider, UI, or LLM
infrastructure. No Phase 1 probe, temporary migration module, or obsolete copy is
present. **KEEP**.

## `managed_access/` Assessment

Responsibilities are clear:

- `domain.py`: access/request/status/usage/pricing-context values and failures;
- `pricing.py`: the one `PricingPolicy` contract plus the single flat and token
  implementations;
- `service.py`: Provider orchestration, reservation/finalization state, migrations,
  and atomic SQLite coordination;
- `__init__.py`: stable public exports.

No duplicate pricing implementation, legacy FlatPricing copy, migration helper file,
or test probe exists in production. The two unused pricing imports noted above are
the only concrete cleanup. The 710-line service is a maintenance signal, but current
state-machine and atomicity coupling does not justify an RC split. **KEEP**.

## `admin_operations/` Assessment

The package remains small: immutable Admin domain values and failures in `domain.py`,
trusted SQLite-backed orchestration in `service.py`, and explicit exports in
`__init__.py`. It depends on Credits and SQLite internals as designed and does not
depend on Managed Provider orchestration.

No Admin UI, authentication system, RBAC, Payment, purchase, public refund workflow,
or future-placeholder module is present. **KEEP**.

## Cross-Package Dependency Assessment

```text
Legacy runtime -> Py/Java, code_maintenance, Provider infrastructure
code_maintenance -> Py/Java
managed_access -> credits, llm_provider
admin_operations -> credits
credits -> standard library only
llm_provider/config/llm_service -> no credits/managed/admin reverse dependency
```

No obvious cross-package cycle was found. The frozen prohibitions remain satisfied:
Credits does not depend on Managed/Admin/Provider; `code_maintenance` does not depend
on Credits/Managed/Admin; Provider infrastructure does not depend on Credits; and
Admin Operations does not depend on Managed Provider orchestration.

## Package Export Assessment

The four audited `__init__.py` files expose coherent contracts:

- `credits`: domain values/failures, Protocol, and both backends;
- `managed_access`: domain values/failures, service/provider ports, and pricing
  policies;
- `admin_operations`: Admin values/failures and trusted service;
- `code_maintenance`: V3 domain, adapters, scanner, graph, snapshot, analysis, and
  sole executable `__version__` source.

No obsolete export was proved. The exported low-level `CreditLedger.refund` remains
a privileged primitive and is not evidence of a user-facing API leak. Public APIs
were not changed.

## Unused Source and Duplication Assessment

No tracked source file qualifies as a DELETE candidate. Entry-chain, import, test,
documentation, and export searches provide uses or contract evidence for every
production module. Public exports without an internal call site remain documented or
tested public contracts, not dead code.

Git blob IDs found no byte-identical tracked files. No copy-paste module, duplicate
schema owner, duplicate pricing implementation, or duplicate class implementation
was found. Similar SQLite schema initialization is owned by the relevant service,
while the in-memory and SQLite Credit ledgers intentionally implement one contract
over different storage backends.

## Tests Assessment

- `tests/` contains **19** `test_*.py` files and the full suite collects **414** tests.
- Naming maps clearly to Legacy parsers/adapters, Processor, Provider, Domain,
  Scanner, Graph, Snapshot, Analysis, Credits, SQLite, Managed Access, Usage/Pricing,
  hardening, and Admin Operations.
- There is no root `Test/`, scattered root test, empty test file, backup/copy,
  temporary probe, or historical QA attack script outside the permanent suite.
- Phase 1–4 hardening and hostile-input tests are permanent regression evidence and
  **KEEP**.

Large test files are a **P2 maintenance signal**, not cleanup evidence:
`test_managed_access.py` (793 lines), `test_admin_credit_service.py` (746),
`test_provider_foundation.py` (629), `test_credits_domain.py` (542),
`test_phase3_hardening.py` (497), `test_project_analysis.py` (496), and
`test_managed_token_pricing.py` (489). RC1 does not require a test-package rewrite.

## Documentation Assessment

`docs/development/`, `docs/qa/`, and `docs/release/` contain engineering evidence,
not disposable duplicates. All new V3.0.1 Development and QA reports are
version-qualified. Historical V3.0.0 reports retain their original unqualified names
and must not be renamed. No empty report, copy, backup, `final-final`, temporary QA
output, or raw agent scratch file was found.

`docs/release/Release_Notes_V3_0_0.md` exists exactly once. There is no V3.0.1 final
Release Notes file, as required at RC1.2. Development and QA evidence is **KEEP** even
where reports summarize the same milestones.

README's Directory Structure does not yet list `credits/`, `managed_access/`, or
`admin_operations/`, and its current-product text still describes V3.0.0. Those are
expected RC1.3 Product Documentation tasks, not reasons to modify README in this gate.
The permanent Version History policy remains present.

## AI Collaboration Assessment

`AGENTS.md` defines active engineering/test/Git rules; `CLAUDE.md` routes reviewers to
those rules and project context; `PROJECT_CONTEXT.md` remains the authoritative
architecture, frozen-contract, phase-state, debt, and roadmap context. No `CODEX.md`,
`TRAE.md`, Cursor scratch file, duplicate context file, or agent temporary output was
found.

At 793 lines before this gate, `PROJECT_CONTEXT.md` is becoming expensive to scan.
It remains usable and authoritative, so splitting or archiving it is **P2 future
maintenance**, not an RC action.

## Generated Artifacts and Git Hygiene

No generated artifact is tracked. Local `.DS_Store`, `.pytest_cache/`, package/root
`__pycache__/`, and bytecode files are ignored and untracked. No local or tracked
coverage output, HTML coverage, log, temp, backup, swap, SQLite database/sidecar,
workspace JSON, dump, or ZIP output was found. Ignored local caches need not be
deleted for release hygiene.

The initial Git status was clean. There were no staged changes. The only authorized
gate changes are this report and `PROJECT_CONTEXT.md`.

## `.gitignore` and Database Artifact Policy

The existing `.gitignore` covers virtual environments, `.env`, Python/pytest caches,
IDE files, OS junk, logs/temp diagnostics, coverage output, and the known local
workspace JSON pattern. It deliberately does not ignore broad `*.db`, `*.sqlite`, or
`*.sqlite3` patterns.

`SQLiteCreditLedger`, `ManagedAccessService`, and `AdminCreditService` all require the
caller to supply an explicit database path; the repository defines no default runtime
database filename or directory. Therefore no SQLite ignore change is needed now, and
broad patterns could hide legitimate future fixtures. If a future UI/backend chooses
a default, it should store runtime data in a dedicated user/runtime-data location and
add only the exact project-relative runtime directory or filename to `.gitignore`.
RC1.2 does not create such a directory.

## Security and Path Hygiene

No tracked real Credential, private-key header, AWS-like access key, bearer token,
password assignment, PEM/key file, token JSON, SQLite dump, or database was found.
The only secret-shaped strings are explicit `sk-your-...-here` placeholders in
`.env.example` and synthetic `sk-secret...` markers in offline privacy tests. They are
not usable Credentials. `.env.example` is required documentation and **KEEP**.

No tracked production code or user documentation contains a local `/Users/...` or
`/home/...` path. Pattern hits were collaboration-role names, generic examples of
paths being prohibited, and historical release-engineering evidence about the scan
itself. They are not environment leaks and remain **KEEP**.

## Large-File Assessment

Large files are maintenance signals only:

- `processor.py`: 2,717 lines;
- `ui.py`: 1,573 lines;
- `managed_access/service.py`: 710 lines;
- `PROJECT_CONTEXT.md`: 793 lines before this gate;
- the large regression files listed in the Tests section.

Line count alone does not prove poor ownership or justify splitting a frozen runtime,
state machine, evidence file, or regression suite. Decomposition is **P2**.

## Cleanup Classification

| Class | Path | Current purpose / evidence | Recommended action | Risk and reason |
|---|---|---|---|---|
| P0 | None | No release-blocking hygiene defect found | None | Release Blockers remain 0 |
| P1 | `ui.py`, `processor.py`, `llm_service.py`, `managed_access/service.py` | Seven imported bindings have no AST load or textual use beyond the import | Remove only in a dedicated cleanup or explicitly approved RC1.3 change; rerun all tests | Very low runtime risk, but production edits are outside RC1.2 and Freeze discourages opportunistic change |
| P2 | `code_maintenance/graph.py`, `snapshot.py`, `analysis.py` | Canonical record/key helpers are duplicated | Evaluate after release with golden identity/hash/order tests | Consolidation can alter frozen canonical contracts |
| P2 | `processor.py`, `ui.py`, `managed_access/service.py`, large tests | High line counts with real responsibilities and regression coverage | Decompose only with focused design and regression work | Large change surface; no current blocker |
| P2 | `PROJECT_CONTEXT.md` | Authoritative context has grown to a large single file | Consider current-state/history separation after release | RC split risks stale or conflicting authority |
| KEEP | `credits/ledger.py`, `credits/sqlite_ledger.py` | In-memory and persistent implementations of one Protocol | Keep both | Intentional backend parity, not duplication |
| KEEP | historical Development/QA reports | Versioned engineering and thesis evidence | Preserve | Similar summaries are not disposable copies |

## DELETE, MOVE, and MERGE Candidates

- **DELETE candidates:** No tracked DELETE candidates.
- **MOVE candidates:** None for RC1. Top-level `credits/`, `managed_access/`, and
  `admin_operations/` conform to the frozen V3.0.1 architecture and remain peers of
  `code_maintenance/`; `Py/`, `Java/`, and root runtime modules remain in place.
- **MERGE candidates:** Only the canonical helper family listed as P2. Do not merge it
  during RC1.

## Explicit KEEP List

The evidence supports keeping all of the following:

- root runtime modules and configuration;
- legacy `Py/` and `Java/`;
- `code_maintenance/`;
- `credits/`, `managed_access/`, and `admin_operations/` as top-level peer packages;
- all 19 test files and all Phase 1–4 hardening regressions;
- Development Reports and QA Reports;
- the unique V3.0.0 Release Notes;
- `AGENTS.md`, `CLAUDE.md`, and `PROJECT_CONTEXT.md`;
- CI, `README.md`, `.env.example`, `.gitignore`, `pytest.ini`, and requirements.

## Hygiene Scorecard

| Area | Rating | Basis |
|---|---|---|
| Root cleanliness | ACCEPTABLE | Deliberate compatibility layout; no junk; README tree update deferred |
| Source organization | ACCEPTABLE | Clear ownership; only unused imports and large-file debt |
| V3.0.1 package organization | GOOD | Frozen peer placement and dependency boundaries hold |
| Tests | GOOD | 19 named files, 414 passing tests, no temporary/empty/duplicate test artifact |
| Docs | ACCEPTABLE | Clear evidence structure; RC1.3 current-product update remains |
| Generated artifacts | GOOD | Local artifacts ignored; none tracked |
| Git hygiene | GOOD | Clean input, no generated/tracked clutter, no byte duplicates |
| Security hygiene | GOOD | No real tracked secret or private host path |

## RC1.3 Product Documentation Handoff

RC1.3 must update product documentation to state, without starting new feature work:

1. Current Version: **3.0.1-rc1** and still Release Candidate, not released.
2. V3.0.1 adds optional Managed AI Access while retaining BYOK.
3. Document the Credit ledger and explicit SQLite persistence boundary.
4. Document usage metering, token pricing, reservation/reconciliation, and flat-price
   compatibility.
5. Document trusted Admin grant and adjustment operations.
6. State clearly that Admin UI is not implemented.
7. State clearly that Payment/recharge/purchase is not implemented.
8. State clearly that authentication and RBAC are not implemented.
9. Record the full offline baseline as **414 passed**.
10. Add `credits/`, `managed_access/`, `admin_operations/`, and the new tests/reports
    to the current Directory Structure.
11. Add the concise permanent V3.0.1 Version History entry while preserving V3.0.0
    and older records.
12. Keep V3.0.2 commercial follow-ups and V3.1 RAG outside the current release.
13. Do not describe `CreditLedger.refund` as an ordinary user-facing API.

The P1 unused-import cleanup may be considered only as an explicitly approved,
separate narrow change; it is not required to write the RC1.3 documentation.

## Final Decision

RC1.2 is **COMPLETED — PASS WITH CLEANUP RECOMMENDED**. Release Blockers are 0;
there is no tracked deletion, move, package restructuring, or database-ignore change
to execute. RC1.3 Product Documentation is allowed to begin after this gate commit.
Core Feature Freeze remains **ACTIVE**. Tag and push are **not allowed** by this gate.

