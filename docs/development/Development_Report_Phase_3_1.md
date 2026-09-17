# V3.0 Phase 3.1

## Background

Phase 3.1 adds project-level discovery before later project intelligence work. The
existing application could process supplied source files, but it did not yet expose a
deterministic, read-only inventory of a project tree. This phase establishes that
inventory without changing the processor, parsers, UI, or provider behavior.

## Capability

Project Discovery

## Technical Implementation

Project Scanner

## Objectives

- Discover project directories and files from a validated root directory.
- Apply built-in ignore rules, root `.gitignore` rules, and caller-supplied rules.
- Detect file languages by suffix and record project metadata.
- Calculate per-file SHA-256 hashes and a deterministic aggregate project hash.
- Avoid following symlinks and tolerate individual filesystem access failures.
- Keep discovery separate from Python, Java, dependency, or semantic analysis.

## Architecture

```text
Project root
    |
    +--> built-in rules
    +--> root .gitignore
    +--> caller rules
    |
    v
ProjectScanner (read-only traversal; no symlink following)
    |
    +--> Project + directories + files
    +--> languages + metadata
    +--> per-file hashes
    +--> deterministic aggregate hash
    |
    v
ScanResult (frozen domain model)
```

## Core Implementation

`ProjectScanner.scan` resolves and validates the requested root, combines the three
ignore-rule sources in deterministic order, and walks the tree top-down without
following symlinks. Ignored directories are pruned before descent. Visible files are
sorted by normalized relative path, classified by suffix, measured, and hashed in
chunks.

The scanner returns frozen domain objects: `Project`, `ProjectDirectory`,
`ProjectFile`, `ScanMetadata`, and `ScanResult`. The aggregate hash incorporates the
ordered visible directory paths and each ordered file's path, language, and content
hash. File modification times are retained as metadata but do not affect the aggregate
hash. The scanner does not read source into analysis models or perform code analysis.

## Testing

Five committed Project Scanner tests cover:

1. Structure, language detection, metadata, and per-file hashes.
2. Built-in, root `.gitignore`, caller, and negated ignore rules.
3. Deterministic aggregate hashing and visible-content changes.
4. Aggregate hash changes caused by empty-directory changes.
5. Missing and non-directory root rejection.

The Phase 3.1 development baseline is `47 passed`. At the final documentation gate,
all 47 tests passed again. The local Anaconda Python 3.13.5 executable crashes while
loading pytest's PDB integration through `rlcompleter`; the successful gate run used
`python -m pytest -p no:debugging`, which disables only that debugging plugin.

## DeepSeek QA Summary

- Final verdict: **PASS**
- Critical: **0**
- Medium: **0**
- Low observations: **8**
- Independent boundary probes: **12 passed**
- Regression: **none**
- Fix: **No Fix Required**
- Retest: **Not Required**

No Codex QA fix or DeepSeek retest occurred in this phase.

## Technical Debt

- Ignore matching is a deterministic Gitignore-like subset, not full Git semantics.
- Nested `.gitignore` files are not supported; only the root `.gitignore` is read.
- A negation rule cannot re-include a file below a directory already pruned by an
  earlier ignore rule.
- Ignore-rule whitespace is normalized, and specialized Windows long-path handling is
  not implemented.
- Language detection is suffix-based and intentionally incomplete; unknown suffixes
  remain `unknown`.
- Symlinks are deliberately not followed.
- `Project.id` depends on the resolved absolute project path and is not a portable
  cross-machine identity.
- Import graphs, dependency analysis, snapshots, RAG, and Java/Python analysis are
  outside the Project Scanner scope.

## Metrics

| Metric | Value |
|---|---|
| Phase implementation commit | `f72b07211b94acef631bb29af824fbfc26ad8db5` |
| Commit subject | `feat(v3): implement project scanner` |
| Scanner implementation | 216 lines added |
| Project Scanner automated tests | 5 |
| Full automated baseline | `47 passed` |
| Independent QA probes | `12 passed` |
| QA findings | Critical 0 / Medium 0 / Low 8 |

## Files Changed

The Phase 3.1 implementation commit changed:

- `PROJECT_CONTEXT.md`
- `code_maintenance/__init__.py`
- `code_maintenance/domain.py`
- `code_maintenance/scanner.py`
- `tests/test_project_scanner.py`

No processor, UI, parser, provider, or README file was changed by the implementation.

## Next Phase

Phase 3.2: Project Knowledge Graph

Phase 3.2 was not started as part of this documentation gate.
