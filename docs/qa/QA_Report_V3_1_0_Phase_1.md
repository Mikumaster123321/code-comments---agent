# V3.1.0 Phase 1 — Corpus & Symbol Content Model QA Report

## Review Classification

- **Review scope:** Initial implementation, Phase 1.1 hardening, directed retest, and
  final documentation gate
- **Initial QA:** PASS WITH MEDIUM FINDINGS
- **Directed Retest:** PASS WITH LOW NOTES
- **Final verdict:** **PASS FOR PHASE 1**
- **Critical:** 0
- **Medium:** 0
- **Documentation Gate:** **CLOSED**
- **Phase 2:** **ALLOWED BUT NOT STARTED**

## 1. Scope and Frozen Expectations

QA verifies the Symbol-primary retrieval corpus, `SymbolId` reuse, snapshot/source
boundary, source extraction, file and symbol freshness, deterministic immutable
output, atomic/read-only behavior, Python and Java coverage, source-reading semantics,
and dependency isolation.

It does not evaluate BM25, embeddings, vector search, graph retrieval, hybrid fusion,
context construction, or Agents because those capabilities are outside Phase 1 and
remain not started.

## 2. Entry and Final Evidence

| Evidence | Result |
| --- | ---: |
| V3.0.1 release baseline | 414 passed |
| Phase 1 initial full regression | 438 passed |
| Phase 1 final corpus tests | 41 passed |
| Phase 1 final full regression | 455 passed |
| Offline LLM-contract smoke | 6 passed |
| DeepSeek directed frozen-core subset | 90 passed |

The 90-test directed frozen-core subset is recorded as independent DeepSeek retest
evidence. It is not the full pytest baseline and is not a repackaged probe count.

The standard pytest command reproduces the known Anaconda Python 3.13.5
debugging-plugin / `rlcompleter` crash. The approved
`python -m pytest -p no:debugging` command produced the recorded project results.

## 3. Initial Independent QA

DeepSeek Initial Independent QA returned **PASS WITH MEDIUM FINDINGS**:

| Severity | Count |
| --- | ---: |
| Critical | 0 |
| Medium | 2 |

The findings were:

- **M1 — Python source-region silent misalignment:** AST line positions followed
  physical newline semantics, while parser and corpus slicing used `str.splitlines()`
  and could treat Unicode/control separators as additional lines. Producer and
  verifier could agree on the same incorrect source and hash.
- **M2 — Snapshot/Corpus parse-failure mismatch:** Snapshot accepted unchanged
  unparseable files as zero-symbol state, while Corpus initially rejected the same
  state.

## 4. Phase 1.1 Hardening

Phase 1.1 made narrowly scoped correctness changes:

- froze Python physical-line semantics;
- added independent literal source-region assertions;
- aligned Snapshot and Corpus UTF-8/replacement/universal-newline decoding;
- allowed unchanged unparseable files only when the snapshot expects zero symbols;
- retained fail-closed file and symbol freshness;
- retained the final scan that detects mid-build mutation.

No SymbolId, graph, analysis, provider, UI, Credits, Managed Access, Admin, BM25,
Embedding, Hybrid, Context, or dependency architecture was changed.

## 5. M1 Final Evidence

The old parser behavior was reproduced before the fix. A source containing a special
separator before a later symbol could map the correct SymbolId to the wrong source
region, and the old producer/verifier hash pair could still match.

The directed physical-line matrix covered nine variants across three newline modes:

| Separator variants | Newline modes | Result |
| --- | --- | ---: |
| baseline, U+2028, U+2029, form feed, vertical tab, NEL, U+001C, U+001D, U+001E | LF, CRLF, CR | 27/27 PASS |

The final evidence aligned:

- literal expected `source_text`;
- Python AST start/end positions;
- `Symbol.content_hash`;
- Snapshot `SymbolState.content_hash`;
- `RetrievalDocument.content_hash`.

Decorated functions/classes, multiline definitions, supported nested constructs, and
non-ASCII source retained correct ranges. The existing decorator boundary remains the
definition line rather than the decorator line.

**M1 final status: CLOSED / RESOLVED.**

## 6. M1 Engineering Conclusion

Identity consistency does not imply semantic correctness. A stable SymbolId and
matching hash cannot prove correct retrieval source if both the source producer and
the verifier share the same faulty range assumption. Phase 1.1 resolves this with a
single physical-line contract plus independent literal-region validation.

This is corpus-integrity engineering evidence, not a new retrieval algorithm claim.

## 7. M2 Final Evidence

The final parse-failure matrix is:

| Snapshot state and current source | Result |
| --- | --- |
| expects zero symbols; unchanged file remains unparseable | allowed; zero documents |
| expects zero symbols; file changed | fail closed at file freshness |
| expects symbols; current parser fails | fail closed |
| old snapshot saw unparseable file; current file becomes parseable | old snapshot rejects unexpected symbols |
| multiple unchanged zero-symbol files | deterministic zero contribution |

The zero-symbol exception never bypasses raw file freshness. It applies only to the
existing parse-error categories and only when the snapshot expects no symbol for that
file.

**M2 final status: CLOSED / RESOLVED.**

## 8. L1 Source-Reading and Newline Evidence

Snapshot and Corpus now use one source-reading policy:

- UTF-8;
- `errors="replace"`;
- universal newline normalization to LF.

| Language | LF | CRLF | CR |
| --- | --- | --- | --- |
| Python | PASS | PASS | PASS |
| Java | PASS | PASS | PASS |

Pre-hardening Java CR-only input could produce an incorrect source range between
Snapshot and Corpus. Hardening aligned the two paths.

**L1 final status: CLOSED / RESOLVED.**

## 9. Hash and Freshness Contract

QA confirms that the hash layers have different purposes:

- `FileState.content_hash` hashes raw file bytes and is the file-identity/freshness
  guard;
- `SymbolState.content_hash` hashes the normalized semantic symbol region and is the
  document-level freshness truth.

LF and CRLF have different raw file hashes, while logically identical normalized
symbols have the same semantic hash. Neither guard was removed. Stale file state,
stale symbol state, missing expected source, and symbol-set mismatch all fail closed.

## 10. TOCTOU and Atomicity

`CorpusBuilder` performs first scan -> source read/hash -> parse/extract -> final scan.
The source text is built from the same bytes checked during source read. A mutation
injected after that read is rejected by the final freshness scan.

This is best-effort read consistency with final verification, not a filesystem
transaction, filesystem lock, or strong snapshot isolation. The caller receives a
complete immutable tuple or an exception, never a partial authoritative corpus.

## 11. Determinism, Read-Only Behavior, and Dependencies

- canonical SymbolId-field ordering is explicit;
- repeated builds are equal;
- `PYTHONHASHSEED` variation does not change results;
- no time or random identity enters corpus output;
- source files, snapshots, indexes, and caches are not modified;
- no API, Credential, network LLM, or network embedding is used;
- `project_intelligence -> code_maintenance` remains the only production dependency
  direction;
- no Credits, Managed Access, Admin, Provider, config, OpenAI, Gradio, embedding, or
  vector dependency was introduced;
- `requirements.txt` is unchanged.

## 12. Snapshot Compatibility

The current repository has no production `ProjectSnapshot` persistence. Correcting the
special-separator symbol hash therefore creates no migration requirement.

If an external system persisted a pre-hardening snapshot, affected special-separator
files may produce a symbol hash mismatch after upgrade. The behavior is fail closed;
the external snapshot must be rebuilt. This is a compatibility note, not a repository
migration task.

## 13. Deferred Low Notes

The following are recorded without reopening Phase 1:

- **LN1 — Java exotic separator boundary:** the legacy Java parser still uses
  `splitlines()` semantics for U+2028, U+2029, form feed, vertical tab, NEL, and
  U+001C-U+001E. Corpus now fails closed instead of returning silent wrong source.
  Future Java benchmark coverage of these separators requires a unified Java
  physical-line splitter; ordinary Java coverage is not blocked.
- **LN2 — `ValueError` category:** zero-symbol parse-failure tolerance uses the
  existing, slightly broad `ValueError` category. File freshness and zero-symbol
  snapshot expectation bound the effect.
- **LN3 — pre-hardening Python hash drift:** old special-separator symbol hashes can
  differ, but there is no production persistence and therefore no migration blocker.
- hostile `str` subclass hardening remains deferred.

These notes are Low. Critical and Medium counts remain zero.

## 14. Future Test Quality Recommendations

DeepSeek recommended, but did not require for this gate:

- an additional AST-oracle regression for M1;
- permanent U+001C-U+001E regression cases;
- Java exotic-separator fail-closed regression;
- unexpected adapter `RuntimeError` propagation regression; and
- a permanent becomes-parseable-after-old-snapshot regression.

These are future test-quality additions, not current product blockers.

## 15. Final Architecture Status

| Contract | Status |
| --- | --- |
| `RetrievalDocument` | IMPLEMENTED / FROZEN FOR PHASE 1 |
| `CorpusBuilder` | IMPLEMENTED |
| Primary retrieval unit | Symbol |
| `SymbolId` | UNCHANGED / REUSED |
| Snapshot | UNCHANGED AS STATE CONTRACT |
| Source text | Owned by `CorpusBuilder` |
| Build | Offline / read-only / atomic / deterministic |
| Freshness | FileState + SymbolState validation |
| BM25 | NOT STARTED |
| Embedding | NOT STARTED |
| Graph Retrieval | NOT STARTED |
| Hybrid | NOT STARTED |
| ContextBuilder | NOT STARTED |
| V3.2 | NOT STARTED |

## 16. Final Verdict and Gate

DeepSeek Directed Retest: **PASS WITH LOW NOTES**.

- Critical: **0**
- Medium: **0**
- M1: **CLOSED / RESOLVED**
- M2: **CLOSED / RESOLVED**
- L1: **CLOSED / RESOLVED**
- Final Phase 1: **PASS FOR PHASE 1**
- Documentation Gate: **CLOSED**

Phase 2 — Lexical Baseline / BM25 is **ALLOWED BUT NOT STARTED**. The deferred Low
notes do not reopen Phase 1, but the Java exotic-separator limitation must be addressed
before any future Java benchmark claims require that input class.
