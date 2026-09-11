# Project Context

## Project

毕业设计：《基于大语言模型与多智能体协同的软件代码智能维护系统设计与实现》。项目正从 **Code Comments Agent** 渐进演进为智能软件代码维护系统；现有 Gradio 应用必须持续可用。

## Current State

- Development branch: `v3.0-migration`
- V3.0 roadmap:
  - Phase 0 — Engineering Baseline: completed
  - Phase 1 — Domain Core & Stable Symbol Identity: completed
  - Phase 2: next
  - V3.1 — Project Intelligence / RAG
  - V3.2 — Multi-Agent
  - V3.3 — Multi-Model Router
  - V3.4 — VS Code
- Test baseline: `25 passed, 1 xfailed`

## Current Architecture

Current domain: `Project`, `SourceFile`, `Symbol`, `SymbolId`, `AnalysisFinding`.

`PythonAdapter` and `JavaAdapter` reuse the existing parsers. `SymbolId` is:

`language + relative_path + qualified_name + kind + semantic_disambiguator`

For Java overloads, `semantic_disambiguator` uses the normalized parameter signature. `fallback_line` is collision fallback only. `content_hash` is not part of normal identity.

## Known Debt and Boundaries

- The strict xfail documents a processor concurrency issue: results use the symbol `name` as a key, so same-named symbols can overwrite one another.
- The legacy Python parser does not extract nested functions or local classes inside functions.
- The Java regex parser guarantees only basic overload and parameter-declaration handling.
- V3.0 does not add RAG, Multi-Agent, Router, API, or VS Code integration; do not rewrite the Java parser. Migrate incrementally and keep Gradio working.

## Collaboration

- Codex / GPT: primary implementation.
- Trae Work / DeepSeek: cost-effective independent QA, boundary tests, README/documentation, and small explicit assistance tasks.
- Cursor / Claude: advanced architecture reviewer and second opinion for complex refactors.
- ChatGPT: roadmap and architecture arbitration, thesis writing, and experiment design.
- The user makes final decisions and acceptance.

After each phase, update only facts that changed in **Current State**, **Test Baseline**, or **Known Debt**.
