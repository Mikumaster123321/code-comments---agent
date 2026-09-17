# V3.0 Phase 3.2

## Background

Phase 3.1 established deterministic project discovery but intentionally stopped before
code relationships. Phase 3.2 adds the first project relationship graph on top of the
existing `ScanResult`, language adapters, and stable symbol identity. The goal is a
small, deterministic, in-memory graph, not a complete code knowledge graph.

The initial implementation passed its automated suite and then received an independent
DeepSeek verdict of **PASS WITH ISSUES**. Two identity defects had to be closed before
snapshot work: duplicate class names could misattribute containment, and unresolved
relative Python imports could retain raw rather than canonical identities. Those issues
were corrected in Phase 3.2.1 and the targeted DeepSeek retest returned **PASS**.

## Capability

Project Relationship Awareness

## Objectives

- Represent projects, files, symbols, and unresolved import targets as graph nodes.
- Represent only `CONTAINS` and `IMPORTS` relationships.
- Reuse `Project.id`, `ProjectFile.relative_path`, and `SymbolId` rather than create a
  second identity system.
- Discover Python imports with the standard AST and Java imports with the existing
  best-effort compatibility strategy.
- Resolve imports to project files only when a deterministic local match is available.
- Produce stable node and edge identities and ordering across repeated builds.
- Remain offline, read-only, in-memory, and independent of the LLM and processor.

## Architecture

```text
ScanResult
    |
    v
ProjectGraphBuilder
    |-- existing PythonAdapter / JavaAdapter --> Symbol + SymbolId
    |-- Python AST ---------------------------> import targets
    |-- Java best-effort package/import scan -> import targets
    |
    v
ProjectGraph
    |-- ordered GraphNode tuple
    `-- ordered GraphEdge tuple
```

The builder reads only files already present in `ScanResult`. It creates all project and
file nodes first, parses supported source files into existing symbols, adds containment,
then resolves imports against deterministic local lookup tables. It does not call an
LLM, modify source, persist graph state, or perform code review.

## ProjectGraph Design

`ProjectGraph` is a frozen data object containing tuples of nodes and edges. Its small
query helpers filter nodes by kind and edges by relation. The graph deliberately has no
database, persistence, snapshot, semantic search, or incremental-update layer.

Set-based assembly deduplicates identical nodes and edges. Final tuples are sorted by
stable keys so graph equality includes deterministic identity and ordering.

## GraphNode

`GraphNode` is frozen and hashable. It contains a node kind, identity, and display label.

| Node kind | Identity |
|---|---|
| `PROJECT` | Existing `Project.id` |
| `FILE` | Existing normalized `ProjectFile.relative_path` |
| `SYMBOL` | Existing `SymbolId` object |
| `EXTERNAL_MODULE` | Canonical or deterministic unresolved import target |

`EXTERNAL_MODULE` means that the target did not resolve to one unique known project
file. It does not claim that the target is definitely a third-party dependency.

## GraphEdge

`GraphEdge` is frozen and hashable and contains source node, target node, and relation.
Only two relation kinds exist:

- `CONTAINS`
- `IMPORTS`

No `CALLS`, `REFERENCES`, `INHERITS`, or `IMPLEMENTS` relationship is inferred.

## CONTAINS

The graph creates:

- Project `CONTAINS` File;
- File `CONTAINS` every extracted Symbol;
- Class `CONTAINS` directly nested Class or Method where existing adapter data can
  establish the relationship.

File and project relationships use their existing identities. Symbol relationships use
`SymbolId`; Java overloads therefore retain normalized parameter signatures, and
fallback line numbers remain limited to true semantic identity collisions.

After Phase 3.2.1, class parent selection no longer assumes a qualified class name is
unique. It keeps all matching class candidates, uses existing symbol line ranges to
select the nearest class that actually encloses the child, and then uses that class's
`SymbolId` to construct the edge.

## IMPORTS

Python import discovery uses `ast.Import` and `ast.ImportFrom`. It covers ordinary
imports, dotted imports, aliases, from-imports, and relative imports. Alias spelling
does not affect target identity.

Java import discovery masks comments and strings, reads package declarations, and
recognizes normal import syntax with best-effort compatibility. Exact package/type
matches can resolve to known Java files. Static and wildcard ownership is not inferred.

Internal Python resolution uses project-root-relative module names. Java resolution
uses exact, unique package/type matches derived from known source files and symbols.
Targets without a unique local match become `EXTERNAL_MODULE` nodes.

Phase 3.2.1 freezes the Python relative-import rule: importer package context produces
the canonical dotted target before either local lookup or external-node creation. If a
package context cannot be established conservatively, the graph uses a deterministic
`unresolved-relative:<context>:<level>:<name>` identity rather than guessing a module.

## Determinism

- No random UUIDs are used.
- Project, file, and symbol identities reuse the established domain identities.
- Import aliases and repeated identical imports deduplicate to the same edge.
- Node and edge sets are converted to tuples using stable sorting keys.
- Repeated builds from the same project state produce equal node and edge tuples.
- Unicode paths retain deterministic normalized relative-path identities.

## Testing

The initial Phase 3.2 commit added eight offline graph tests covering graph structure,
symbol identity, nested classes, Java overloads, Python imports, Java imports,
determinism, and empty projects.

Phase 3.2.1 added five regression tests covering:

1. Duplicate same-file class names with same-named methods and correct parent edges.
2. Cross-file same-class-name containment isolation.
3. Canonical unresolved relative Python import identity.
4. Explicit self-import and star-import behavior.
5. Unicode paths and duplicate/aliased import invariance.

The final Graph test count is 13. The complete final suite is `60 passed`, and the
offline LLM-contract smoke is `6 passed`. No real provider request, API key, or network
access was used.

The local Anaconda Python 3.13 environment can segfault while loading pytest's debugging
plugin through `readline`/locale integration. Validation used the documented invocation
workaround `python -m pytest -p no:debugging`; `pytest.ini` was not changed.

## Initial QA

DeepSeek independently reviewed the initial implementation at commit
`5531e608e94c2737a98016f84853384d439a4df8` and returned:

- Verdict: **PASS WITH ISSUES**
- Critical: **0**
- D1: duplicate class `qualified_name` could select the wrong containment parent.
- D2: unresolved relative Python import nodes could retain raw relative spelling as
  identity instead of the canonical target used during resolution.

Both issues were required to be closed before Phase 3.3 snapshot work.

## Post-QA Hardening — Phase 3.2.1

Commit `dd76fabb3ee607297e455fd0844be76e53394131` implemented the directed fixes.

For D1, the builder now preserves same-name class candidates, filters candidates using
existing symbol source ranges, selects the nearest enclosing scope, and constructs the
edge through the selected class's existing `SymbolId`. It does not modify the parser or
the overall symbol identity design.

For D2, canonical Python import targets are now used consistently for both internal
resolution and unresolved external-node identity. Raw relative spelling is not used as
identity when canonicalization is supported. Contexts that cannot be resolved safely
remain explicit and deterministic rather than being mapped to a guessed module.

The hardening did not change the UI, processor, providers, scanners, parsers, or README.

## Final Retest

DeepSeek performed a directed retest after Phase 3.2.1 and returned:

- Final verdict: **PASS**
- D1 fix: **VERIFIED**
- D2 policy: **VERIFIED**
- Retest blocker: **NONE**

Final local validation also passed all 60 tests, all 13 Graph tests, and all 6 offline
LLM-contract smoke tests.

## Technical Debt

- Self-imports produce explicit self-loop `IMPORTS` edges.
- Star imports remain coarse targets such as `a.*`.
- `EXTERNAL_MODULE` does not model individual package members.
- Python `src`-layout discovery is not implemented.
- `pyproject` packaging semantics are not implemented.
- Namespace packages are not resolved.
- `site-packages` resolution is not performed.
- Root `__init__.py` relative imports have a narrow precision gap because the project
  root does not provide a reliable package name.
- Java package/import parsing remains deterministic best-effort compatibility rather
  than a complete Java parser.
- The graph has no `CALLS`, `REFERENCES`, `INHERITS`, or `IMPLEMENTS` relations.
- `Project.id` depends on the resolved absolute root path. Phase 3.3's first snapshot
  version therefore defaults to time-series comparison under the same project root.

## Metrics

| Metric | Value |
|---|---|
| Initial implementation commit | `5531e608e94c2737a98016f84853384d439a4df8` |
| Initial commit subject | `feat(v3): add project relationship graph` |
| Hardening commit | `dd76fabb3ee607297e455fd0844be76e53394131` |
| Hardening commit subject | `fix(v3): harden graph identity and containment` |
| Node kinds | 4 |
| Relation kinds | 2 |
| Initial Graph tests | 8 |
| Hardening regression tests | 5 |
| Final Graph tests | 13 passed |
| Final full suite | 60 passed |
| Offline LLM-contract smoke | 6 passed |
| Initial QA | PASS WITH ISSUES; Critical 0 |
| Final retest | PASS; D1/D2 verified; no blocker |

## Files Changed

The initial Phase 3.2 implementation changed:

- `PROJECT_CONTEXT.md`
- `code_maintenance/__init__.py`
- `code_maintenance/graph.py`
- `tests/test_project_graph.py`

Phase 3.2.1 hardening changed:

- `PROJECT_CONTEXT.md`
- `code_maintenance/graph.py`
- `tests/test_project_graph.py`

No README, UI, processor, provider, parser, or test configuration file was changed.

## Next Phase

Phase 3.3: Project Snapshot / State.

Phase 3.3 was not started during Phase 3.2, Phase 3.2.1, or this documentation gate.
