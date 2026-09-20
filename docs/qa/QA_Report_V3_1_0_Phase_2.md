# V3.1.0 Phase 2 — Lexical Baseline / Deterministic BM25 QA Report

## Status

**Initial Implementation QA: SELF-CHECK ONLY**

**Independent QA: PASS WITH ISSUES**

- Product Critical: **0**
- Product Medium: **1 initially**
- M1: **BM25Index public config mutability — RESOLVED BY PHASE 2.1**
- L1: **Optional sentinel tie-key collision — RESOLVED BY PHASE 2.1**
- Phase 2.1 hardening: **COMPLETED**
- Directed Retest: **PASS WITH LOW NOTES**
- Final Phase 2 Verdict: **PASS FOR PHASE 2 WITH LOW NOTES**
- Final Product Critical / Medium: **0 / 0**
- Phase 2.2: **NOT REQUIRED**
- Documentation Gate: **CLOSED**

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
queries without any network or Provider path. These are smoke evidence only, not a
retrieval-quality claim.

## Final Directed Retest Evidence

The independent read-only Directed Retest re-executed the original M1 attacks,
nested `BM25Config` mutation, public authoritative-state mutation attempts, and
100 repeated searches. All rebinding/mutation attempts were blocked and all
identity/rank/score triples remained stable.

The L1 collision pair (`None` versus `""`, `None` versus `-1`) produced equal BM25
scores and identical ranking under forward and reversed corpus order. A real
current-tree corpus contained 913 unique documents; representative maintenance
queries were finite and deterministic, and normal production ties were stable.

Additional independent evidence included 100 random corpus permutations with one
result digest, 1,000 repeated searches, table-level length/df/avgdl checks, the
hand-calculated BM25 oracle, `b=0`/`b=1`, extreme valid `k1`, rejected NaN/Infinity,
zero-token and adversarial text cases, and tokenizer/version regression checks.

The Directed Retest found no new Critical or Medium issue. Remaining Low findings
are accepted baseline limitations: no NFC/NFD normalization, coarse CJK/Japanese
tokenization, operator tokens, transitive parser-stack coupling, and linear query
scanning without postings optimization.

## Test Evolution and Gate Decision

The evidence count is deliberately separated by stage:

| Stage | Evidence |
| --- | ---: |
| V3.0.1 release baseline | 414 passed |
| Phase 1 final | 455 passed |
| Phase 2 initial implementation | 463 passed |
| Phase 2 final | 469 passed |
| Phase 2 lexical | 14 passed |
| Phase 1 corpus regression | 41 passed |
| Offline LLM smoke | 6 passed |

The Phase 2 Documentation Gate is **CLOSED**. Phase 3 is **ALLOWED BUT NOT
STARTED**; its semantic model selection and evidence boundary remain mandatory.

## Deferred Scope

Embedding retrieval, graph-aware expansion, hybrid fusion, incremental indexing,
ContextBuilder, RetrievalService, benchmark design, and multi-agent behavior remain
deferred to their frozen future phases. Unicode normalization, CJK segmentation,
tokenizer registries, operator policy changes, stop words, and parser-aware source
filtering remain deferred baseline limitations.
