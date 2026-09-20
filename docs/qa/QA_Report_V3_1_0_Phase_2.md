# V3.1.0 Phase 2 — Lexical Baseline / Deterministic BM25 QA Report

## Verdict

**PASS FOR PHASE 2**

- Product Critical: **0**
- Product Medium: **0**
- Release Blocker: **0**
- New lexical tests: **8 passed**
- Full offline regression: **463 passed**
- Real LLM/provider/network request: **none**

## Scope Checked

QA verified the Phase 2 boundary against the frozen Phase 0/1 architecture:

- symbol-level `RetrievalDocument` input and direct `SymbolId` reuse;
- stdlib-only implementation with no `requirements.txt` change;
- deterministic tokenizer and one shared document/query tokenization contract;
- standard BM25 `k1=1.5`, `b=0.75`, and the single documented IDF formula;
- document frequency, term frequency, average length, and length normalization;
- finite non-negative scores, strict query/top-k validation, empty/unknown behavior;
- canonical SymbolId tie ordering independent of corpus order and hash randomization;
- duplicate identity rejection, empty corpus safety, immutable results, and private
  read-only index statistics;
- no scanner, filesystem write, cache, LLM, embedding, graph, hybrid, or network path.

## Regression Result

The existing Phase 1 corpus suite remains green after its package-boundary assertion
was advanced from the completed Phase 1 file set to the Phase 2 implemented file set.
The new lexical suite provides an independent hand-calculation oracle rather than
reusing the index's private scoring helper. No protected `docs/thesis/` content was
modified, moved, staged, or committed.

## Deferred Scope

Embedding retrieval, graph-aware expansion, hybrid fusion, incremental indexing,
ContextBuilder, RetrievalService, benchmark design, and multi-agent behavior remain
deferred to their frozen future phases.
