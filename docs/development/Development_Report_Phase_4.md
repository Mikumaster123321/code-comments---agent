# V3.0 Phase 4 — Project Analysis Engine

## Background

Phase 3.1 established deterministic project discovery, Phase 3.2 established the
project relationship graph, and Phase 3.3 established immutable project state. Phase 4
adds the final major V3.0 Core analysis capability: deterministic project-level
findings derived from the existing `ProjectSnapshot` and `ProjectGraph`.

The initial implementation passed 100 tests and received an independent DeepSeek
verdict of **PASS WITH ISSUES**, with zero Critical and two Medium findings. Phase
4.0.1 corrected the per-tool Finding isolation boundary (M1) and recursion-dependent
cycle detection (M2). The directed retest passed both fixes, caller-stack independence,
fan-out regression, determinism, and the complete 110-test regression suite. The final
QA verdict is **PASS** and another retest is not required.

## Capability

Project-level Deterministic Analysis

## Objectives

- Analyze an existing `ProjectSnapshot` without scanning or reparsing source.
- Keep analysis deterministic, read-only, offline, and independent of LLMs.
- Isolate one tool's failure without losing findings from healthy tools.
- Reuse the existing Finding, Symbol, Snapshot, and Graph identity contracts.
- Provide a small set of useful structural and dependency rules without introducing an
  Agent, planner, registry framework, rule DSL, or dependency-injection framework.

## Architecture

```text
ProjectSnapshot
    |-- FileState / SymbolState
    `-- ProjectGraph (CONTAINS / IMPORTS)
             |
             v
       AnalysisEngine (Service)
             |
             +-- ComplexityTool
             +-- StructureTool
             `-- DependencyTool
             |
             v
     ordered AnalysisFinding[]
```

`AnalysisEngine` is a service, not an Agent. `AnalysisTool` is a deterministic tool
contract, not an Agent abstraction. Neither layer plans work, modifies source, calls an
LLM, or coordinates providers.

## AnalysisTool Contract

An `AnalysisTool` exposes a stable `tool_id` and one operation:

```python
analyze(snapshot: ProjectSnapshot) -> list[AnalysisFinding]
```

The contract is:

- deterministic for the same snapshot and configuration;
- read-only;
- no filesystem reread;
- no Scanner, parser, or language-adapter call;
- no network, API key, provider, or LLM dependency;
- output limited to `AnalysisFinding` values.

Phase 4 deliberately does not introduce a registry, plugin manager, rule DSL, planner,
or dependency-injection framework.

## AnalysisEngine

The engine accepts one `ProjectSnapshot`, orders its tools by stable `tool_id`, runs
each tool inside its own failure boundary, validates and canonically orders that tool's
complete output, aggregates healthy findings, and applies the final deterministic
ordering.

A failed or malformed tool produces one project-level `analysis.tool_failure` finding.
Its message contains only the tool id and exception type; raw exception messages,
object representations, and memory addresses are excluded. Other tools continue and
their findings remain available.

## MVP Analysis Tools

### ComplexityTool

`ComplexityTool` uses existing symbol-containment edges to count unique direct methods
per class. It emits `complexity.class_method_count` when the configured maximum is
exceeded. Because the Snapshot does not retain reliable source ranges, the finding is
reported at file scope with line `0`, while the deterministic message identifies the
class.

### StructureTool

`StructureTool` counts Snapshot symbols per file and emits
`structure.symbol_density` when the configured maximum is exceeded. It does not infer
file size or read source text.

### DependencyTool

`DependencyTool` consumes only existing `IMPORTS` edges. It emits:

- `dependency.cycle` for internal file strongly connected components, including
  self-cycles;
- `dependency.concentration` when unique outgoing import targets exceed the configured
  fan-out maximum.

Phase 4.0.1 uses deterministic iterative Kosaraju traversals. Cycle detection is
independent of Python recursion depth and caller-stack depth. Duplicate `IMPORTS` edges
continue to count as one fan-out target.

## AnalysisFinding Contract

The existing `AnalysisFinding` schema remains unchanged.

| Scope | `relative_path` | `line` | `symbol_id` |
|---|---|---:|---|
| Project | `""` | `0` | `None` |
| File | actual relative path | actual line or `0` | `None` |
| Symbol | `Symbol.relative_path` | `Symbol.start_line` | `Symbol.id` |

Phase 4.0.1 validates the fields required for safe canonical ordering:

- `rule_id`, `message`, `severity`, and `relative_path`: strings;
- `line`: integer;
- `symbol_id`: `SymbolId` or `None`, including the ordering-relevant `SymbolId` fields.

Quality findings use `warning`. Tool execution or output-contract failures use `error`.
Rule ids are stable lowercase machine-readable dotted names:

- `complexity.class_method_count`;
- `structure.symbol_density`;
- `dependency.cycle`;
- `dependency.concentration`;
- `analysis.tool_failure`.

## No Third Parsing Pipeline

Analysis operates exclusively on existing Snapshot and Graph state. No analysis tool
opens source files, calls `read_text()`, invokes `ast.parse()`, calls a language adapter,
or invokes a legacy parser. Phase 4 does not expand the Graph relation scope beyond
`CONTAINS` and `IMPORTS`.

The implementation contains no LLM, Agent, Provider, API-key, Router, RAG, or network
integration.

## Initial Implementation and Testing

Commit `2e42d7767f09e7e4030cbdaed0976fa41cbf7fa5`
(`feat(v3): add project analysis engine`) introduced the tool contract, engine, three
MVP tools, deterministic ordering, failure findings, exports, context documentation,
and 22 Phase 4 tests.

The full suite increased from 78 to **100 passed**. Initial coverage included zero,
one, and multiple tools; deterministic ordering; tool failure isolation; Finding scope;
threshold boundaries; acyclic and cyclic dependencies; fan-out; empty projects;
repeatability; and proof that analysis does not reread files.

## Initial DeepSeek QA

DeepSeek returned:

- Verdict: **PASS WITH ISSUES**;
- Critical: **0**;
- Medium: **2**;
- M1: a malformed `AnalysisFinding` could pass the shallow instance check and fail in
  final sorting outside the originating tool's isolation boundary;
- M2: recursive SCC traversal depended on Python recursion depth and the caller's
  current stack depth.

The review identified additional Low and technical-debt observations, but only M1 and
M2 were directed for Phase 4.0.1 correction.

## Phase 4.0.1 — Analysis Engine Post-QA Hardening

Commit `bbd081ee7ca6f0e83585adf9a2817ef385aa8b36`
(`fix(v3): harden project analysis after QA`) implemented the two directed fixes.

### M1 — Finding Validation and Per-Tool Canonicalization

Every returned Finding is now validated and canonically sorted inside the originating
tool's exception boundary. Invalid values for the six Finding fields are attributed to
that tool and converted into one deterministic `analysis.tool_failure`. Healthy tool
findings survive. Multiple malformed and raising tools remain isolated and produce a
stable failure order.

### M2 — Iterative Strongly Connected Components

The recursive SCC implementation was replaced with a two-pass iterative Kosaraju
implementation. Both traversals use explicit stacks and deterministic neighbor order.
No recursion-limit mutation or `RecursionError` fallback is used.

Repository regression coverage includes a 1,601-file deep chain, a deep graph with a
real cycle, self-cycle, two disjoint cycles, duplicate import edges, and a deterministic
3,000-file / 5,000-`IMPORTS` synthetic graph. Independent DeepSeek probes extended
depth and caller-stack coverage further.

## Testing and Final QA

Phase 4.0.1 added 10 collected cases. The Phase 4 suite increased from 22 to 32 tests,
and the full suite increased from 100 to **110 passed**. The offline LLM-contract smoke
suite remained **6 passed**. No real LLM, provider, credential, or network call was
used.

The DeepSeek directed retest reported:

- M1: **PASS**;
- M2: **PASS**;
- Caller Stack Independence: **PASS**;
- Fan-out Regression: **PASS**;
- Determinism: **PASS**;
- Full Regression: **110 passed**;
- Final Verdict: **PASS**;
- Retest Again: **Not Required**.

The local Codex Anaconda Python 3.13 environment can segfault while pytest loads its
debugging plugin through `readline` integration. Validation used the documented
`python -m pytest -p no:debugging` workaround; project test configuration was not
changed.

## Performance Baseline

Performance numbers distinguish the AnalysisEngine-only path from the full pipeline,
which includes discovery, source-state construction, graph construction, and Snapshot
construction.

| Measurement | Environment | State | Result |
|---|---|---|---|
| AnalysisEngine-only | Codex environment | 48 files, 318 symbols, 520 nodes, 685 edges | approximately 0.18 ms/run |
| AnalysisEngine-only | DeepSeek independent environment | 48 files, 318 symbols, 521 nodes, 686 edges | approximately 0.42 ms/run |
| Full pipeline | DeepSeek independent environment | same independent fixture | approximately 132 ms median |

The two Engine-only figures are environment-specific measurements, not contradictory
claims. The 0.18 ms figure is not a complete project-analysis pipeline time. Formal
performance comparisons must retain environment and pipeline-boundary labels.

## Deferred Analysis Capabilities

The following require state that the current Snapshot does not retain and are not
Phase 4 bugs:

- cyclomatic complexity;
- function or method source size;
- file byte and line metrics;
- source-level `StyleTool` rules;
- richer symbol-level findings that require reliable source locations.

## Technical Debt

Phase 4 Low / technical debt remains documented but unfixed:

- `structure.symbol_density` naming;
- Finding deduplication is not enforced;
- duplicate `tool_id` values are accepted;
- missing `tool_id` construction behavior;
- `_symbol_id_key` duplication;
- `TYPE_CHECKING` cleanup;
- R1: hostile cross-tool `str` subclass behavior at final sort;
- R2: hostile mutable `tool_id` behavior while reporting a failure.

Core deferred debt remains unchanged:

- M3: `Project.id` path portability and case spelling;
- M4: Scanner/Snapshot non-atomicity;
- L1: incomplete explicit-graph validation;
- L2/L3: class content-hash semantics include method bodies;
- duplicate graph/snapshot record helpers.

None of these items blocks Phase 4.1.

## Files Changed

The initial Phase 4 implementation changed:

- `PROJECT_CONTEXT.md`;
- `code_maintenance/__init__.py`;
- `code_maintenance/analysis.py`;
- `tests/test_project_analysis.py`.

Phase 4.0.1 changed:

- `PROJECT_CONTEXT.md`;
- `code_maintenance/analysis.py`;
- `tests/test_project_analysis.py`.

The Documentation Gate adds only this Development Report, the Phase 4 QA Report, and
factual `PROJECT_CONTEXT.md` updates. README, business code, tests, UI, Processor,
providers, and test configuration are unchanged by the Documentation Gate.

## Next Phase

Phase 4 and Phase 4.0.1 are complete and Final QA is **PASS**. After this Documentation
Gate closes, the project may proceed to **Phase 4.1 — Provider / BYOK Foundation** under
the frozen credential policy. Phase 4.1 is not started by this report.
