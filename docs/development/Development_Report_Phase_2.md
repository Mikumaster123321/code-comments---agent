# V3.0 Phase 2 — Processor Symbol Migration

## Background

After Phase 1.1, `SymbolId` was stable enough to identify Python methods in different
classes and Java overloads. The processor still discarded that distinction by using
`item["name"]` as the key for concurrent generation results and for annotated-source
lookup. Two same-named symbols could therefore overwrite each other's generated
documentation or be associated with the wrong source slice.

The defect was captured by a strict xfail regression test. Phase 2 performed an
internal identity migration while preserving the public processing API, Gradio flow,
legacy parsers, and user-visible feature set.

---

## Objectives

- Attach a stable `SymbolId` to every legacy parser item entering the processor.
- Establish a `SymbolId -> Symbol` lookup for processor operations.
- Key Python and Java generation results and errors by `SymbolId`.
- Preserve identity through annotation insertion and annotated-source reparsing.
- Associate Markdown source slices and navigation anchors with the correct symbol.
- Pass real relative paths into batch processing identities.
- Verify that diff output contains every same-named symbol result.
- Close the historical strict xfail only after the underlying defect is fixed.

---

## Architecture Changes

The migration introduced a domain-identity bridge inside `processor.py` and reused
the existing adapters. The parsers and UI were not changed.

```text
Source code + relative path
            |
            v
      Legacy parser items
            |
            +----------------------+
            |                      |
            v                      v
   PythonAdapter / JavaAdapter   legacy node metadata
            |
            v
    SymbolId -> Symbol lookup
            |
            +--> item["symbol_id"]
            +--> item["qualified_name"]
            +--> SymbolId-keyed navigation slug
            |
            v
Concurrent generation
  results[SymbolId]
  errors[SymbolId]
            |
            v
Annotation insertion
            |
            v
Reparse annotated source
            |
            v
SymbolId-keyed source backfill
            |
            +--> Markdown association
            +--> navigation anchors
            +--> line-based diff rendering
```

Both synchronous and progress-reporting Python/Java paths use the same mapping and
backfill helpers.

---

## Core Implementation

### Parser item to Symbol mapping

`_parse_items_with_symbols` parses legacy items, runs the corresponding domain
adapter, verifies item count and ordering, attaches the resulting `SymbolId` and
qualified name to each item, and builds a `dict[SymbolId, Symbol]` lookup. Duplicate
identities are rejected explicitly rather than silently overwriting processor state.

Single-file processing uses deterministic synthetic paths, while batch processing
passes the actual normalized relative path into `process_code`.

### Concurrent generation migration

All four generation paths were migrated:

- synchronous Python;
- progress-reporting Python;
- synchronous Java;
- progress-reporting Java.

Worker results now return `SymbolId`; both `results` and `errors` use it as their key.
Human-readable names remain only for logs and prompts. Reverse-order annotation
insertion retrieves generated documentation using the item's attached identity.

### Annotated-source backfill

The former name-keyed `new_items_map` was replaced by `_refresh_doc_entry_code`.
Annotated source is reparsed and associated by `SymbolId`. For the rare case where
`fallback_line` changes after inserted documentation shifts line numbers, the helper
groups candidates by the full semantic identity excluding the fallback line and
matches them deterministically in source order.

### Markdown, navigation, and diff

Processor items receive a unique slug that is stored in a `SymbolId`-keyed mapping.
Python and Java Markdown builders preserve that preassigned slug, while still
retaining their original name-based fallback behavior for independent callers.

The outline builder now uses `SymbolId` for slug lookup and qualified names for class
containment. This also fixes navigation hierarchy for declarations that share a
physical line. Diff generation remains intentionally line-based and symbol-agnostic;
regression tests verify that both same-named generated results reach its input and
appear in the rendered output.

### Historical xfail closure

`test_same_named_methods_keep_their_own_generated_docstrings` was not deleted and its
assertions were not weakened. Once the implementation used `SymbolId`, the test
became an `XPASS(strict)`, which demonstrated that the original defect was fixed.
The xfail marker was then removed and the same test became a normal regression test.

---

## Testing

Seven new offline processor regression tests were added, and the historical strict
xfail was promoted to a normal passing regression test. The eight processor tests now
cover:

1. Python same-named methods retaining their own generated docstrings.
2. Parser-item `SymbolId` backfill and `SymbolId -> Symbol` lookup.
3. Python Markdown association for same-named methods.
4. Multiline Java overload result and Markdown association.
5. Single-line Java overload results without collisions.
6. Diff output containing both same-named method results.
7. Navigation anchors matching Markdown anchors.
8. Progress-reporting processing without same-name result overwrite.

The project baseline changed from `34 passed, 1 xfailed` to `42 passed`, with zero
skips and zero xfails. The targeted offline LLM contract smoke test passed all six
tests. Python 3.9 syntax compilation also passed.

---

## DeepSeek QA

### Findings

The processor name-key collision was already documented as a known defect and strict
xfail before Phase 2. The required QA focus is therefore the preservation of distinct
Python scoped methods and Java overloads through concurrency, insertion, Markdown,
diff, and navigation.

No separate Phase 2 DeepSeek QA report or machine-readable QA artifact exists in the
repository at the time this report was written.

### Fix status

The known name-key collision is fixed and removed from `PROJECT_CONTEXT.md` technical
debt. Static inspection found no remaining `results[name]`, `errors[name]`, name-keyed
annotated-source map, or object-id-keyed navigation slug map in the processor.

### Retest status

Codex implementation verification completed with `42 passed`; the six-test offline
LLM contract smoke check also passed. Independent DeepSeek Phase 2 retesting is not
documented in the repository and should be recorded separately if performed.

---

## Technical Debt

- Synchronous and progress-reporting processing remain separate implementations;
  future processing-stage changes must keep both paths aligned.
- The legacy Java annotator is line-oriented. When several declarations share one
  physical line, their identities and Markdown documentation remain distinct, but
  generated Javadocs are inserted above the shared line rather than immediately
  before each declaration.
- The known lexical boundaries of the legacy Python and Java parsers remain.
- A truly duplicate `SymbolId` that cannot be separated even by `fallback_line` is
  rejected explicitly; the processor does not invent a new identity component.

---

## Next Phase

The implementation and offline regression gates are green for the next roadmap
stage, V3.1 Project Intelligence / RAG. Before expanding architecture, the recommended
handoff is an independent Phase 2 QA pass that records edge-case results against the
committed baseline. No RAG, Multi-Agent, Router, API, or VS Code work was started in
Phase 2.

---

## Metrics

| Metric | Value |
|---|---|
| New regression tests | 7 |
| Promoted historical regression | 1 strict xfail -> normal passing test |
| Baseline before phase | `34 passed, 1 xfailed` |
| Baseline after phase | `42 passed` |
| Offline LLM contract smoke | `6 passed` |
| Skips / xfails after phase | `0 / 0` |
| Phase commit | `f531c9a744b522780956cface228dfa6b58be5b6` |
| Phase completion HEAD | `f531c9a744b522780956cface228dfa6b58be5b6` |
| Report-generation HEAD | `f531c9a744b522780956cface228dfa6b58be5b6` |
| Branch | `v3.0.0-test1` |
| Commit subject | `feat(v3): migrate processor to SymbolId` |

---

## Files Changed

- `Java/java_annotator.py`
- `PROJECT_CONTEXT.md`
- `Py/annotator.py`
- `processor.py`
- `tests/test_processor_regressions.py`
