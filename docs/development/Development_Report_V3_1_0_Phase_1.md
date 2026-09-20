# V3.1.0 Phase 1 — Corpus & Symbol Content Model Development Report

## Status

**COMPLETED — DOCUMENTATION GATE CLOSED**

- Implementation: **COMPLETED**
- Phase 1.1 Corpus Integrity Hardening: **COMPLETED**
- DeepSeek Directed Retest: **PASS WITH LOW NOTES**
- Final product findings: **Critical 0 / Medium 0**
- Phase 1 architecture: **FROZEN**
- Phase 2 — Lexical Baseline / BM25: **ALLOWED BUT NOT STARTED**

This is a version- and phase-qualified engineering report. It is evidence for the
future V3.1.0 Thesis-Oriented Development Report, not that final thesis report.

## 1. Phase Objective

Phase 1 closes the source-text gap between the existing project-maintenance state
model and future retrieval. It converts the existing Scanner, language Adapters,
`SymbolId`, and `ProjectSnapshot` contracts into a stable, immutable, snapshot-aligned
symbol corpus suitable for later retrieval phases.

Phase 1 implements no ranking, search, BM25, embedding, vector index, graph expansion,
hybrid fusion, `ContextBuilder`, `RetrievalService`, or Agent runtime.

## 2. Inherited Phase 0 Decisions

Phase 1 preserves the frozen Phase 0 decisions:

- Symbol is the primary retrieval unit;
- File is secondary and Chunk is fallback only;
- retrieval identity reuses `code_maintenance.SymbolId`;
- `ProjectSnapshot` stores state and hashes, not source text;
- source text belongs to a separate Corpus Builder;
- stale or missing content fails closed;
- the allowed dependency direction is
  `project_intelligence -> code_maintenance`;
- core behavior remains deterministic, offline, and testable without credentials or
  network access.

## 3. Source Text Gap

Before Phase 1, `ProjectSnapshot` represented project identity, file state, symbol
state, and graph state, but deliberately persisted no source text. Retrieval requires
the real source region for each symbol. Adding full source to `ProjectSnapshot` would
have mixed state identity with retrieval content and violated the frozen boundary.

Phase 1 therefore introduces `CorpusBuilder`. Given a project root and a
`ProjectSnapshot`, it reads current source through the existing scanner/adapter
contracts, verifies freshness, and projects snapshot symbols into immutable retrieval
documents. `ProjectSnapshot`, `FileState`, and `SymbolState` remain source-text-free.

## 4. RetrievalDocument Design

`project_intelligence.domain.RetrievalDocument` is a frozen dataclass containing:

- the existing `SymbolId`;
- language, relative path, qualified name, and `SymbolKind`;
- signature;
- exact normalized symbol `source_text`;
- optional `documentation_text`, currently `None` because the existing `Symbol`
  contract does not expose a stable documentation field;
- symbol content hash;
- reliable start and end lines supplied by the existing adapters.

The dataclass validates that its duplicated descriptive identity fields agree with the
embedded `SymbolId` and that its line range is valid. It neither generates nor
canonicalizes a new symbol identity.

## 5. CorpusBuilder Design

`CorpusBuilder.build(project_root, snapshot)` returns a deterministic
`tuple[RetrievalDocument, ...]`. Its build sequence is:

1. validate snapshot file and symbol structure, including duplicate identities;
2. scan the project root using `ProjectScanner` and validate project identity;
3. compare every snapshot file with the current scan by language and raw file hash;
4. read the exact expected source file bytes and verify the same bytes against the
   snapshot file hash;
5. decode with the shared source-reading policy;
6. parse only languages supported by the existing adapters;
7. compare parsed and expected symbol sets;
8. compare every parsed symbol hash with `SymbolState.content_hash`;
9. extract and independently hash the literal source region;
10. perform a final project scan to detect mid-build source mutation; and
11. return all documents only after the complete build succeeds.

New files added after the snapshot are not absorbed into the old snapshot corpus.
Missing expected files, changed expected files, path/scope mismatch, duplicate symbol
identity, missing symbols, unexpected symbols, and stale symbol hashes fail closed.

## 6. SymbolId Reuse

The only symbol identity remains `code_maintenance.SymbolId`. Corpus construction uses
the language, normalized relative path, qualified name, kind, Java semantic
disambiguator, and fallback-line behavior already produced by existing adapters.

Phase 1 does not copy `SymbolId`, calculate a retrieval-specific identity, change Java
overload disambiguation, or alter fallback-line rules.

## 7. Snapshot Boundary

The snapshot is the state-identity reference for every build. Disk content is never
treated as authoritative merely because it can be scanned or parsed. The builder must
prove that the expected snapshot files and symbols are represented by the bytes and
symbol regions read during the build.

The snapshot contract itself is unchanged. Source text is owned by the corpus layer,
and a corpus build never mutates the snapshot or silently rewrites a stored hash.

## 8. Source Extraction and Physical-Line Semantics

Python and Java adapters expose real `start_line` and `end_line` values. Phase 1 slices
those ranges and verifies that the resulting source text hashes to the adapter's symbol
hash.

Phase 1.1 freezes the physical-line model needed by Python AST coordinates:

- LF, CRLF, and CR are physical newline forms;
- source decoding normalizes these forms to LF;
- source-region slicing splits only on LF;
- U+2028, U+2029, form feed, vertical tab, NEL, and U+001C-U+001E do not become extra
  Python AST lines merely because `str.splitlines()` recognizes them.

Decorators remain outside a Python symbol's source region because the existing AST
contract begins at the definition line. Multiline definitions, nested supported
constructs, non-ASCII source, and final-newline behavior retain their adapter-defined
ranges.

## 9. File and Symbol Freshness

Phase 1 preserves two distinct hash layers:

| Hash | Meaning |
| --- | --- |
| `FileState.content_hash` | SHA-256 identity of raw file bytes |
| `SymbolState.content_hash` | SHA-256 identity of the normalized semantic symbol region |

LF and CRLF files therefore have different raw file hashes, while logically identical
symbols can have the same normalized semantic symbol hash. The two hashes are not
interchangeable: file freshness detects any raw source change, while symbol freshness
proves that the retrieval document matches the snapshot's intended symbol content.

Stale `FileState` and stale `SymbolState` are tested independently and both fail closed.

## 10. Atomic, Deterministic, Read-Only Build

Corpus construction is all-or-nothing. Internal documents may be constructed while a
build is in progress, but no partial authoritative corpus is returned after any file,
parse, identity, range, or hash failure.

Documents are sorted by a canonical tuple of existing `SymbolId` fields; output never
depends on filesystem traversal, dictionary insertion, set iteration, random UUIDs, or
time. Repeated builds and directed `PYTHONHASHSEED` runs preserve logical and byte-level
ordering.

The builder reads source and snapshot state only. It writes no source, snapshot, cache,
index, or retrieval artifact and invokes no LLM, embedding service, provider, or
network operation.

## 11. TOCTOU Protection and Boundary

The build sequence is first scan -> exact source-byte read and hash -> parse/extract ->
final scan. The document is built from the same decoded bytes that passed the in-build
file hash check. A tested mutation after source read is rejected by the final scan.

This is best-effort read consistency with final freshness verification. It is not a
filesystem transaction, filesystem lock, watcher, or claim of strong snapshot
isolation.

## 12. Language Support

### Python

Coverage includes module functions, classes, methods, same-named methods in distinct
classes, nested classes and methods, decorated definitions, multiline signatures,
docstrings inside source regions, non-ASCII source, and the physical-line separator
matrix. The legacy parser does not expose nested functions as independent symbols;
their source remains inside the containing function document.

### Java

Coverage includes classes, methods, multiple classes, overload signatures,
same-named methods in distinct classes, and LF/CRLF/CR source input. Java continues to
use the existing lightweight parser; Phase 1 introduces no new parser framework or
dependency.

## 13. Dependency Boundary

The production package contains only `project_intelligence/__init__.py`, `domain.py`,
and `corpus.py`. It depends only on standard-library modules and the allowed
`code_maintenance` contracts. A structural guard rejects imports from Credits,
Managed Access, Admin Operations, provider/config/UI modules, OpenAI/Gradio, and known
embedding/vector libraries. `code_maintenance` has no reverse dependency on
`project_intelligence`.

`requirements.txt` is unchanged.

## 14. Initial Implementation and Test Evidence

The initial implementation commit was
`e31dd5e4fee93229b0e88f988760015e459db1e6`.

It added `RetrievalDocument`, the minimal error hierarchy, `CorpusBuilder`, public
Phase 1 exports, and concentrated corpus regression coverage. Initial evidence was:

| Evidence | Result |
| --- | ---: |
| V3.0.1 released baseline | 414 passed |
| Phase 1 corpus tests | 24 passed |
| Phase 1 initial full regression | 438 passed |
| Offline LLM-contract smoke | 6 passed |

## 15. Initial DeepSeek Independent QA

The Initial Independent QA verdict was **PASS WITH MEDIUM FINDINGS**:

- Critical: 0
- Medium: 2
- **M1:** Python source-region silent misalignment;
- **M2:** Snapshot/Corpus parse-failure semantic mismatch.

### 15.1 M1 Finding and Engineering Lesson

Python AST line numbers count physical newlines, but both the old parser extraction and
the corpus verifier used `str.splitlines()`, which recognizes additional Unicode and
control separators. A later symbol could therefore receive the wrong source region.
Because producer and verifier shared the same incorrect source-region assumption, the
wrong source could still have a matching hash.

The lesson is: **identity consistency does not imply semantic correctness**. Stable
identity and hash consistency are necessary but cannot prove that retrieval source is
semantically correct when both producer and verifier repeat the same mistake.

This is a software-engineering and RAG corpus-integrity case, not a claim of a new
retrieval algorithm.

### 15.2 M2 Finding

`SnapshotBuilder` tolerated `SyntaxError`/`ValueError` parse failures by allowing a
scanned file to contribute zero symbols. The initial `CorpusBuilder` instead failed the
whole build on the same unchanged file. Snapshot and corpus therefore disagreed about
the meaning of a valid zero-symbol source state.

## 16. Phase 1.1 Corpus Integrity Hardening

The hardening commit was
`898f7bce3b20530492a2c747a84a1bcffd6a5d0b`.

### 16.1 M1 Fix

The Python parser now uses one explicit physical-line splitter, and corpus extraction
uses LF-only slicing after shared newline normalization. Regression assertions compare
literal expected source independently rather than trusting only a producer/verifier
pair that could share an error.

Directed evidence covered nine separator variants — baseline, U+2028, U+2029, form
feed, vertical tab, NEL, U+001C, U+001D, and U+001E — across LF, CRLF, and CR:
**27/27 passed**. AST positions, literal source regions, `Symbol.content_hash`,
`SymbolState.content_hash`, and `RetrievalDocument.content_hash` aligned.

### 16.2 M2 Fix

The final parse-failure contract is:

- snapshot expects zero symbols + unchanged file remains unparseable -> zero documents
  are allowed;
- a zero-symbol file changes -> fail closed at file freshness;
- snapshot expects symbols + current parsing fails -> fail closed;
- an unparseable file becomes parseable after the old snapshot -> the old snapshot
  cannot absorb the unexpected symbols;
- multiple unchanged zero-symbol files -> deterministic zero contribution.

The implementation does not broadly swallow parser failures: the tolerance is limited
to the existing parse-error categories and only when the snapshot itself expects zero
symbols.

### 16.3 L1 Source-Reading Fix

Snapshot and corpus source paths now share one explicit policy:

- encoding: UTF-8;
- decode errors: `replace`;
- newline mode: universal newline normalization to LF.

Python and Java passed LF, CRLF, and CR fixtures. Before hardening, Java CR-only input
could produce an incorrect source range between Snapshot and Corpus; the shared policy
removes that divergence.

## 17. Directed Retest and Final QA

DeepSeek Directed Retest returned **PASS WITH LOW NOTES**:

- Critical: 0
- Medium: 0
- M1: CLOSED / RESOLVED
- M2: CLOSED / RESOLVED
- L1: CLOSED / RESOLVED
- directed frozen-core subset: 90 passed.

The directed subset is independent retest evidence; it is not presented as the full
pytest baseline or as a probe count.

The final Phase 1 verdict is **PASS FOR PHASE 1**.

## 18. Final Test Baseline

| Evidence | Result |
| --- | ---: |
| V3.0.1 released baseline | 414 passed |
| Phase 1 initial full regression | 438 passed |
| Phase 1 final corpus tests | 41 passed |
| Phase 1 final full regression | 455 passed |
| Offline LLM-contract smoke | 6 passed |
| DeepSeek directed frozen-core subset | 90 passed |

The standard pytest command still reproduces the known current-host Anaconda Python
3.13.5 debugging-plugin / `rlcompleter` crash. The approved
`python -m pytest -p no:debugging` command produced the recorded suite results. No real
API, Credential, network LLM, or network embedding request was used.

## 19. Known Limitations and Deferred Low Notes

- **LN1 — Java exotic separator boundary:** the legacy Java parser still uses
  `splitlines()` semantics. If a relevant Java source region contains U+2028, U+2029,
  form feed, vertical tab, NEL, or U+001C-U+001E, Corpus now fails closed instead of
  returning silently wrong source. This safer behavior is still a Java parser
  availability limitation. A future Java benchmark that needs those separators must
  first unify the Java physical-line splitter. Ordinary Java benchmark work is not
  blocked.
- **LN2 — broad `ValueError` parse category:** zero-symbol tolerance still treats the
  existing `ValueError` category as a parse failure. The impact is bounded by file
  freshness and the requirement that the snapshot expect zero symbols.
- **LN3 — pre-hardening Python hash compatibility:** special-separator symbol hashes
  produced before hardening may differ. The repository has no production snapshot
  persistence, so no migration is required. An external persisted old snapshot will
  fail closed on affected files and must be rebuilt.
- Hostile `str` subclass hardening remains deferred.
- File-level retrieval and Chunk fallback remain future retrieval capabilities; Phase 1
  intentionally implements the Symbol corpus foundation only.

Future medium-priority test additions suggested by QA, but not required for this gate,
are an additional AST-oracle regression, permanent U+001C-U+001E cases, a Java exotic
separator fail-closed regression, unexpected adapter `RuntimeError` propagation, and
an explicit becomes-parseable-after-old-snapshot regression.

## 20. Thesis Relevance

Phase 1 establishes six thesis-relevant foundations:

1. a stable retrieval corpus;
2. a Symbol-aware primary retrieval unit;
3. snapshot-aligned source projection;
4. two-layer freshness verification;
5. deterministic experimental input; and
6. a corpus-integrity foundation for later BM25, Embedding, Graph, and Hybrid
   experiments.

M1 is retained as a thesis-usable RAG data-integrity engineering case study: stable
identity and internally consistent hashes can still certify the wrong retrieval text
when all validation paths share one faulty source-region assumption. Independent
literal-region validation and a single physical-line contract corrected that failure.

## 21. Final Architecture Status and Next Boundary

| Contract | Final Phase 1 status |
| --- | --- |
| `RetrievalDocument` | IMPLEMENTED / FROZEN FOR PHASE 1 |
| `CorpusBuilder` | IMPLEMENTED |
| Primary retrieval unit | Symbol |
| `SymbolId` | UNCHANGED / REUSED |
| Snapshot | UNCHANGED AS STATE CONTRACT |
| Source text | Owned by `CorpusBuilder` |
| Corpus build | Offline / read-only / atomic / deterministic |
| Freshness | `FileState` + `SymbolState` validation |
| BM25 | NOT STARTED |
| Embedding | NOT STARTED |
| Graph Retrieval | NOT STARTED |
| Hybrid | NOT STARTED |
| `ContextBuilder` | NOT STARTED |
| V3.2 | NOT STARTED |

The Phase 1 Documentation Gate is **CLOSED**. Phase 2 — Lexical Baseline / BM25 is
**ALLOWED BUT NOT STARTED** and must begin only as a separate task.
