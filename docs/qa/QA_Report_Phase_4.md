# V3.0 Phase 4 — Project Analysis Engine QA Report

## Final Verdict

**PASS**

The initial DeepSeek review returned **PASS WITH ISSUES**, with zero Critical and two
Medium findings. Codex implemented the directed Phase 4.0.1 fixes in commit
`bbd081ee7ca6f0e83585adf9a2817ef385aa8b36`. The DeepSeek directed retest passed M1,
M2, caller-stack independence, fan-out regression, determinism, and the complete
110-test regression suite. Another retest is **Not Required**.

```text
Initial DeepSeek QA: PASS WITH ISSUES
    -> Critical: 0
    -> Medium: 2
    -> M1 malformed Finding isolation
    -> M2 recursive SCC depth dependence
Codex Phase 4.0.1: bbd081ee7ca6f0e83585adf9a2817ef385aa8b36
DeepSeek directed retest:
    -> M1 PASS
    -> M2 PASS
    -> Caller Stack Independence PASS
    -> Fan-out Regression PASS
    -> Determinism PASS
Final Verdict: PASS
```

## Review Scope

The QA cycle covered:

- the deterministic, read-only `AnalysisTool` contract;
- `AnalysisEngine` tool ordering, aggregation, canonical Finding ordering, and failure
  isolation;
- Finding field validation and deterministic failure reporting;
- `ComplexityTool`, `StructureTool`, and `DependencyTool` behavior;
- import-cycle SCC correctness, deep-graph safety, caller-stack independence, and
  unique-target fan-out semantics;
- repeated-run and cross-process determinism;
- empty projects and malformed tool output;
- regression isolation from the existing application and offline LLM contract.

The review did not expand scope into source reparsing, richer Graph relations, Finding
deduplication, LLMs, Agents, Providers, Router, RAG, APIs, VS Code, or Phase 4.1.

## Environment and Versions

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Initial implementation | `2e42d7767f09e7e4030cbdaed0976fa41cbf7fa5` |
| Phase 4.0.1 fix | `bbd081ee7ca6f0e83585adf9a2817ef385aa8b36` |
| Initial full suite | 100 passed |
| Final Phase 4 suite | 32 passed |
| Final full suite | 110 passed |
| Offline LLM-contract smoke | 6 passed |
| Real network/provider calls | None |

The Codex host uses Anaconda Python 3.13 and requires the previously documented
`-p no:debugging` pytest workaround for a native `readline`/debugging-plugin crash.
Project configuration was not changed.

## Initial DeepSeek QA

- Verdict: **PASS WITH ISSUES**;
- Critical: **0**;
- Medium: **2**;
- Required fixes: **M1**, **M2**.

The initial implementation otherwise satisfied the Phase 4 architecture: Snapshot-only
analysis, deterministic tools and ordering, no third parsing pipeline, and no LLM,
Agent, Provider, or network dependency.

## M1 — Malformed AnalysisFinding Isolation

### Finding

The initial engine checked only that tool outputs were `AnalysisFinding` instances.
Malformed field values could therefore reach the final canonical sort, which was
outside the originating tool's failure boundary. Invalid `symbol_id`, `line`, severity,
or other ordering fields could raise `AttributeError` or `TypeError`, abort the entire
engine call, and discard healthy-tool findings.

### Fix

Phase 4.0.1 validates each tool's complete output and canonically sorts it inside that
tool's exception boundary. Validation covers the six Finding fields and the
ordering-relevant `SymbolId` fields. A malformed tool now produces one deterministic
project-level `analysis.tool_failure`; healthy-tool findings survive. Failure messages
contain the stable tool id and exception type but exclude raw exception messages,
object representations, and memory addresses.

### Directed Retest Evidence

- malformed Finding attacks against all six fields were isolated;
- malformed `symbol_id`: **PASS**;
- malformed `line`: **PASS**;
- malformed `severity`: **PASS**;
- multiple simultaneous malformed and raising tools: **PASS**;
- healthy-tool findings survived every bad-tool probe;
- deterministic failure count and order: **PASS**;
- M1 result: **PASS**.

## M2 — Recursive SCC Depth Dependence

### Finding

The initial `DependencyTool` used recursive SCC traversal. Correctness therefore
depended on Python's recursion limit and on how much caller stack was already consumed.
A deep acyclic import chain could produce `RecursionError` and be converted into
`analysis.tool_failure` even though the graph itself was valid.

### Fix

Phase 4.0.1 replaced recursive SCC traversal with deterministic two-pass iterative
Kosaraju traversal. Explicit stacks are used for finishing order and reverse-graph
component discovery. Neighbor and component ordering remains canonical. The fix does
not call `sys.setrecursionlimit()` and does not catch `RecursionError` to simulate
success.

### Directed Retest Evidence

- deep graph probes at 1,601, 3,000, 5,000, 10,000, and 20,000 vertices completed
  without recursion failure;
- deep acyclic graphs produced no cycle Finding or tool-failure Finding;
- a real cycle at depth was detected correctly;
- self-cycle detection: **PASS**;
- two disjoint cycles and stable ordering: **PASS**;
- caller-stack depths from 0 through 900 produced identical output: **PASS**;
- M2 result: **PASS**.

## Determinism and Fan-out Regression

- duplicate `IMPORTS` edges count as one unique fan-out target;
- acyclic, cycle, and fan-out behavior remained compatible;
- repeated runs produced identical Finding sets and order;
- multi-process probes across `PYTHONHASHSEED` values passed;
- 3,000 files / 5,000 `IMPORTS` synthetic graph: **PASS**;
- Caller Stack Independence: **PASS**;
- Fan-out Regression: **PASS**;
- Determinism: **PASS**.

## Performance Evidence

Performance measurements distinguish the Engine-only path from the full pipeline.

| Measurement | Environment | State | Result |
|---|---|---|---|
| AnalysisEngine-only | DeepSeek independent environment | 48 files, 318 symbols, 521 nodes, 686 edges | approximately 0.42 ms/run |
| Full pipeline | DeepSeek independent environment | same fixture | approximately 132 ms median |

The earlier Codex measurement of approximately 0.18 ms/run was an
**AnalysisEngine-only measurement in the Codex environment**, not full project-analysis
time. Environment-specific measurements are retained with their boundaries and are not
treated as contradictory.

## Regression Evidence

- Phase 4 tests: **32 passed**;
- complete pytest suite: **110 passed**;
- offline LLM-contract smoke: **6 passed**;
- malformed Finding six-field isolation: **PASS**;
- multiple bad-tool isolation: **PASS**;
- 1,601 / 3,000 / 5,000 / 10,000 / 20,000 deep-graph probes: **PASS**;
- deep real-cycle detection: **PASS**;
- caller-stack 0–900 output equality: **PASS**;
- cross-process `PYTHONHASHSEED` determinism: **PASS**;
- 3,000-file / 5,000-`IMPORTS` synthetic graph: **PASS**;
- real LLM, provider, credential, or network calls: **none**.

## Deferred Low and Technical Debt

The following Phase 4 observations are recorded and not fixed:

- `structure.symbol_density` naming;
- Finding deduplication is not enforced;
- duplicate `tool_id` values are accepted;
- missing `tool_id` construction behavior;
- `_symbol_id_key` duplication;
- `TYPE_CHECKING` cleanup;
- R1: hostile cross-tool `str` subclass final-sort edge case;
- R2: hostile mutable `tool_id` failure-report edge case.

Core deferred debt remains unchanged:

- M3: `Project.id` path portability and case spelling;
- M4: Scanner/Snapshot non-atomicity;
- L1: incomplete explicit-graph validation;
- L2/L3: class content-hash semantics include method bodies;
- graph/snapshot record-helper duplication.

These items do not block Phase 4.1.

## Deferred Analysis Capabilities

The current Snapshot does not retain sufficient data for:

- cyclomatic complexity;
- function or method source size;
- file byte and line metrics;
- source-level `StyleTool` rules;
- richer symbol-level source-location findings.

These are intentionally deferred capabilities, not Phase 4 defects.

## Final Assessment

- Initial verdict: **PASS WITH ISSUES**;
- Critical findings: **0**;
- Medium findings: **2**;
- M1: **PASS**;
- M2: **PASS**;
- Caller Stack Independence: **PASS**;
- Fan-out Regression: **PASS**;
- Determinism: **PASS**;
- Full regression: **110 passed**;
- Final verdict: **PASS**;
- Retest again: **Not Required**.

## Next Gate

Phase 4 QA is closed. Phase 4 and Phase 4.0.1 are complete, and the project may proceed
to **Phase 4.1 — Provider / BYOK Foundation** under the frozen credential policy. This
QA report does not start Phase 4.1.
