# V3.1.0 Phase 2 — Lexical Baseline / Deterministic BM25 Development Report

## Status

- Phase: **COMPLETED**
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

The public Phase 2 contracts are the immutable `BM25Config`, `LexicalHit`, and
`BM25Index` values, plus the frozen tokenizer version `code-lexical-v1`.

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
seed. Unknown-only and empty queries return an empty tuple. `top_k` must be an
actual positive `int`; `bool`, floats, strings, zero, and negative values are
rejected.

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
