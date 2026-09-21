# V3.1.0 Phase 3.1 — Embedding Core Architecture QA Report

## Final Verdict

**PASS WITH LOW NOTES**

- Critical: **0**
- Medium: **0**
- Phase blocker: **0**
- Phase 3.1.1 Hardening: **NOT REQUIRED**
- Phase 3.1 Intermediate Documentation Gate: **CLOSED**
- This is not a verdict for the whole Phase 3; Phase 3.2 remains outstanding.

## Scope Checked

Independent QA verified the Phase 3.1 boundary against the frozen Phase 1/2
corpus and lexical contracts:

- independent `EmbeddingProvider` query/document port;
- immutable credential-free fingerprint with canonical deterministic SHA-256;
- exact-dimension, finite, non-zero immutable vectors;
- semantic-boundary L2 normalization and exact cosine;
- deterministic fake provider with separate query/document instruction paths;
- exactly one `qualified_name + "\\n" + source_text` document input;
- direct SymbolId reuse, duplicate rejection, and canonical tie-breaking;
- exact in-memory indexing with no persistence, filesystem, or network path;
- provider alignment, build atomicity, build/query fingerprint drift detection;
- explicit semantic failure without BM25 fallback;
- read-only authoritative public state and input-order independence.

## Core Evidence

Fingerprint identity is deterministic, immutable, credential-free, and sensitive
to its identity fields. Canonical serialization uses an ordered JSON list, so no
field-boundary collision was found. Vectors enforce exact dimension, finite
values, non-zero magnitude, and immutability. L2 normalization is mathematically
correct, and the cosine implementation uses exact dot products over normalized
vectors. The independent oracle covered orthogonal/identical/opposite behavior.

The fake provider is deterministic and PYTHONHASHSEED-independent. Query and
document instructions are owned by the provider and applied once. Duplicate
SymbolId values fail closed. Provider failure, invalid vectors, count mismatch,
and build-time drift produce no partial authoritative index. Query-time drift and
cross-space ranking are rejected. Tie-breaking is deterministic and unaffected by
corpus input order. No BM25 fallback exists in the standalone semantic branch.

No filesystem, network, real API, Credential, model download, or forbidden ML
dependency was used.

## Corpus and Regression Snapshot

- Phase 3.1 formal corpus smoke: **976 documents**, **51 contributing files**
- Phase 2 reference corpus: **913 documents**
- Growth: **+63**, with **0 removed**
- `embedding.py`: **39 symbols**
- `test_project_intelligence_embedding.py`: **24 symbols**
- Phase 3.1 tests: **12 passed**
- Phase 2 lexical regression: **14 passed**
- Phase 1 corpus regression: **41 passed**
- Offline LLM smoke: **6 passed**
- Full pytest: **481 passed**

The 976 count corrects the earlier 971 implementation summary. It is a smoke
count correction, not a CorpusBuilder regression and not semantic-quality
evidence. Independent probes and repeated-search/permutation runs are recorded
separately from pytest test counts.

## Deferred Low Notes

The accepted non-blocking notes are:

- extreme finite numerics fail closed, but one error path may use zero-vector
  wording;
- provider exception chaining is retained through `__cause__`, while public
  errors do not expose secrets;
- output-order alignment is enforced by the index but not fully stated in the
  Protocol docstring;
- additional repository regression could later cover extreme numerics, public
  rebinding, provider ordering, hostile string subclasses, and empty-query
  provider-call behavior.

No Critical or Medium issue requires a Phase 3.1.1 hardening round.

## Boundary and Next Phase

The fake provider is architecture/regression evidence only. This QA report makes
no RQ2/RQ4 semantic-quality claim. Phase 3.2 is **ALLOWED BUT NOT STARTED** and
is reserved for validating the reviewed local `intfloat/multilingual-e5-base`
revision `d128750597153bb5987e10b1c3493a34e5a4502a`. The overall Phase 3
Documentation Gate remains **OPEN** until that real-model work is complete.

