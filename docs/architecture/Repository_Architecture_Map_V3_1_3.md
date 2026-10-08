# Repository Architecture Map — V3.1.3

Status: V3.1.3 `IMPLEMENTATION / PRE-RELEASE`

This map describes the tracked repository as it exists in V3.1.3. It is navigation
and responsibility guidance, not a proposal to migrate the root application into a
package.

## 1. Runtime entry and orchestration — ACTIVE RUNTIME

| Path | Responsibility | Boundary |
| --- | --- | --- |
| `main.py` | Stable application entrypoint | Keep the root path |
| `ui.py` | Gradio construction, callbacks, and root `CUSTOM_CSS` compatibility re-export | UI behavior stays here |
| `processor.py` | Main processing, progress, batch, diff, and analysis orchestration plus workspace compatibility re-exports | Pipeline behavior stays here |
| `config.py` | Runtime configuration and Provider selection | No V3.1.3 semantic change |
| `i18n.py` | UI and output presentation language data | No V3.1.3 semantic change |
| `llm_provider.py` / `llm_service.py` | Provider abstraction and LLM calls/prompts | **DO NOT TOUCH in V3.1.3** |

## 2. Bounded support package — ACTIVE RUNTIME

`code_comments_agent/` is deliberately limited to two internal seams:

- `ui_styles.py` owns the unchanged `CUSTOM_CSS` value re-exported by `ui.py`;
- `workspace.py` owns save/load/clear persistence and related constants re-exported
  by `processor.py`;
- `__init__.py` marks the internal package and does not create a new public API.

UI callbacks, Gradio construction, Provider flow, processing, progress, ZIP, diff,
analysis, and formatting remain in their established root modules.

## 3. Language and maintenance domains — ACTIVE RUNTIME

- `Py/` — Python parsing, annotation insertion, documentation formatting, and
  analysis adapters.
- `Java/` — Java parsing, Javadoc insertion, documentation formatting, and
  validation adapters.
- `code_maintenance/` — language-neutral source, symbol, snapshot, graph, scanner,
  adapter, and analysis domain. `code_maintenance.__version__` is the project version
  checked by release tooling.
- `project_intelligence/` — released corpus, lexical/embedding, graph expansion,
  hybrid/index/context, and service implementation. **DO NOT TOUCH for V3.1.3
  semantics**.

## 4. Access and accounting domains — ACTIVE RUNTIME

- `credits/` — credit domain and ledger implementations.
- `managed_access/` — managed access, pricing, and service logic.
- `admin_operations/` — administrative domain and service operations.

These domains are present runtime responsibilities, not targets of the V3.1.3
extraction.

## 5. Experiment runtime and commands

- `experiments/` — benchmark schemas, configuration, baselines, metrics, execution,
  artifacts, serialization, eligibility, and reference lifecycle code. **ACTIVE
  RUNTIME for experiment tooling; Formal semantics DO NOT TOUCH**.
- `scripts/` — **DEVELOPER TOOLING**. `scripts/dev.py` is the stable command hub;
  the other scripts perform bounded validation or deterministic exports.
- `tests/` — **TEST**. Offline unit, compatibility, workflow, production, experiment,
  and release gates. Tests do not contact real LLM Providers or write real remotes.

## 6. Documentation information architecture

- `docs/development/` — **HISTORICAL DOCUMENTATION** plus the current V3.1.3 scope,
  development report, thesis materials, and the archived pre-V3.1.3 root context.
- `docs/qa/` — **HISTORICAL DOCUMENTATION / QA EVIDENCE**. The future
  `V3_1_3_Final_Release_QA.md` becomes authoritative only after independent QA
  actually executes.
- `docs/release/` — current release navigation, the permanent release contract,
  versioned release-note snapshots, and machine-readable `release_state.json`.
- `docs/experiments/` — **FROZEN FORMAL EVIDENCE**. Read-only; it is not current
  release-state authority.
- `docs/thesis/` — **USER-PROTECTED PATH / DO NOT TOUCH**. Its contents are outside
  this map and were not inspected.

Current human summaries are the root README, the current section of root
`PROJECT_CONTEXT.md`, and `docs/release/README.md`. Git objects plus
`docs/release/release_state.json` are the machine-readable current-state authority.

## 7. Runtime-generated data — RUNTIME GENERATED / UNTRACKED

- Python and pytest caches, coverage output, logs, and `*.tmp` files;
- local environment and IDE state;
- the workspace JSON in the operating-system temporary directory, named with a
  non-secret user hash;
- user-selected downloads and batch ZIP output produced during an application run.

These are not repository Source of Truth and must not be committed as release
evidence.

## 8. Change routing

- Repository navigation or release identity: V3.1.3 scope and release contract.
- Runtime behavior: established root/domain module and its existing tests.
- Formal result questions: frozen evidence and its validators; do not reinterpret or
  mutate in V3.1.3.
- Current status: Git plus `release_state.json`, then the three human current summaries.
- Historical claims: the versioned document that originally recorded the phase.
