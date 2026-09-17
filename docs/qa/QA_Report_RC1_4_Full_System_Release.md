# V3.0 RC1.4 Full-System Release QA

## Environment

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| HEAD | `932f6c29fb63b967a2ea9dbf6bda0440d37aa7aa` |
| Version | `3.0.0-rc1` |
| Python environment | CPython 3.10.20 |
| Clean venv | repository-external clean virtual environment |
| git status | clean (no staged, unstaged, or untracked change) |

RC1.4 was a read-only full-system release QA. No product code, test, README, or
version metadata was changed by the QA run.

The QA host was CPython 3.10.20 rather than the Anaconda Python 3.13.5 host recorded
in RC1.1, and `gradio` was not present in the base environment. All UI, install, and
startup validation was therefore performed in the repository-external clean virtual
environment. This is a known host difference and is not a product defect.

## Final Verdict

**PASS**

| Item | Result |
|---|---|
| Release Blockers | **0** |
| Medium | **0** |
| Low | 6 (all NON-BLOCKING) |

## Clean Install

A fresh virtual environment was created outside the repository with standard CPython,
then installed exactly as the README documents (`python -m venv`, activation, and
`python -m pip install -r requirements.txt`).

| Check | Result |
|---|---|
| clean venv install | **PASS** |
| `pip check` | **PASS** (`No broken requirements found.`) |
| Network failure | none |
| Repository dependency failure | none |

Resolved key dependency versions: `gradio 6.27.0`, `openai 1.109.1`,
`python-dotenv 1.2.3`, `pytest 8.4.2`, `pip 26.1.2`.

Network failure and repository dependency failure are distinguished here explicitly:
neither occurred, so the install result is attributable to the repository manifest
alone.

## README Command Validation

Every user-facing README command was executed or verified against the real
repository.

| Command | Result |
|---|---|
| `git clone` (documented remote) | **PASS** (remote reachable) |
| `python -m venv .venv` | **PASS** |
| venv activation (POSIX and Windows forms) | **PASS** |
| `python -m pip install -r requirements.txt` | **PASS** |
| `python -m pytest` | **PASS** |
| `python main.py` | **PASS** |

No `Test/` path, obsolete filename, developer-machine absolute path, or nonexistent
CLI argument was found. Windows and macOS/Linux instructions are reasonably
distinguished.

## No-Credential Startup

All Provider environment variables were isolated and no real API key was used.

| Check | Result |
|---|---|
| import | **PASS** (18 modules, including `main`, `ui`, `processor`, `llm_service`, `llm_provider`, `config`, `code_maintenance`) |
| UI creation | **PASS** (`Blocks` constructed successfully) |
| launch boundary | **PASS** (launch boundary reached with the documented `css` argument; no permanent web server was left running) |
| credential requirement | no API Credential required before an actual LLM request |

A missing key does not crash import or startup. The OpenAI-compatible client
constructs safely with the existing placeholder fallback, and `ModelConfig` remains
credential-free.

## BYOK User Flow

The BYOK flow was exercised fully offline against stub/mock providers.

| Path | Result |
|---|---|
| DeepSeek-style Provider | **PASS** |
| Custom OpenAI-compatible | **PASS** |
| Task-scoped Provider | **PASS** |

Available registry providers were `deepseek`, `openai`, `azure`, `dashscope`,
`moonshot`, and `custom`. Provider selection, model configuration, runtime credential
injection, and task start were consistent, and the README description of BYOK matches
the observed behavior. No real network request was made.

## Legacy Feature Integration

The legacy user-visible pipeline was exercised end to end with an offline stub
provider (13 stub calls, zero network traffic).

| Capability | Result |
|---|---|
| Python comment generation | **PASS** |
| Java Javadoc generation | **PASS** |
| Comment translation | **PASS** |
| Markdown / API documentation output | **PASS** |
| Diff output | **PASS** |
| Batch processing | **PASS** |
| Workspace save / restore | **PASS** |

The purpose of this section is release-integration confirmation, not a re-run of the
per-phase parser QA. No integration break was found.

## V3 Core Integration

| Capability | Result |
|---|---|
| ProjectScanner | **PASS** (deterministic result; built-in rules, root `.gitignore`, and ignored artifacts applied; symlinks not followed) |
| Stable SymbolId | **PASS** (Python same-named methods in two classes and Java overloads each keep distinct, stable identities) |
| ProjectGraph | **PASS** (node kinds project/file/symbol/external_module; relations limited to `CONTAINS` and `IMPORTS`; 19 nodes and 21 edges in the probe project) |
| ProjectSnapshot | **PASS** (content identity stable across repeated builds; `SnapshotDiff` detected a modified file and an added symbol) |
| AnalysisEngine | **PASS** (deterministic, read-only; all implemented rules fire; tool failure isolated through `analysis.tool_failure`) |

The README does not claim `CALLS`, `REFERENCES`, or `INHERITS` graph support, and the
implementation matches that boundary.

## Provider / Security

| Contract | Result |
|---|---|
| Task isolation | **PASS** (a running task's captured provider is unchanged by later switches) |
| legacy switch isolation | **PASS** (already-started tasks do not drift) |
| failed switch atomicity | **PASS** (a failed legacy update leaves active state unchanged) |
| workspace credential persistence | **0** (persisted keys limited to the credential-free whitelist) |

`RuntimeCredential` remains excluded from ordinary serialization, is rejected by
pickle, and is redacted in representations. The tracked repository contains no
credential: `.env` is not tracked, only `.env.example` with placeholder values, and
the apparent scan hits were all code identifiers such as `api_key: Optional[str]` or
`credential: RuntimeCredential` rather than secrets.

## Version Consistency

Current version is `3.0.0-rc1`, consistently reflected in:

| Location | Result |
|---|---|
| `code_maintenance/__init__.py` | **PASS** |
| `README.md` | **PASS** |
| `PROJECT_CONTEXT.md` | **PASS** |
| `main.py` | **PASS** |
| `.env.example` | **PASS** |

No location claims that V3.0.0 has been finally released.

## Version History

| Item | Result |
|---|---|
| V3.0.0 RC1 entry | **PASS** (concise main phases; `129 passed` baseline; hardening sub-phases not enumerated) |
| Historical V2 separation | **PASS** (historical V2.4.1 facts, including its 139-test record, are preserved and not rewritten as V3 current state) |

## Roadmap

| Version | Status |
|---|---|
| V3.0.1 Managed AI Access & Credits | **PLANNED** |
| V3.1 RAG | **PLANNED** |
| V3.2 Multi-Agent | **PLANNED** |
| V3.3 Router | **PLANNED** |
| V3.4 VS Code | **PLANNED** |

The V3.0.1 entry states its security boundary explicitly: the platform Provider
credential is server-side only and must never reach a client or ordinary
configuration. No unimplemented capability is described as completed. No V3.0.1
implementation artifact (`CreditAccount`, `CreditLedger`, payment, user backend, or
managed Provider gateway) exists in the repository; the V3.0.0 feature freeze holds.

## Repository Hygiene

| Check | Result |
|---|---|
| tracked repository clean | **PASS** (56 tracked files) |
| unexpected generated artifacts | none found (no cache, temporary file, backup, copy, workspace, coverage, or IDE metadata) |
| `.env` / workspace / credential tracked | no |
| `.gitignore` | **PASS** (the narrow RC1.2-approved coverage and local workspace rules are present and precise) |

Ignored local caches were not treated as failures.

## Tests

| Environment | Result |
|---|---|
| Development environment | **129 passed** |
| Clean venv | **129 passed** |

Per-suite counts were 6 / 11 / 3 / 6 / 8 / 32 / 13 / 5 / 18 / 19 / 4 / 4, totalling
129. Coverage includes the Provider foundation, Analysis, Graph, Snapshot, Scanner,
Processor regression, and LLM contract suites.

No real LLM or API network request was made, and no real credential was used. On this
host, plain `python -m pytest` completed without the documented Anaconda debugging
plugin workaround, so no workaround was required for this run.

## CI

`.github/workflows/pytest.yml` was reviewed.

| Item | Result |
|---|---|
| Python 3.10 | **PASS** |
| requirements install | **PASS** |
| pytest | **PASS** |
| secrets | none injected |

The workflow does not conflict with the README's Python 3.10+ statement.

## Known Low Issues

The following non-blocking observations were recorded during RC1.4. All are
**NON-BLOCKING**.

| Id | Observation |
|---|---|
| E1 | `config.py` retains a historical `v2.4.0` module docstring |
| E2 | `ui.py` retains a historical `v2.4.1` module header |
| E3 | `llm_service.py` retains a historical `v2.4.0` module docstring |
| E4 | Remaining V2.x inline comments in `i18n.py`, `processor.py`, and `ui.py` |
| E5 | `CUSTOM_MODEL_NAME` populates the startup dropdown but does not set the active model; the UI switch path itself behaves correctly |
| E6 | A historical tag exists and no git remote is configured |

E1 to E4 are source-comment wording only and are outside the user-facing README path,
so they do not reach Medium severity.

## QA Traceability

| Item | Result |
|---|---|
| All probes and the temporary venv | located outside the repository |
| Repository pollution | none |
| Real credentials copied | none |
| Repository state after QA | branch `v3.0.0-test1`, HEAD `932f6c29fb63b967a2ea9dbf6bda0440d37aa7aa`, clean status, `129 passed` |

All temporary probe scripts and the clean virtual environment were kept outside the
repository. No real credential value appears in this report or anywhere in the
repository.

## Final Recommendation

RC1.4 closed with **zero Release Blockers** and **zero Medium findings**, and the
repository was confirmed unmodified after the QA run. At the time of RC1.4, the
recommendation was to allow the project to proceed to:

**RC1.5 Claude Final Release Review**

At that time the RC1.5 review had not yet been recorded. This report therefore records
the RC1.4-stage conclusion only.
