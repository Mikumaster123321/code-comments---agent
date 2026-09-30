# V3.1.0 Phase 3 — Semantic Embedding Foundation Development Report

## Final Status

- Phase 3.0 Semantic Embedding Selection: **COMPLETED / FROZEN**
- Phase 3.1 Embedding Core: **COMPLETED**; Intermediate Documentation Gate **CLOSED**
- Phase 3.1 Independent QA: **PASS WITH LOW NOTES**
- Phase 3.2 Real Local Model Adapter: **IMPLEMENTED / HARDENING COMPLETE**
- Phase 3.2 Initial Independent QA: **FAIL / BLOCKED** (Critical 1, Medium 2, Low 7)
- Phase 3.2.1 Hardening: **IMPLEMENTED / HARDENING COMPLETE**
- Directed Retest: **PASS WITH LOW NOTES**
- Final Critical / Medium / Phase blocker: **0 / 0 / 0**
- Phase 3.2.2: **NOT REQUIRED**
- Phase 3 Documentation Gate: **CLOSED**
- Semantic Embedding Foundation: **FROZEN FOR V3.1**
- Phase 4: **ALLOWED BUT NOT STARTED**

This report is the final development history for the complete Semantic Embedding
Foundation. It preserves the implementation, independent-review, hardening, and
directed-retest sequence; it does not rewrite the initial Phase 3.2 failure as a
clean first-pass result.

## 1. Phase 3.0 — Selection and Frozen Research Boundary

The read-only Semantic Embedding Selection Review completed with **APPROVE WITH
NON-BLOCKING OPEN QUESTIONS** and no architecture or research-methodology blocker.
It froze a local-first, revision-pinned primary model and the RQ2/RQ4 fairness
contract. Lexical and semantic retrieval receive exactly one shared document text:

```text
qualified_name + "\\n" + source_text
```

The main benchmark language is English, with Chinese as a separately labelled
coverage set. Fake or hash embeddings are restricted to architecture and regression
tests; they cannot support semantic-quality claims. The selection review also froze
explicit truncation, exact cosine similarity, L2 normalization, and the requirement
that formal semantic comparisons use a real, reproducible model.

## 2. Phase 3.1 — Embedding Core

Phase 3.1 implemented the standard-library-only embedding boundary over immutable
Phase 1 `RetrievalDocument` values. The independent `EmbeddingProvider` port keeps
query and document paths separate from chat providers. `EmbeddingFingerprint` is
immutable, credential-free, and deterministically hashed over runtime, model,
revision, dimension, normalization, similarity, instructions, and max-input policy.

`EmbeddingVector` validates exact dimension, finite values, and non-zero magnitude;
the semantic boundary performs L2 normalization and the `SemanticIndex` uses exact
cosine similarity. The deterministic fake provider is tests-only. `SemanticIndex`
canonicalizes SymbolId order, rejects duplicate identities, detects provider and
fingerprint drift, and exposes no partial build. Standalone semantic failure is
explicit; it does not silently fall back to BM25.

Phase 3.1 evidence was **12 tests**, **41** Phase 1 corpus tests, **14** Phase 2
lexical tests, **6** offline LLM-contract tests, and **481** full-regression tests.
The formal smoke corpus was **976 documents** across **51 contributing files**,
correcting an earlier 971-document implementation summary. No real model, model
download, network inference, or API request was used. Independent QA returned
**PASS WITH LOW NOTES** with Critical 0, Medium 0, and blocker 0.

## 3. Phase 3.2 — Real Local Model Adapter

The selected adapter is `transformers==4.56.2` plus `torch==2.8.0` in an optional,
isolated environment. The adapter is lazy-loaded, local-first, CPU-validatable, and
does not change core `requirements.txt`. It checks repository/revision consistency,
hidden dimension, vector validity, and fingerprint identity. Inference uses
attention-mask-aware mean pooling, float32 CPU baseline execution, and L2
normalization. The default test suite does not import the heavy runtime or download
a model.

The real model evidence uses:

- repository: `intfloat/multilingual-e5-base`;
- frozen revision: `d128750597153bb5987e10b1c3493a34e5a4502a`;
- dimension: **768**;
- query instruction: `query: `; document instruction: `passage: `;
- exact cosine over L2-normalized vectors; and
- explicit, observable **512-token** truncation.

The adapter integrates with the exact in-memory `SemanticIndex`, carries the
unchanged fingerprint through hits, and provides history-independent tokenizer
diagnostics. Remote embedding is not the default and no persistent vector/cache
artifact is committed.

## 4. Phase 3.2 Initial QA and Phase 3.2.1 Hardening

The initial independent QA returned **FAIL / BLOCKED** with one Critical, two
Medium, and seven Low findings. The Critical finding (C-1) was that fast-tokenizer
backend truncation state contaminated diagnostics, causing an incorrectly low
truncation count. The hardening change temporarily disables backend truncation for
measurement, computes the untruncated sequence, and restores prior state in a
`finally` block while inference continues to use explicit truncation.

The hardening also addressed the associated Medium contract findings, including
history-independent diagnostics and validation-path robustness. It added focused
offline regression coverage without changing the production architecture or the
frozen model selection. The directed retest then returned **PASS WITH LOW NOTES**:
C-1 is **CLOSED / RESOLVED**, M-1 is **CLOSED / RESOLVED**, final Critical and
Medium are both zero, and Phase 3.2.2 is **NOT REQUIRED**.

## 5. Final Corpus and Token-Boundary Evidence

The evidence sequence distinguishes corpus history from hardening additions:

| Evidence point | Documents | Over 512 / truncated | Ratio |
| --- | ---: | ---: | ---: |
| Phase 3.1 baseline | 976 | — | — |
| Audited Phase 3.2 baseline | 1003 | 78 | 7.7767% |
| Phase 3.2.1 post-hardening tree | 1020 | 79 | 7.7451% |

The post-hardening token distribution is: min **19**, median **144**, p90 **415**,
p95 **627**, p99 **2321**, max **8886**, and max dropped **8374** tokens. The
additional 17 documents came from hardening test expansion, not CorpusBuilder
regression and not model/cache contamination.

With two special tokens, 510 raw tokens produce 512 total tokens and are not
truncated; 511 raw tokens produce 513 total tokens and are truncated. Actual
inference remains at or below 512 total tokens. The previous `1002 documents / 0
truncated / 0.00%` result is **INVALID INITIAL EVIDENCE** because shared tokenizer
backend truncation state polluted diagnostics. It is superseded by the audited
1003-document and post-hardening 1020-document evidence and must not be used as a
Phase 3 result.

## 6. Validation and Reproducibility Evidence

Final independent evidence records:

- 100-repeat determinism: maximum delta **0**;
- single/batch consistency: delta **0**;
- offline reload: **PASS**;
- wrong revision: fail closed;
- wrong dimension: fail closed;
- zero, NaN, and Infinity vectors: fail closed;
- query-time fingerprint drift: fail closed;
- pooling oracle: **PASS**;
- padding exclusion: **PASS**;
- Phase 3.2 adapter tests: **10 passed**;
- Phase 3.1 tests: **12 passed**;
- Phase 2 regression: **14 passed**;
- Phase 1 regression: **41 passed**;
- offline LLM-contract smoke: **6 passed**; and
- full regression: **491 passed**.

The ordinary host debugging-plugin segmentation fault remains a host-specific
Anaconda/Python 3.13.5 issue; the documented no-debugging-plugin command is green.
The real-model directed retest also ran successfully in an independent Python
3.13.5 virtual environment with `torch 2.8.0` and `transformers 4.56.2`. This does
not change core Python 3.10+ support.

## 7. Engineering Feasibility and Dependency Boundary

The measured runtime is engineering feasibility evidence, not a performance SLA:
cold load approximately **1–2 seconds**, warm query approximately **0.5–0.6
seconds**, full embedding of roughly one thousand Symbols approximately **90
seconds**, and peak RSS approximately **1.5 GB**. These values are acceptable for
the undergraduate thesis experiment. Future Phase 4 incremental indexing owns the
problem of avoiding repeated full-build cost.

Core `requirements.txt` remains unchanged. The real runtime is supplied by the
optional `requirements-embedding.txt` boundary, is lazy-loaded, and is not needed
to import the core package or run default offline tests.

## 8. Thesis Relevance and Deferred Claims

Phase 3 demonstrates a runnable, reproducible, offline-reloadable real semantic
embedding engineering chain with correct contracts, exact similarity, truncation
policy, fingerprint identity, and SemanticIndex integration. It does **not** prove
that embedding retrieval is better than BM25, that hybrid retrieval is better than
single retrieval, or that RAG improves maintenance quality. Those RQ2/RQ4 claims
remain for a separately reviewed benchmark and ablation.

Independent QA's discovery and correction of invalid experimental truncation
statistics is itself evidence of experimental credibility and software-engineering
quality control. Registered non-blocking Low notes remain deferred, including
extreme-numeric wording, exception chaining, Protocol output-order documentation,
hostile `str` subclasses, and very small cosine floating-point boundaries. The
Final Documentation Gate does not reopen production code to clear those notes.

## 9. Phase Boundary

Phase 3 freezes the Semantic Embedding Foundation for V3.1. Phase 4 is only
**ALLOWED BUT NOT STARTED**. Graph Expansion, Index Identity, Incremental Indexing,
Hybrid retrieval, and ContextBuilder are outside this gate and were not implemented
in this documentation task.
