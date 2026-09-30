# V3.1.0 Phase 3.1 — Embedding Core Architecture Development Report

## Status

- Implementation: **COMPLETED**
- Phase 3.1 Intermediate Documentation Gate: **CLOSED**
- Independent QA: **PASS WITH LOW NOTES**
- Critical / Medium: **0 / 0**
- Phase blocker: **0**
- Phase 3.1.1 hardening: **NOT REQUIRED**
- Phase 3.2: **ALLOWED BUT NOT STARTED**
- Phase 3 overall Documentation Gate: **OPEN**
- Dependencies: Python standard library only; `requirements.txt` unchanged
- Real model: **NOT IMPLEMENTED**
- Fake provider: architecture and regression tests only

## 1. Scope and Architecture

Phase 3.1 implements the offline embedding boundary frozen by the Phase 3.0
selection review. The implementation is independent of `LLMProvider`,
`TaskScopedLLMProvider`, Credits, Managed Access, Graph, Hybrid, Agent, and
persistent storage. It consumes only Phase 1 immutable `RetrievalDocument`
values and reuses their authoritative `code_maintenance.SymbolId` identities.

The public contracts are `EmbeddingProvider`, `EmbeddingFingerprint`,
`EmbeddingVector`, `DeterministicFakeEmbeddingProvider`, `SemanticIndex`, and
`SemanticHit`. `SemanticIndex` is an exact in-memory index; it neither scans the
filesystem nor reparses source.

## 2. Fingerprint and Vector Contracts

`EmbeddingFingerprint` is immutable, credential-free, and deterministically
hashed with canonical SHA-256 serialization over all identity fields:
runtime kind, repository, revision, dimension, normalization, similarity metric,
query/document instructions, and maximum-input policy. Supplied hashes must
match the fields; field changes cannot be silently accepted. No Credential, API
key, object identity, memory address, or random UUID participates in the hash.

`EmbeddingVector` is immutable and fail-closed. It requires the exact fingerprint
dimension, numeric non-boolean values, finite values, and a non-zero vector. The
semantic boundary applies mathematically correct L2 normalization before vectors
enter the index. Exact cosine is then computed as the dot product of the
normalized query and document vectors.

## 3. Fake Provider and Fair Input Boundary

`DeterministicFakeEmbeddingProvider` uses stable `hashlib` inputs and never uses
Python `hash()`, network, filesystem, or a model runtime. Equal text produces the
same vector; different text normally produces a different vector. Query and
document entry points are separate, and their frozen instructions participate
exactly once in the deterministic input identity.

Every semantic document input is exactly:

```text
qualified_name + "\n" + source_text
```

No graph metadata, analysis finding, hidden label, ground truth, or other signal
is added. This preserves the lexical/semantic fairness boundary.

## 4. Exact Semantic Index

The index canonicalizes input order by the full SymbolId ordering and rejects
duplicate SymbolIds. Provider document output is required to align one-for-one
with the input sequence; count mismatch, invalid vectors, provider failure, and
build-time fingerprint drift abort the complete build without exposing a partial
index. Query-time fingerprint drift is also detected, so one index cannot rank
across embedding spaces. There is no BM25 fallback in standalone semantic
retrieval.

`SemanticHit` is immutable, uses one-based ranks, carries SymbolId and content
hash identity, a finite score, and the index fingerprint. Equal scores use stable
canonical SymbolId ordering. Public documents, vectors, fingerprint, and hit
values are read-only.

## 5. Validation Evidence

- Phase 3.1 tests: **12 passed**
- Phase 2 lexical regression: **14 passed**
- Phase 1 corpus regression: **41 passed**
- Offline LLM-contract smoke: **6 passed**
- Full regression: **481 passed**
- Independent QA: **PASS WITH LOW NOTES**, Critical 0, Medium 0, blocker 0
- Formal current-commit corpus smoke: **976 documents**, **51 contributing files**
- Phase 2 corpus smoke reference: **913 documents**
- Corrected growth: **+63 documents**, with **0 removed**

The earlier 971-document implementation smoke was corrected by the independent
QA rebuild. The 976 count is formal Phase 3.1 evidence, not a CorpusBuilder
regression: `project_intelligence/embedding.py` contributes 39 symbols and
`tests/test_project_intelligence_embedding.py` contributes 24 symbols.

The regression suite and independent probes covered deterministic fingerprints,
canonical serialization, finite/non-zero vectors, L2 normalization, exact cosine
oracles, query-time and build-time fingerprint integrity, duplicate identity,
provider failures, output alignment, all-or-nothing build behavior, deterministic
tie-breaking, input-order independence, public immutability, and the absence of
filesystem/network/forbidden dependency paths. Repeated searches and corpus
permutations are evidence runs, not additional pytest test counts.

## 6. Deferred Low Notes

The following non-blocking observations remain deferred:

1. Extreme finite numeric inputs fail closed, although one error path may describe
   the condition as a zero-vector error.
2. Provider exception chaining preserves the original exception through
   `__cause__`; the public `SemanticRetrievalError` message itself contains no
   secret or source text.
3. The `EmbeddingProvider` Protocol does not yet spell out output-order alignment
   in its type-level docstring; the index enforces exact positional alignment.
4. Some edge behavior is not yet repository-regressed, including extreme numeric
   cases, public rebinding attacks, provider ordering, hostile string subclasses,
   and the empty-query provider-call guard.

These notes do not require Phase 3.1.1 hardening. They may be revisited during
Phase 3.2 or later release hardening.

## 7. Thesis Relevance and Boundary

Phase 3.1 provides reproducible embedding abstraction, fixed identity, fair
lexical/semantic input construction, exact similarity infrastructure, embedding
space integrity guards, and a deterministic test double. It provides no RQ2 or
RQ4 semantic-quality conclusion. Such a conclusion requires Phase 3.2 validation
with the reviewed local `intfloat/multilingual-e5-base` revision and a later
formal benchmark.

