# V3.1.0 Phase 3 — Semantic Embedding Foundation Final QA Report

## Final Verdict

**PASS FOR PHASE 3 WITH LOW NOTES**

- Final Critical: **0**
- Final Medium: **0**
- Release / Phase blocker: **0**
- Phase 3.2 Initial QA: **FAIL / BLOCKED**
- Initial Critical: **1**
- Initial Medium: **2**
- Directed Retest: **PASS WITH LOW NOTES**
- C-1: **CLOSED / RESOLVED**
- M-1: **CLOSED / RESOLVED**
- Phase 3.2.2: **NOT REQUIRED**
- Phase 3 Documentation Gate: **CLOSED**

This is the final QA record for Phase 3. It covers the frozen Phase 3.0 selection,
the Phase 3.1 embedding core, the Phase 3.2 real local adapter, and the Phase 3.2.1
hardening and directed retest. The initial Phase 3.2 failure remains part of the
record and is not reclassified as a clean initial pass.

## 1. Scope and Entry Contracts

QA checked the final implementation against the frozen Architecture Decision and
Semantic Embedding Selection documents, the Phase 1 Symbol-primary corpus, and the
Phase 2 lexical fairness boundary. The final contract is:

| Contract | Frozen result |
| --- | --- |
| Primary model | `intfloat/multilingual-e5-base` |
| Revision | `d128750597153bb5987e10b1c3493a34e5a4502a` |
| Dimension | 768 |
| Pooling | attention-mask-aware mean pooling |
| Normalization | L2 |
| Similarity | exact cosine |
| Query instruction | `query: ` |
| Document instruction | `passage: ` |
| Maximum input | 512 total tokens |
| Truncation | explicit and observable |
| Remote embedding | not default |
| Fake provider | tests only |

The lexical and semantic branches use exactly one shared document input,
`qualified_name + "\\n" + source_text`. Graph metadata, labels, findings, and hidden
ground truth are excluded. Formal RQ2/RQ4 quality claims remain outside this gate.

## 2. Phase-by-Phase QA Result

### Phase 3.0 — Selection

The selection review completed with **APPROVE WITH NON-BLOCKING OPEN QUESTIONS**.
No architecture blocker or research-methodology blocker remained. The local,
revision-pinned primary, backup boundary, fairness contract, and failure ownership
were frozen for implementation.

### Phase 3.1 — Embedding Core

Independent QA returned **PASS WITH LOW NOTES**: Critical 0, Medium 0, blocker 0.
The immutable provider/fingerprint/vector contracts, exact in-memory cosine index,
duplicate identity rejection, deterministic tie-breaking, input-order independence,
fingerprint drift checks, and explicit semantic failure were verified. The fake
provider was used only for offline architecture and regression evidence. The
intermediate Documentation Gate is closed and Phase 3.1.1 was not required.

### Phase 3.2 — Real Local Model Adapter

The initial independent QA returned **FAIL / BLOCKED** with Critical 1, Medium 2,
and Low 7. C-1 identified tokenizer backend state contamination of diagnostics,
which made the initial truncation evidence invalid. The hardening implementation
made diagnostics history-independent while preserving explicit production
truncation. The associated Medium contract issue recorded as M-1 was also closed by
the hardening evidence.

The Directed Retest returned **PASS WITH LOW NOTES**. C-1 and M-1 are closed, no
Critical or Medium issue remains, and Phase 3.2.2 is not required.

## 3. Final Evidence

The final evidence set is:

- **10 passed** Phase 3.2 adapter tests;
- **12 passed** Phase 3.1 embedding tests;
- **14 passed** Phase 2 lexical tests;
- **41 passed** Phase 1 corpus tests;
- **6 passed** offline LLM-contract smoke tests;
- **491 passed** full regression;
- dimension **768** verified;
- 100-repeat determinism maximum delta **0**;
- single/batch consistency delta **0**;
- offline reload **PASS**;
- wrong revision and wrong dimension fail closed;
- zero/NaN/Infinity vectors fail closed;
- query-time fingerprint drift fails closed;
- pooling oracle **PASS**; and
- padding exclusion **PASS**.

No real API, credential, network inference, model cache, or vector artifact was
used in the default suite. The real model was validated through the explicit local
entry point in an optional isolated environment.

## 4. Corpus and Token-Boundary Audit

| Evidence point | Documents | Truncated | Ratio |
| --- | ---: | ---: | ---: |
| Phase 3.1 baseline | 976 | — | — |
| Audited Phase 3.2 baseline | 1003 | 78 | 7.7767% |
| Post-hardening tree | 1020 | 79 | 7.7451% |

Post-hardening distribution: min 19, corrected median **144**, p90 415, p95 627,
p99 2321, max 8886, max dropped 8374. The +17 documents are hardening test
expansion, not a CorpusBuilder regression or model/cache contamination.

Two special tokens mean 510 raw tokens yield 512 total and are not truncated, while
511 raw tokens yield 513 total and are truncated. Actual inference is always at or
below 512 total tokens. The historical `1002 / 0 / 0.00%` result is explicitly
**INVALID INITIAL EVIDENCE** because backend truncation state polluted diagnostics;
it is superseded and cannot support a Phase 3 claim.

## 5. Environment and Dependency Review

The adapter uses optional `transformers==4.56.2` and `torch==2.8.0`; core
`requirements.txt` remains unchanged. The runtime is lazy-loaded, and core import
and default offline tests do not require torch or transformers. The real model was
verified in an isolated Python environment; the directed retest also succeeded in
an independent Python 3.13.5 virtual environment with the same runtime versions.
The earlier Anaconda/debugging-plugin segmentation fault is host-specific and does
not alter core Python 3.10+ support.

Performance observations are engineering feasibility evidence, not an SLA: cold
load approximately 1–2 seconds, warm query approximately 0.5–0.6 seconds, about 90
seconds for a roughly thousand-Symbol full embedding, and approximately 1.5 GB
peak RSS.

## 6. Deferred Low Notes and Research Boundary

Accepted non-blocking Low notes include extreme numeric wording, exception-chaining
documentation, Protocol output-order documentation, hostile `str` subclasses, and
very small cosine floating-point boundaries. They do not reopen production code for
this gate.

Phase 3 proves that the real semantic embedding chain is runnable, reproducible,
offline-reloadable, contract-correct, and integrated with `SemanticIndex`. It does
not prove embedding superiority to BM25, hybrid superiority to a single strategy,
or RAG improvement to maintenance quality. Those conclusions require a later
benchmark and ablation with fixed evaluation protocol.

## 7. Gate Decision

Phase 3 is **COMPLETED**. The Semantic Embedding Foundation is **FROZEN FOR V3.1**
and the Phase 3 Documentation Gate is **CLOSED**. Phase 4 is **ALLOWED BUT NOT
STARTED**; Graph Expansion, Index Identity, Incremental Indexing, Hybrid retrieval,
and ContextBuilder remain outside this gate.
