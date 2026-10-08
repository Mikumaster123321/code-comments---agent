# V3.1.3 Repository / Directory / Documentation Architecture Scope Freeze

发布门禁：V3.1.3 `IMPLEMENTATION / PRE-RELEASE`

## 1. Authority and audit verdict

- Version: `3.1.3`
- Status: `SCOPE FROZEN / IMPLEMENTATION AUTHORIZED / NOT RELEASED`
- Authoritative baseline and branch point:
  `93e4c0ab326e5eaf2fb6051c241fc5c76072afe9`
- Development branch: `v3.1.3-dev`
- Audit verdict: `READY FOR SCOPE FREEZE`
- Audit P0 findings: `0`
- Baseline regression: `951 passed`
- Baseline host limitation: bare `python -m pytest` on Anaconda Python 3.13.5
  terminates in the pytest debugging plugin while importing `rlcompleter`; the
  equivalent run with that plugin disabled passes all 951 tests.
- V3.1.0 / V3.1.1 / V3.1.2: `RELEASED + DOCUMENTATION CLOSED`
- V3.1.4: `NOT STARTED`
- V3.2: `NOT STARTED`

This tracked document is the Source of Truth for V3.1.3 implementation scope. Chat
history does not extend it. The release is an engineering-maintainability,
repository-architecture, documentation-information-architecture, release-traceability,
and backward-compatible-modularization release. It creates no retrieval or model
quality result.

## 2. Frozen six-item scope

### V313-REL-01 — Two-stage release identity validator

Strengthen `docs/release/release_state.json`, `scripts/dev.py`, the release workflow
tests, and the permanent documentation contract. Tracked metadata records stable
release intent, not the SHA of the commit containing the metadata itself. Runtime
validation derives `final_head` from the current checkout, verifies that
`release_commit` is its ancestor, and verifies that the annotated tag peels to
`release_commit`. Remote mode dynamically verifies GitHub and Gitee main and
development branches against the runtime final HEAD and both remote tags against the
release commit. Dynamic SHAs must not be written back into tracked metadata.

The existing V3.1.2 v1 record remains readable and validatable. A prospective schema
may require the V3.1.3 Final QA evidence path, but implementation must not fabricate a
PASS or claim that Final QA has run.

### V313-DOC-02 — Current-state Source of Truth

Current machine-readable state is derived from Git objects plus
`docs/release/release_state.json`. Current human summaries are limited to README,
the top-level current section of `PROJECT_CONTEXT.md`, and `docs/release/README.md`.
Historical scope, thesis, report, release-note, and experiment documents remain
time-point snapshots rather than current release-state authority. During this phase,
all V3.1.3 current-state wording is `IMPLEMENTATION / PRE-RELEASE` or, after verified
implementation completion, `AWAITING FINAL QA`; it is never `RELEASED`.

### V313-CONTEXT-03 — PROJECT_CONTEXT current/history separation

Keep the root `PROJECT_CONTEXT.md` path as the concise current operational context:
current version and baseline, active architecture and boundaries, release state,
authoritative links, Formal frozen identity, and immediate roadmap. Preserve its
historical body verbatim in
`docs/development/PROJECT_CONTEXT_History_Through_V3_1_2.md` before removing that body
from the root file. Provide forward and reverse navigation. Historical facts must not
be silently summarized away, corrected, or reinterpreted.

### V313-APP-04 — Strictly bounded internal seam extraction

Only two implementation seams may move:

1. `ui.py::CUSTOM_CSS` to `code_comments_agent/ui_styles.py`;
2. workspace persistence implementation from `processor.py` to
   `code_comments_agent/workspace.py`.

Create `code_comments_agent/__init__.py` only to support those seams. Preserve the
public paths `from ui import CUSTOM_CSS`, `processor.save_workspace`,
`processor.load_workspace`, `processor.clear_workspace`, and every currently public
workspace helper by direct import or re-export. CSS content and workspace path,
security, serialization, return-value, and exception behavior remain equivalent.

### V313-NAV-05 — Repository architecture and documentation navigation

Create `docs/README.md`,
`docs/architecture/Repository_Architecture_Map_V3_1_3.md`, and lightweight local
indexes for `docs/development/` and `docs/qa/`. The map must describe the actual root
runtime modules, the bounded support package, language adapters, maintenance and
project-intelligence packages, access/credit/admin areas, experiments, developer
scripts, tests, documentation areas, and runtime-generated outputs. It must label
ACTIVE RUNTIME, DEVELOPER TOOLING, TEST, HISTORICAL DOCUMENTATION, FROZEN FORMAL
EVIDENCE, RUNTIME GENERATED / UNTRACKED, and DO NOT TOUCH boundaries.

### V313-TEST-06 — Architecture compatibility gates

Add `tests/test_repository_architecture.py` and extend
`tests/test_release_workflow.py`. Protect the root entrypoint and command hub,
compatibility imports/re-exports, internal support modules, documentation navigation,
release schemas and C1/C2 ancestry rules, required Final QA evidence, remote mismatch
failures, legacy V3.1.2 readability, and immutable Formal identity/hash. Tests remain
offline and must not write real remotes, push, alter user refs, call an LLM provider,
or weaken existing coverage.

## 3. Hard non-goals

V3.1.3 does not:

- change retrieval, ranking, BM25, E5, graph expansion, Hybrid, RRF,
  ContextBuilder, `project_intelligence` semantics, dataset, Query, Ground Truth,
  Grade, RQ results, Formal protocols, artifacts, metrics, or interpretation;
- change prompts, cleanup, output language, Provider calls, model parameters,
  routing, API requests, `llm_service`, or any other LLM behavior;
- move UI callbacks, Gradio construction, Provider flow, the processor pipeline,
  progress pipeline, batch ZIP, diff engine, analysis logic, formatter, config,
  `Py/`, `Java/`, `project_intelligence/`, or `code_maintenance/` into the new
  support package;
- redesign CSS or UX, change workspace format/storage/temp lifecycle, add a database,
  introduce packaging metadata, a packaging framework, or a dependency;
- rename or delete any repository path. Rename candidates: `NONE`. Delete
  candidates: `NONE`;
- create a tag, push a branch/tag, run Final QA, or mark V3.1.3 released.

If completion would require touching `llm_service` or crossing another frozen
boundary, implementation stops and reports a scope violation.

## 4. Formal and protected-document immutability

V3.1.3 has `Retrieval impact: NONE`, `Formal impact: NONE`, and `LLM behavior impact:
NONE`.

- Formal execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- Formal artifact-set canonical identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Formal artifact-set file SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

`docs/experiments/**` is frozen formal/research evidence: read-only and excluded from
all edits, moves, renames, generated rewrites, and current-status normalization. Its
historical wording is not current release-state authority.

`docs/thesis/` is a user-protected path: `DO NOT TOUCH`. This task must not read,
list, search, modify, move, stage, or delete it. Only its untouched/untracked status may
be observed through repository status output.

## 5. Release identity and migration contract

V3.1.3 uses a non-self-referential two-stage identity:

1. Before C1, tracked release intent contains stable fields such as version, state,
   expected branches, required documents, and the expected Final QA evidence path.
2. The reviewed release commit C1 is later recorded as `release_commit`; the annotated
   tag peels to C1.
3. C2 or later commits may contain that stable C1 identity. The validator derives the
   current `final_head` at runtime and requires C1 to be its ancestor; it never stores
   the containing commit's own SHA as a tracked `final_head`.
4. Remote verification compares live branch refs to the runtime final HEAD and live
   peeled tag refs to C1 without mutating the metadata file.

Schema migration is prospective and backward compatible: the committed V3.1.2 v1
record remains readable. New V3.1.3-only requirements, including Final QA evidence,
must not be retroactively imposed on v1. No migration may rewrite published history
or move an existing tag.

## 6. Compatibility contract

The root `main.py`, `ui.py`, and `processor.py` module paths remain supported. The
extracted modules own implementation while root modules provide compatible imports or
re-exports. Existing callers, tests, `main.py`, Processor tuple shapes, runtime
behavior, workspace files, CSS value, Python/Java flows, and release command paths
must not require import changes. `code_maintenance.__version__`, release metadata, and
current documentation remain subject to consistency validation.

## 7. Test and verification plan

Required validation is:

1. targeted V3.1.3 repository-architecture and release-workflow tests;
2. `python scripts/dev.py test llm`;
3. `python scripts/dev.py test production`;
4. `python scripts/dev.py test experiments`;
5. `python scripts/dev.py test release` when the profile exists;
6. `python scripts/dev.py test full`, with at least 951 tests and zero unexpected
   failures;
7. `python scripts/dev.py experiment-validate archive-v3.1.0`;
8. deterministic Formal CSV checks and immutable revision/identity/SHA checks;
9. CPython 3.10 plus Gradio 6.27.0 `import gradio` and `create_ui()` build smoke.

All release tests use mocks, subprocess fixtures, or temporary repositories. They do
not contact or write GitHub/Gitee, mutate user refs, make paid/network LLM calls, or
use real credentials. The known Anaconda 3.13 host SIGSEGV must be reported as a host
limitation, never converted into a fabricated application PASS.

## 8. Documentation gate

Before independent Final Release QA, V3.1.3 must have tracked updates for README and
Version History, this Scope Freeze, the Repository Architecture Map, Markdown and
independently readable UTF-8 TXT Thesis Materials, Development Report, pre-release
Release Notes, the current `PROJECT_CONTEXT.md`, top-level and local documentation
indexes, the release index, and the permanent version documentation contract.

The expected future Final QA evidence path is
`docs/qa/V3_1_3_Final_Release_QA.md`. It must remain absent or clearly non-passing until
DeepSeek Final QA actually executes; no placeholder may claim PASS. This implementation
creates local logical commits only. It creates no tag, performs no push, and cannot
advance V3.1.3 beyond `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`.
