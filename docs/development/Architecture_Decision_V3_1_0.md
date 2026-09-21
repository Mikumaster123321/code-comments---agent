# V3.1.0 Project Intelligence / RAG Architecture & Research Decision

- **Status:** Frozen
- **Version:** V3.1.0
- **Phase:** Phase 0 — Architecture & Research Design
- **Review:** Claude Architecture & Research Review — no architecture blocker
- **Scope:** Software architecture and research methodology only; no production RAG implementation

## 1. Decision Summary

V3.1.0 establishes a **Project Intelligence / Retrieval-Augmented Context Layer for
Software Maintenance**. Given a maintenance task, the layer retrieves the most
relevant symbols, files, and bounded structural context, then builds an explainable,
reproducible, and evaluable context package.

V3.1.0 is not a generic knowledge-base chatbot, a document-QA demonstration, a thin
embedding wrapper, or an Agent runtime. It builds on the existing deterministic
project-maintenance core rather than replacing it:

```text
ProjectScanner -> ProjectGraph -> ProjectSnapshot
                         |              |
                         +----> Corpus Builder -> Retrieval Index
                                                    |
Task -> RetrievalQuery -> Lexical / Embedding / Graph -> Hybrid Fusion
                                                    |
                                             ContextBuilder
                                                    |
                                          RetrievalService
                                                    |
                                             ContextPackage
```

## 2. Thesis Role and Contribution Boundary

V3.1.0 is a core thesis research stage. Its research value does not come from merely
using embeddings.

Engineering contributions are:

- a stable symbol-aware retrieval corpus built from existing project state;
- deterministic lexical retrieval and an independent embedding port;
- bounded graph-aware expansion, index identity, and incremental indexing;
- an explainable hybrid retrieval and context-construction service;
- offline regression boundaries and reproducible experiment artifacts.

Research contributions are:

- comparing file-, symbol-, and chunk-level retrieval for maintenance tasks;
- measuring the complementary behavior of lexical and semantic retrieval;
- measuring the contribution of existing project-graph signals;
- evaluating explainable hybrid retrieval through controlled ablation;
- studying maintenance-task-oriented context construction with reproducible evidence.

The thesis must not claim a new BM25, embedding, or graph algorithm unless later work
actually creates one. The defensible contribution is a software-maintenance-oriented
Project Intelligence architecture that combines stable symbol identity, project
structure, hybrid retrieval, and controlled empirical validation.

## 3. Core Research Questions

The following four questions are frozen:

- **RQ1 — Retrieval Unit:** How do File, Symbol, and Chunk retrieval units differ in
  code-maintenance retrieval quality? In particular, does symbol-aware retrieval
  outperform coarse File retrieval and unstructured Chunk retrieval?
- **RQ2 — Retrieval Strategy:** How do lexical retrieval and semantic embedding
  retrieval perform on maintenance queries, and where are they complementary?
- **RQ3 — Graph Signal:** Can the existing `CONTAINS` and `IMPORTS` signals in
  `ProjectGraph` improve relevant-code-entity recall?
- **RQ4 — Hybrid Retrieval:** Does a Lexical + Embedding + Graph hybrid strategy
  outperform individual strategies, and which signal accounts for the gain?

`SnapshotDiff` incremental indexing is a secondary engineering performance experiment,
not a core research question. It compares full rebuild time, incremental update time,
and retrieval-result consistency.

V3.1.0 may measure correct file localization, correct symbol localization, and context
size/cost. Patch generation, autonomous test-pass rate, and full autonomous maintenance
evaluation are deferred to V3.2.

## 4. Retrieval Units and Identity

The unit policy is frozen as:

- **Primary:** Symbol;
- **Secondary:** File;
- **Fallback only:** Chunk.

Symbol is primary because it provides a semantic boundary, higher expected precision,
stable `SymbolId` identity, incremental identity across snapshots, and a meaningful
research comparison. File remains necessary for file-level context and content without
supported symbols. Chunk is limited to oversized symbols, unsupported or no-symbol
files, and documentation text. Fixed-token chunking must not become the default code
retrieval unit.

Retrieval identity must reuse `code_maintenance.SymbolId`. V3.1.0 must neither invent
a second retrieval symbol ID nor modify the frozen `SymbolId` contract.

## 5. Retrieval Corpus Contract

Phase 0 freezes the minimum future `RetrievalDocument` contract without implementing a
production dataclass:

| Category | Minimum fields |
| --- | --- |
| Identity | `SymbolId`, language, relative path, qualified name, kind |
| Retrieval text | signature, source text, optional documentation text |
| Metadata | content hash, imports, start/end lines, optional `AnalysisFinding` metadata |

`ProjectSnapshot` intentionally stores state and identity, not source text. V3.1.0 must
not put full source content into the snapshot. A separate Corpus Builder will combine
the snapshot, project root, and existing language adapters to construct retrieval
documents.

After reading source, the Corpus Builder must compare the actual content hash with the
hash recorded by the snapshot. A mismatch is stale input and must fail closed or request
a rebuild; stale content must never be silently indexed. This is the corpus freshness
contract that closes the time-of-snapshot/time-of-read gap.

## 6. Query, Hit, and Context Contracts

The minimum future `RetrievalQuery` supports task text, language filter, path scope,
symbol scope, task type, `top_k`, and an explicit context budget. It contains no
Credential, Provider client, or Credits state.

The minimum future `RetrievalHit` contains document identity, score, rank, strategy,
content hash, and metadata. Hits must support evaluation, explanation, and future Agent
consumption.

Retrieval and context building remain separate. `ContextBuilder` owns deduplication,
ordering, bounded graph context, source snippets, and budget truncation. It does not own
prompt templates, few-shot examples, or Agent planning. The context budget is explicit
and model-agnostic; V3.1.0 does not depend on the future V3.3 Router to choose it.

`ContextPackage` is the future immutable handoff produced by the retrieval layer. Its
exact production fields remain a Phase 5 implementation decision, but it must preserve
document identity, ordering, source provenance, and budget/explanation metadata.

## 7. Lexical Baseline

A BM25-style lexical retriever is the formal baseline. The preferred implementation is
Python standard library only, with no new retrieval dependency. It must be deterministic,
offline, unit-testable, and explainable.

The project must not skip the lexical baseline and proceed directly to embeddings.
Phase 2 covers BM25 correctness, tokenization, document frequency, IDF, length
normalization, ranking, deterministic tie ordering, empty queries, unknown terms,
input-order independence, and corpus compatibility. Incremental indexing, incremental
index consistency, and `SnapshotDiff` add/delete/replace/reuse operations belong to
Phase 4, not Phase 2.

## 8. Embedding Architecture and Evidence Boundary

`EmbeddingProvider` is an independent Protocol. It must not reuse `LLMProvider` or
`TaskScopedLLMProvider`, because chat completion and embedding have different inputs,
outputs, error semantics, and cost models.

Two evidence levels are strictly separated:

1. **Architecture/regression tests** may use a deterministic fake embedding provider
   for offline fingerprint, index, hybrid, and failure tests.
2. **Thesis semantic-retrieval experiments** for RQ2 or RQ4 must use a real semantic
   embedding model with fixed identity/version, dimension, normalization, and
   reproducible fingerprint.

Fake or hash embeddings must never support a thesis claim comparing BM25 with semantic
embedding quality. Phase 3 requires a separate Real Semantic Embedding Selection Review
covering model/version, dimension, normalization, local/offline feasibility, license,
reproducibility, and hardware/runtime cost. Phase 0 deliberately does not select a
vendor or model.

Remote embedding is never enabled silently. Any future remote use requires explicit
configuration because source code may leave the local machine. Core thesis tests and
all regression tests must be runnable completely offline.

The minimum `EmbeddingFingerprint` identity is:

- provider ID;
- model ID/version;
- dimension;
- normalization;
- deterministic fingerprint hash.

A change to any field invalidates silent reuse of an old embedding cache or index.

## 9. Vector Retrieval and Index Identity

V3.1.0 does not require FAISS, Chroma, or a dedicated vector database. Exact similarity
search is preferred using in-memory or lightweight local persistence. At the expected
undergraduate-project scale, exact retrieval is sufficient and avoids approximate
nearest-neighbor recall contaminating strategy comparisons. Evidence of a real scale
need would require a new Architecture Review.

Phase 0 does not select NumPy, SQLite BLOB storage, or another concrete persistence
mechanism. The implementation phase must choose the smallest justified option.

The future `RetrievalIndexIdentity` must include at least:

- project ID;
- snapshot content hash;
- retrieval-config hash;
- optional embedding fingerprint.

Any identity change invalidates silent reuse of the old index.

## 10. Incremental Indexing

`SnapshotDiff` maps to index operations as follows:

| Snapshot state | Index action |
| --- | --- |
| Added | Add |
| Removed | Delete |
| Changed | Replace |
| Unchanged | Reuse |

Incremental output must be tested for equivalence with a full rebuild. Incremental
indexing is an engineering performance capability and is evaluated with full-build
time, incremental-update time, and result consistency.

## 11. Graph-Aware Retrieval

Graph retrieval reads only the existing `CONTAINS` and `IMPORTS` relations. V3.1.0 does
not change the frozen `ProjectGraph` contract. Graph signals are used for bounded
context expansion and hybrid score boosts, not unbounded traversal.

Every expansion must enforce:

- a hop limit;
- a relation whitelist;
- a per-seed budget;
- a global context-node budget.

`max_hops = 1` is the initial candidate, not a Phase 0 hard-coded production default;
implementation tests may adjust the exact value. Infinite expansion across the project
graph is prohibited.

## 12. Hybrid Retrieval and Reranking

Weighted score fusion is the primary hybrid method because it is explainable and easy
to ablate. Reciprocal Rank Fusion (RRF) is an optional comparison. V3.1.0 does not add a
learned ranker.

LLM rerankers and cross-encoder rerankers are deferred because they add cost,
dependencies, nondeterminism, and experimental confounding. Graph or heuristic boosts
are part of hybrid fusion, not a separate model reranker.

### 12.1 Clarification / Refined Phase Ownership

The earlier Phase 0 wording that “embedding failure -> lexical fallback” described
the final Hybrid/system-resilience behavior. It did not require the Phase 3 Semantic
Retriever to absorb a provider failure. This is a contract clarification, not a Phase
0 architecture reversal:

- Phase 3 standalone Semantic Retrieval: an `EmbeddingProvider` failure must fail
  explicitly as a stable semantic retrieval error; it must not silently return BM25
  results or claim semantic success.
- Phase 5 Hybrid Retrieval: the embedding branch may degrade to lexical-only fallback,
  provided the result explicitly marks degraded mode and strategy provenance. It must
  not be presented as a complete Hybrid success.

Failure ownership is layered: `EmbeddingProvider` reports provider/model failure;
the Semantic Retriever converts it to the stable semantic retrieval error; the Phase
5 Hybrid Retriever decides whether lexical fallback is permitted; and the future
`RetrievalService` exposes the final strategy/provenance. Hybrid fallback is not
implemented in Phase 3.

## 13. Package and Dependency Architecture

The new production package is frozen as top-level `project_intelligence/`, but Phase 0
does not create it. Its minimum responsibilities are:

```text
domain.py             retrieval values and contracts
corpus.py             source extraction and freshness
lexical.py            BM25-style baseline
embedding_port.py     independent embedding Protocol and fingerprint
graph_expansion.py    bounded graph signal
index.py              identity, exact retrieval, incremental updates
hybrid.py             explainable fusion
context.py            context construction and budgets
service.py            RetrievalService boundary
```

Implementation may combine files when that keeps the package smaller, but these
responsibility boundaries remain. Evaluation code is not a production `evaluation.py`
module unless a future product-runtime requirement justifies it; experiment code stays
separate from production code.

Allowed dependency direction:

```text
project_intelligence -> code_maintenance
```

`project_intelligence` may consume public read-only contracts such as `SymbolId`,
`ProjectScanner`, `ProjectGraph`, `ProjectSnapshot`, `SnapshotDiff`, and
`AnalysisFinding`. The reverse dependency is prohibited. `project_intelligence` must
not strongly depend on `credits`, `managed_access`, or `admin_operations`.

## 14. Analysis and Future Agent Boundaries

`AnalysisEngine` remains a deterministic analysis service. `AnalysisFinding` may be
retrieval metadata, but RAG must not control the engine lifecycle or turn it into a
general framework.

The future V3.2 Agent layer consumes `RetrievalService` and `ContextPackage`; it must
not directly manipulate index, lexical, embedding, or graph internals. V3.1.0 defines
this consumption boundary but implements no Agent runtime, planner, memory,
collaboration, or Router.

## 15. Failure Model

The minimum failure behavior is frozen as:

- stale content -> fail closed or rebuild;
- missing source -> fail closed;
- snapshot mismatch -> reject or rebuild;
- corrupt index -> rebuild;
- standalone Phase 3 embedding-provider failure -> explicit semantic retrieval error;
  Phase 5 Hybrid Retrieval may use an explicitly marked degraded lexical-only fallback.

V3.1.0 does not create a complex retry framework.

## 16. Offline Testability

All core regression tests are offline and use deterministic fake embeddings, fixture
projects, fixed queries, and fixed ground truth. Regression tests must use no real API,
Credential, network embedding, or network LLM request.

This offline rule does not authorize fake embeddings as semantic research evidence.
A separately reviewed real semantic model is required for formal RQ2/RQ4 experiments
if those questions retain embedding comparisons.

## 17. Evaluation Dataset and Queries

The primary benchmark combines:

1. this project's own codebase; and
2. manually constructed fixture projects.

An external open-source project is optional for generalization validation. Python is
the main experiment language; Java is a coverage-validation language and need not have
a fully symmetric experiment matrix. The thesis must state known Java-adapter limits.

The benchmark covers at least symbol lookup, feature localization, dependency
questions, bug localization, maintenance tasks, and cross-file understanding. It must
not consist only of exact-name symbol lookup.

Every dataset version records dataset ID/version, source commit/hash, language, project
size, file count, and symbol count. An external project additionally records repository,
commit/tag, license, and selection reason.

## 18. Ground Truth and Fairness

Ground truth is primarily human annotated. Project-graph structural facts may assist
validation, but the retriever under evaluation must never generate its own ground truth.

Each annotation stores query ID, query text, relevant files/symbols, optional graded
relevance for nDCG, and preferably an annotation rationale. Important queries should
receive an independent review when feasible.

All compared strategies use the same dataset, query set, ground truth, `top_k`, and
metric definitions. Strategy-specific data substitutions are prohibited.

## 19. Metrics, Ablation, and Statistics

Primary metrics are **Recall@K** and **MRR** because missing relevant maintenance
context is a central risk. Secondary metrics are nDCG@K, Precision@K, and Hit Rate@K.

The ablation matrix is capped at five core groups:

1. Lexical only;
2. Embedding only;
3. Hybrid Lexical + Embedding without Graph;
4. Hybrid Lexical + Embedding + Graph;
5. Graph-focused variant.

The study must not expand into a large model x weight x hop grid search. Deterministic
retrieval is not repeatedly run merely to report meaningless mean/standard deviation or
complex significance tests. If a real remote model later introduces randomness, the
experiment plan must explicitly decide an appropriate repeated-run policy.

## 20. Reproducibility and Result Integrity

Every experiment record contains:

- dataset version/hash;
- query-set version/hash;
- ground-truth version/hash;
- retrieval config/hash;
- embedding fingerprint;
- random seed when applicable;
- index identity;
- code commit;
- evaluation output.

Future experiment artifacts may use `docs/experiments/` for dataset manifests, configs,
and result summaries; the exact layout is frozen before implementation in Phase 6.
Large vector indexes and embedding caches must not be committed to Git.

Raw experiment output, summary tables, and paper-ready figures are distinct artifacts.
Raw results must never be manually edited to improve thesis data. A rerun preserves its
config, commit, dataset, and fingerprint.

## 21. Performance Evidence

Engineering performance records at least full index build time, incremental update
time, query latency, index size, and context size. Claims state hardware, Python
version, dataset size, index size, and run scope. Millisecond results from small
fixtures must not be presented as production scalability evidence.

## 22. Frozen Phase Plan

1. **Phase 0 — Architecture & Research Design**
2. **Phase 1 — Corpus & Symbol Content Model**
3. **Phase 2 — Lexical Baseline: BM25**
4. **Phase 3 — Embedding Port & Semantic Retrieval Foundation**
5. **Phase 4 — Graph-aware Retrieval, Index Identity & Incremental Indexing**
6. **Phase 5 — Hybrid Retrieval, Context Builder & RetrievalService**
7. **Phase 6 — Evaluation Benchmark, Ablation Study & Reproducible Results**
8. **RC — Release Engineering, Documentation & Thesis Materials**

Phase 1 closes the source-text gap with `RetrievalDocument` and Corpus Builder. Phase 2
creates the deterministic lexical baseline. Phase 3 adds the embedding port, fake test
provider, exact similarity foundation, and the separate real-model selection review.
Phase 4 adds index identity, `SnapshotDiff` operations, and bounded graph signals.
Phase 5 delivers explainable hybrid fusion, `ContextBuilder`, `ContextPackage`, and the
future-Agent-facing `RetrievalService`. Phase 6 produces the benchmark, ground truth,
evaluation runner, ablation, and performance/reproducibility evidence.

## 23. RC Stop Conditions

V3.1.0 may enter RC only when:

1. the symbol-aware corpus is stable;
2. the BM25 lexical baseline is complete;
3. the embedding architecture is complete;
4. at least one fixed real semantic model supports formal RQ2/RQ4 experiments if those
   questions retain embedding comparisons;
5. graph-aware and hybrid retrieval are complete;
6. incremental indexing is complete and equivalent to full rebuild results;
7. `RetrievalService` and `ContextPackage` are frozen;
8. benchmark, query set, and ground truth are complete;
9. RQ1-RQ4 have reproducible results;
10. Recall@K, MRR, and secondary metrics can be recomputed consistently;
11. the five performance measurements are recorded;
12. Python main experiments and Java coverage validation are complete; and
13. fixed config, dataset, fingerprint, commit, and outputs can reproduce results.

## 24. Thesis Mapping

The frozen work maps to thesis sections on requirements analysis, overall architecture,
Project Intelligence retrieval-layer design, symbol-aware retrieval, graph-aware
retrieval, hybrid retrieval, incremental indexing, experiment design, ablation,
performance evaluation, result discussion, and limitations.

## 25. Explicitly Deferred

V3.1.0 does not implement Multi-Agent runtime/planner/memory/collaboration, Router or
model routing, VS Code integration, LLM or cross-encoder reranking, autonomous patch
generation, an autonomous test-pass loop, a required Vector DB, Payment, Recharge,
Admin UI, Auth/RBAC, or a production SaaS backend.

## 26. Documentation Policies

Every formal release retains an accurate, concise README Version History entry with
Version, Status, actual Major Updates or Changes, necessary Phase Summary, and Test
Baseline. Internal finding IDs, probe counts, and directed-retest workflow details do
not belong in README history.

After every formal release, create a version-level Thesis-Oriented Development Report.
V3.1.0 must eventually create
`docs/thesis/V3_1_0_Thesis_Development_Report.md` from real code, Development Reports,
QA Reports, experiment results, and release evidence.

The tracked V3.0.0 thesis report remains missing/backlog. The existing untracked
`docs/thesis/V3_0_1_Thesis_Development_Report.md` is a user document pending separate
review; Phase 0 must not modify, move, delete, or commit it.

## 27. Consequences and Next Step

The Software Architecture and Research Methodology are **FROZEN** with no blocking
issue. At the time of this original Phase 0 decision, the documentation gate
authorized a separate Phase 1 — Corpus & Symbol Content Model task. That historical
authorization is retained; Phase 1 and the subsequent Phase 2 Lexical Baseline are
now completed with their documentation gates closed. Phase 3 is allowed but not
started, and the next task is the Phase 3.0 Documentation Freeze based on the
completed Claude Semantic Embedding Selection Review.
