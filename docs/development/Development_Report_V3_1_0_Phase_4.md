# V3.1.0 Phase 4 — Graph Expansion + Index Identity / Incremental Indexing Development Report

## Final Status

- Phase 4 implementation: **COMPLETED**
- Initial Independent QA: **PASS WITH NON-BLOCKING FINDINGS**
- Phase 4.1 Hardening: **COMPLETED**
- Directed Retest: **PASS WITH LOW NOTES**
- F1 Graph traversal direction contract: **CLOSED / RESOLVED**
- F2 incremental unchanged lookup complexity: **CLOSED / RESOLVED**
- Final Critical / Medium / Phase blocker: **0 / 0 / 0**
- Phase 4.1.1: **NOT REQUIRED**
- Phase 4 Documentation Gate: **CLOSED**
- Phase 5: **ALLOWED BUT NOT STARTED**

This report preserves the complete Phase 4 history: the initial implementation, the
two non-blocking Independent QA findings, the Phase 4.1 hardening, and the Directed
Retest. It does not rewrite the initial implementation as defect-free and does not
start Phase 5.

## 1. Objective and Scope

Phase 4 adds the engineering foundation required to keep Project Intelligence indexes
identifiable, incrementally maintainable, and graph-aware without changing the frozen
Phase 1–3 contracts. Its delivered scope is:

- deterministic `RetrievalIndexIdentity` and retrieval-config identity;
- authoritative reuse of `ProjectSnapshot` identity;
- immutable `IncrementalIndexPlan` values derived from `SnapshotDiff`;
- add, delete, replace, and reuse semantics for Symbol-primary indexes;
- semantic-vector reuse with exact Embedding call accounting;
- equivalence between incremental update and full rebuild;
- bounded Graph Expansion over `CONTAINS` and `IMPORTS`; and
- explicit direction-aware graph provenance.

Phase 4 does not implement Hybrid Retrieval, Graph score boost, Weighted Fusion, RRF,
`ContextBuilder`, a final `RetrievalService` facade, persistent embedding cache, Vector
DB, ANN, Agent, or Router. It changes neither `ProjectGraph` nor `ProjectSnapshot`.

## 2. Index and Configuration Identity

`RetrievalIndexIdentity` is an immutable, deterministic, credential-free value with:

- `project_id`;
- `snapshot_content_hash`;
- `retrieval_config_hash`; and
- an optional `embedding_fingerprint`.

The project and Snapshot fields reuse `ProjectSnapshot.project_id` and
`ProjectSnapshot.content_hash`; Phase 4 does not invent a second Project ID or Snapshot
hash. The retrieval-config hash covers the Symbol retrieval unit, BM25/tokenizer
configuration, whether Embedding is enabled, the Embedding fingerprint, and the Graph
Expansion configuration. Runtime timestamps, random values, object identities,
Credential material, cache paths, and machine-local absolute paths are excluded.

Any authoritative identity change prevents silent reuse. A different Snapshot,
retrieval configuration, or Embedding fingerprint fails closed and requires an
explicit incremental update or full rebuild as appropriate. Embedding-space changes
never reuse old semantic vectors.

## 3. IncrementalIndexPlan and Update Semantics

`IncrementalIndexPlan` is immutable and retains canonical tuples for `added`,
`removed`, `changed`, and `unchanged` Symbol IDs. Its deterministic mapping is:

| SnapshotDiff state | Index operation | Final behavior |
| --- | --- | --- |
| added | add | create the new document/index entry; embed only the new Symbol when enabled |
| removed | delete | omit the old document, lexical state, semantic vector, and retrievable graph result |
| changed | replace | replace the old entry and generate a new vector; stale content/vector reuse is rejected |
| unchanged | reuse | retain the existing semantic vector and avoid document Embedding calls |

The primary unit remains Symbol and continues to use the frozen `SymbolId`. File is a
secondary structural concept; Phase 4 does not introduce a chunk-first index.

The update path validates Project/Snapshot identity, document identity and content
hashes, config identity, Provider fingerprint, and `SnapshotDiff` consistency before a
new authoritative index is returned. It constructs a new index rather than mutating
the old one. Provider, validation, identity, or index-construction failure therefore
leaves the prior index intact and usable; no half-updated authoritative state is
published.

## 4. Embedding Reuse and Full-Rebuild Equivalence

The independent 5,000-Symbol probe changed 3 Symbols, added 2, and removed 2. The
incremental update generated exactly 5 new document embeddings:

- changed: **3** new embeddings;
- added: **2** new embeddings;
- removed: **0** embeddings; and
- unchanged: **0** embeddings.

Unchanged entries retained the same `EmbeddingVector` object. Changed entries did not
reuse their old vectors. Removed entries disappeared completely.

The same probe independently compared the incremental result with a full rebuild of
the final Snapshot. Equality held for:

- index identity;
- ordered documents and content hashes;
- index entries and vectors;
- BM25 rank and score; and
- Semantic rank and score.

This is the central Phase 4 correctness contract. Incremental indexing is an
engineering and performance capability, not a new retrieval algorithm.

## 5. Graph Expansion Contract

Graph Expansion reads the existing directed `ProjectGraph` and only admits the frozen
relations `CONTAINS` and `IMPORTS`. It does not add `CALLS`, `INHERITS`, `REFERENCES`,
`DEPENDS_ON`, or another `GraphRelationKind`.

`GraphExpansionConfig` is immutable and supplies:

- `max_hops`;
- relation whitelist;
- `max_expanded_per_seed`; and
- `max_total_context_nodes`.

The production defaults are one hop, `CONTAINS + IMPORTS`, five expanded nodes per
seed, and thirty total context nodes. Traversal uses a visited set, hop limit,
per-seed budget, global budget, canonical ordering, and duplicate suppression. Cycles,
duplicate edges, multiple seeds sharing a neighbor, and input-edge permutations remain
bounded and deterministic.

## 6. Directed Graph Traversal and Provenance

`ProjectGraph` remains directed. Graph Expansion may traverse a directed edge in both
directions, but the chosen direction is recorded explicitly:

| Relation | `FORWARD` (`edge.source → edge.target`) | `REVERSE` (`edge.target → edge.source`) |
| --- | --- | --- |
| `CONTAINS` | container → contained | contained → container |
| `IMPORTS` | importer → dependency | dependency → importer/dependent |

`GraphTraversalDirection` is retrieval provenance, not a new graph relation. Every
production expansion candidate carries:

- `seed_identity`;
- `relation`;
- `direction`;
- `hop`; and
- `node_identity`.

Direction must not be inferred from node kind. This matters because the later Phase 6
RQ3 ablation must distinguish `(relation, direction)` pairs rather than merge forward
and reverse `IMPORTS` into one signal. Phase 4 provides this observability but makes no
retrieval-quality claim.

## 7. Structural Nodes, Graph Freshness, and Score Isolation

`FILE` and `PROJECT` nodes may be returned as structural context with `document=None`.
They still consume both per-seed and global budgets. `ExternalModule` or another node
without a valid source `RetrievalDocument` never receives a fabricated document.
Missing/stale Symbol documents are not returned as retrievable source.

When `expected_graph` has the same semantic nodes and edges but a different tuple
order, canonical comparison accepts it. A genuinely different graph still fails
closed. The frozen `ProjectGraph` and Snapshot contracts remain unchanged.

Graph Expansion returns structured candidates and provenance only. It does not alter
BM25 score/rank or Semantic score/rank. Graph score boost, Weighted Fusion, RRF, and
Hybrid Retrieval remain outside Phase 4.

## 8. Initial Independent QA and Phase 4.1 Hardening

Initial Independent QA returned **PASS WITH NON-BLOCKING FINDINGS** and identified two
real issues:

### F1 — Graph Direction Contract

The initial bidirectional traversal did not formally freeze whether a result followed
an edge forward or reverse. A caller could not reliably distinguish importer →
dependency from dependency → importer using provenance alone.

Phase 4.1 added immutable `GraphTraversalDirection.FORWARD/REVERSE` and placed the
direction directly in `GraphExpansionProvenance`. The underlying directed graph and
relation whitelist did not change. F1 is **CLOSED / RESOLVED**.

### F2 — Incremental Unchanged Lookup Complexity

The initial `update()` performed:

```text
document.symbol_id in plan.unchanged
```

where `plan.unchanged` is a tuple. Across N documents and an N-sized unchanged tuple,
this caused N tuple scans and O(N²) membership behavior.

Phase 4.1 now constructs `set(plan.unchanged)` once per update and performs average
O(1) membership checks. The public immutable `IncrementalIndexPlan` tuple contract is
unchanged. F2 is **CLOSED / RESOLVED**.

## 9. Directed Retest and Engineering Performance Evidence

The independent Directed Retest returned **PASS WITH LOW NOTES**, with new Critical 0,
new Medium 0, one new Low, and phase blockers 0.

| Synthetic corpus | Incremental update | Full rebuild | Incremental/full ratio |
| ---: | ---: | ---: | ---: |
| 5,000 Symbols | approximately 0.1059 s | approximately 0.1152 s | approximately 0.919 |
| 10,000 Symbols | approximately 0.2158 s | approximately 0.2332 s | approximately 0.926 |

Doubling from 5,000 to 10,000 Symbols produced approximately **2.038×** incremental
scaling. The retest therefore did not observe stable O(N²) behavior after F2. These
measurements are Phase 4 engineering evidence only: they are not a formal thesis
performance result, benchmark SLA, or retrieval-quality result.

The retest also confirmed one deterministic output across 100 graph permutations and
green Phase 4 tests under `PYTHONHASHSEED=1`, `17`, and `310`.

## 10. Immutability, Determinism, and Dependency Boundary

Identity, configuration, plan, entry, provenance, and expansion-result contracts use
immutable values. Canonical Symbol/Graph ordering excludes set/dict insertion order,
input-edge order, random UUIDs, object IDs, and Python hash seed from authoritative
results. Updates publish a new index and preserve the old index on success or failure.

Production Phase 4 code adds no third-party dependency. Dependency direction remains
`project_intelligence -> code_maintenance`; it does not depend on Credits, Managed
Access, Admin Operations, LLM providers, Gradio, OpenAI, or a network service.
`requirements.txt` and `requirements-embedding.txt` remain unchanged. Default tests
use `DeterministicFakeEmbeddingProvider`; no real model is loaded or downloaded.

## 11. Deferred Low

The Directed Retest registered one non-blocking Low: a caller can directly construct
`GraphExpansionProvenance` with an invalid `direction` value because the dataclass has
no `__post_init__` validation for that field. The authoritative production
`expand_graph()` path creates only `GraphTraversalDirection.FORWARD` or
`GraphTraversalDirection.REVERSE`, so production expansion behavior is unaffected.
This remains future defensive hardening and does not require Phase 4.1.1.

## 12. Validation Evidence

- Phase 4 index and graph tests: **37 passed**;
- Phase 3.2 local-adapter regression: **10 passed**;
- Phase 3.1 embedding regression: **12 passed**;
- Phase 2 lexical regression: **14 passed**;
- Phase 1 corpus regression: **41 passed**;
- offline LLM-contract smoke: **6 passed**; and
- full regression: **528 passed**.

The ordinary host invocation still reproduces the documented Anaconda Python 3.13.5
debugging-plugin / `rlcompleter` segmentation fault. The repository's established
`python -m pytest -p no:debugging` workaround completed all 528 tests. No production
code or test was changed by this documentation gate.

## 13. Thesis and Phase Boundary

Phase 4 contributes reproducible engineering evidence for index identity, incremental
indexing, Graph-aware context expansion, direction-aware provenance, correctness, and
update scaling. It does not demonstrate that Graph improves Recall, Graph beats BM25
or Embedding, or Hybrid Retrieval improves retrieval. Those claims require the fixed
Phase 6 benchmark and ablation protocol.

Phase 4 is **COMPLETED**, Final QA is **PASS FOR PHASE 4 WITH LOW NOTES**, and the
Documentation Gate is **CLOSED**. Phase 5 is **ALLOWED BUT NOT STARTED**.
