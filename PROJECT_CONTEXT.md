# Project Context

<!-- release-state: V3.1.3 IMPLEMENTATION COMPLETE / AWAITING FINAL QA -->

## Current State

- Current version: `3.1.3`
- Lifecycle: `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`
- Development branch: `v3.1.3-dev`
- Authoritative main baseline / branch point:
  `93e4c0ab326e5eaf2fb6051c241fc5c76072afe9`
- Scope Freeze commit: `2a6233d`
- V3.1.0 / V3.1.1 / V3.1.2: `RELEASED + DOCUMENTATION CLOSED`
- V3.1.4: `NOT STARTED`
- V3.2: `NOT STARTED`
- Tag created for V3.1.3: `NO`
- Push performed for V3.1.3: `NO`
- Final QA evidence: `NOT YET EXECUTED`

V3.1.3 is a repository, directory, documentation-information-architecture, release
traceability, and backward-compatible modularization maintenance release. It changes
no retrieval, Formal, or LLM behavior. Its six frozen work items are defined by the
[V3.1.3 Scope Freeze](docs/development/V3_1_3_Repository_Architecture_Scope.md).

The pre-migration 1,809-line context remains available verbatim in
[PROJECT_CONTEXT History Through V3.1.2](docs/development/PROJECT_CONTEXT_History_Through_V3_1_2.md).
That archive is historical evidence, not current-state authority.

## Current Architecture

### Stable root runtime

- `main.py` remains the application entrypoint.
- `ui.py` owns Gradio construction and callbacks and re-exports `CUSTOM_CSS`.
- `processor.py` owns the processing, progress, batch, diff, and analysis pipelines
  and re-exports workspace persistence helpers.
- `config.py`, `i18n.py`, `llm_provider.py`, and `llm_service.py` retain their existing
  responsibilities.

### Bounded internal support package

`code_comments_agent/` contains exactly the two V3.1.3 extraction seams:

- `ui_styles.py` owns the content-equivalent `CUSTOM_CSS` value;
- `workspace.py` owns the unchanged save/load/clear persistence implementation;
- `__init__.py` only marks the package.

Compatibility paths remain valid: `from ui import CUSTOM_CSS`,
`processor.save_workspace`, `processor.load_workspace`,
`processor.clear_workspace`, `processor._default_workspace_path`, and
`processor.WS_ALLOWED_FIELDS`.

### Established domain packages

- `Py/` and `Java/`: language parsing, annotation, documentation, and analysis.
- `code_maintenance/`: language-neutral maintenance domain and project version.
- `project_intelligence/`: released retrieval/index/context behavior, unchanged in
  V3.1.3.
- `credits/`, `managed_access/`, and `admin_operations/`: accounting, access, pricing,
  and administrative services.
- `experiments/`: experiment runtime; Formal semantics remain frozen.
- `scripts/`: developer workflow and deterministic validation/export tooling.
- `tests/`: offline regression, compatibility, architecture, and release gates.

The detailed current map is
[Repository Architecture Map V3.1.3](docs/architecture/Repository_Architecture_Map_V3_1_3.md).

## Active Invariants and Boundaries

- LLM behavior impact: `NONE`. Prompts, cleanup, output language, Provider calls,
  model parameters, routing, and API requests are unchanged.
- Retrieval impact: `NONE`. Ranking, BM25, E5, graph expansion, Hybrid, RRF,
  ContextBuilder, datasets, Query/GT/Grade, and RQ interpretation are unchanged.
- Formal impact: `NONE`. Protocols, evidence, artifacts, metrics, and identities are
  immutable.
- UI behavior impact: `NONE`; CSS content is unchanged.
- Workspace behavior impact: `NONE`; paths, security filtering, serialization,
  messages, return values, exceptions, and temp lifecycle are unchanged.
- Root module paths remain the compatibility surface; V3.1.3 is not a general package
  migration.
- `docs/experiments/**` is frozen formal/research evidence and not current
  release-state authority.
- `docs/thesis/` is a user-protected path: `DO NOT TOUCH`.
- Tests must remain offline and must not call a real LLM Provider, use a real API key,
  write a real remote, or mutate user refs.

## Release Identity and Current Source of Truth

Machine-readable current state is Git objects plus
`docs/release/release_state.json`. Human-readable current summaries are the root
README, this file, and `docs/release/README.md`. Versioned scope, thesis, report,
release-note, QA, and experiment documents are snapshots of their recorded phase.

V3.1.3 uses release schema `v2`:

- tracked metadata records stable intent and never stores a self-referential
  `final_head`;
- future C1 is recorded as `release_commit`, and the annotated tag must peel to C1;
- runtime derives the current HEAD and requires C1 to be its ancestor, so a later C2
  release-record commit is valid;
- `--remote` dynamically verifies GitHub and Gitee main/development branches against
  runtime HEAD and both peeled tag targets against C1;
- `docs/qa/V3_1_3_Final_Release_QA.md` is required before release but is not created or
  claimed by implementation;
- the V3.1.2 v1 record remains readable by the validator.

The permanent requirements are in
[Version Documentation Contract](docs/release/Version_Documentation_Contract.md).

## Frozen Formal Identity

- Execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- Artifact-set canonical identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Artifact-set file SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

These values must remain unchanged. V3.1.3 makes no retrieval-quality, model-quality,
user-satisfaction, statistical-significance, or external-generalization claim.

## Verification State

- Pre-change full baseline: `951 passed` using the recorded Anaconda host workaround.
- Bare Anaconda Python 3.13.5 pytest/Gradio paths may terminate in the known
  IPython/`rlcompleter` host SIGSEGV; this is not an application PASS or failure.
- V3.1.3 architecture + release targeted: `24 passed`; LLM: `6 passed`;
  production: `198 passed`; experiments: `240 passed`; full: `968 passed`.
- Release profile: `24 passed`; the final gate explicitly remains unexecuted pending
  real Final QA evidence.
- CPython 3.10.22 + Gradio 6.27.0 `create_ui()` build smoke: `PASS` (`Blocks`, 106
  blocks).
- Archive validator and deterministic Formal CSV checks: `PASS`; frozen identity and
  SHA unchanged.

## Authoritative Navigation

- [Documentation index](docs/README.md)
- [Development index](docs/development/README.md)
- [QA index](docs/qa/README.md)
- [Release index](docs/release/README.md)
- [V3.1.3 Scope Freeze](docs/development/V3_1_3_Repository_Architecture_Scope.md)
- [Repository Architecture Map](docs/architecture/Repository_Architecture_Map_V3_1_3.md)
- [Machine-readable release state](docs/release/release_state.json)

## Immediate Roadmap

1. Complete and record all required offline, full-regression, archive, CSV, Formal
   immutability, and CPython 3.10 UI-smoke evidence.
2. Commit the implementation and V3.1.3 documentation package locally.
3. Hand off to DeepSeek V4.1 Flash for independent Final Release QA and the separately
   authorized release sequence.
4. Do not create a V3.1.3 tag or push in this implementation task.
5. Keep V3.1.4 and V3.2 `NOT STARTED` until separately scoped and authorized.
