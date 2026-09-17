# V3.0 Phase 3.3

## Background

Phase 3.1 established deterministic project discovery, and Phase 3.2 established a
deterministic in-memory relationship graph with stable project, file, and symbol
identities. Phase 3.3 adds the state-value layer needed to represent what the system
observed about one project at one point in time. It remains an in-memory capability;
it is not a repository, history service, database, or incremental analysis engine.

The initial implementation passed 70 tests and received an independent DeepSeek verdict
of **PASS WITH ISSUES**, with zero Critical findings. Two issues were directed for
correction: malformed Python input could abort Graph/Snapshot construction (M1), and
GraphBuilder and SnapshotBuilder used different canonical graph ordering rules (M2).
Phase 3.3.1 corrected both issues. The directed retest passed M1, M2, golden-hash
compatibility, and the complete 78-test regression suite.

## Capability

Project State Management

## Objectives

- Represent project, file, symbol, and graph state as one immutable in-memory value.
- Reuse `Project.id`, normalized relative file paths, `SymbolId`, and `ProjectGraph`.
- Produce deterministic content identity for unchanged project content.
- Exclude observation time and incidental runtime ordering from content identity.
- Compare two snapshots from the same project for file and symbol state changes.
- Remain offline and independent of persistence, LLM, agent, router, API, and IDE layers.

## Architecture

```text
ScanResult
    |-- ProjectFile state -----------------------+
    |-- existing language adapters -> Symbol ----+--> SnapshotBuilder
    `-- ProjectGraphBuilder -> ProjectGraph -----+          |
                                                           v
                                                   ProjectSnapshot
                                                   |-- files
                                                   |-- symbols
                                                   |-- graph
                                                   |-- metadata
                                                   `-- content_hash

ProjectSnapshot(old) + ProjectSnapshot(new) -> SnapshotDiff
```

`SnapshotBuilder` accepts a `ScanResult`, derives immutable file and symbol state,
builds or accepts the existing `ProjectGraph`, canonicalizes that graph, validates its
project identity, and calculates snapshot metadata and content identity.

## ProjectSnapshot

`ProjectSnapshot` is a frozen data object with:

- `project_id`: the existing location-dependent `Project.id`;
- `created_at`: observation time, excluded from content identity;
- `files`: ordered immutable `FileState` records;
- `symbols`: ordered immutable `SymbolState` records;
- `graph`: the existing immutable `ProjectGraph` representation;
- `content_hash`: deterministic SHA-256 content identity;
- `metadata`: file, symbol, graph-node, and graph-edge counts.

`FileState` contains normalized relative path, detected language, and file content hash.
It deliberately excludes mtime from change identity. `SymbolState` contains the existing
`SymbolId` and `Symbol.content_hash`; it does not introduce a second symbol identity.

## SnapshotBuilder

The builder performs four bounded operations:

1. Convert scanned `ProjectFile` records to ordered immutable file states.
2. Parse supported files with the existing Python and Java adapters and capture symbol
   identity/content state.
3. Build or accept a `ProjectGraph`, apply the graph module's canonical ordering, and
   confirm that its project node matches the scan.
4. Calculate immutable metadata and the canonical snapshot hash.

Malformed source is handled at the file parsing boundary. After Phase 3.3.1, an
`OSError`, `SyntaxError`, or `ValueError` skips symbol/import extraction for that file
without removing its scanned file state or aborting other files.

## SnapshotDiff

`SnapshotDiff` reports ordered tuples for:

- added, removed, changed, and unchanged files;
- added, removed, changed, and unchanged symbols.

File identity is the normalized relative path. A shared file is changed when its
language or content hash differs. Symbol identity is the existing `SymbolId`; a shared
symbol is changed when its content hash differs. Comparison rejects snapshots with
different `project_id` values. It is state comparison, not semantic diff, AST edit
script, or a replacement for Git.

## Canonical Snapshot Identity

The snapshot hash is SHA-256 over explicit canonical JSON containing:

- schema marker and `project_id`;
- ordered file identity, language, and content hash;
- ordered `SymbolId` fields and symbol content hash;
- canonical graph nodes and edges.

The identity excludes `created_at`, file mtime, random UUIDs, Python object
representations, and Python `hash()` values. Graph ordering is semantic and stable; it
does not depend on set iteration order.

## File, Symbol, and Graph State

File state supports content-based added/removed/changed/unchanged classification.
Changing only a function body preserves its `SymbolId`, changes its symbol content
hash, and produces a changed-symbol result. The class content slice includes method
bodies under current parser semantics, so a method edit can also change its enclosing
class state.

The snapshot reuses `ProjectGraph` rather than defining a second relationship model.
After Phase 3.3.1, `graph.py` and its `canonicalize_graph()` function are the single
source of truth for ProjectGraph node and edge ordering. For the same scan:

```python
ProjectGraphBuilder().build(scan) == SnapshotBuilder().build(scan).graph
```

## Immutability and Serialization

Snapshot records use frozen dataclasses and tuples. Canonicalization copies graph node
and edge collections into tuples, so a caller's mutable collection cannot later alter
the snapshot. `to_dict()` provides a deterministic, JSON-serializable in-memory view
for testing and diagnostics. Phase 3.3 does not implement save/load, a snapshot
repository, a history service, or database persistence.

## Initial Implementation and Testing

Commit `45bbd6dc177fd1b063db2f3faa17843d8f83555f`
(`feat(v3): add project snapshot state`) introduced `ProjectSnapshot`,
`SnapshotBuilder`, `SnapshotDiff`, immutable state records, canonical hashing,
file/symbol comparison, graph state handling, and `to_dict()`.

The initial suite increased from 60 to 70 tests. The 10 initial Snapshot tests covered
repeat-build identity, `created_at` exclusion, file addition/removal/change, function
body changes with stable `SymbolId`, graph-order invariance, empty projects,
immutability, serialization, and project-identity validation.

## Initial DeepSeek QA

DeepSeek returned:

- Verdict: **PASS WITH ISSUES**
- Critical: **0**
- M1: malformed, NUL-containing, or abnormal-encoding Python source could raise
  `ValueError` outside the handled exception boundary and abort Graph/Snapshot build.
- M2: `ProjectGraphBuilder` and Snapshot graph normalization used different
  deterministic sort keys, so equal graph semantics could have different tuple order.

M3, M4, L1, and L2/L3 were explicitly deferred rather than included in the directed
fix scope.

## Phase 3.3.1 — Snapshot Post-QA Hardening

Commit `e59149c75fa01d3b08a890baf09336790a5e469b`
(`fix(v3): harden project snapshot after QA`) implemented the two directed fixes.

### M1 Fix

The actual parsing boundaries in `graph.py` and `snapshot.py` now handle `ValueError`
in addition to the existing narrow exception set. No broad `except Exception` was
introduced. Regression coverage uses NUL-containing and invalid-UTF-8 Python files and
verifies that both Graph and Snapshot retain file state, skip invalid symbol/import
data, and continue processing a valid neighboring file.

### M2 Fix

The Snapshot-specific graph sort keys were removed. The ordering compatible with the
existing Snapshot semantic identity was moved into `graph.py` and exposed through the
small `canonicalize_graph()` helper. Both builders now use the same contract, eliminating
the cross-module representation mismatch without introducing a service or repository.

### Golden Hash Compatibility

Before the fix, a stable fixture with fixed project identity produced:

`1c5307cc3b26d24943e585a77029b9c00b7cc13955cef3eccc8b3acb9c9d5ac3`

The same fixture produces the identical hash after Phase 3.3.1. The ordering fix
therefore changed the ownership of canonical ordering without changing valid Snapshot
semantic identity.

### Additional Regression Coverage

Phase 3.3.1 added eight collected cases covering:

1. NUL-containing Python source;
2. invalid-UTF-8 Python source;
3. direct GraphBuilder/Snapshot graph equality;
4. golden hash compatibility;
5. comparison of a snapshot with itself;
6. forward/reverse comparison direction;
7. isolation from mutable graph inputs;
8. deterministic, JSON-serializable `to_dict()` output.

The suite increased from 70 to 78 tests. Final targeted results were 18 Snapshot tests,
13 Graph tests, and 6 offline LLM-contract smoke tests. No network, provider, credential,
or real LLM call was used.

The local Anaconda Python 3.13 environment can segfault while loading pytest's debugging
plugin through `readline`/locale integration. Validation used the documented invocation
workaround `python -m pytest -p no:debugging`; `pytest.ini` was not changed.

## Final QA

The DeepSeek directed retest returned:

- M1: **PASS**;
- M2: **PASS**;
- Golden Hash: **PASS**;
- Regression: **78 passed**;
- Final Verdict: **PASS**;
- Further retest: **Not Required**.

## Deferred Issues

- M3: case-sensitive absolute-path spelling can affect `Project.id`; changing this would
  alter the frozen identity contract.
- M4: Scanner and SnapshotBuilder do not provide an atomic filesystem transaction.
- L1: explicit `graph=` validation confirms the project node but does not exhaustively
  validate every node and edge.
- L2/L3: class content hashes include method bodies under current source-slice semantics.
- Low maintenance note: `graph.py` and `snapshot.py` retain separate
  `_symbol_id_record` and `_node_record` implementations. This is not a current bug and
  is a future cleanup candidate before or within Phase 4.

## Metrics

| Metric | Value |
|---|---|
| Initial implementation commit | `45bbd6dc177fd1b063db2f3faa17843d8f83555f` |
| Hardening commit | `e59149c75fa01d3b08a890baf09336790a5e469b` |
| Initial full suite | 70 passed |
| Final full suite | 78 passed |
| Final Snapshot tests | 18 passed |
| Final Graph tests | 13 passed |
| Offline LLM-contract smoke | 6 passed |
| Initial QA | PASS WITH ISSUES; Critical 0 |
| Directed retest | M1 PASS; M2 PASS; Golden Hash PASS |
| Final QA | PASS; further retest not required |

## Files Changed

The initial Phase 3.3 implementation changed:

- `PROJECT_CONTEXT.md`
- `code_maintenance/__init__.py`
- `code_maintenance/snapshot.py`
- `tests/test_project_snapshot.py`

Phase 3.3.1 hardening changed:

- `PROJECT_CONTEXT.md`
- `code_maintenance/graph.py`
- `code_maintenance/snapshot.py`
- `tests/test_project_snapshot.py`

No README, UI, processor, provider, parser architecture, or test configuration file was
changed.

## Next Phase

V3 Core Architecture Review is the next gate. Phase 4 Project Analysis Engine may begin
only after that review; it was not started during Phase 3.3, Phase 3.3.1, or this
documentation gate.
