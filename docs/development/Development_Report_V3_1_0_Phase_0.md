# V3.1.0 Phase 0 — Architecture & Research Design Development Report

## Status

**COMPLETED — DOCUMENTATION GATE CLOSED**

Phase 0 freezes the V3.1.0 software architecture and research methodology. It contains
no production RAG package, embedding implementation, vector database, Agent, Router,
source-code change, test change, or dependency change.

## 1. Entry Baseline

| Item | Baseline |
| --- | --- |
| Branch | `v3.1.0-dev` |
| Gate input HEAD | `0deb4985efa0588c16beb479687bb02d5aa92d23` |
| Released version metadata | `3.0.1` |
| Previous release | V3.0.1 `RELEASED / FROZEN` |
| Phase 0.0 | `COMPLETED` |
| Regression baseline | `414 passed` |
| Offline LLM-contract smoke | `6 passed` |
| V3.1.0 status | `DEVELOPMENT STARTED` |
| Theme | Project Intelligence / RAG |

The known Anaconda Python 3.13.5 debugging-plugin / `rlcompleter` interpreter crash is
unchanged. The approved `python -m pytest -p no:debugging` command provides the current
host validation. Tests use no real API, Credential, network LLM, or network embedding.

## 2. Review Input

Claude completed the V3.1 Architecture & Research Review with **no architecture
blocker**. The review authorized documentation freeze before Phase 1, not implementation
inside Phase 0.

Phase 0 also inspected the existing code contracts that V3.1.0 must reuse:

- `SymbolId` is the stable language/path/qualified-name/kind identity;
- `ProjectSnapshot` stores hashes and graph state, not source text;
- `SnapshotDiff` classifies added, removed, changed, and unchanged files/symbols;
- `ProjectGraph` exposes only `CONTAINS` and `IMPORTS` relations;
- `AnalysisEngine` remains deterministic and failure-isolated;
- Python and Java adapters expose symbol ranges, signatures, and content hashes.

## 3. Documentation Outputs

Phase 0 creates:

- `docs/development/Architecture_Decision_V3_1_0.md`;
- `docs/development/Development_Report_V3_1_0_Phase_0.md`;
- `docs/qa/QA_Report_V3_1_0_Phase_0.md`;
- current-state and frozen-decision updates in `PROJECT_CONTEXT.md`.

README, Release Notes, `requirements.txt`, Python source, tests, `.gitignore`, historical
V3.0/V3.0.1 reports, and `docs/thesis/` remain unchanged.

## 4. Frozen Product Positioning

V3.1.0 is a Project Intelligence / Retrieval-Augmented Context Layer for software
maintenance. It retrieves symbols, files, and bounded structural context for a
maintenance task and constructs an explainable, reproducible, evaluable context
package. It is not a generic chatbot, document-QA demo, embedding wrapper, or Agent
runtime.

The primary retrieval unit is Symbol, using the existing `SymbolId`. File is secondary;
Chunk is fallback only for oversized symbols, unsupported/no-symbol files, and
documentation. Fixed-token chunks are not the default code unit.

## 5. Source Text and Corpus Decision

The existing snapshot intentionally does not persist source text. Phase 1 therefore
introduces a separate Corpus Builder and future `RetrievalDocument` contract rather
than modifying `ProjectSnapshot`.

The Corpus Builder reads source through the project root and existing adapters, then
compares actual content hashes with snapshot-recorded hashes. Stale or missing content
fails closed or requests a rebuild and is never silently indexed.

## 6. Retrieval Architecture

- **Lexical:** deterministic, offline BM25-style retrieval is the formal baseline and
  should prefer a standard-library implementation.
- **Embedding:** an independent `EmbeddingProvider` Protocol; it does not reuse chat
  completion Provider contracts.
- **Fake embedding:** allowed only for offline architecture/regression tests.
- **Semantic evidence:** formal RQ2/RQ4 experiments require a fixed real semantic model
  selected through a separate Phase 3 review.
- **Vector storage:** exact similarity search; no required FAISS, Chroma, or dedicated
  vector database.
- **Index identity:** project ID + snapshot hash + retrieval-config hash + optional
  embedding fingerprint.
- **Incremental indexing:** added/add, removed/delete, changed/replace,
  unchanged/reuse; results must equal a full rebuild.
- **Graph:** read-only `CONTAINS` and `IMPORTS`, bounded by hop, relation, per-seed, and
  global budgets.
- **Hybrid:** weighted score fusion is primary; RRF is an optional comparison; learned,
  LLM, and cross-encoder rerankers are deferred.
- **Context:** retrieval is separate from deduplication, ordering, graph context,
  snippets, and budget truncation.
- **Service:** future V3.2 consumers use `RetrievalService` and `ContextPackage`, not
  internal indexes or retrievers.

## 7. Core Research Questions

- **RQ1:** File vs Symbol vs Chunk retrieval units, emphasizing whether symbol-aware
  retrieval improves on coarse files and unstructured chunks.
- **RQ2:** lexical vs semantic embedding retrieval performance and complementarity.
- **RQ3:** contribution of existing `CONTAINS` and `IMPORTS` graph signals.
- **RQ4:** whether Lexical + Embedding + Graph hybrid retrieval is superior and which
  signal provides the gain.

`SnapshotDiff` incremental indexing remains a secondary engineering experiment.

## 8. Research Methodology

The primary dataset combines this repository and manually constructed fixture
projects. External open-source projects are optional generalization validation. Python
is the main experiment language and Java is coverage validation.

Queries cover symbol lookup, feature localization, dependency questions, bug
localization, maintenance tasks, and cross-file understanding. Human annotation is the
ground-truth source; graph facts may assist checks, but evaluated retrievers may not
define their own truth.

Primary metrics are Recall@K and MRR. Secondary metrics are nDCG@K, Precision@K, and
Hit Rate@K. Every strategy uses the same dataset, queries, truth, `top_k`, and metric
definitions.

The core ablation is capped at Lexical only, Embedding only, Hybrid without Graph,
Hybrid with Graph, and a Graph-focused variant. It avoids a large model/weight/hop grid.
Deterministic runs are not repeated for meaningless variance statistics.

## 9. Reproducibility and Performance

Experiment records include dataset, query-set, ground-truth, and retrieval-config
versions/hashes; embedding fingerprint; applicable seed; index identity; code commit;
and evaluation output. Raw outputs, summaries, and paper-ready figures stay distinct,
and raw output is never manually rewritten.

Performance evidence includes full build time, incremental update time, query latency,
index size, and context size, with hardware, Python version, dataset/index size, and run
scope.

## 10. Frozen Phase Plan

| Phase | Objective |
| --- | --- |
| 0 | Architecture & Research Design |
| 1 | Corpus & Symbol Content Model |
| 2 | Lexical Baseline — BM25 |
| 3 | Embedding Port & Semantic Retrieval Foundation |
| 4 | Graph-aware Retrieval + Index Identity + Incremental Indexing |
| 5 | Hybrid Retrieval + Context Builder + RetrievalService |
| 6 | Evaluation Benchmark + Ablation + Reproducible Results |
| RC | Release Engineering + Documentation + Thesis Materials |

Phase 1 remains **NOT STARTED**. It must deliver `RetrievalDocument`, Corpus Builder,
freshness validation, deterministic Python/Java fixtures, retrieval-unit fixtures, and
corpus statistics without modifying snapshots to store source text.

## 11. Thesis Mapping

The architecture maps to thesis requirements analysis, overall architecture, Project
Intelligence layer design, symbol-aware retrieval, graph-aware retrieval, hybrid
retrieval, incremental indexing, experiment design, ablation, performance evaluation,
results, and limitations.

Research claims remain limited to a maintenance-oriented system design, structural
signal fusion, and experimental validation. No novel BM25, embedding, or graph
algorithm is claimed.

## 12. Deferred Scope

V3.1.0 defers Multi-Agent runtime/planner/memory/collaboration, Router/model routing,
VS Code integration, LLM/cross-encoder reranking, autonomous patch generation and
test-pass loops, required Vector DB infrastructure, Payment, Recharge, Admin UI,
Auth/RBAC, and a production SaaS backend.

## 13. Documentation Policies and Backlog

The permanent README Version History and per-release Thesis-Oriented Development Report
policies remain frozen. V3.1.0 must produce
`docs/thesis/V3_1_0_Thesis_Development_Report.md` after final release from real code,
QA, experiment, and release evidence.

The V3.0.0 thesis report is missing/backlog. The existing untracked
`docs/thesis/V3_0_1_Thesis_Development_Report.md` is a user document pending separate
review and is not modified, moved, deleted, staged, or committed by Phase 0.

## 14. Validation and Closure

- Claude Architecture & Research Review: no blocker;
- architecture/research document consistency: PASS;
- production implementation introduced: none;
- full regression: **414 passed** with the approved current-host workaround;
- offline LLM-contract smoke: **6 passed**;
- real API, Credential, network LLM, or network embedding: none.

The V3.1.0 Phase 0 Documentation Gate is **CLOSED**. A separate Phase 1 task is allowed,
but Phase 1 was not started here.
