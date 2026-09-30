# V3.1.0 Phase 0 — Architecture & Research Methodology QA Report

## Review Classification

- **Review type:** Architecture and Research Methodology Consistency Review
- **Architecture review input:** Claude — no architecture blocker
- **Final verdict:** **PASS / FROZEN**
- **Blocking issues:** 0
- **Business-code QA:** Not applicable; Phase 0 is documentation-only

## 1. Scope

This review verifies that the Architecture Decision, Development Report, QA Report, and
`PROJECT_CONTEXT.md` express one consistent V3.1.0 architecture and research plan. It
does not claim functional RAG behavior because no production RAG implementation exists.

## 2. Hard-Gate Evidence

| Check | Result |
| --- | --- |
| Branch | `v3.1.0-dev` |
| Gate input HEAD | `0deb4985efa0588c16beb479687bb02d5aa92d23` |
| Version metadata | `3.0.1` |
| Previous release | V3.0.1 `RELEASED / FROZEN` |
| Phase 0.0 | `COMPLETED` |
| V3.1.0 | `DEVELOPMENT STARTED` |
| V3.2 / V3.3 | `NOT STARTED` / `NOT STARTED` |
| Commercial track | `DEFERRED / OPTIONAL` |
| Production RAG code at gate input | None |

The pre-existing untracked
`docs/thesis/V3_0_1_Thesis_Development_Report.md` remains outside this gate and is not
modified or committed.

## 3. Architecture Consistency Matrix

| Decision | Frozen result |
| --- | --- |
| Product position | Maintenance-oriented Project Intelligence context layer |
| Retrieval units | Symbol primary; File secondary; Chunk fallback only |
| Symbol identity | Existing `code_maintenance.SymbolId` |
| Source-text gap | Separate Corpus Builder; no source text added to snapshot |
| Freshness | Actual hash must match snapshot hash; otherwise reject/rebuild |
| Lexical baseline | Deterministic offline BM25-style retrieval |
| Embedding | Independent `EmbeddingProvider` Protocol |
| Fake embedding | Offline architecture/regression tests only |
| Semantic experiment | Fixed real semantic model required for formal RQ2/RQ4 evidence |
| Vector database | Not required; dedicated Vector DB deferred |
| Index identity | Project + snapshot + config + optional embedding fingerprint |
| Incremental indexing | `SnapshotDiff` add/delete/replace/reuse; equivalent to full rebuild |
| Graph | Existing `CONTAINS` and `IMPORTS` only, with bounded expansion |
| Hybrid | Weighted fusion primary; RRF optional |
| Context | Separate `ContextBuilder` with explicit model-agnostic budget |
| Consumption | Future Agent consumes `RetrievalService` / `ContextPackage` |
| Dependency | `project_intelligence -> code_maintenance`, never reverse |

No contradiction was found between the frozen architecture and the existing public
`code_maintenance` contracts.

## 4. Research Methodology Consistency

| Area | Frozen result |
| --- | --- |
| Core questions | RQ1 retrieval unit; RQ2 lexical/semantic; RQ3 graph; RQ4 hybrid |
| Primary metrics | Recall@K, MRR |
| Secondary metrics | nDCG@K, Precision@K, Hit Rate@K |
| Dataset | Project repository + fixtures; optional external generalization project |
| Language coverage | Python main experiment; Java coverage validation |
| Ground truth | Human annotation; graph facts may assist but retriever cannot self-label |
| Fairness | Same dataset, queries, truth, `top_k`, and metric definitions |
| Ablation cap | Five core groups |
| Statistics | No meaningless repeats for deterministic retrieval |
| Reproducibility | Versioned data/config/truth, fingerprint, index ID, commit, output |
| Performance | Full/incremental build, latency, index size, context size |

The methodology distinguishes deterministic fake embedding test evidence from real
semantic-model evidence. It does not permit hash/fake embeddings to support semantic
quality claims.

## 5. Ambiguities and Controlled Open Decisions

No blocking ambiguity remains. The following details are intentionally deferred to the
named implementation/review gates and do not conflict with the frozen architecture:

- exact BM25 tokenization and numeric parameters — Phase 2;
- concrete exact-vector storage dependency/persistence — Phase 3 implementation;
- real semantic model/vendor/version — Phase 3 Selection Review;
- exact graph `max_hops` default and score weights — Phases 4-5 tests;
- concrete `ContextPackage` fields — Phase 5;
- experiment artifact directory layout — before Phase 6.

These are bounded implementation choices, not unresolved architecture blockers.

## 6. Scope and Claim Review

The documents do not claim a new BM25, embedding, or graph algorithm. They define a
maintenance-oriented integration and evaluation contribution. Multi-Agent, Router,
rerankers, autonomous maintenance loops, Vector DB infrastructure, commercial features,
and SaaS backend work are explicitly deferred.

## 7. Document Consistency Check

The four Phase 0 artifacts agree on:

- RQ1-RQ4;
- Symbol/File/Chunk unit policy;
- snapshot/source boundary and freshness;
- `ProjectGraph` / `SnapshotDiff` reuse and incremental mapping;
- BM25 baseline and independent embedding port;
- fake-test versus real-semantic evidence boundary;
- no required Vector DB;
- frozen graph relations and bounded expansion;
- weighted hybrid fusion and optional RRF;
- metrics, dataset, ground truth, ablation, and reproducibility;
- explicit Phase 0 through Phase 6 plus RC plan;
- deferred scope and thesis/report policies.

## 8. Regression Evidence

- standard `python -m pytest`: known current-host `rlcompleter` /
  debugging-plugin segmentation fault reproduced;
- approved `python -m pytest -p no:debugging`: **414 passed**;
- offline LLM-contract smoke: **6 passed**;
- real API, Credential, network LLM, or network embedding: none.

## 9. Final Freeze Status

**PASS / FROZEN**

- Architecture: **FROZEN**
- Research Methodology: **FROZEN**
- Blocking issues: **0**
- Documentation Gate: **CLOSED**
- Phase 1 — Corpus & Symbol Content Model: allowed as a separate task, **NOT STARTED**
