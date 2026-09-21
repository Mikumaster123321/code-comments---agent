# V3.1.0 Phase 3.2 — Real Local Model Adapter & Semantic Feasibility Validation

## Status

- Implementation: **IMPLEMENTED / VALIDATION COMPLETE**
- Independent QA: **PENDING**
- Phase 3 overall Gate: **OPEN**
- Core `requirements.txt`: **UNCHANGED**
- Primary: `intfloat/multilingual-e5-base`
- Primary revision: `d128750597153bb5987e10b1c3493a34e5a4502a`
- Real model: **LOADED AND VALIDATED LOCALLY**
- Persistent vectors/cache artifacts: **NOT ADDED**

## 1. Runtime Decision and Isolation

Stage A selected the smallest direct runtime: `transformers + torch`. The
validated optional environment used Python 3.12.14 on macOS arm64 with:

| Package | Version |
| --- | --- |
| `torch` | 2.8.0 |
| `transformers` | 4.56.2 |
| `safetensors` | 0.6.2 |

The runtime was selected because it exposes the frozen XLM-R model directly,
allows explicit attention-mask-aware mean pooling, supports the immutable
revision pin, and runs on the CPU baseline as well as Apple MPS. The
`sentence-transformers` alternative was not selected because it adds a second
wrapper/configuration layer that is unnecessary for this model contract. ONNX
Runtime was not selected because it would require model export/conversion and
introduce an additional artifact and precision/runtime variable. No quantization,
fine-tuning, or CoreML/ONNX conversion was introduced.

The host Python 3.13.5 environment can install the arm64 torch wheel but its
torch import exits with code 139. It is not used as Phase 3.2 evidence. The
reproducible validation environment is the isolated Python 3.12 environment;
the core package and default test suite remain independent of it.

On the Apple Silicon host, torch reported CPU support and MPS built/available.
The required evidence uses CPU only; MPS remains an optional execution location
and is not part of semantic identity.

## 2. Adapter and Contract

`project_intelligence.local_embedding.LocalE5EmbeddingProvider` implements the
existing `EmbeddingProvider` without changing `embedding.py`. It imports no ML
package at module import time and loads the tokenizer/model only on explicit
`load()` or first embedding call. Stable errors are provided for missing
dependencies, model loading, tokenization, and inference; no source text,
credential, or local cache path is included in public messages, and no BM25
fallback is performed.

The fingerprint is `transformers-torch` plus the frozen repository, revision,
768 dimension, L2/cosine semantics, `query: ` and `passage: ` instructions, and
`512-token-explicit-truncation-v1`. Device, cache path, memory address, and
machine-specific values are excluded from semantic identity. Query/document
instructions are applied exactly once. Real tokenizer diagnostics expose raw
token count, special-token count, effective content limit, and truncation status
without changing the `EmbeddingProvider` vector shape.

Inference uses `model.eval()`, `torch.inference_mode()`, attention-mask-aware
mean pooling, and float32 CPU baseline inference followed by L2 normalization.
The model and tokenizer are loaded from the same repository and requested
revision; the resolved model commit and 768 hidden dimension are checked.

## 3. Explicit Validation Entry

The default `python -m pytest` suite never downloads, initializes, or imports a
real model runtime. Offline contract tests cover lazy loading, stable missing
dependency errors, frozen fingerprints, revision identity, and single-prefix
instruction behavior. Real validation is explicitly separated in:

```text
python scripts/validate_phase32_real_model.py --cache-dir <external-cache> --device cpu
```

The script reports model identity, tokenizer boundary evidence, vector shape and
normalization, 100-repeat determinism, batch consistency, current corpus token
statistics, full in-memory `SemanticIndex` integration, representative query
hits, latency, and process RSS. A cached snapshot path can be supplied for an
offline reload with `--model-path ... --offline`.

## 4. Validation Evidence

The successful explicit run used the pinned snapshot in an external cache,
Python 3.12.14, CPU, and batch size 8:

- model/tokenizer config: XLM-R, hidden dimension **768**, float32;
- cold load: **2.451 s**;
- RSS before/after load: **21.5 / 763.0 MB**;
- 100 repeated query embeddings: maximum absolute delta **0**;
- single-versus-batch embedding: maximum absolute delta **0**;
- current post-implementation corpus: **1002 documents**;
- corpus embedding/index build: **94.453 s**;
- peak measured RSS during corpus indexing: **1496.1 MB**;
- Git `HEAD` baseline corpus: **976 documents**, **95.139 s** embedding time,
  **1509.3 MB** peak RSS in the same CPU environment;
- warm single-query latency: **0.636 s**;
- query results were finite, deterministic, and carried the unchanged adapter
  fingerprint through `SemanticIndex`.

The formal Phase 3.1 entry evidence remains 976 documents; its direct
embedding-cost run is recorded above. The validation
smoke count is 1002 because the Phase 3.2 adapter, validation tests, and
validation entry themselves add symbols to the current working-tree corpus; it
does not indicate a CorpusBuilder mutation. No vector files, persistent cache,
SQLite vectors, or corpus dump were written to the repository.

Boundary evidence uses the actual tokenizer and special tokens: 510 raw tokens
produce 512 total tokens and are not truncated; 511–514 raw tokens exceed the
512-token input limit and are explicitly truncated. The validation script also
covered English, Chinese, Japanese, Unicode identifiers, Python non-ASCII
comments/strings, and Java non-ASCII source without inference failure.

## 5. Research and Scope Boundary

The sanity queries and corpus smoke establish local adapter feasibility only.
They are not RQ2/RQ4 recall, MRR, or benchmark results. Formal semantic-quality
claims remain deferred to the reviewed benchmark and ablation phases. Graph
retrieval, hybrid retrieval, incremental indexing, ContextBuilder, Agent,
Router, and Phase 4 work were not started.
