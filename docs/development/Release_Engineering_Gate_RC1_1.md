# V3.0 RC1.1 — Release Engineering Gate

## Verdict

**PASS WITH ISSUES**

The repository is suitable to proceed to RC1.2 Product Documentation. V3.0 remains a
Release Candidate and is not marked released. No tag or push was created.

## Gate Identity

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Gate input HEAD | `686da8c6ee96b6ea3e88313e9fac04fa494df49e` |
| Initial status | Clean |
| Phase 4.1 Final QA | `PASS` |
| Phase 4.1 Critical / Medium | `0 / 0` |
| Phase 4.1 Documentation Gate | `CLOSED` |
| Initial test baseline | `129 passed` |

The default Anaconda Python 3.13.5 host segfaults while importing `rlcompleter` and
`gradio`. The `rlcompleter` path is the previously documented reason pytest requires
`-p no:debugging` on that host; direct module probes also isolated the UI-import crash
to `gradio`. The gate baseline passed with `python -m pytest -p no:debugging`, while a
separate clean Homebrew Python 3.13.7 environment passed ordinary pytest, all required
imports, UI construction, and startup without either failure. This is recorded as a
non-blocking host-environment issue rather than hidden with a product-code change.

## Repository Audit

- All tracked files were reviewed by category.
- No tracked cache, bytecode, pytest cache, `.DS_Store`, Windows junk file, temporary
  test artifact, generated workspace, `.env`, or credential file was found.
- Local `.DS_Store`, Python bytecode caches, and pytest cache are present only as
  ignored development artifacts. They were not deleted because they are not release
  blockers.
- `.gitignore` covers virtual environments, `.env`, Python/pytest caches, IDE files,
  macOS/Windows junk, and the repository's known temporary diagnostic files.
- No development-machine absolute path appears in production code or user
  documentation. The only synthetic absolute path is `/tmp/example` in a unit test.
- References to Codex, Trae, Cursor, and Claude are project collaboration instructions,
  not runtime working-directory dependencies.

## Python Support

- Minimum supported version: **Python 3.10**.
- Recommended version: **Python 3.10**.
- Evidence: the code parses with the Python 3.10 grammar, CI uses Python 3.10, and the
  resolved Gradio 6 distribution declares `Requires-Python >=3.10`.
- Python 3.13.7 also passed clean install, import, startup, and the full suite. The
  Anaconda 3.13.5 pytest-debugging crash is distribution-specific and does not change
  the supported floor.

## Dependency Audit

`requirements.txt` declares every mandatory direct dependency:

| Dependency | Role | Constraint | Clean-install version |
|---|---|---|---|
| `openai` | OpenAI-compatible Provider client | `>=1,<2` | `1.109.1` |
| `gradio` | Web UI | `>=6,<7` | `6.27.0` |
| `python-dotenv` | `.env` loading | `>=1,<2` | `1.2.3` |
| `pytest` | Test runner | `>=8,<9` | `8.4.2` |

`pycodestyle` is intentionally optional. `processor.py` imports it only inside the
style-check path and uses the documented built-in fallback when it is absent. The
clean environment did not contain `pycodestyle`, so the gate also verified that this
optional dependency is not an undeclared runtime requirement.

The bounded direct dependency ranges installed and tested successfully. No lockfile or
new packaging framework is required for this RC gate. The clean environment passed
`pip check` with no broken requirements.

## Clean Install, Import, and Startup

- A new virtual environment was created under `/private/tmp`, outside the repository.
- `pip install -r requirements.txt` completed successfully in 22 seconds after network
  access was permitted.
- The required imports passed without a real credential or network request:
  `config`, `llm_provider`, `llm_service`, `processor`, `ui`, `code_maintenance`, and
  the V3 `domain`, `scanner`, `graph`, `snapshot`, and `analysis` modules.
- Startup passed by executing `main.py` with only `gradio.Blocks.launch` replaced by a
  local sentinel. The application created its Gradio UI and reached the launch boundary
  exactly once without starting a persistent web server.
- No API key was present or required for install, imports, UI construction, or tests.
  An actual LLM request continues to require a user-supplied runtime credential.

## Version Metadata

The repository previously had no V3 release-version source. RC1.1 establishes the
minimal single source of truth:

```python
code_maintenance.__version__ = "3.0.0-rc1"
```

No packaging system or final `v3.0.0` tag was introduced.

## CI Assessment

`.github/workflows/pytest.yml` is appropriate for RC1:

- Python 3.10 matches the minimum and recommended supported version;
- dependencies are installed from `requirements.txt`;
- the job runs `python -m pytest`;
- no repository secret is requested;
- the test suite stubs LLM behavior and does not make real Provider calls.

No CI change was required.

## Security Check

The tracked tree was scanned for private-key blocks and common API-key, GitHub-token,
AWS-key, password, token, and secret assignment patterns. No suspected real credential
was found. `.env` and workspace data are not tracked. `.env.example` contains only
clearly marked placeholder values.

## Test Evidence

| Gate | Result |
|---|---|
| Full suite, documented Anaconda workaround | `129 passed` |
| Full suite, clean Python 3.13.7 environment | `129 passed` |
| Provider foundation | `19 passed` |
| Analysis | `32 passed` |
| Graph | `13 passed` |
| Snapshot | `18 passed` |
| Offline LLM contracts | `6 passed` |

No test was skipped or xfailed, and no real API, Provider, credential, or LLM network
request was used.

## Release Blockers

None.

## Non-Blocking Release Debt

- Direct dependencies use bounded compatible ranges rather than a fully pinned
  transitive lock. The clean-install gate proves the current resolution; a complex lock
  workflow is not justified for this project.
- Local ignored cache and OS metadata files remain in the developer checkout.
- The existing Anaconda Python 3.13.5 installation cannot import `gradio` or
  `rlcompleter`. Pytest requires `-p no:debugging`, and application startup should use
  the recommended clean Python 3.10 environment instead of that broken host runtime.
- Existing architecture and QA debt remains recorded in `PROJECT_CONTEXT.md`.

## RC1.2 Documentation Fix List

RC1.1 deliberately does not rewrite README content. RC1.2 should:

1. Change the README product version from `v2.4.1` to `v3.0.0-rc1` while preserving
   historical V2 changelog entries.
2. State Python 3.10 as both the minimum and recommended version.
3. Replace the ad-hoc dependency install command with
   `python -m pip install -r requirements.txt` and document the test command.
4. Replace the obsolete `Test/` references in `main.py` and README structure material
   with the current `tests/` tree.
5. Add the V3 `code_maintenance/` core, `docs/development/`, `docs/qa/`, and CI files to
   the documented repository structure.
6. Reconcile historical `139 tests` V2 statements with the current committed
   `129 passed` V3 baseline without rewriting historical evidence as current evidence.
7. Describe V3 Project Scanner, Graph, Snapshot, Analysis Engine, stable `SymbolId`, and
   task-scoped BYOK foundation, while clearly preserving the V3.0 feature boundaries.
8. Update the stale V2.4 header in `.env.example` and the V2-centric module docstrings
   without changing Provider behavior or placeholder credentials.

## Next Gate

RC1.2 Product Documentation is allowed to begin. V3.0 Core Feature Freeze remains in
effect. This gate does not release V3.0.0, create Release Notes, create a Git tag, push
changes, or start V3.1.
