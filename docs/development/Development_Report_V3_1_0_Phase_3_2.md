# V3.1.0 Phase 3.2 — Real Local Model Adapter & Semantic Feasibility Validation

## Status

- Initial Independent QA: **FAIL / BLOCKED** (Critical 1, Medium 2, Low 7)
- Phase 3.2.1: **IMPLEMENTED / HARDENING COMPLETE**
- C-1 truncation diagnostics: **CLOSED / RESOLVED**
- M-1: **CLOSED / RESOLVED**
- Directed Retest: **PASS WITH LOW NOTES**
- Phase 3.2.2: **NOT REQUIRED**
- Phase 3 overall Documentation Gate: **CLOSED**
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
- audited commit `1c950ec` corpus: **1003 documents**;
- audited HEAD token distribution: min **19**, median **147**, p90 **422**, p95
  **635**, p99 **2236**, max **8886**; over-512/truncated **78**;
  ratio **7.7767%**; maximum dropped tokens **8374** (matches the Independent QA
  evidence);
- post-hardening working-tree corpus: **1020 documents**;
- post-hardening delta: **+17**, all from
  `tests/test_project_intelligence_local_embedding.py` additions;
- corrected post-hardening token distribution: min **19**, median **144**, p90
  **415**, p95 **627**, p99 **2321**, max **8886**;
- post-hardening documents over 512: **79**; truncated documents: **79**;
  truncated ratio **7.7451%**; maximum dropped tokens **8374**;
- the audited pre-Phase-3.2 baseline remains **976 documents**;
- prior `1002 documents / 0 truncated / 0.00%` evidence is **INVALID** and is
  retained only as superseded historical evidence;
- corrected full validation run: **90.420 s** corpus embedding/index build and
  **1520.7 MB** peak RSS;
- corrected cold load: **2.241 s**; warm single-query latency: **0.585 s**;
- query results were finite, deterministic, and carried the unchanged adapter
  fingerprint through `SemanticIndex`.

The formal Phase 3.1 entry evidence remains 976 documents. The audited Phase
3.2 commit contained 1003 documents; the post-hardening tree contains 1020,
with the +17 change attributable solely to the expanded local-adapter regression
test file. These counts do not indicate a CorpusBuilder mutation. No vector files, persistent cache,
SQLite vectors, or corpus dump were written to the repository.

Boundary evidence uses the actual tokenizer and special tokens: 510 raw tokens
produce 512 total tokens and are not truncated; 511–514 raw tokens exceed the
512-token input limit and are explicitly truncated. The validation script also
covered English, Chinese, Japanese, Unicode identifiers, Python non-ASCII
comments/strings, and Java non-ASCII source without inference failure.

## 5. Phase 3.2.1 Hardening History

The initial Phase 3.2 implementation passed its local smoke checks but reported
incorrectly low truncation counts because `diagnose()` read shared fast-tokenizer
backend state after inference had enabled truncation. DeepSeek Independent QA
classified this as one Critical and two Medium findings and rejected the phase.

This hardening makes diagnostics temporarily disable backend truncation, measure
the untruncated sequence, and restore the prior tokenizer state in `finally`.
Inference still uses `truncation=True, max_length=512`. It also makes direct
validation-script execution bootstrap the repository root without requiring
`PYTHONPATH`, and adds focused offline regression tests for state independence,
empty batches, wrong revision, and wrong dimension. The corrected statistics
above were recomputed through the production diagnostic path rather than copied
from QA.

Post-hardening offline evidence: local adapter tests **10 passed**, Phase 3.1
embedding regression **12 passed**, Phase 2 lexical regression **14 passed**,
Phase 1 corpus regression **41 passed**, LLM smoke **6 passed**, and full
regression **491 passed**. The ordinary host `python -m pytest` debugging-plugin
segmentation fault remains an environment-specific issue; the documented
workaround `python -m pytest -p no:debugging` is green.

The documented direct command now starts from repository root without a manual
`PYTHONPATH`; the script performs a minimal repository-root bootstrap before
project imports. The offline reload used the pinned external snapshot and
`pip check` passed in the optional environment.

## 6. Research and Scope Boundary

The sanity queries and corpus smoke establish local adapter feasibility only.
They are not RQ2/RQ4 recall, MRR, or benchmark results. Formal semantic-quality
claims remain deferred to the reviewed benchmark and ablation phases. Graph
retrieval, hybrid retrieval, incremental indexing, ContextBuilder, Agent,
Router, and Phase 4 work were not started.
