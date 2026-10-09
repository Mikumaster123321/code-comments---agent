# V3.1.3 Release Notes — Repository Architecture

Status: `RELEASED`

V3.1.3 is released. Independent Final Release QA executed and its real evidence at
`docs/qa/V3_1_3_Final_Release_QA.md` records `FINAL RELEASE QA: PASS`. The annotated
tag `v3.1.3` points to the reviewed release commit C1 (its exact SHA is recorded in
`release_state.json`). Main synchronization and GitHub/Gitee push with live remote
verification have completed.

## Highlights

- Added a non-self-referential v2 release-state schema and two-stage C1/C2 validator.
- Runtime validation accepts a later HEAD only when the tagged release commit is its
  ancestor.
- Optional remote validation checks GitHub and Gitee main/development branches against
  runtime HEAD and peeled tags against the release commit.
- Preserved V3.1.2 v1 release-state readability.
- Split current and historical project context without discarding the prior 1,809-line
  body.
- Extracted unchanged CSS and workspace persistence into a bounded internal package
  while keeping root imports compatible.
- Added repository architecture, documentation navigation, and executable
  compatibility gates.

## Compatibility

`main.py`, `ui.py`, and `processor.py` remain stable paths. Existing
`from ui import CUSTOM_CSS` and processor workspace imports continue to work. CSS,
workspace storage, Processor flows, UI callbacks, Provider behavior, Python/Java
support, downloads, and batch behavior are unchanged.

There is no dependency, packaging, workspace-format, storage-root, database, rename,
or deletion migration.

## Verification

- Architecture + release targeted: `24 passed`
- LLM contracts: `6 passed`
- Production: `198 passed`
- Experiments: `240 passed`
- Release profile: `24 passed`; final gate passed with real Final QA evidence
- Full regression: `968 passed`
- CPython 3.10.22 / Gradio 6.27.0 `create_ui()` build smoke: `PASS` (`Blocks`, 106 blocks)
- V3.1.0 archive validator and deterministic Formal CSV checks: `PASS`

The known Anaconda Python 3.13.5 pytest/Gradio import SIGSEGV remains a host
limitation; it is not represented as a passing application smoke.

## Frozen boundaries

Retrieval impact: `NONE`. Formal impact: `NONE`. LLM behavior impact: `NONE`.

Formal execution revision, artifact identity, and artifact file SHA-256 remain:

- `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

`docs/experiments/**` remains frozen. `docs/thesis/` remains user-protected and
untouched.

## Release gate

The Final QA evidence path is `docs/qa/V3_1_3_Final_Release_QA.md`. Independent Final
Release QA executed and its real evidence records `FINAL RELEASE QA: PASS`, satisfying
the permanent version documentation contract. The release advanced to `RELEASED` with
the reviewed release commit C1, the annotated tag `v3.1.3`, main synchronization,
dual-remote publication, and runtime remote verification completed.
