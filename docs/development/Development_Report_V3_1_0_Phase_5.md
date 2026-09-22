# V3.1.0 Phase 5 — Hybrid Retrieval + ContextBuilder Development Report

## Final Status

- Phase 5 implementation: **COMPLETED**
- Independent QA: **PASS WITH LOW NOTES**
- Final QA: **PASS FOR PHASE 5 WITH LOW NOTES**
- Final Critical / Medium / Low: **0 / 0 / 6**
- Phase blockers: **0**
- Phase 5.1: **NOT REQUIRED**
- Directed Retest: **NOT REQUIRED**
- Phase 5 Documentation Gate: **CLOSED**
- Phase 6: **ALLOWED BUT NOT STARTED**
- V3.2 Multi-Agent: **NOT STARTED**

This is the final engineering record for Phase 5. It closes documentation and freezes
the implemented Hybrid Retrieval, context-construction, and service boundary. This gate
does not modify production code, tests, dependencies, or thesis documents, and it does
not begin Phase 6 or V3.2.

## 1. Objective and Architecture

Phase 5 completes the retrieval-facing architecture frozen in
`Architecture_Decision_V3_1_0.md`:

```text
RetrievalQuery
      |
      v
BM25 + SemanticIndex + Graph Expansion
      |
      v
HybridRetriever (Weighted Fusion; optional RRF)
      |
      v
ContextBuilder (ordering, deduplication, character budget)
      |
      v
RetrievalService.retrieve(...) -> ContextPackage
```

The implementation consumes the Phase 1 immutable `RetrievalDocument` corpus, Phase 2
BM25 results, Phase 3 exact Semantic results, and Phase 4 bounded Graph Expansion. It
does not rescan the project, replace `SymbolId`, mutate branch scores, add a learned
ranker, or introduce an Agent runtime.

The authoritative candidate identity is `code_maintenance.SymbolId`. The ranked
candidate set is the union `lexical candidates ∪ semantic candidates`; duplicate
appearances across branches collapse to one candidate by `SymbolId`. Equal final scores
use the canonical `SymbolId` key as a stable secondary ordering, so input iteration,
set order, and hash randomization do not define the result.

## 2. Weighted Score Fusion Contract

Weighted Score Fusion is the default and primary Phase 5 strategy:

```text
final_score =
    lexical_weight  * normalized_lexical_score
  + semantic_weight * normalized_semantic_score
  + graph_weight    * graph_score
```

All weights are explicit, finite, and non-negative. They do not need to sum to one:
the final score is a relative ranking value, not a calibrated probability. At least
one candidate-producing branch, Lexical or Semantic, must have positive weight. A
missing component for a candidate contributes `0` and does not fabricate a raw branch
score or rank.

The original BM25 and Semantic score/rank values remain available on `HybridHit` and
are not overwritten by the Graph signal or normalization. `HybridHit` records raw
branch values, normalized values, Graph score and provenance, fusion configuration,
final score, and final rank.

## 3. Normalization Contract

BM25 uses branch-maximum normalization:

```text
normalized_lexical_score = lexical_score / max(branch lexical scores)
```

An empty branch is absent. If the maximum is zero, every present lexical candidate
receives normalized lexical contribution `0`; division by zero is not attempted.

Semantic scores use the fixed exact-cosine interval mapping:

```text
bounded_cosine = clamp(cosine_score, -1, 1)
normalized_semantic_score = (bounded_cosine + 1) / 2
```

The production `SemanticIndex` uses L2-normalized vectors and exact cosine similarity.
Finite values just beyond the nominal interval may be saturated by the clamp, including
reasonable floating-point drift. Phase 5 does not implement learned normalization,
score calibration, or corpus-fitted scaling.

## 4. Retrieval Modes and Optional RRF

The same explicit configuration supports independently ablatable modes:

- Lexical-only;
- Semantic/Embedding-only;
- Hybrid without Graph;
- Hybrid with Graph; and
- a Graph-focused variant that still obtains candidates from an enabled retrieval
  branch.

Deterministic weighted Reciprocal Rank Fusion is implemented as an optional comparison
baseline. RRF uses branch ranks, explicit weights, and positive `rrf_k`; it does not
replace Weighted Fusion as the primary strategy and is not a learned reranker.

## 5. Degraded-Mode Contract

Standalone Semantic Retrieval continues to fail explicitly. In Hybrid mode, a
Semantic branch failure may degrade to a complete Lexical-only result only when the
Lexical branch is enabled. The returned result and final `ContextPackage` then carry:

- `degraded=True`;
- a stable type-based `degradation_reason`; and
- immutable `failure_provenance`.

No Semantic hit, rank, raw score, normalized score contribution, or claimed Semantic
success is retained in that degraded result. The normal degraded path does not include
the provider's original exception text in the reason or failure provenance.

Semantic-only retrieval cannot degrade because no Lexical branch exists; it raises an
explicit `HybridRetrievalError`. Its exception chaining may preserve the upstream
provider exception as Python `__cause__`, so the original provider message may appear
in a traceback. This is accepted future privacy-oriented defensive hardening, not a
Phase 5 blocker.

## 6. Graph Signal Contract

Phase 5 consumes Phase 4 Graph candidates and immutable provenance without modifying
the directed `ProjectGraph`. The frozen heuristic is composed from relation, traversal
direction, and hop:

```text
graph_score = relation_factor * direction_factor / hop
```

The current factors are `IMPORTS=1.0`, `CONTAINS=0.75`, `FORWARD=1.0`, and
`REVERSE=0.8`; when multiple provenances exist for one candidate, the maximum signal
is the score while the deterministic provenance tuple remains available. The following
signals stay distinguishable:

- `IMPORTS/FORWARD`;
- `IMPORTS/REVERSE`;
- `CONTAINS/FORWARD`; and
- `CONTAINS/REVERSE`.

Graph Expansion may also return structural nodes with no source document. Graph
provenance is preserved even when a structural node or a later budget decision yields
no rendered source snippet. Phase 5 makes no claim that Graph improves Recall.

## 7. ContextBuilder Contract

`ContextBuilder` consumes only retrieval-layer values: `HybridRetrievalResult`,
`RetrievalDocument`, Graph candidates/provenance, and `RetrievalIndexIdentity`. It does
not read the filesystem, rescan source, parse source, rebuild an index, or embed text.

Its responsibilities are:

- deduplicate source documents by authoritative `SymbolId`;
- order final Hybrid hits by Hybrid rank;
- place renderable Graph-only context adjacent to its ranked seed when possible;
- append remaining renderable Graph context deterministically;
- assemble source exclusively from `RetrievalDocument.source_text` with stable symbol
  and path/line metadata;
- apply the explicit character budget; and
- expose every truncation decision.

Graph-only source snippets have `ContextSnippet.hybrid_rank=None`; this distinguishes
context expansion from final ranked retrieval hits. Structural Graph nodes never gain
fabricated source text.

## 8. Hits, Snippets, and Budget Semantics

`ContextPackage.hits` is the complete tuple of final ranked Hybrid hits returned for
the query. It is not the list of source snippets actually rendered into
`context_text`. Because the context budget may stop construction, some hits may have no
corresponding `ContextSnippet`. Conversely, a Graph-only source snippet may be rendered
without being a ranked hit and therefore has `hybrid_rank=None`.

`ContextPackage.snippets` is the authoritative record of rendered content. The package
may also retain Graph provenance for candidates that were not rendered. Future V3.2
consumers must not infer that every hit is already present in the prompt context or
that every recorded Graph provenance has visible source in `context_text`.

The budget unit is **characters** and the package enforces:

```text
budget_used == len(context_text)
budget_used <= budget
```

If the highest-priority next snippet exceeds the remaining budget, it is truncated
deterministically to the available character count. The affected `ContextSnippet` and
the package set `truncated=True`. Construction stops after that partial snippet; no
silent truncation occurs.

## 9. RetrievalService and V3.2 Boundary

The recommended future consumption boundary is:

```text
RetrievalService.retrieve(RetrievalQuery) -> ContextPackage
```

`RetrievalQuery` is immutable and carries task text, final `top_k`, and character
context budget. `ContextPackage` is immutable and carries ranked hits, rendered text,
rendered snippets, index identity, Graph/failure provenance, degradation state, and
budget/truncation metadata.

Future V3.2 Agent code should depend on this facade rather than BM25 internals,
`SemanticIndex` internals, Graph traversal internals, or Hybrid fusion internals. Phase
5 implements only this stable boundary; it does not implement an Agent, planner,
memory, collaboration runtime, or Router. V3.2 remains **NOT STARTED**.

## 10. Ablation Readiness and Research Boundary

The completed architecture can express the frozen Phase 6 comparison groups:
Lexical-only, Embedding-only, Hybrid without Graph, Hybrid with Graph, and a
Graph-focused variant. This establishes experiment-architecture readiness only.

Phase 5 demonstrates that the Hybrid pipeline, deterministic provenance, degraded
mode, and character-budgeted context construction are implemented and regression
tested. It does not prove:

- Hybrid > BM25;
- Hybrid > Embedding;
- Graph improves Recall;
- RQ1–RQ4 are answered; or
- RAG improves software-maintenance quality.

Those conclusions require the Phase 6 benchmark, ground truth, ablation, metrics, and
reproducibility evidence. Phase 6 is now **ALLOWED BUT NOT STARTED**; this gate creates
no benchmark, ground truth, formal experiment, or protocol change.

## 11. Independent QA and Corpus Evidence

Independent QA returned **PASS WITH LOW NOTES**. Final counts are Critical **0**,
Medium **0**, Low **6**, and phase blockers **0**. Phase 5.1 and Directed Retest are
both **NOT REQUIRED**.

Independent QA executed **243 / 243 probes**:

| Probe category | Result |
| --- | ---: |
| fusion | 77 / 77 |
| normalization extremes | 19 / 19 |
| context | 48 / 48 |
| service | 52 / 52 |
| scope | 21 / 21 |
| determinism | 9 / 9 |
| performance | 17 / 17 |

These are independent probes, not 243 pytest tests.

The final Independent QA corpus contained **1233 RetrievalDocuments**, **131 files**,
and **1233 symbols**. The earlier implementation smoke recorded 1232 documents; that
remains valid implementation-time evidence. The one-document difference reflects the
natural addition of Python symbols as repository documentation/test support evolved,
not a `CorpusBuilder` regression. Final QA evidence uses 1233.

## 12. Engineering Performance Evidence

On the final real corpus, Independent QA measured approximately:

- `HybridRetriever.retrieve` median: **13.981 ms**;
- `RetrievalService.retrieve` end-to-end median: **13.959 ms**.

The end-to-end service value must not be described as pure `ContextBuilder` latency.

Synthetic fusion scaling was approximately:

| Candidate count | Fusion time |
| ---: | ---: |
| 100 | 0.391 ms |
| 1,000 | 3.920 ms |
| 5,000 | 20.435 ms |

With deep `top_k=N`, the measurements were:

| N | Fusion | ContextBuilder |
| ---: | ---: | ---: |
| 100 | 0.723 ms | 0.240 ms |
| 1,000 | 7.318 ms | 2.402 ms |
| 5,000 | 36.799 ms | 12.252 ms |

The probes did not observe obvious O(N²) scaling. All latency values are engineering
smoke evidence, not formal thesis performance results, production SLAs, or an RQ4
result.

## 13. Deferred Low Notes

The six accepted findings are non-blocking:

1. the Semantic clamp comment is narrower than the actual frozen saturating behavior;
2. an exception path that cannot degrade uses exception chaining, so the provider's
   original message may remain in a traceback;
3. `ContextPackage.hits` may contain more entries than rendered snippets and requires
   explicit consumer documentation;
4. `graph_provenance` may include provenance for candidates not rendered into context;
5. implementation-time and final-QA corpus/latency evidence can drift naturally as the
   repository gains Python symbols; and
6. `DeterministicFakeEmbeddingProvider` remains a public export as part of the existing
   Phase 3.1 contract.

None requires production-code changes for this gate. The fake provider remains valid
only for architecture, regression, and failure tests and provides no semantic-quality
evidence.

## 14. Validation Evidence

| Suite | Final result |
| --- | ---: |
| Phase 5 Hybrid + Context + Service | **48 passed** |
| Phase 4 Index + Graph Expansion | **37 passed** |
| Phase 3.2 local adapter | **10 passed** |
| Phase 3.1 embedding core | **12 passed** |
| Phase 2 lexical | **14 passed** |
| Phase 1 corpus | **41 passed** |
| Offline LLM-contract smoke | **6 passed** |
| Full regression | **576 passed** |

The ordinary host invocation still triggers the known Anaconda Python 3.13.5 pytest
debugging-plugin / `rlcompleter` segmentation fault before collection. The established
`python -m pytest -p no:debugging` workaround produced the recorded results. No real
API, Credential, network LLM, remote Embedding request, or model download was used.

## 15. Thesis Relevance and Final Boundary

Phase 5 supplies thesis-ready engineering material for Hybrid Retrieval architecture,
multi-signal fusion, Graph-aware scoring, degraded-mode design, deterministic
provenance, context-budget construction, and the `RetrievalService` handoff boundary.
It makes the five Phase 6 ablation configurations implementable through explicit
configuration and preserves the evidence needed to explain each result.

Experimental validity and comparative findings still belong to Phase 6. Final Phase 5
QA is **PASS FOR PHASE 5 WITH LOW NOTES**, Phase 5 is **COMPLETED**, and its
Documentation Gate is **CLOSED**. Phase 6 is **ALLOWED BUT NOT STARTED**; V3.2 remains
**NOT STARTED**.
