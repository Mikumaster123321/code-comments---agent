# V3.0 Phase 1.1 — Symbol Identity Hardening

## Background

Phase 1 introduced the V3.0 domain core and stable `SymbolId`, but independent
DeepSeek QA found identity defects that made the initial implementation unsafe as a
foundation for processor migration. The most important defect was a real Java
single-line overload collision: methods with different parameter types could receive
the same identity because class containment and signature extraction relied on
line-oriented legacy parser output.

Phase 1.1 hardened the existing identity model without redesigning it, replacing the
legacy parser, or starting the Phase 2 processor migration.

---

## Objectives

- Distinguish Java single-line overloads such as `foo(int)` and `foo(String)`.
- Canonicalize the limited Java parameter syntax required by V3.0 so cosmetic edits
  do not change identity.
- Split Java parameters without treating commas inside nested types as parameter
  separators.
- Normalize Windows and Unix path separators at the `SymbolId` boundary.
- Keep `fallback_line` as a collision-only fallback rather than a normal identity
  component.
- Preserve the established whole-file and per-symbol `content_hash` semantics.

---

## Architecture Changes

The phase changed only the domain and adapter layer. The legacy parsers remained the
source of syntax extraction.

```text
Java/Python source
        |
        v
Legacy parser output
        |
        +-- Java character offsets (decl_start / brace_pos / close_pos)
        |
        v
Language Adapter
  - lexical class containment
  - parameter extraction
  - deterministic normalization
        |
        v
Symbol ----------------------> Symbol.content_hash (symbol source slice)
        |
        v
SymbolId
  language + normalized path + qualified name + kind + signature
        |
        +---------------------> fallback_line (collision fallback only)

SourceFile.content_hash ------> whole file content
```

Affected modules were `code_maintenance/domain.py` and
`code_maintenance/adapters.py`; processor behavior was deliberately left unchanged.

---

## Core Implementation

### Java lexical scope and overload identity

The legacy Java parser already exposed reliable character offsets for parsed
declarations. The adapter now uses those offsets to determine containing classes,
instead of relying only on `lineno < child_lineno`. This fixes same-line class and
method containment without rewriting the parser.

Signature extraction now reads the declaration slice identified by the parser's
`decl_start` and `brace_pos`. Each overload therefore reads its own parameter list,
rather than searching an entire physical source line and repeatedly matching the
first method.

### Parameter canonicalization

A small best-effort helper canonicalizes the parameter type portion used by
`semantic_disambiguator`:

- removes the parameter modifier `final`;
- normalizes repeated whitespace;
- removes cosmetic whitespace around `<`, `>`, `,`, `[` and `]`;
- canonicalizes spaced and unspaced varargs to `...`;
- removes the parameter variable name while preserving relevant array dimensions.

This is deterministic normalization for the declarations currently required by
V3.0. It is not a Java compiler signature parser and does not attempt type erasure,
generic resolution, annotation semantics, or overload legality checks.

### Depth-aware parameter splitting

The former `split(",")` behavior was replaced by a small scanner that tracks nesting
depth for angle brackets, square brackets, and parentheses. A declaration such as
`foo(Map<String, List<Integer>> data, int count)` is therefore treated as two
parameters.

### Path and fallback behavior

`SourceFile` and direct `SymbolId` construction now share one relative-path
normalization helper. Frozen dataclass and hashable behavior remains intact.

The existing collision counting policy remains unchanged: `fallback_line` is added
only when language, path, qualified name, kind, and semantic disambiguator are still
insufficient to distinguish parsed symbols.

---

## Testing

Nine offline regression tests were added:

1. Java single-line class overload identity.
2. `final int x` versus `int x` normalization.
3. `int[] x` versus `int [] x` normalization.
4. `String... args` versus `String ... args` normalization.
5. `List<String>` versus `List <String>` normalization.
6. Nested generic comma splitting.
7. Direct `SymbolId` Windows/Unix path normalization and hash equality.
8. Verification that a unique symbol does not use `fallback_line`.
9. Verification that a true semantic identity collision does use `fallback_line`.

The test baseline changed from `25 passed, 1 xfailed` to
`34 passed, 1 xfailed`. The remaining xfail documented the separate processor
name-key collision and was intentionally not addressed during Phase 1.1.

---

## DeepSeek QA

### Findings

Independent DeepSeek QA identified the following Phase 1 risks:

- Java single-line overloads could collide.
- Containing-class inference failed when declarations shared a line.
- Signature extraction could read the wrong method declaration.
- Cosmetic Java parameter formatting leaked into identity.
- Nested generic commas were split as top-level parameters.
- Direct `SymbolId` construction did not normalize path separators.
- `fallback_line` and the two `content_hash` meanings needed explicit verification
  and documentation.

### Fix status

All listed identity-hardening findings were addressed within the constrained adapter
and domain scope. No Java parser framework or parser rewrite was introduced.

### Retest status

The follow-up regression suite passed at `34 passed, 1 xfailed`. The retained xfail
was unrelated to Phase 1.1 and represented the planned Phase 2 processor migration.
The project record states that DeepSeek completed QA and retesting before Phase 2
started.

---

## Technical Debt

- Java signature normalization remains best-effort and does not implement the full
  Java type system.
- The regex Java parser does not guarantee extraction of complex annotation syntax
  or every legal Java declaration.
- The legacy Python parser does not extract nested functions or local classes inside
  functions.
- Processor data flow still used `name` as a unique key at the end of this phase;
  this was intentionally deferred to Phase 2.

---

## Next Phase

Phase 2 would migrate processor identity from symbol names to `SymbolId`, including
concurrent generation results, errors, annotated-source backfill, Markdown document
association, diff verification, and navigation anchors. The migration was required
to preserve the newly hardened identities throughout the complete processing flow.

---

## Metrics

| Metric | Value |
|---|---|
| New regression tests | 9 |
| Baseline before phase | `25 passed, 1 xfailed` |
| Baseline after phase | `34 passed, 1 xfailed` |
| Phase commit | `b9a4a2a2df123a368bf97f94f9cf45454ea45cc6` |
| Phase completion HEAD | `b9a4a2a2df123a368bf97f94f9cf45454ea45cc6` |
| Report-generation HEAD | `f531c9a744b522780956cface228dfa6b58be5b6` |
| Branch | `v3.0.0-test1` |
| Commit subject | `fix(v3): harden stable symbol identity` |

---

## Files Changed

- `PROJECT_CONTEXT.md`
- `code_maintenance/adapters.py`
- `code_maintenance/domain.py`
- `tests/test_domain.py`
- `tests/test_java_adapter.py`
