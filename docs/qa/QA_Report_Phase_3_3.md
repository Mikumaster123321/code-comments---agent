# V3.0 Phase 3.3 — Project Snapshot QA Report

## Final Verdict

**PASS**

The initial DeepSeek review returned **PASS WITH ISSUES** with zero Critical findings.
M1 and M2 required directed correction. Codex implemented Phase 3.3.1, and the DeepSeek
directed retest passed M1, M2, golden-hash compatibility, and full regression. A further
retest is **Not Required**.

```text
Initial DeepSeek QA: PASS WITH ISSUES (Critical 0)
    -> M1 malformed Python failure isolation
    -> M2 canonical graph ordering mismatch
Codex Phase 3.3.1: e59149c75fa01d3b08a890baf09336790a5e469b
DeepSeek directed retest:
    -> M1 PASS
    -> M2 PASS
    -> Golden Hash PASS
Final Verdict: PASS
```

## Review Scope

The QA cycle covered:

- immutable `ProjectSnapshot`, `FileState`, `SymbolState`, and metadata;
- `SnapshotBuilder` composition of scan, symbol, and graph state;
- deterministic Snapshot content identity;
- file and symbol comparison semantics;
- Graph ordering invariance and cross-builder canonical equality;
- malformed-source failure isolation;
- empty projects, input isolation, and JSON-serializable `to_dict()` output;
- regression isolation from the existing application and offline LLM contract.

The review did not expand scope into persistence, snapshot history, incremental
analysis, RAG, agents, routers, APIs, VS Code, Git integration, or Phase 4.

## Environment

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Initial implementation | `45bbd6dc177fd1b063db2f3faa17843d8f83555f` |
| Phase 3.3.1 fix | `e59149c75fa01d3b08a890baf09336790a5e469b` |
| Initial full suite | 70 passed |
| Final full suite | 78 passed |
| Final Snapshot tests | 18 passed |
| Final Graph tests | 13 passed |
| Offline LLM-contract smoke | 6 passed |
| Network/provider calls | None |

The Codex host uses Anaconda Python 3.13 and can segfault while pytest loads its
debugging plugin through `readline`/locale integration. Validation used the documented
`-p no:debugging` invocation workaround; project test configuration was not changed.

## Initial DeepSeek QA

- Verdict: **PASS WITH ISSUES**
- Critical: **0**
- Required fixes: **M1**, **M2**
- Deferred: **M3**, **M4**, **L1**, **L2/L3**

The implementation otherwise established the intended deterministic, immutable,
in-memory Project State capability and preserved prior regression behavior.

## M1 — Malformed Python Failure Isolation

### Finding

Malformed Python input, including NUL-containing or abnormal-encoding source, could
reach AST/parser paths that raise `ValueError`. The relevant Graph and Snapshot parsing
boundaries handled only `OSError` and `SyntaxError`. One bad Python file could therefore
abort construction for the whole project instead of losing only that file's derived
symbol/import data.

### Fix

Phase 3.3.1 added `ValueError` to the narrow exception boundary in Graph symbol/import
parsing and Snapshot symbol parsing. It did not add a broad exception handler or change
parser architecture. Scanner discovery and file state remain intact; only derived
symbol/import information for the malformed file is skipped, while valid files continue
to be processed.

### Directed Retest Evidence

- Independent M1 probe suite: **77/77 PASS**.
- NUL-containing Python input did not abort Graph or Snapshot construction.
- Invalid-UTF-8 Python input did not abort construction after replacement decoding.
- Malformed files remained present as file state.
- Valid neighboring files retained their symbols.
- M1 result: **PASS**.

## M2 — Canonical Graph Ordering

### Finding

`ProjectGraphBuilder` and Snapshot normalization each used a deterministic but different
sort key. They could contain the same node and edge sets while failing full
`ProjectGraph` equality because their canonical tuple order differed.

### Fix

Phase 3.3.1 made `graph.py` the ordering authority. Its `canonicalize_graph()` function
is now used by both `ProjectGraphBuilder` and `SnapshotBuilder`. Snapshot-specific graph
sort definitions were removed. No Graph service, manager, repository, or abstraction
hierarchy was introduced.

### Directed Retest Evidence

- Independent M2 probe suite: **17/17 PASS**.
- For the same `ScanResult`, direct GraphBuilder output equals Snapshot graph state.
- Canonical ordering remained stable across `PYTHONHASHSEED` values.
- M2 result: **PASS**.

## Pre-Fix / Post-Fix Dual-Tree Comparison

The directed QA used separate source trees for the initial implementation and the
hardening result:

| Tree | Commit | Purpose |
|---|---|---|
| Pre-fix | `45bbd6dc177fd1b063db2f3faa17843d8f83555f` | Reproduce M1/M2 and record compatible Snapshot identity |
| Post-fix | `e59149c75fa01d3b08a890baf09336790a5e469b` | Verify failure isolation, shared canonical ordering, and regression |

This comparison separated behavior changes from workspace state and confirmed that the
directed fixes closed M1/M2 without changing valid Snapshot semantic identity.

## Golden Snapshot Hash

The stable fixture hash recorded before hardening was:

`1c5307cc3b26d24943e585a77029b9c00b7cc13955cef3eccc8b3acb9c9d5ac3`

The post-fix implementation produced the same value.

- Pre-fix: **PASS**
- Post-fix: **PASS**
- Compatibility result: **PASS**

The production implementation does not hardcode this value; it is a regression fixture
assertion proving that canonical-order ownership changed without changing semantic
Snapshot content identity.

## Regression

Final evidence:

- Complete suite: **78 passed**.
- Snapshot suite: **18 passed**.
- Graph suite: **13 passed**.
- Offline LLM-contract smoke: **6 passed**.
- Independent M1 probes: **77/77 PASS**.
- Independent M2 probes: **17/17 PASS**.
- Canonical ordering across `PYTHONHASHSEED`: **stable**.
- Real LLM/provider/network calls: **none**.

## Deferred Issues

The following findings are recorded but not fixed:

- **M3 — Project identity path spelling:** case-sensitive absolute-path spelling can
  affect `Project.id`. A change would alter the frozen identity contract.
- **M4 — Non-atomic observation:** Scanner and SnapshotBuilder do not provide an atomic
  filesystem transaction across scan and build.
- **L1 — Explicit graph validation:** `graph=` validation confirms the project node but
  does not exhaustively validate all supplied nodes and edges.
- **L2/L3 — Class content semantics:** a class symbol's source slice includes method
  bodies, so a method-body edit can mark both the method and enclosing class as changed.

These are limitations or future design decisions, not claims of completed fixes.

## Maintenance Note

`graph.py` and `snapshot.py` currently retain separate `_symbol_id_record` and
`_node_record` implementations. This duplication is not a current correctness bug. It
is a low-priority cleanup candidate before or within Phase 4.

## Final Assessment

- Initial verdict: **PASS WITH ISSUES**
- Critical findings: **0**
- M1: **PASS**
- M2: **PASS**
- Golden Hash: **PASS**
- Regression: **78 passed**
- Final verdict: **PASS**
- Retest again: **Not Required**

## Next Gate

Phase 3.3 QA is closed. The project may proceed to **V3 Core Architecture Review**.
Phase 4 Project Analysis Engine remains after that review and was not started by this
QA cycle.
