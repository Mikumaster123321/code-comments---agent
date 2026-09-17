# V3.0 Phase 3.1 — Project Scanner QA Report

## QA Status

**PASS**

The Project Scanner passed independent DeepSeek QA with non-blocking Low-level
observations. No Critical or Medium defects were found. The implementation is suitable
to enter Phase 3.2.

**No Fix Required.**

**Retest Not Required.** No Codex fix was made after this QA, so no separate DeepSeek
retest cycle was necessary. The results below are from the original independent QA
run and must not be interpreted as a post-fix retest.

---

## Environment

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Reviewed HEAD | `f72b07211b94acef631bb29af824fbfc26ad8db5` |
| Reviewed commit | `feat(v3): implement project scanner` |
| Git status | Clean |
| Pytest baseline | `47 passed` |
| Baseline consistency | Matches `PROJECT_CONTEXT.md` |

---

## Review Scope

The independent review covered:

- `code_maintenance/scanner.py`;
- the Phase 3.1 domain additions in `code_maintenance/domain.py`:
  `Project`, `ProjectDirectory`, `ProjectFile`, `ScanMetadata`, and `ScanResult`;
- the existing Project Scanner unit tests;
- regression safety for the Phase 1 and Phase 2 code paths.

The QA was read-only. DeepSeek did not modify source code or tests.

---

## Method

DeepSeek performed a full code review of the Scanner and domain objects, ran the
existing pytest suite, and used independent temporary scripts to probe Scanner edge
cases. Twelve independently probed boundary scenarios passed.

The review focused on:

- directory traversal;
- ignore-rule behavior;
- symlink safety;
- metadata collection;
- deterministic per-file and aggregate hashing;
- permission and filesystem boundaries;
- regression isolation from processor, adapters, parsers, UI, LLM, and providers.

---

## Verdict

The final recorded verdict is **PASS**, with Low-level observations that do not block
Phase 3.2.

- Critical defects: 0
- Medium defects: 0
- Low observations: 8
- Independently probed boundary scenarios: 12 passed
- Existing automated suite: `47 passed`

Core behavior was accepted:

- symlinks are not followed;
- the documented `.gitignore` subset behaves consistently;
- project hashes are deterministic for unchanged visible content;
- ignored content does not affect the aggregate hash;
- permission failures do not crash the full scan;
- Phase 1 and Phase 2 behavior did not regress.

---

## Critical Findings

None.

---

## Medium Findings

None.

---

## Low Observations

### D1 — `skipped_entries` may undercount permission failures

The `Path.is_symlink()` and `Path.is_file()` checks are outside the local
`try`/`except` block. On supported Python versions these helpers may return `False`
for some `OSError` conditions rather than raising, causing an inaccessible entry to
be silently excluded without incrementing `skipped_entries`.

This affects metadata precision, not scan safety or result correctness. It is not a
Phase 3.1 blocker.

### D2 — Hidden files and directories are scanned by default

Generic hidden entries such as `.foo/` and `.env` are not ignored automatically.
This matches Git's default behavior. `ScanResult` stores hashes and metadata rather
than file contents, and callers can add explicit ignore rules when required.

### D3 — The root `.gitignore` file is included

The `.gitignore` file itself appears in the scan result unless a rule excludes it.
The existing test suite explicitly records this behavior. It is an accepted design
choice.

### D4 — Language suffix coverage is intentionally incomplete

Unmapped suffixes such as `.m`, `.mm`, `.ipynb`, `.lock`, and `.proto` are reported
as `unknown`. The `.h` suffix is classified as C even though some projects use it for
C++. This is a classification limitation, not a scanner failure.

### D5 — Negation cannot re-include content below a pruned directory

With rules such as `build/` followed by `!build/keep.py`, `build/` is pruned during
top-down traversal and `keep.py` is not revisited. This behavior is compatible with
the documented Gitignore-like subset and does not claim full Git ignore semantics.

### D6 — Ignore-rule whitespace is normalized

`_clean_rules` uses `.strip()`, so leading and trailing spaces with special meaning
in native Gitignore syntax are not preserved. Such patterns are uncommon and outside
the documented subset.

### D7 — Windows long-path handling is not specialized

The scanner does not add the Windows `\\?\` long-path prefix. The reviewed macOS
environment is unaffected. Windows projects with paths beyond the platform's normal
limit may require a future compatibility enhancement.

### D8 — `Project.id` is location-dependent

`Project.id` is derived from the resolved absolute root path. The same repository at
different paths or on different machines receives a different project ID. This is
acceptable for the current single-machine workflow but is not a portable project
identity for future cross-machine snapshots or synchronization.

---

## Missing Automated Tests

DeepSeek independently probed the following behaviors successfully, but identified
them as missing or incomplete regression coverage:

1. File, directory, broken, and root-escaping symlinks are skipped.
2. Windows backslashes in ignore rules, including `build\\*.log` and `dist\`.
3. Root-anchored rules such as `/foo` and `/build/`.
4. Default handling of `.config/` and `.env`.
5. Unicode and Chinese filenames and directory names.
6. Empty-root metadata and 64-character aggregate hash.
7. Deep directory traversal, independently tested to 120 levels.
8. Duplicate filenames in different directories.
9. Chunked hashing for files larger than 1 MiB.
10. Read-only or inaccessible directory accounting in `skipped_entries`.
11. Project hash stability when only mtime changes.
12. Fixed behavior for negation below an already ignored directory.

The recommended minimum Phase 3.2 entry follow-up is to add regression coverage for
items 1, 2, 3, and 11. These are test-hardening recommendations, not required fixes
for the accepted Phase 3.1 implementation.

---

## Regression Assessment

No regression was found.

`scanner.py` is an independent module importing only the new domain models. The
implementation did not modify `processor.py`, adapters, legacy Python/Java parsers,
UI, LLM behavior, or providers. The complete `47 passed` suite confirmed that Phase
1 and Phase 2 behavior remained intact.

---

## Fix Record

**No Fix Required.**

- Critical and Medium findings requiring correction: none.
- Codex remediation after this QA: none.
- Business code changes caused by this QA: none.
- Test changes caused by this QA: none.

The Low observations are retained as explicit constraints and future test-hardening
opportunities.

---

## Retest Record

**Retest Not Required.**

No post-QA implementation changes were made, so a separate DeepSeek retest was not
performed. The initial independent QA already completed code review, the full
`47 passed` regression run, and twelve passing boundary probes.

---

## Phase 3.2 Recommendation

DeepSeek recommends entering Phase 3.2. Directory traversal, ignore handling,
deterministic hashing, symlink safety, and boundary tolerance passed independent
verification with no blocking defect.

Phase 3.2 should keep D1 and D8 visible when designing future metadata, snapshot, or
incremental comparison behavior. The Project Graph must not silently turn the
location-dependent `Project.id` into a cross-machine identity guarantee.

---

## Evidence Source

This report is a structured record of the DeepSeek independent QA findings supplied
for V3.0 Phase 3.1. It does not claim any Codex fix or DeepSeek retest that did not
occur.
