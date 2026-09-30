# V3.1.0 Phase 4 — Graph Expansion + Index Identity / Incremental Indexing Final QA Report

## Final Verdict

**PASS FOR PHASE 4 WITH LOW NOTES**

- Final Critical: **0**
- Final Medium: **0**
- Phase blockers: **0**
- Initial Independent QA: **PASS WITH NON-BLOCKING FINDINGS**
- Directed Retest: **PASS WITH LOW NOTES**
- New Critical / Medium / Low: **0 / 0 / 1**
- F1 Graph traversal direction contract: **CLOSED / RESOLVED**
- F2 incremental unchanged lookup complexity: **CLOSED / RESOLVED**
- Phase 4.1.1: **NOT REQUIRED**
- Phase 4 Documentation Gate: **CLOSED**

This report is the final QA record for Phase 4. It retains the initial findings and
their hardening history rather than reclassifying the initial implementation as
problem-free.

## 1. Scope and Frozen Boundaries

QA evaluated deterministic index/config identity, Snapshot identity reuse,
`SnapshotDiff` planning, add/delete/replace/reuse behavior, Embedding call accounting,
incremental/full-rebuild equivalence, bounded Graph Expansion, direction-aware
provenance, failure atomicity, determinism, and dependency boundaries.

The primary retrieval unit remains Symbol. Phase 1 `RetrievalDocument`/`SymbolId`,
Phase 2 BM25, Phase 3 Embedding contracts, `ProjectSnapshot`, and directed
`ProjectGraph` remain frozen. No Hybrid Retrieval, score fusion, RRF,
`ContextBuilder`, final service facade, persistent cache, Vector DB, ANN, Agent, or
Router was introduced.

## 2. Initial Independent QA

Initial Independent QA returned **PASS WITH NON-BLOCKING FINDINGS**. It found:

- **F1:** bidirectional Graph Expansion existed, but traversal direction was not
  formally represented in provenance; and
- **F2:** `document.symbol_id in plan.unchanged` scanned an immutable tuple for every
  document, producing O(N²) unchanged-membership behavior.

Both were real findings. They were corrected in Phase 4.1 and were not present only as
documentation concerns.

## 3. F1 Directed-Retest Result

F1 is **CLOSED / RESOLVED**. `ProjectGraph` remains a directed graph and its relation
kinds remain `CONTAINS` and `IMPORTS`. Graph Expansion may traverse each edge as:

| Relation | `FORWARD` | `REVERSE` |
| --- | --- | --- |
| `CONTAINS` | container → contained | contained → container |
| `IMPORTS` | importer → dependency | dependency → importer/dependent |

Direction is an explicit `GraphTraversalDirection` value in retrieval provenance; it
is not a new `GraphRelationKind` and cannot be inferred from node kind. Final
`GraphExpansionProvenance` records `seed_identity`, `relation`, `direction`, `hop`,
and `node_identity`. Tests independently verified forward and reverse `CONTAINS` and
`IMPORTS`, deterministic shared-neighbor provenance, and direction stability under
100 graph input permutations.

## 4. F2 Directed-Retest Result

F2 is **CLOSED / RESOLVED**. The root cause was N index documents performing
membership against an N-sized `plan.unchanged` tuple. The final update path constructs
`set(plan.unchanged)` once and uses average O(1) membership for each document. The
public frozen `IncrementalIndexPlan` tuple contract did not change.

An instrumented 600-Symbol test confirmed that the update path performs no per-document
membership operation against the tuple. Independent 5,000/10,000-Symbol evidence did
not show stable O(N²) scaling.

## 5. Identity and Incremental Correctness

`RetrievalIndexIdentity` deterministically identifies the Project, authoritative
Snapshot content, retrieval configuration, and optional Embedding space. Config or
fingerprint drift fails closed. Credential values, random/time state, cache locations,
object identity, and absolute machine paths are excluded.

The final `SnapshotDiff` semantics are:

- added → add and embed the new Symbol only;
- removed → delete completely;
- changed → replace and generate a new vector; and
- unchanged → reuse the existing entry/vector without Provider document calls.

The 5,000-Symbol independent probe changed 3, added 2, and removed 2 Symbols. Exactly 5
new embeddings were generated; removed and unchanged Symbols generated zero. Unchanged
entries retained the same `EmbeddingVector` object, changed entries did not reuse the
old vector, and removed IDs disappeared.

Incremental update and full rebuild were equal for identity, ordered documents,
content hashes, entries, vectors, BM25 rank/score, and Semantic rank/score. Updates
return a new index; failures do not mutate or partially replace the old authoritative
index.

## 6. Graph Safety and Structural Context

Expansion is bounded by relation whitelist, hop limit, per-seed budget, global budget,
visited set, canonical ordering, and duplicate suppression. Cycle, duplicate-edge,
shared-neighbor, multi-seed, and input-order tests passed.

`FILE` and `PROJECT` can be returned as structural nodes with `document=None`; they
still consume per-seed and global budgets. `ExternalModule` and stale/missing Symbol
nodes do not receive fabricated `RetrievalDocument` values.

Semantically equal graphs whose node/edge tuples use a different order are accepted by
canonical comparison. A genuinely different graph still fails closed. Neither
`ProjectGraph` nor the Snapshot contract was modified.

Graph Expansion does not modify BM25 score/rank or Semantic score/rank. No Graph score
boost, Weighted Fusion, RRF, or Hybrid Retrieval is part of the Phase 4 result.

## 7. Performance and Determinism Evidence

Independent Directed Retest measurements were:

| Symbols | Incremental | Full rebuild | Ratio |
| ---: | ---: | ---: | ---: |
| 5,000 | approximately 0.1059 s | approximately 0.1152 s | approximately 0.919 |
| 10,000 | approximately 0.2158 s | approximately 0.2332 s | approximately 0.926 |

Incremental scaling from 5,000 to 10,000 Symbols was approximately **2.038×**. These are
engineering observations, not a formal thesis performance result or SLA.

One deterministic result was observed across 100 graph permutations. Phase 4 tests
were also **37 passed** under `PYTHONHASHSEED=1`, `17`, and `310`.

## 8. Regression Evidence

| Suite | Result |
| --- | ---: |
| Phase 4 index + Graph Expansion | **37 passed** |
| Phase 3.2 local adapter | **10 passed** |
| Phase 3.1 embedding core | **12 passed** |
| Phase 2 lexical | **14 passed** |
| Phase 1 corpus | **41 passed** |
| Offline LLM-contract smoke | **6 passed** |
| Full regression | **528 passed** |

The ordinary Anaconda Python 3.13.5 invocation reproduces the documented debugging
plugin / `rlcompleter` segmentation fault before collection. The established
`-p no:debugging` invocation completed the full 528-test regression. No real model,
model download, API, Credential, or network request was used.

## 9. Deferred Low

The one new Low is direct manual construction of `GraphExpansionProvenance`: the
dataclass currently has no `__post_init__` guard that rejects an invalid `direction`
value. The authoritative production `expand_graph()` path emits only
`GraphTraversalDirection.FORWARD` or `GraphTraversalDirection.REVERSE`; production
expansion is therefore unaffected. This is registered for future defensive hardening
and is not a phase blocker.

No new Critical or Medium issue was found. Phase 4.1.1 is **NOT REQUIRED**.

## 10. Research Boundary and Gate Decision

Phase 4 proves implementation correctness, controlled graph expansion, explicit
direction provenance, and incremental-index engineering feasibility. It does not prove
that Graph improves Recall, that Graph beats BM25 or Embedding, or that Hybrid improves
retrieval. Phase 6 must evaluate `(relation, direction)` pairs through the frozen
benchmark and ablation protocol before any RQ3 conclusion.

Final QA is **PASS FOR PHASE 4 WITH LOW NOTES**. Final Critical and Medium are zero,
phase blockers are zero, F1 and F2 are closed, and the Phase 4 Documentation Gate is
**CLOSED**. Phase 5 is **ALLOWED BUT NOT STARTED**.
