# V3.1.0 Phase 2 — Lexical Baseline / Deterministic BM25 QA Report

## Status

**Initial Implementation QA: SELF-CHECK ONLY**

**Independent QA: PASS WITH ISSUES**

- Product Critical: **0**
- Product Medium: **1 initially**
- M1: **BM25Index public config mutability — RESOLVED BY PHASE 2.1**
- Phase 2.1 hardening: **COMPLETED**
- Directed Retest: **PENDING**
- Final Phase 2 Verdict: **PENDING**
- Documentation Gate: **OPEN**

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

The independent M1 finding was that the implementation's public `BM25Index.config`
attribute could be rebound after construction, changing ranking parameters or
causing a later `AttributeError`. This was a genuine reproducible Medium issue,
not a documentation-only observation.

## Regression Result

Phase 2.1 adds a read-only public configuration property and a regression proving
that rebinding `config` or mutating any frozen config field fails while 100 repeated
searches retain identical scores. It also hardens Optional-preserving SymbolId tie
keys and freezes the supported tokenizer version. The lexical suite now contains
14 tests; the hand-calculation oracle uses an independent mathematical expression
with approximate comparison and does not call private index helpers.

The existing Phase 1 corpus suite remains green after its package-boundary assertion
was advanced from the completed Phase 1 file set to the Phase 2 implemented file set.
No protected `docs/thesis/` content was modified, moved, staged, or committed.

The current validation snapshot is 14 lexical tests, 41 Phase 1 corpus tests, 6
offline LLM-contract tests, and 469 tests in the complete suite. A real current-tree
corpus smoke indexed 913 documents and answered the representative maintenance
queries without any network or Provider path. These are implementation/hardening
evidence only; the independent directed retest remains required.

## Deferred Scope

Embedding retrieval, graph-aware expansion, hybrid fusion, incremental indexing,
ContextBuilder, RetrievalService, benchmark design, and multi-agent behavior remain
deferred to their frozen future phases. Unicode normalization, CJK segmentation,
tokenizer registries, operator policy changes, stop words, and parser-aware source
filtering remain deferred baseline limitations.
