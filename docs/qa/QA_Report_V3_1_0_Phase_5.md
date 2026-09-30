# V3.1.0 Phase 5 — Hybrid Retrieval + ContextBuilder Final QA Report

## Final Verdict

**PASS FOR PHASE 5 WITH LOW NOTES**

- Independent QA: **PASS WITH LOW NOTES**
- Final Critical: **0**
- Final Medium: **0**
- Final Low: **6**
- Phase blockers: **0**
- Phase 5.1: **NOT REQUIRED**
- Directed Retest: **NOT REQUIRED**
- Phase 5 Documentation Gate: **CLOSED**
- Phase 6: **ALLOWED BUT NOT STARTED**
- V3.2: **NOT STARTED**

This report closes the Phase 5 QA and documentation gate. It records implementation
correctness and experiment readiness without beginning Phase 6 or claiming retrieval
quality results.

## 1. Scope and Frozen Boundaries

QA covered deterministic Hybrid candidate union, `SymbolId` deduplication, stable
tie-breaking, Weighted Score Fusion, normalization, optional RRF, Lexical-only,
Semantic-only, Hybrid, Graph-aware scoring, degraded fallback, context construction,
character budgets, `RetrievalQuery`, `ContextPackage`, and the `RetrievalService`
facade.

Phase 1 `RetrievalDocument`/`SymbolId`, Phase 2 BM25, Phase 3 Embedding and exact
`SemanticIndex`, Phase 4 directed Graph provenance and index identity, and the frozen
V3.1 architecture remain unchanged. No learned normalization/ranker, benchmark,
ground truth, Agent runtime, Router, or V3.2 behavior is part of this result.

## 2. Independent QA Evidence

Independent QA returned **PASS WITH LOW NOTES**. All **243 / 243 independent probes**
passed:

| Probe category | Result |
| --- | ---: |
| fusion | 77 / 77 |
| normalization extremes | 19 / 19 |
| context | 48 / 48 |
| service | 52 / 52 |
| scope | 21 / 21 |
| determinism | 9 / 9 |
| performance | 17 / 17 |

The 243 items are independent QA probes. They are not pytest tests and are not added to
the repository test count.

## 3. Hybrid and Weighted Fusion Result

The final candidate set is the union of Lexical and Semantic branch candidates. The
authoritative identity is `SymbolId`, so a document appearing in both branches becomes
one `HybridHit`. Results sort by descending final score and then by the canonical
`SymbolId` tuple for stable ties.

The default primary formula is:

```text
lexical_weight  * normalized lexical
+ semantic_weight * normalized semantic
+ graph_weight    * graph component
```

Weights are finite and non-negative and need not sum to one; the score is used for
relative ranking. Missing branch components contribute zero. Raw BM25 and Semantic
scores/ranks remain isolated and observable. Deterministic weighted RRF is available
only as an optional comparison baseline.

Lexical-only, Semantic-only, Hybrid without Graph, Hybrid with Graph, and a
Graph-focused configuration are expressible independently. This is ablation readiness,
not evidence that one strategy is better.

## 4. Normalization Result

BM25 uses safe branch-maximum normalization. Empty branches contribute nothing, and an
all-zero branch produces zero normalized values without division by zero.

Semantic exact cosine is mapped from `[-1, 1]` to `[0, 1]` after finite saturation to
the nominal interval. Production `SemanticIndex` uses L2-normalized vectors and exact
cosine. The clamp safely absorbs reasonable floating-point drift and also defines the
current saturating behavior for larger finite extremes. No learned normalization is
implemented or claimed.

## 5. Degraded-Mode and Privacy Result

When the Semantic branch fails and the Lexical branch is enabled, Hybrid retrieval may
return a Lexical-only result with `degraded=True`, a stable type-based
`degradation_reason`, and `failure_provenance`. The degraded result contains no
Semantic score, rank, normalized contribution, or false claim of Semantic success.
The normal degraded metadata does not expose the provider's original exception text.

Semantic-only mode cannot degrade and fails explicitly. That raised error uses Python
exception chaining, so `__cause__` may retain the upstream provider message in a
traceback. This privacy-oriented defensive-hardening item is Low and non-blocking.

## 6. Graph Signal Result

Graph scoring preserves the complete `(relation, direction, hop)` distinction. The
current frozen heuristic applies relation and direction factors divided by hop, while
retaining deterministic provenance. It distinguishes:

- `IMPORTS/FORWARD` from `IMPORTS/REVERSE`; and
- `CONTAINS/FORWARD` from `CONTAINS/REVERSE`.

The Graph component does not mutate the original BM25 or Semantic values. Graph
Expansion provenance may remain in the package even if a candidate is structural or
is not rendered under the context budget. QA makes no claim that Graph improves
Recall.

## 7. ContextBuilder and Hit/Snippet Semantics

`ContextBuilder` consumes retrieval values only. It performs no filesystem read,
source parsing, index rebuild, or Embedding call. It owns deterministic `SymbolId`
deduplication, Hybrid-rank ordering, seed-adjacent Graph context placement, remaining
Graph context ordering, source assembly from authoritative
`RetrievalDocument.source_text`, the character budget, and observable truncation.

`ContextPackage.hits` represents all final ranked Hybrid hits. The context budget may
prevent some hits from entering `context_text`; therefore hits and rendered snippets
are not the same collection. `ContextPackage.snippets` explicitly records what was
rendered. A Graph-only rendered snippet has `hybrid_rank=None`. A package may also
retain Graph provenance for a candidate that was not rendered. These distinctions are
part of the frozen future-consumer contract.

## 8. Character-Budget Result

The budget unit is characters. Every package enforces:

```text
budget_used == len(context_text)
budget_used <= budget
```

Exact fits are not marked truncated. If the highest-priority next snippet exceeds the
remaining budget, the available prefix is selected deterministically, both snippet and
package expose `truncated=True`, and construction stops. Truncation is never silent.

## 9. RetrievalService and V3.2 Boundary

The stable facade is:

```text
RetrievalService.retrieve(RetrievalQuery) -> ContextPackage
```

Future V3.2 Agent code should consume this boundary and should not bind directly to
BM25, `SemanticIndex`, Graph Expansion, or Hybrid implementation internals. Phase 5
does not implement an Agent; V3.2 remains **NOT STARTED**.

## 10. Corpus and Performance Evidence

Final Independent QA measured **1233 RetrievalDocuments**, **131 files**, and **1233
symbols**. The implementation-time smoke count of 1232 documents remains historical
evidence; the final QA count is 1233. Repository additions can naturally add Python
symbols, so this change is not a `CorpusBuilder` regression.

Final real-corpus engineering observations were:

- `HybridRetriever.retrieve` median: approximately **13.981 ms**;
- `RetrievalService.retrieve` end-to-end median: approximately **13.959 ms**.

The service result is end-to-end and is not pure `ContextBuilder` latency.

| Synthetic N | Fusion | Deep top_k=N fusion | Deep top_k=N ContextBuilder |
| ---: | ---: | ---: | ---: |
| 100 | 0.391 ms | 0.723 ms | 0.240 ms |
| 1,000 | 3.920 ms | 7.318 ms | 2.402 ms |
| 5,000 | 20.435 ms | 36.799 ms | 12.252 ms |

No obvious O(N²) behavior was observed. These are engineering smoke measurements, not
formal thesis performance results or an SLA.

## 11. Deferred Low Findings

The six Low findings are accepted as non-blocking:

1. the Semantic clamp comment is weaker than its actual frozen saturating behavior;
2. the non-degradable exception chain can retain the provider message in a traceback;
3. ranked hits may outnumber rendered snippets;
4. `graph_provenance` may include unrendered candidate provenance;
5. real-corpus and latency evidence naturally differs between implementation-time and
   final-QA repository states; and
6. `DeterministicFakeEmbeddingProvider` remains a public export under the existing
   Phase 3.1 contract.

No Low requires Phase 5.1 or a Directed Retest. No production code is changed to clear
these notes during the documentation gate.

## 12. Regression Evidence

| Suite | Result |
| --- | ---: |
| Phase 5 Hybrid + Context + Service | **48 passed** |
| Phase 4 Index + Graph Expansion | **37 passed** |
| Phase 3.2 local adapter | **10 passed** |
| Phase 3.1 embedding core | **12 passed** |
| Phase 2 lexical | **14 passed** |
| Phase 1 corpus | **41 passed** |
| Offline LLM-contract smoke | **6 passed** |
| Full pytest regression | **576 passed** |

The standard command on this Anaconda Python 3.13.5 host reaches the known pytest
debugging-plugin / `rlcompleter` segmentation fault before collection. The approved
`python -m pytest -p no:debugging` workaround completed the suites. No real API,
Credential, network request, model download, or remote Embedding call was used.

## 13. RQ4 and Thesis Boundary

Phase 5 proves engineering implementation correctness for Hybrid Retrieval,
multi-signal fusion, Graph-aware scoring, degraded behavior, deterministic provenance,
context-budget construction, and the `RetrievalService` boundary. It does not prove
Hybrid > BM25, Hybrid > Embedding, Graph improves Recall, RAG improves maintenance
quality, or that RQ1–RQ4 are answered.

Formal experimental validity belongs to Phase 6. Phase 6 is **ALLOWED BUT NOT
STARTED**; no benchmark, ground truth, formal RQ experiment, or protocol change is part
of this gate.

## 14. Gate Decision

Final QA is **PASS FOR PHASE 5 WITH LOW NOTES**. Final Critical is **0**, Final Medium
is **0**, Final Low is **6**, and phase blockers are **0**. Phase 5.1 and Directed
Retest are **NOT REQUIRED**. Phase 5 is **COMPLETED**, the Documentation Gate is
**CLOSED**, Phase 6 is **ALLOWED BUT NOT STARTED**, and V3.2 is **NOT STARTED**.
