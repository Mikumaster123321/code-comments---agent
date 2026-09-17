# Project Context

## Project

毕业设计：《基于大语言模型与多智能体协同的软件代码智能维护系统设计与实现》。项目正从 **Code Comments Agent** 渐进演进为智能软件代码维护系统；现有 Gradio 应用必须持续可用。

## Current State

- Current branch: `v3.0.0-test1`
- V3.0 roadmap:
  - Phase 0 — Engineering Baseline: completed
  - Phase 1 — Domain Core & Stable Symbol Identity: completed
  - Phase 2 — Processor Symbol Migration: completed
  - Phase 3.1 — Project Discovery / Project Scanner: completed
  - Phase 3.2 — Project Relationship Awareness / Project Graph: completed
  - Phase 3.2.1 — Graph Identity & Containment Hardening: completed
  - Phase 3.3 — Project Snapshot / State: next
  - V3.1 — Project Intelligence / RAG
  - V3.2 — Multi-Agent
  - V3.3 — Multi-Model Router
  - V3.4 — VS Code
- Test baseline: `60 passed`
- Phase 3.1 QA: `PASS` (Critical 0, Medium 0, Low observations 8; 12 independent probes passed)
- Phase 3.2: `Completed`
- Phase 3.2.1 hardening: `Completed`
- Next: Phase 3.3 — Project Snapshot / State

## Current Architecture

Current domain: `Project`, `SourceFile`, `Symbol`, `SymbolId`, `AnalysisFinding`.

`PythonAdapter` and `JavaAdapter` reuse the existing parsers. `SymbolId` is:

`language + relative_path + qualified_name + kind + semantic_disambiguator`

For Java overloads, `semantic_disambiguator` uses the normalized parameter signature. `fallback_line` is collision fallback only. `content_hash` is not part of normal identity.

Processor concurrency results, errors, annotated-source backfill, Markdown document
association, and navigation anchors use `SymbolId` as their internal identity key.

`ProjectScanner` builds a read-only `ScanResult` containing the project, directories,
files, detected languages, applied ignore rules, metadata, per-file hashes, and a
deterministic aggregate project hash. It does not perform code analysis.

`ProjectGraphBuilder` builds a deterministic in-memory `ProjectGraph` from a
`ScanResult`. Graph nodes are `PROJECT`, `FILE`, `SYMBOL`, and `EXTERNAL_MODULE`;
relations are limited to `CONTAINS` and `IMPORTS`. Project, file, and symbol identities
reuse `Project.id`, `ProjectFile.relative_path`, and `SymbolId`. Python imports are
discovered with the standard AST, while Java package and import discovery remains
best-effort compatibility without a parser framework. Exact, unique local module/type
matches resolve to file nodes; all other import targets remain deterministic unresolved
external-module nodes.

Class containment is attributed with the existing symbol source ranges and the parent
class `SymbolId`, rather than treating a bare qualified class name as unique. Python
relative imports use their importer package context to produce canonical graph
identities before local resolution; imports without a reliable package context use a
deterministic unresolved-relative identity instead of a guessed module.

`SourceFile.content_hash` hashes the entire file content. `Symbol.content_hash` hashes the
source slice returned for that symbol; neither hash is part of `SymbolId`.

## Known Debt and Boundaries

- The legacy Python parser does not extract nested functions or local classes inside functions.
- Java signature normalization is deterministic best-effort canonicalization for the
  parameter declarations currently needed by V3.0, not a complete Java compiler
  signature parser. The legacy regex parser guarantees only basic overload and
  parameter-declaration handling.
- V3.0 does not add RAG, Multi-Agent, Router, API, or VS Code integration; do not rewrite the Java parser. Migrate incrementally and keep Gradio working.
- Processor retains separate synchronous and progress-reporting pipelines; changes to
  processing stages must keep both paths behaviorally aligned.
- The legacy Java annotator is line-oriented: when several declarations share one
  physical line, their identities and documentation remain distinct, but generated
  Javadocs are inserted above the shared line rather than directly before each declaration.
- Project Scanner applies built-in rules, root `.gitignore`, and caller rules with a
  deterministic Gitignore-like subset. Nested ignore files and full Git ignore
  semantics are not implemented; symlinks are deliberately not followed.
- The Project Graph does not infer calls, references, inheritance, or wildcard/static
  import ownership. Python local resolution uses project-root module paths only; Java
  resolution requires an exact unique package/type match. Unmatched targets are
  unresolved rather than claimed to be third-party dependencies.
- Self-imports currently produce explicit self-loop `IMPORTS` edges. Star imports remain
  coarse targets such as `a.*`, and external-module nodes do not model package members.
- Python `src` layouts, `pyproject` packaging semantics, namespace-package semantics,
  installed packages, and complete import resolution remain deferred.
- Snapshots, dependency semantics beyond imports, graph persistence/databases, RAG,
  and incremental graph updates are outside Phase 3.2.

## Frozen Decisions

### BYOK / Credential & Provider Policy

- Official releases do not include a developer API key.
- Users configure their own Provider, Model, and Credential.
- API keys must not enter Git, ordinary configuration files, or logs.
- Phase 4.1 establishes the Provider/BYOK Foundation.
- The V3.4 IDE stage provides a secure credential-configuration UI.

## Collaboration

- Codex / GPT: primary implementation.
- Trae Work / DeepSeek: cost-effective independent QA, boundary tests, README/documentation, and small explicit assistance tasks.
- Cursor / Claude: advanced architecture reviewer and second opinion for complex refactors.
- ChatGPT: roadmap and architecture arbitration, thesis writing, and experiment design.
- The user makes final decisions and acceptance.

After each phase, update only facts that changed in **Current State**, **Test Baseline**, or **Known Debt**.
