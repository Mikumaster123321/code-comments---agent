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
  - Phase 3.3 — Project Snapshot / State: completed
  - Phase 3.3.1 — Snapshot Post-QA Hardening: completed
  - V3 Core Architecture Review: frozen by the Phase 4 architecture decisions
  - Phase 4 — Project Analysis Engine: completed
  - Phase 4.0.1 — Analysis Engine Post-QA Hardening: completed
  - Phase 4 Documentation Gate: completed
  - Phase 4.1 — Provider / BYOK Foundation: completed
  - Phase 4.1.1 — Legacy Provider Atomicity Hardening: completed
  - Phase 4.1 Documentation Gate: completed
  - V3.0 RC1.1 — Release Engineering Gate: completed (`PASS WITH ISSUES`)
  - V3.0 RC1.2 — Repository Hygiene Gate: completed (`PASS WITH CLEANUP RECOMMENDED`)
  - V3.0.0 — RC1 / current release candidate
  - V3.0.1 — Managed AI Access & Credits: planned
  - V3.1 — Project Intelligence / RAG: planned
  - V3.2 — Multi-Agent: planned
  - V3.3 — Data-driven Model Router: planned
  - V3.4 — VS Code Integration + Secure Credential UI: planned
- Test baseline: `129 passed`
- Phase 3.1 QA: `PASS` (Critical 0, Medium 0, Low observations 8; 12 independent probes passed)
- Phase 3.2: `Completed`
- Phase 3.2.1 hardening: `Completed`
- Phase 3.2 QA: `Final PASS` (initial `PASS WITH ISSUES`; D1/D2 verified in retest)
- Graph identity contract: `Preserved by Phase 3.3.1`
- Phase 3.3: `Completed`
- Phase 3.3 QA: `PASS WITH ISSUES` (Critical 0; M1/M2 resolved in Phase 3.3.1)
- Phase 3.3.1 Snapshot Post-QA Hardening: `Completed`
- Phase 3.3 DeepSeek directed retest: `PASS` (M1 PASS; M2 PASS; Golden Hash PASS)
- Phase 3.3 Final QA: `PASS` (further retest not required)
- Phase 4: `Completed`
- Phase 4 Independent QA: `PASS WITH ISSUES` (Critical 0; M1/M2 resolved in Phase 4.0.1)
- Phase 4.0.1 M1 finding validation/isolation: `Resolved`
- Phase 4.0.1 M2 recursion-depth-dependent SCC: `Resolved`
- Phase 4 DeepSeek directed retest: `PASS` (M1 PASS; M2 PASS; caller-stack independence PASS; fan-out regression PASS; determinism PASS)
- Phase 4 Final QA: `PASS` (further retest not required)
- Phase 4 tests: `32 passed`
- Offline LLM-contract smoke: `6 passed`
- Phase 4.1: `Completed`
- Phase 4.1 BYOK foundation: immutable credential-free `ModelConfig`, redacted
  runtime-only `RuntimeCredential`, read-only `ProviderRegistry`, and task-scoped
  provider/client construction over the existing Provider set
- Phase 4.1 task isolation: processor, analysis, batch, progress, preflight, retry,
  and direct LLM-service paths can use one explicitly captured provider/client without
  rereading mutable legacy active state during the task
- Phase 4.1 legacy compatibility: existing `switch_provider()`, `set_api_key()`,
  active getters, and Gradio UI remain available as a bridge that configures future
  task contexts
- Phase 4.1 security: credentials are excluded from `ModelConfig`, ordinary
  serialization, workspace persistence, provider/client representations, and sanitized
  provider error messages
- Phase 4.1 Independent QA: `PASS WITH ISSUES` (M1 directed for Phase 4.1.1)
- Phase 4.1.1: `Completed`
- Phase 4.1.1 M1 legacy Provider atomicity: `Resolved`
- Legacy Provider update contract: success atomically commits the complete active state;
  failure leaves every active scalar, client, and task-scoped provider unchanged
- Phase 4.1 tests: `19 passed`
- Phase 4.1 DeepSeek Directed Retest: `PASS`
- Phase 4.1 Final QA: `PASS` (Critical 0, Medium 0; further retest not required)
- Phase 4.1 Documentation Gate: `CLOSED`
- BYOK foundation: `Completed`; workspace persistence and `code_maintenance/` remain
  Credential/Provider-free at their respective persistence and domain boundaries
- Release metadata source: `code_maintenance.__version__ = "3.0.0-rc1"`
- Python support: minimum and recommended `3.10`; CI validates Python 3.10
- RC1.1 clean install: `PASS` in a repository-external Python 3.13.7 virtual
  environment; install, import, startup, dependency, and 129-test gates passed
- RC1.1 host note: the existing Anaconda Python 3.13.5 installation segfaults while
  importing both `gradio` and `rlcompleter`; this is isolated from the clean
  environment and is non-blocking for the release candidate
- RC1.1 security and portability checks: `PASS`; no tracked credential, workspace,
  cache, junk file, or production/user-document local absolute path was found
- RC1.2 repository hygiene: `PASS WITH CLEANUP RECOMMENDED`; Release Blockers `0`,
  no tracked delete candidate, and no directory restructuring approved for RC1
- V3.0 Core Feature Freeze: active; only release-blocker, packaging, startup,
  reproducibility, security, release-metadata, and necessary test changes are allowed
- Next: RC1.3 Product Documentation

## Planned Version Roadmap

### V3.0.0 — Current Release Candidate

V3.0.0 remains in RC1. It contains the completed V3 core and BYOK foundation and is
not yet a final release.

### V3.0.1 — Managed AI Access & Credits

Status: **PLANNED**. This is not part of V3.0.0 RC1, and no implementation module is
authorized by this roadmap entry.

V3.0.1 is intended to preserve BYOK while optionally allowing users without their own
API configuration to use platform-managed AI access. Planned capabilities are:

- BYOK mode remains available;
- optional platform-managed AI access;
- `CreditAccount` and `CreditLedger` concepts;
- administrative credit grants;
- usage metering;
- a `PricingPolicy` abstraction;
- a reserved recharge/payment interface.

The first implementation stage should support only `ADMIN_GRANT` and `USAGE`.
`PURCHASE` and payment-provider integration remain interface reservations rather than
mandatory first-stage integrations.

The platform Provider credential must never be delivered to a client or written into
a plugin, frontend, ordinary configuration file, or client package. Managed mode must
use this server-side boundary:

`Client -> Platform Backend -> Authentication / Credit Check -> Server-side Provider Credential -> LLM Provider`

### Later Planned Versions

- V3.1 — Project Intelligence / RAG: **PLANNED**
- V3.2 — Multi-Agent: **PLANNED**
- V3.3 — Data-driven Model Router: **PLANNED**
- V3.4 — VS Code Integration + Secure Credential UI: **PLANNED**

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

`SnapshotBuilder` builds an immutable in-memory `ProjectSnapshot` from a `ScanResult`
and the existing `ProjectGraph`. Snapshot file state uses normalized relative paths and
file content hashes; symbol state reuses `SymbolId` and `Symbol.content_hash`. Snapshot
content identity is a SHA-256 hash of an explicit canonical representation containing
the project identity, sorted file and symbol states, and sorted graph nodes and edges.
It excludes `created_at`, file mtimes, random values, object representations, and Python
hash values. `SnapshotDiff` compares snapshots from the same project root and reports
added, removed, changed, and unchanged files and symbols. Snapshot serialization is
limited to an in-memory `to_dict()` representation; no persistence layer exists.

`AnalysisEngine` is a deterministic service, not an Agent, over an existing
`ProjectSnapshot`. Each `AnalysisTool` is deterministic and read-only and consumes
only existing Snapshot/Graph state without reparsing source. The engine runs a small
ordered collection of tools, isolates each tool failure,
validates every returned `AnalysisFinding`, and canonically orders each tool's complete
output inside that tool's isolation boundary before final aggregation. A failed or
malformed tool produces a project-level `analysis.tool_failure` finding while the
remaining tools continue. Finding validation covers the string fields, integer line,
and optional `SymbolId` fields required by canonical ordering. Failure messages contain
only the stable tool id and exception type. The engine and tools do not scan, read
files, parse source, call adapters, use the network, or call an LLM.

Phase 4 provides `ComplexityTool`, `StructureTool`, and `DependencyTool`.
`ComplexityTool` reports direct method concentration per class from graph containment;
`StructureTool` reports per-file symbol density from snapshot symbol state; and
`DependencyTool` reports internal import cycles and high import fan-out from existing
`IMPORTS` edges. Dependency cycle detection uses deterministic iterative strongly
connected-component traversals and does not depend on Python's recursion limit. The
stable rule ids are `complexity.class_method_count`,
`structure.symbol_density`, `dependency.cycle`, `dependency.concentration`, and the
engine-owned `analysis.tool_failure`. Quality findings use `warning`; tool execution
failures use `error`.

`AnalysisFinding` scope conventions are: project-level findings use
`relative_path=""`, `line=0`, and `symbol_id=None`; file-level findings use the actual
relative path, an actual line or `0`, and `symbol_id=None`; symbol-level findings use
`Symbol.relative_path`, `Symbol.start_line`, and `Symbol.id`. Phase 4 keeps the existing
schema unchanged. Rule ids are deterministic, stable, lowercase machine-readable
dotted names.

`graph.py` owns the canonical graph node and edge ordering used by both
`ProjectGraphBuilder` and `SnapshotBuilder` through `canonicalize_graph()`; it is the
single source of truth for ProjectGraph canonical ordering. A graph built directly from
a scan is equal to the graph stored in its snapshot. Python parse boundaries skip
file-level symbol and import extraction on `SyntaxError` or `ValueError`, while
retaining the scanned file state and continuing to process other files.

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
- Root `__init__.py` relative imports retain a narrow precision gap because the project
  root does not provide a reliable package name.
- `Project.id` depends on the resolved absolute project root path. The first Phase 3.3
  Snapshot version defaults to time-series comparison under the same project root.
- Phase 3.3 QA M3 remains deferred: case-sensitive absolute-path spelling can affect
  `Project.id`; resolving it would change the frozen project identity contract.
- Snapshot construction reads supported source files again to capture symbol content;
  Phase 3.3 QA M4 remains a known limitation because concurrent filesystem changes
  during a scan/build sequence are not made atomic.
- Phase 3.3 QA L1 remains deferred: validation of an explicitly supplied `graph=` checks
  its project node identity but does not exhaustively validate every node and edge.
- Phase 3.3 QA L2/L3 retain the current content semantics: a class symbol's content hash
  includes its method bodies, so a method-body edit can mark both method and class as
  changed.
- Low maintenance note: `graph.py` and `snapshot.py` retain duplicate
  `_symbol_id_record` and `_node_record` implementations. This remains deferred and was
  not changed by Phase 4.
- Snapshot comparison is state comparison by file and symbol identity/content hash; it
  does not provide semantic diffs, AST edit scripts, history, repositories, or storage.
- Function/method source size, cyclomatic complexity, oversized-file byte/line rules,
  and source-text style rules are deferred because `ProjectSnapshot` does not retain
  the required source ranges, file sizes, or source text. Phase 4 does not reread or
  reparse source and does not expand the frozen Snapshot contract for these metrics.
- Symbol-level Phase 4 findings that require `Symbol.start_line` are deferred for the
  same reason. The implemented class-method concentration rule is reported at file
  scope with line `0` and identifies the class in its deterministic message.
- A Phase 4 `StyleTool` is deferred because no reliable style rule can be proved from
  the current `ProjectSnapshot`, `FileState`, `SymbolState`, and `ProjectGraph` data
  without reading source text.
- Phase 4 QA Low / technical debt remains deferred: the
  `structure.symbol_density` rule id, Finding deduplication, duplicate tool-id
  enforcement, missing `tool_id` behavior, `_symbol_id_key` helper duplication, and
  `TYPE_CHECKING` import cleanup. R1 retains the hostile cross-tool `str` subclass
  final-sort edge case, and R2 retains the hostile mutable `tool_id` failure-report
  edge case. These items do not block Phase 4.1.
- Dependency semantics beyond imports, graph persistence/databases, RAG, and
  incremental graph updates remain outside the current implementation.
- Phase 4.1 provides only an in-memory runtime credential boundary. It does not provide
  Keychain, Secret Service, Vault, encryption, database persistence, or credential UI;
  secure IDE credential storage remains deferred to V3.4.
- The legacy Gradio Provider selection remains process-level state for compatibility.
  Each started task now captures an isolated provider/client, while per-session UI
  configuration state remains future work.
- Provider clients still use the existing OpenAI-compatible SDK surface. Phase 4.1 adds
  no Provider, automatic selection, fallback policy, benchmark, model scoring, or Router.
- Phase 4.1 QA Low issues remain deferred: preflight price-footer presentation (L1),
  a dedicated `TaskScopedLLMProvider` serialization guard (L2), broader `base_url`
  validation (L3), unused public Provider APIs (L4), and normalized Registry errors for
  malformed metadata instead of raw `KeyError` (L5).
- Phase 4.1 QA note N1 remains deferred: `get_models_for_provider()` reads the custom
  model name without acquiring the active-state lock.

## Frozen Decisions

### Phase 3.3 Graph Identity Contract

- `PROJECT`, `FILE`, and `SYMBOL` identities continue to reuse `Project.id`, normalized
  relative paths, and `SymbolId`.
- Class containment uses existing symbol ranges to select the enclosing class and links
  through that class's `SymbolId`.
- Canonical Python import targets are used for both internal resolution and unresolved
  external-module identity.
- Phase 3.3 does not treat the current location-dependent `Project.id` as a portable
  cross-machine identity.

### BYOK / Credential & Provider Policy

- Official releases do not include a developer API key.
- Users configure their own Provider, Model, and Credential.
- API keys must not enter Git, ordinary configuration files, or logs.
- Phase 4.1 established the Provider/BYOK Foundation.
- `ModelConfig` is immutable ordinary configuration and remains credential-free.
- `RuntimeCredential` is runtime-only and excluded from ordinary serialization,
  workspace persistence, and non-redacted representations.
- `TaskScopedLLMProvider` is captured once per task; later legacy global switches do
  not alter an already-started task.
- Legacy Provider updates use atomic semantics: success commits the complete active
  state, while failure performs no active-state mutation.
- Workspace persistence remains credential-free, and `code_maintenance/` remains free
  of Provider, Credential, OpenAI SDK, and LLM dependencies.
- A future Router uses only providers already configured by the user.
- No secure credential store exists in Phase 4.1; the V3.4 IDE stage provides the
  secure credential-configuration UI.

## Collaboration

- Codex / GPT: primary implementation.
- Trae Work / DeepSeek: cost-effective independent QA, boundary tests, README/documentation, and small explicit assistance tasks.
- Cursor / Claude: advanced architecture reviewer and second opinion for complex refactors.
- ChatGPT: roadmap and architecture arbitration, thesis writing, and experiment design.
- The user makes final decisions and acceptance.

After each phase, update only facts that changed in **Current State**, **Test Baseline**, or **Known Debt**.
