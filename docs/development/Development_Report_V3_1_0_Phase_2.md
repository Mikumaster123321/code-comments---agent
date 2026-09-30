# V3.1.0 Phase 2 — Lexical Baseline / Deterministic BM25 Development Report

## Status

- Implementation: **COMPLETED**
- Phase objective: **Deterministic BM25 Lexical Baseline**
- Independent QA: **PASS WITH ISSUES**
- Phase 2.1 hardening: **COMPLETED**
- M1: **RESOLVED BY PHASE 2.1**
- L1: **RESOLVED BY PHASE 2.1**
- Directed retest: **PASS WITH LOW NOTES**
- Final QA: **PASS FOR PHASE 2 WITH LOW NOTES**
- Final Product Critical / Medium: **0 / 0**
- Phase 2.2: **NOT REQUIRED**
- Documentation Gate: **CLOSED**
- Scope: deterministic, offline lexical retrieval over the Phase 1 symbol corpus
- Dependencies: Python standard library only; `requirements.txt` unchanged
- Retrieval unit: Phase 1 `RetrievalDocument` / `code_maintenance.SymbolId`
- Deferred: embeddings, graph expansion, hybrid fusion, incremental indexing,
  context construction, evaluation benchmark, and multi-agent orchestration

## 1. Implementation Boundary

Phase 2 adds only `project_intelligence.lexical`. `BM25Index` consumes an immutable
sequence of Phase 1 `RetrievalDocument` values and does not scan files, build a
snapshot, call a Provider or LLM, write a cache, or access the network. Duplicate
`SymbolId` values fail closed. No second document identity is introduced.

The Phase 1 Corpus Builder is the sole corpus producer for this phase. Phase 2
does not scan the filesystem or parse source independently; it consumes the
immutable symbol-level `RetrievalDocument` tuple and reuses its authoritative
`code_maintenance.SymbolId` identity.

The objective is a minimal, standard, explainable lexical reference for future
RQ2 lexical-versus-semantic comparison and the lexical component of RQ4 hybrid
retrieval. This phase does not claim a new BM25 algorithm or a retrieval-quality
winner.

The public Phase 2 contracts are the immutable `BM25Config`, `LexicalHit`, and
`BM25Index` values, plus the frozen tokenizer version `code-lexical-v1`. `BM25Index`
exposes its authoritative configuration through a read-only `config` property;
rebinding or mutating the public configuration is rejected.

## 2. Tokenizer Contract

Documents and queries use the same standard-library tokenizer. Unicode words are
case-folded with `str.casefold()`; underscore-connected, camelCase, PascalCase,
acronym, and ASCII letter/digit boundaries produce deterministic identifier parts
while retaining the original identifier token. Qualified names are naturally split
at punctuation. Operators are retained as tokens and all other punctuation is a
separator. Comments and strings remain part of `source_text`; no parser-aware
stripping or stop-word list is applied.

The indexed text is exactly one occurrence of `qualified_name` followed by one
occurrence of `source_text`. `signature` is not injected separately because it is
normally represented in the source range; this avoids an unexplained signature
weight. The qualified name is an explicit, once-only symbol-identity enrichment.

## 3. BM25 Contract

The default configuration is `k1 = 1.5` and `b = 0.75`. For query term `t` and
document `d`, the implementation uses:

```text
score(t,d) = IDF(t) * tf(t,d) * (k1 + 1)
            / (tf(t,d) + k1 * (1 - b + b * dl / avgdl))
IDF(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
```

`N` is the indexed document count, `df(t)` counts documents containing the term,
`tf(t,d)` counts occurrences in one document, `dl` is token length, and `avgdl` is
the arithmetic mean of all document lengths. Empty corpora and all-empty documents
are safe and return no hits. Query terms are de-duplicated in tokenizer order; no
separate query-term-frequency weight is introduced.

Only finite, positive scores are returned. Hits are ordered by descending score and
then by the canonical `SymbolId` tuple (language, relative path, qualified name,
kind, semantic disambiguator, fallback line), independent of input order or hash
seed (`PYTHONHASHSEED` included). Unknown-only and empty queries return an empty
tuple. `top_k` must be an
actual positive `int`; `bool`, floats, strings, zero, and negative values are
rejected.

The tie key retains Optional value types for both semantic disambiguators and
fallback lines. Thus `None` cannot collide with an empty string or with a numeric
sentinel such as `-1`.

## 4. Immutability and Explainability

The index snapshots canonical document order and keeps private read-only token
statistics. Public documents, frequencies, lengths, configuration, and hits are
immutable/read-only views. `LexicalHit` retains the complete Phase 1 document,
authoritative `symbol_id`/`document_id`, content hash, score, and one-based rank for
future explanation and evaluation layers.

## 5. Validation Evidence

The focused lexical suite covers configuration and finite-score validation,
tokenization across Python/Java-style identifiers and Unicode, empty/unknown
queries, strict `top_k`, duplicate identities, hand-calculated BM25, IDF and
document frequency, length normalization, TF saturation, multi-term ranking,
stable tie-breaking, input-order independence, repeated searches, corpus
immutability, read-only metadata, and the no-filesystem boundary.

The Phase 1 package-boundary regression was updated to recognize the now-authorized
Phase 2 `lexical.py` module. Existing corpus, scanner, provider, Credits, and UI
contracts were not changed.

## 6. Phase 2.1 Hardening and Deferred Baseline Limits

The hardening regression covers public configuration immutability, frozen config
fields, tokenizer-version validation, Optional-preserving tie ordering, 100 fixed
seed input permutations, boundary `b=0`/`b=1` and large valid `k1`, zero-token
documents, partial-unknown and long queries, and the existing deterministic and
non-mutation checks.

The following remain deliberate `code-lexical-v1` limitations, not Phase 2.1
blockers: no tokenizer registry or retrieval-config identity, no Unicode NFC/NFD
normalization, coarse contiguous CJK/Japanese tokenization, operator tokens remain
searchable, and no stop-word or parser-aware comment/string processing. A query
with no indexed tokens returns no hits; operator-only queries may match source
operators by design.

For future RQ2 experiments, semantic retrieval must use the same baseline input
text—exactly one `qualified_name` plus one `source_text`—to preserve lexical versus
embedding fairness.

The implementation phase must not pre-classify its self-check as independent QA.
The remaining sequence is directed retest, final report evidence, and then the
Documentation Gate decision.

## 7. Phase 2.1 Validation Snapshot

- Phase 2 lexical tests: **14 passed**
- Phase 1 corpus regression: **41 passed**
- Offline LLM-contract smoke: **6 passed**
- Full regression: **469 passed**
- Current-project real corpus smoke: **913 documents indexed**
- Real API, Credential, network LLM, and network embedding requests: **none**

The 913-document smoke count includes the current working tree after adding the
hardening tests and reports; it is a smoke check only, not a retrieval-quality claim.

## 8. Phase Timeline and Final QA

The Phase 2 evidence sequence is:

1. implementation of the standard deterministic BM25 baseline;
2. implementation-side provisional self-check (not independent QA);
3. Independent QA: **PASS WITH ISSUES**, Product Critical 0, Product Medium 1;
4. Phase 2.1 hardening: public configuration immutability, Optional-preserving
   tie-key ordering, and tokenizer-version validation;
5. Directed Retest: **PASS WITH LOW NOTES**;
6. Final Phase 2 QA: **PASS FOR PHASE 2 WITH LOW NOTES**.

The original M1 was a public writable `BM25Index.config` attribute. Phase 2.1
stores the authoritative object in `_config`, exposes it through a read-only
property, and retains frozen `BM25Config` fields. Directed Retest blocked both
whole-object rebinding and nested mutation; 100 repeated searches remained stable.

The original L1 was a non-injective secondary key caused by flattening `None` to
`""` and `-1`. The hardened key retains Optional type information without changing
the frozen `SymbolId` contract. Synthetic collision identities and normal corpus
ties remain deterministic under reversed input.

The implementation phase previously generated provisional reports before
Independent QA. Those reports were subsequently reclassified as self-check/draft
evidence; only Independent QA and the Directed Retest support this final gate.

## 9. Thesis Relevance and Phase Boundary

Phase 2 provides the RQ2 lexical baseline and an RQ4 hybrid component: a standard
BM25 mathematical reference, a reproducible `code-lexical-v1` tokenizer, stable
SymbolId ranking, and an explainable deterministic comparison anchor. It does not
claim that BM25 outperforms embeddings and does not present retrieval-quality
results as a thesis conclusion.

The RQ2/RQ4 fairness entry contract is frozen: any formal future lexical-versus-
embedding comparison must give both strategies exactly one `qualified_name` plus
one `source_text`. Fake or hash embeddings remain limited to architecture,
regression, and failure tests; formal semantic claims require a separately reviewed
real model with fixed version, dimension, normalization, license, reproducibility,
and runtime characteristics.

Phase 3 — Embedding Port & Semantic Retrieval Foundation is **allowed but not
started**. It must begin with a Semantic Embedding Selection Review and may not
silently select a remote API as the thesis semantic baseline.
