# Thesis Materials — V3.1.3 Repository Architecture

Status: `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`

## 1. Contribution positioning

V3.1.3 is an engineering-maintainability contribution. Its thesis value is in five
areas: Repository Architecture, Documentation Information Architecture, Release
Traceability, Backward-compatible Modularization, and executable Architecture
Compatibility Gates. It does not claim a retrieval, model, user-satisfaction, or
Formal experimental improvement.

## 2. Problem and design boundary

The repository had stable runtime behavior and released Formal evidence, but three
maintenance risks remained:

1. release identity mixed a reviewed release commit with a later record HEAD;
2. the 1,809-line root `PROJECT_CONTEXT.md` mixed current operational facts with a
   long chronological history;
3. root UI and processor modules owned two separable support concerns while their
   public import paths had to remain stable.

The solution was frozen to six items: two-stage release identity, current-state
Source of Truth, PROJECT_CONTEXT current/history separation, extraction of only CSS
and workspace persistence, repository/document navigation, and compatibility tests.
No general root-module migration, rename, deletion, dependency, or packaging framework
was introduced.

## 3. Non-self-referential release identity

Schema v2 stores stable release intent: version, lifecycle, expected development/main
branches, C1 `release_commit`, tag, required documents, and Final QA evidence path. It
does not store a `final_head` equal to the commit containing the metadata because that
would be self-referential.

At validation time, the current Git HEAD is the derived final HEAD. A released state
passes only when C1 is an ancestor of that HEAD and the annotated tag peels to C1.
Remote mode reads GitHub and Gitee refs and requires both main and development branches
to equal runtime HEAD and both peeled tag targets to equal C1. The derived SHAs are
never written back. The released V3.1.2 v1 record remains readable.

Final QA is fail-closed: `docs/qa/V3_1_3_Final_Release_QA.md` is a required future
evidence path, but implementation does not create it or fabricate PASS.

## 4. Documentation information architecture

Current machine state is Git objects plus `docs/release/release_state.json`. Current
human summaries are the root README, root `PROJECT_CONTEXT.md`, and
`docs/release/README.md`. Versioned scope, thesis, development-report, QA,
release-note, and experiment documents are phase snapshots rather than implicit
current-state authorities.

The old root context body is preserved in
`docs/development/PROJECT_CONTEXT_History_Through_V3_1_2.md`. The new root context
contains only current version/state, active architecture and boundaries, release
identity, Formal identity, navigation, verification state, and immediate roadmap.
Top-level and local documentation indexes make the authority model visible.

## 5. Backward-compatible modularization

Only two internal seams moved:

- `code_comments_agent/ui_styles.py` owns the unchanged `CUSTOM_CSS` value while
  `ui.py` re-exports it;
- `code_comments_agent/workspace.py` owns workspace save/load/clear behavior and
  constants while `processor.py` re-exports the same function objects and fields.

The root application entrypoint, Gradio construction, callbacks, processor pipeline,
Provider flow, progress, batch ZIP, diff, analysis, formatters, Python/Java modules,
Project Intelligence, and maintenance domain stayed in place. Workspace paths,
whitelist security, JSON format, atomic replacement, messages, returns, and exceptions
did not change. CSS content equality is tested independently of Gradio import.

## 6. Executable evidence

- Pre-change baseline: `951 passed`.
- V3.1.3 architecture + release targeted: `24 passed`.
- Offline LLM contracts: `6 passed`.
- Production profile: `198 passed`.
- Experiments profile: `240 passed`.
- Full regression: `968 passed`.
- Formal execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`.
- Formal artifact identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`.
- Formal artifact file SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`.

The archive validator and deterministic Formal CSV checks pass without regenerating
or editing frozen evidence. A fresh CPython 3.10.22 environment with Gradio 6.27.0
builds `create_ui()` as `Blocks` with 106 blocks: `PASS`. Anaconda Python 3.13.5's
pytest/Gradio import SIGSEGV remains a host limitation and is not reported as an
application PASS.

## 7. Claim boundary

Supported claim: V3.1.3 makes repository responsibilities, current-state authority,
release identity, and compatibility boundaries more explicit and executable while
preserving established import paths and behavior.

Unsupported claims include retrieval improvement, model-output improvement,
statistical significance, user-satisfaction improvement, external-project
generalization, or a completed V3.1.3 release. Independent Final QA, tag creation,
main synchronization, push, and remote verification have not occurred.

## 8. Source identity

- Baseline: `93e4c0ab326e5eaf2fb6051c241fc5c76072afe9`
- Scope: `docs/development/V3_1_3_Repository_Architecture_Scope.md`
- Architecture map: `docs/architecture/Repository_Architecture_Map_V3_1_3.md`
- Development report: `docs/development/Development_Report_V3_1_3.md`
- Release notes: `docs/release/Release_Notes_V3_1_3.md`
- Release commit/tag: `NOT YET CREATED`
