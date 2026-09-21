# V3.1.0 Phase 3.0 — Semantic Embedding Selection

## Documentation Freeze Status

**FROZEN FOR PHASE 3**

This document records the approved result of the read-only Claude Phase 3.0
Semantic Embedding Selection Review. It freezes the research selection and the
contracts that Phase 3.1 must implement. It does not implement an embedding
provider, download a model, add a dependency, or establish semantic-quality
evidence. Real-model empirical feasibility remains a separately gated **Phase
3.2** activity.

The review verdict was **APPROVE WITH NON-BLOCKING OPEN QUESTIONS**. There is no
architecture blocker and no research-methodology blocker.

## 1. Frozen Selection

### Primary model

| Field | Frozen value |
| --- | --- |
| Repository | `intfloat/multilingual-e5-base` |
| Revision | `d128750597153bb5987e10b1c3493a34e5a4502a` |
| License | MIT |
| Dimension | 768 |
| Normalization | L2 |
| Similarity | Exact cosine similarity |
| Query instruction | `query: ` |
| Document instruction | `passage: ` |
| Maximum input | 512 tokens |
| Runtime posture | Local-first |

The revision is immutable for the planned experiment. `latest` or an otherwise
floating repository revision is not an acceptable substitute.

The primary is selected for local reproducibility, no `trust_remote_code`
requirement, single-repository revision pinning, MIT licensing, multilingual
support, Chinese coverage capability, a standard XLM-R architecture, and a
manageable undergraduate-project scale. It is **not** a code-specialized model
and this selection must not be described as the strongest code embedding model.

### Backup model

| Field | Frozen value |
| --- | --- |
| Repository | `BAAI/bge-base-en-v1.5` |
| Revision | `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` |
| License | MIT |
| Dimension | 768 |

The backup may be enabled only if the primary produces an unacceptable Phase
3.2 issue involving installation, compatibility, performance, or resource
availability. The default thesis main experiment uses only the primary.

### Candidates not selected as primary or backup

The review compared `jinaai/jina-embeddings-v2-base-code`,
`Alibaba-NLP/gte-base-en-v1.5`, and `sentence-transformers/all-MiniLM-L6-v2`.
This is a design comparison, not a leaderboard. Jina's code specialization is
a real advantage, but its `trust_remote_code` path and cross-repository version
pinning reduce reproducibility simplicity for this project. The other candidates
do not provide a better combined fit for the frozen multilingual, local-first,
revision-pinned, undergraduate-scale requirements. None is promoted to a thesis
baseline by this document.

## 2. RQ2/RQ4 Fairness Contract

The lexical and semantic branches receive the same retrieval text. For every
document, the input is exactly:

```text
qualified_name + "\n" + source_text
```

The BM25 document input is that string. The embedding document input is the
same string, with the model-layer document instruction `passage: ` applied by
the embedding adapter. A query uses the same query text for both strategies;
the embedding adapter applies the model-layer query instruction `query: `.
The comparison also holds the dataset, query set, ground truth, `top_k`, metric
definitions, and evaluation procedure constant.

The embedding branch must not receive information that BM25 does not receive:
Graph metadata, `AnalysisFinding`, ground truth, hidden labels, or any other
extra signal are prohibited. The existing Phase 2 `code-lexical-v1` tokenizer
and its known coarse CJK behavior remain the lexical baseline; the semantic
adapter must not alter that baseline.

## 3. Query Language Policy

The main RQ2/RQ4 benchmark uses English queries. Chinese queries form a separate
coverage/extension set and must not be merged into the main RQ2 aggregate without
an explicit language label and separate reporting. This keeps retrieval-strategy
effects distinct from the lexical tokenizer's CJK capability.

## 4. Phase 3.1 Contracts

### EmbeddingProvider

Phase 3.1 defines an independent provider port with query/document separation:

```text
EmbeddingProvider
  embed_query(text)
  embed_documents(texts)
  fingerprint
```

The port must not reuse `LLMProvider` or `TaskScopedLLMProvider`. Embedding and
chat completion have different inputs, outputs, failure semantics, and cost
models.

### Embedding fingerprint

The fingerprint is credential-free and must include at least:

- `runtime_kind`;
- `model_repository`;
- `revision`;
- `dimension`;
- `normalization`;
- `similarity_metric`;
- `query_instruction`;
- `document_instruction`;
- `max_input_policy`; and
- a deterministic `fingerprint_hash` over the identity fields.

It must never contain a Credential, API key, memory address, or random UUID.
Changing any identity field invalidates silent reuse of an embedding index or
cache in future phases.

### EmbeddingVector

Vectors are immutable values (a tuple of floats is the recommended representation)
and are validated fail-closed. Every vector must have the exact configured
dimension, contain only finite values, contain neither NaN nor Infinity, and be
non-zero for cosine similarity. Dimension mismatch and zero vectors are errors;
they are not silently repaired, padded, normalized, or dropped.

### Similarity and scale

Semantic retrieval uses exact cosine similarity. Phase 3 does not introduce
FAISS, Chroma, a vector database, ANN search, or another approximate index. The
current corpus is approximately 900+ Symbols, for which exact in-memory search
is sufficient and more directly reproducible.

### Oversized symbols

The primary model's 512-token limit is explicit. The default policy is explicit
truncation with a recorded truncation marker; silent truncation is forbidden.
Experiments must record the truncated-document count and proportion. If Phase
3.2 finds a materially high truncation rate, it records a sensitivity-analysis
requirement. Chunk fallback is not implemented in Phase 3.

## 5. Provider Boundaries

### Deterministic fake provider

`DeterministicFakeEmbeddingProvider` is permitted only for unit, architecture,
ranking, dimension, failure, and determinism tests. Fake or hash embeddings must
never support RQ2/RQ4 semantic-quality conclusions or be presented as evidence
that embedding retrieval is better than BM25.

### Real-model adapter

The real primary adapter belongs to Phase 3.2. It must be local, optional, and
lazy-loaded. Importing `project_intelligence` must not force installation or
import of `torch`, `transformers`, `sentence-transformers`, or comparable heavy
runtime dependencies.

## 6. Dependency, CI, and Storage Strategy

The core `requirements.txt` remains unchanged. Real local embedding runs in an
optional dependency environment, documented separately in a later phase (for
example, a future `requirements-embedding.txt` or equivalent). The choice among
`transformers + torch`, `sentence-transformers`, and ONNX is deferred to Phase
3.2's installation and runtime validation. This freeze does not create that
optional requirements file.

Core CI and tests do not download a real model, use a GPU, access a network
embedding service, or use a real API key. Phase 3.1 tests use only the fake
provider. Phase 3.2 real-model validation is an independent manual/experiment
gate.

Phase 3 storage is in-memory only. Persistent embedding caches, SQLite vector
storage, vector databases, and index-artifact persistence are deferred with
`RetrievalIndexIdentity` and incremental indexing to Phase 4.

## 7. Failure and Privacy Contracts

In the Phase 3 semantic retriever, a provider or model failure becomes an
explicit semantic-retrieval error. It must not silently fall back to BM25. A
future Phase 5 hybrid retriever may use a lexical-only fallback for an embedding
branch failure, but only with an explicit degraded-mode marker and strategy
provenance.

The runtime is local-first: source code does not leave the machine by default.
Any future remote embedding is explicit opt-in. Credentials must not enter the
fingerprint, vector, index, cache, or logs.

## 8. Phase Plan and Exclusions

| Phase | Frozen scope |
| --- | --- |
| 3.0 | Semantic model selection and this documentation freeze |
| 3.1 | `EmbeddingProvider`, fingerprint, vector validation, deterministic fake provider, exact semantic retrieval, `SemanticHit`, and offline tests |
| 3.2 | Real multilingual-e5-base adapter, optional dependency installation/load validation, dimension validation, latency/memory evidence, real truncation-rate measurement, and basic semantic sanity checks |

Phase 3.1 does not implement a real model download, Graph Retrieval, Hybrid,
Incremental Indexing, `ContextBuilder`, `RetrievalService`, a Vector DB,
persistent cache, Agent, or Router. Independent and final QA plus a
Documentation Gate follow the implementation phases.

## 9. Non-Blocking Open Questions

These questions remain intentionally open and do not block Phase 3.1:

1. The primary model's measured latency and memory footprint.
2. The proportion of real-corpus Symbols exceeding 512 tokens.
3. The Phase 3.2 runtime choice among `transformers/torch`,
   `sentence-transformers`, and ONNX.
4. Whether a future implementation needs NumPy.

## 10. Thesis Claim Boundary

The thesis must not claim that embedding retrieval is universally better than
BM25. Any future claim must be conditioned on the fixed benchmark, the fixed
BM25 baseline, and the fixed `intfloat/multilingual-e5-base` revision recorded
here, and must report the observed experiment rather than a universal model
ranking.

## 11. Freeze Gate Evidence and Next State

The freeze is entered on branch `v3.1.0-dev` at
`f6f4df2adafff0105e7dc9166d84e4eb4ae3d4a3`. Historical Audit P1 is resolved;
Phase 0 is frozen; Phase 1 and Phase 2 documentation gates are closed. The
current full regression baseline is **469 passed**, and the offline LLM-contract
smoke is **6 passed**. No real embedding, model download, dependency
installation, network inference, or real API request is part of this gate.

After this documentation-only change:

- Phase 3.0 Selection Review: **COMPLETED**;
- Phase 3.0 Documentation Freeze: **CLOSED**;
- selection, primary/backup, RQ2/RQ4 fairness, and failure ownership:
  **FROZEN**;
- Phase 3.1: **ALLOWED BUT NOT STARTED**; and
- next: **Phase 3.1 — Embedding Core Architecture**.

The freeze does not authorize implementation beyond the Phase 3.1 scope and does
not authorize push or tag operations.
