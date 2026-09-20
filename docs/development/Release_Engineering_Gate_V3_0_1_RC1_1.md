# V3.0.1 RC1.1 — Release Engineering Gate

## Verdict

**PASS**

V3.0.1 may proceed to RC1.2 Repository Hygiene Audit. Release blockers: **0**.
Core Feature Freeze is **ACTIVE**. V3.0.1 remains a Release Candidate and is not
released. RC1.3 did not start, and no tag or push was created.

## Gate identity

| Item | Result |
|---|---|
| Branch | `v3.0.1-dev` |
| Gate input HEAD | `a833a7fc14f1d486a7b593378dd47509723522ed` |
| Initial status | Clean |
| Previous release | V3.0.0, released and frozen |
| Phase 0 through Phase 4 | Closed |
| Phase 4 Final QA | `PASS FOR PHASE 4` |
| Critical / Medium | `0 / 0` |
| Initial baseline | `414 passed` |
| Admin UI / Payment | Skipped for V3.0.1 |

Every hard-gate input matched. No feature, Admin UI, Payment, Recharge, `PURCHASE`,
authentication/RBAC, RAG, Agent, Router, API, or VS Code work was added.

## Version metadata decision

`code_maintenance.__version__` is the sole executable release-version source. The
tracked tree contains no packaging manifest or second executable version constant.
README still describes the released V3.0.0 product by design and is an RC1.3 update,
while older Development and QA reports retain historical V3.0.0 RC evidence.

RC1.1 changes the single source from `3.0.0` to `3.0.1-rc1`. It does not claim
`3.0.1` final and does not change README to Stable.

## Python support

- Minimum Python: **3.10**.
- Recommended Python: **3.10**.
- README and CI agree; CI uses Python 3.10.
- The dependency floor remains compatible with Python 3.10.
- Python 3.10 was not installed on this host, so the clean-environment execution used
  standard Homebrew CPython 3.13.7. This does not raise the supported minimum.

## Dependency audit

`requirements.txt` is unchanged from V3.0.0 and declares the existing direct
dependencies only:

| Dependency | Purpose | Constraint | Clean resolution |
|---|---|---|---|
| `openai` | OpenAI-compatible BYOK client | `>=1,<2` | `1.109.1` |
| `gradio` | Web UI | `>=6,<7` | `6.28.0` |
| `python-dotenv` | optional `.env` loading | `>=1,<2` | `1.2.3` |
| `pytest` | test runner | `>=8,<9` | `8.4.2` |

`credits/`, `managed_access/`, and `admin_operations/` import only the Python standard
library, existing project modules, and one another in the approved direction. SQLite
uses stdlib `sqlite3`. No ORM, SQLAlchemy, Redis client, PostgreSQL driver, Payment SDK,
or web-backend framework was introduced for V3.0.1. No missing mandatory or unused
V3.0.1-specific dependency was found.

## Clean install and full test

A new virtual environment was created outside the repository at a `/private/tmp` path.
The first dependency-install attempt was blocked by the execution sandbox's network
policy; this was a network-access failure, not a repository dependency failure. After
network access was approved, installation completed in **16.96 seconds**, with no
build failure. `python -m pip check` reported `No broken requirements found`.

The clean CPython 3.13.7 environment ran ordinary `python -m pytest` without a plugin
workaround: **414 passed in 3.50s**. No test was skipped or xfailed.

## Host test

The Anaconda Python 3.13.5 host reproduced the documented failure before test
collection: `rlcompleter` crashed while pytest's debugging plugin initialized, with
exit code 139. The approved host-only command `python -m pytest -p no:debugging`
passed **414 tests in 1.35s**. `pytest.ini` was not changed. The clean environment's
ordinary pytest pass isolates this as a host-distribution issue, not a product defect.

## Import, UI, startup, and no-credential safety

With all known Provider API-key variables removed and automatic `.env` loading
disabled, the clean environment successfully imported:

- `main`, `ui`, `processor`, `config`, `llm_provider`, and `llm_service`;
- `credits`, `credits.domain`, `credits.ledger`, and `credits.sqlite_ledger`;
- `managed_access`, `managed_access.domain`, `managed_access.pricing`, and
  `managed_access.service`;
- `admin_operations`, `admin_operations.domain`, and `admin_operations.service`;
- `code_maintenance` and its domain, adapters, scanner, graph, snapshot, and analysis
  modules.

`ui.create_ui()` completed without a key. Running `main.py` with only
`gradio.Blocks.launch` replaced by a local sentinel built the UI and reached the launch
boundary exactly once. No real Provider or network LLM request occurred. The legacy
BYOK layer may construct an inert client using its existing `EMPTY_API_KEY` fallback,
but an actual request still requires a runtime credential. Managed Access did not add
any startup credential requirement.

## BYOK and Managed Access assessment

The Provider-foundation regression suite passed **19 tests**. BYOK remains optional,
user-configured, independent of Credits, and independent of Admin Operations. The new
packages are not linked into the legacy Gradio/BYOK path.

An offline release-composition probe verified the technical loop using one explicitly
configured temporary SQLite file:

`Admin grant -> Credits -> Managed request -> reservation -> Provider stub -> usage -> token pricing -> USAGE debit -> ledger/history`

The probe granted 10 Credits, priced actual usage at 1 Credit, persisted
`ADMIN_GRANT` and `USAGE`, and returned balance 9. No Payment, Admin UI, authentication,
or real SaaS backend was required.

## SQLite safety and privacy

All SQLite-backed constructors require an explicit database path; no default database
path points at the repository. Tests use pytest temporary paths, and gate probes used a
repository-external temporary directory. The repository contained no `.db`, `.sqlite`,
`.sqlite3`, journal, WAL, or SHM file before or after validation.

The effective schemas are:

| Table | Columns |
|---|---|
| `credit_transactions` | sequence, transaction_id, account_id, transaction_type, amount, request_id, created_at, note |
| `credit_idempotency` | transaction_type, account_id, request_id, transaction_id |
| `managed_requests` | account_id, request_id, provider_id, model, base_url, reserved_credits, status, payload_hash, pricing_policy_id, payload_version, max_input_tokens, max_output_tokens |
| `managed_usage` | account_id, request_id, provider_id, model, input_tokens, output_tokens, final_credits |
| `admin_credit_operations` | actor_id, operation_id, operation_type, account_id, amount, reason, credit_transaction_id, created_at |

None contains `api_key`, `credential`, `password`, `prompt`, `completion`,
`raw_response`, or `client`. `note` and `reason` are intentional accounting/audit
business fields.

`.gitignore` does not need a broad `*.db` or `*.sqlite` rule: the application has no
default runtime database filename or directory, and broad patterns could hide a future
legitimate fixture. RC1.2 should reassess only if a precise runtime location or filename
is introduced.

## Security and path portability

Tracked files were scanned for private-key blocks, common live API/token signatures,
credential assignments, `.env`, databases, workspace data, dumps, and SQLite sidecars.
No suspected real credential or sensitive generated artifact was found. `.env.example`
and README contain explicit placeholder values only; tests use plainly fake markers.

Production code and user-facing README/release documentation contain no
`/Users/guo_wang/...`, `/home/...`, Codex/Trae temporary path, or other development-host
absolute path. Synthetic and pytest-managed paths in tests are acceptable.

## CI assessment

`.github/workflows/pytest.yml` remains appropriate:

- Python 3.10 matches the minimum and recommended version;
- it installs `requirements.txt` and runs standard `python -m pytest`;
- the current command collects and passes all 414 tests;
- no API, Payment, or platform Credential secret is referenced.

## Test inventory

The repository contains **19 test files** and **414 tests**.

| Group | Result |
|---|---|
| Admin Operations | `71 passed` |
| Phase 3 usage/pricing/hardening | `75 passed` |
| Managed Access | `44 passed` |
| SQLite ledger | `29 passed` |
| Credits | `66 passed` |
| BYOK Provider foundation | `19 passed` |
| Offline LLM contracts | `6 passed` |

No skip or xfail marker exists, and the full run reported none.

## Release scope

Implemented and release-assessed: Credits Domain, stdlib SQLite persistence, Managed AI
Access foundation, reservation and idempotency, Usage Metering, deterministic Token
Pricing, and trusted Admin grant/adjustment operations.

Not implemented: Admin UI, Payment, Recharge, `PURCHASE`, Auth/RBAC, real SaaS backend,
RAG, Multi-Agent, Router, and VS Code integration. `REFUND` remains a low-level Credits
primitive and is not exposed by the Admin or Managed services.

## Deferred technical debt

Release blockers: **none**. The following remain post-release Low/non-blocking debt and
were deliberately not fixed during feature freeze:

- Phase 4 L-2 close-after-use SQLite exception wrapping;
- cumulative SQLite `SUM(amount)` overflow after multiple individually valid amounts;
- Phase 3 L7 initialization connection-close structure and L8 proactive validation of
  a malformed pre-existing `managed_usage` table;
- Phase 1 Low items: transaction-ID collision enforcement, private-container exposure,
  integer upper bounds, global `RLock`, note normalization, hostile string subclasses,
  history-object hardening, and validation-helper duplication;
- Phase 2 single-process/reconciliation limitations, BYOK empty-account exception
  normalization, optional managed-request status index, unbounded positive Python
  integer flat price, and mutation-targeted coverage for defensive row-count branches;
- the pre-existing V3.0 Core and BYOK Low items already catalogued in
  `PROJECT_CONTEXT.md`.

## Repository artifact audit

No tracked cache, bytecode, coverage output, SQLite file, workspace, dump, temporary
file, backup/copy/old/final-final artifact, IDE metadata, or OS junk file was found.
Ignored local `.DS_Store`, pytest cache, and Python bytecode caches remain untracked and
are not release artifacts. Meaningful historical Development, QA, and Release evidence
was preserved.

## README RC1.3 fix list

RC1.1 does not modify README. RC1.3 should:

1. Change Current Version from V3.0.0 Stable to V3.0.1 RC, without calling it released.
2. Describe V3.0.1 as feature-complete and in release-candidate validation.
3. Add Credits Domain, SQLite persistence, Managed AI Access, reservations,
   idempotency, Usage Metering, Token Pricing, and Admin Operations to Available Now.
4. Preserve BYOK and explicitly state that it bypasses Credits/Admin dependencies.
5. State that Managed Provider credentials remain server-side.
6. State clearly that Admin UI, Payment, Recharge, `PURCHASE`, and Auth/RBAC are not
   implemented.
7. Update the test baseline from 129 to 414 while preserving the V3.0.0 historical
   baseline.
8. Add `credits/`, `managed_access/`, and `admin_operations/` to the directory tree.
9. Add a V3.0.1 RC entry to Version History and keep V3.0.0 as released history.
10. Preserve Python 3.10 minimum/recommended guidance and standard install/test commands.

## Release Notes plan

Future `docs/release/Release_Notes_V3_0_1.md` should include: release identity and
status; highlights; Credits Domain; SQLite persistence and migration; Managed Access
state machine, reservations, idempotency, recovery states, and server-side Credential
boundary; Usage Metering and Token/Flat Pricing; Admin grant/adjustment and audit;
BYOK compatibility; security/privacy; install and Python support; test/QA evidence;
upgrade/migration notes; known limitations and deferred debt; excluded scope; and
version history/acknowledgements. Final Release Notes must not be created before the
final release gate.

## RC1.2 repository-hygiene handoff

RC1.2 should explicitly audit:

- repository root: purpose and ownership of every tracked root file;
- `credits/`: public surface, package boundaries, generated artifacts, and naming;
- `managed_access/`: public surface, persistence/service separation, and artifacts;
- `admin_operations/`: trusted boundary, public surface, and artifacts;
- `code_maintenance/`: unchanged V3.0 Core ownership and stale metadata;
- `tests/`: 19-file inventory, temporary-path discipline, duplication, and fixtures;
- `docs/`: version-qualified reports, historical evidence, stale/duplicate artifacts;
- `AGENTS.md`, `CLAUDE.md`, and other AI collaboration files: purpose and consistency;
- generated caches, coverage, SQLite sidecars, dumps, temp/backup/copy files, IDE and OS
  artifacts;
- `.gitignore`: retain narrow project-specific rules and avoid broad database ignores
  without an actual runtime filename/directory.

RC1.2 must not perform a large directory restructuring or delete meaningful history.

## Gate result and next step

- V3.0.1 RC1 started.
- Core Feature Freeze: **ACTIVE**.
- RC1.1: **COMPLETED — PASS**.
- Release Blockers: **0**.
- Current RC baseline: **414 passed**.
- Next: **RC1.2 Repository Hygiene Audit**.
- RC1.3: allowed only after RC1.2; not started in this gate.
- Tag/push: **not allowed**.
