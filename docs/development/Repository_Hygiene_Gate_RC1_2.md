# V3.0 RC1.2 — Repository Hygiene Gate

## Purpose

This document records the completed V3.0 RC1.2 repository hygiene audit. It
preserves the audit decision and cleanup boundaries without rerunning or extending
the audit, changing the repository structure, or starting RC1.3.

## Environment

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Gate input HEAD | `43d3eff56f01721ddce3a676542a3a4ece30e86b` |
| Version | `3.0.0-rc1` |
| Initial status | Clean |
| Full suite | `129 passed` |
| Core Feature Freeze | Active |

The existing Anaconda Python 3.13.5 host requires the RC1.1-documented
`-p no:debugging` workaround. The complete 129-test suite passed with that
workaround; this remains a non-blocking host-environment issue.

## Verdict

**PASS WITH CLEANUP RECOMMENDED**

Release blockers: **0**.

No tracked file deletion, move, rename, source change, test change, or directory
restructuring is approved by this gate.

## Root Assessment

Root cleanliness is **ACCEPTABLE**. Root files are limited to runtime entry points,
configuration, legacy compatibility, documentation, tests, collaboration guidance,
and release engineering. The existing flat runtime layout does not justify a package
migration during the release candidate.

## Source Assessment

Source organization is **ACCEPTABLE**. Root runtime modules retain the existing
Gradio application, while `code_maintenance/` contains the V3 core. The size of
`processor.py` and `ui.py` is maintenance debt, not release clutter.

## Legacy Py/Java Assessment

`Py/` and `Java/` are **KEEP**. They remain production dependencies of `processor`,
the V3 adapters, graph and snapshot construction, and their parser tests. They have
not been replaced by `code_maintenance/`.

## code_maintenance Assessment

`code_maintenance/` is **KEEP**. Its domain, adapter, scanner, graph, snapshot, and
analysis responsibilities are clearly separated. The duplicated canonical helpers
`_symbol_id_record`, `_node_record`, and `_symbol_id_key` remain non-blocking
technical debt and must not be consolidated during RC1.

## Tests Assessment

Tests are **GOOD**. The `tests/` directory contains the committed automated suite;
no obsolete root test tree, temporary probe, empty fixture, skipped test, or duplicate
test body was identified. All 129 tests remain required.

## Docs Assessment

Documentation is **ACCEPTABLE**. Development and QA reports are engineering and
thesis evidence and remain **KEEP**. No empty report, backup copy, or duplicate report
was identified. Current-product README and entry-point documentation corrections are
deferred to RC1.3.

## AI Collaboration Files

`AGENTS.md`, `CLAUDE.md`, and `PROJECT_CONTEXT.md` are **KEEP**. They are active
collaboration policy and architecture context, not temporary tool output.

## Generated/System Files

Generated-artifact hygiene is **GOOD**. Local `.DS_Store`, `__pycache__/`, bytecode,
and `.pytest_cache/` content is ignored and untracked. No tracked cache, log,
workspace JSON, temporary archive, coverage output, IDE directory, or system junk was
identified. Manual deletion of ignored local caches is not a release requirement.

## .gitignore Assessment

The current `.gitignore` is **ACCEPTABLE** and correctly covers credentials, Python
and pytest caches, IDE settings, OS junk, logs, and known diagnostics. RC1.3 may add
only these approved narrow rules:

```gitignore
.coverage
.coverage.*
htmlcov/
coverage.xml
*_code_comments_agent_workspace.json
```

Broad rules such as `*.json` and `*.zip` are not approved.

## DELETE / MOVE / MERGE Candidates

- **DELETE:** no tracked candidate.
- **MOVE:** no move is recommended during RC1. `Py/`, `Java/`, root runtime modules,
  Development Reports, and QA Reports remain in place.
- **MERGE:** canonical helper consolidation is a post-V3.0.0 technical-debt candidate,
  not an RC cleanup.

## KEEP List

The gate explicitly keeps:

- root runtime and configuration modules;
- `Py/`, `Java/`, and `code_maintenance/`;
- `tests/` and its 129-test baseline;
- `docs/development/` and `docs/qa/`;
- `AGENTS.md`, `CLAUDE.md`, and `PROJECT_CONTEXT.md`;
- CI, dependency, environment-example, pytest, and ignore configuration.

## P0 / P1 / P2 Cleanup Decision

- **P0:** none; there is no release-blocking hygiene cleanup.
- **P1:** the only approved hygiene change for RC1.3 is the narrow `.gitignore`
  hardening listed above. The separately approved RC1.3 documentation corrections are
  recorded below.
- **P2:** after V3.0.0, evaluate canonical helper consolidation, `processor.py` and
  `ui.py` decomposition, package migration, and a future `docs/release/` structure.

No cleanup is executed as part of RC1.2.

## Hygiene Scorecard

| Area | Result |
|---|---|
| Root cleanliness | ACCEPTABLE |
| Source organization | ACCEPTABLE |
| Tests | GOOD |
| Docs | ACCEPTABLE |
| Generated artifacts | GOOD |
| Git hygiene | GOOD |

## RC1.3 Documentation Fix List

RC1.3 should:

1. Present the current version as V3.0.0 RC1 while preserving historical V2 entries.
2. State Python 3.10+ support and recommend Python 3.10.
3. Use `python -m pip install -r requirements.txt` and document the test command.
4. Record the current `129 passed` baseline without rewriting historical V2 counts.
5. Replace current-structure `Test/` references with `tests/`, including the old tree
   in `main.py`.
6. Document the V3 `code_maintenance/` architecture, `docs/development/`, `docs/qa/`,
   and CI.
7. Describe Project Scanner, Project Graph, Project Snapshot, Analysis Engine, stable
   `SymbolId`, and the BYOK Foundation.
8. Update the old V2.4 header in `.env.example`.
9. Keep RAG, Multi-Agent, the data-driven Model Router, and VS Code integration clearly
   identified as roadmap-only capabilities.
10. Apply the approved narrow `.gitignore` hardening without adding broad JSON or ZIP
    patterns.

## Final Recommendation

Close the RC1.2 Repository Hygiene Documentation Gate and allow RC1.3 to begin. Keep
the V3.0 Core Feature Freeze active. Do not perform repository restructuring, release
V3.0.0, create a tag, push, or begin roadmap implementation as part of this gate.
