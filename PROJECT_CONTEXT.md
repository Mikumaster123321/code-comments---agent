# Project Context

<!-- release-state: V3.1.4 IMPLEMENTATION COMPLETE / AWAITING FINAL QA -->

## Current State

- Current version: `3.1.4`
- Lifecycle: `RELEASE_CANDIDATE / AWAITING FINAL QA`
- Development branch: `v3.1.4-dev`
- Authoritative main baseline / branch point:
  `7f6ac6ffe20991d47f094d271213f1d57d3c5efd`
- Scope Freeze commit: `47ee7d7`
- P0 credential commit: `37905ac`
- Runtime/reliability implementation commit: `593109d`
- V3.1.0 / V3.1.1 / V3.1.2 / V3.1.3:
  `RELEASED + DOCUMENTATION CLOSED`
- V3.2: `NOT STARTED`
- Tag created for V3.1.4: `NO`
- Push performed for V3.1.4: `NO`
- Final QA evidence: `NOT YET EXECUTED`; expected path
  `docs/qa/V3_1_4_Final_Release_QA.md`

V3.1.4 is the final reliability, maintainability, failure-handling, resource-lifecycle,
and compatibility stabilization version before V3.2. Its seven frozen work items are
defined by the
[V3.1.4 Scope Freeze](docs/development/V3_1_4_Reliability_Stabilization_Scope.md).

The pre-V3.1.3 long-form historical context remains available in
[PROJECT_CONTEXT History Through V3.1.2](docs/development/PROJECT_CONTEXT_History_Through_V3_1_2.md).
Versioned V3.1.3 records remain historical release evidence and were not rewritten.

## Current Architecture and Reliability Boundary

- `main.py`: Gradio entrypoint.
- `ui.py`: UI construction/callbacks and compatible `CUSTOM_CSS` re-export.
- `processor.py`: compatible single/progress/batch tuples, cancellation, intake,
  archive, temporary-resource, diff, and analysis coordination.
- `config.py`: Provider registry and lazy, atomic active-provider construction.
- `llm_provider.py`: stable model/credential/provider values.
- `llm_service.py`: one-attempt generation, bounded preflight, safe output cleanup,
  and redacted diagnostics.
- `code_comments_agent/ui_styles.py`: CSS owner.
- `code_comments_agent/workspace.py`: workspace v1 persistence and atomic recovery.
- `code_comments_agent/reliability.py`: internal runtime/resource limits, attempt
  constants, operation IDs, timers, and diagnostic allow-list.
- `code_maintenance/`: stable maintenance domain/adapters, version `3.1.4`.
- `project_intelligence/`: released retrieval/index/context behavior, frozen here.

See the
[runtime/reliability contract](docs/architecture/V3_1_4_Runtime_Reliability_Contract.md)
and
[Pre-V3.2 compatibility contract](docs/architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md).

## Active V3.1.4 Contracts

- Credential precedence: explicit current-provider UI key, provider-specific env, then
  unconfigured. No cross-provider inheritance. `OPENAI_API_KEY` is OpenAI/Custom only.
- Provider switching: build complete candidate first; failure preserves prior coherent
  state.
- Startup: imports construct no Provider client, send no request, and do not load E5.
- Generation: one application × one transport attempt; SDK `max_retries=0`; explicit
  90-second default timeout.
- Preflight: one one-token request, default six-second timeout, no retry.
- Cancellation: cancel pending work, stop new stages, wait for in-flight calls, then
  `Cancelled`; immediate network/token termination is not promised.
- Intake: 2 MiB source, 25 MiB upload, 200 files, 1,000 ZIP members, 100 MiB
  uncompressed, 100:1 ratio; retrieval budgets are unchanged.
- Batch: all-symbol failure is `FAILED`; partial/cancelled useful results are explicit
  internally while public tuples remain compatible.
- Diagnostics: allow-listed operation/stage/provider/model/attempt/duration/category;
  no credential, prompt, source, raw response, reasoning, or user-visible absolute path.
- Workspace: v1 persists `output_lang` and `rewrite_existing`; unknown future version
  fails closed; failed save removes `.tmp`.
- Threat model: localhost, single-user, desktop style; not multi-tenant.

## Runtime Support

- CPython 3.10: `SUPPORTED / RECOMMENDED`;
- CPython 3.11: `BEST-EFFORT / UNVERIFIED`;
- CPython 3.12: `BEST-EFFORT CORE`; E5 evidence is not UI certification;
- standard CPython 3.13: `BEST-EFFORT / UNVERIFIED UI`;
- Anaconda Python 3.13.5: `UNSUPPORTED FOR UI / BARE PYTEST` on the known host;
- Ubuntu + CPython 3.10: supported CI evidence;
- Windows: best-effort unless separately tested.

Implementation host: Anaconda Python 3.13.5, Gradio 6.27.0, OpenAI SDK 1.109.1,
pytest 8.3.4. No local CPython 3.10 interpreter was available, so current-version
`create_ui()` smoke remains required in CI/Final QA and is not marked PASS here.

## Compatibility and Non-Goals

Provider IDs/default models, Processor/batch tuple shapes, progress frames,
`CancelToken`, root workspace helpers, `ui.CUSTOM_CSS`, valid downloads/ZIP naming,
code-maintenance public values, Project Intelligence facades, and release schema v2
remain compatible.

No Agent, Planner, Critic, Router, Memory, Tool, Orchestrator, multi-tenant session
architecture, dependency container, config rewrite, retrieval change, or new research
claim was introduced. V3.2 is `NOT STARTED`.

## Release Source of Truth

Machine-readable current state is Git objects plus
`docs/release/release_state.json`. Human current summaries are README, this file, and
`docs/release/README.md`. V3.1.4 preserves the v2 C1/annotated-tag/C2 architecture but
has not executed that release sequence. Final QA evidence is required and absent by
design; release-check therefore fails closed until the real report exists.

`docs/thesis/` is user-protected. It was not read, listed, searched, modified, moved,
staged, or deleted; only its untracked status was observed through `git status`.

## Frozen Formal Identity

- execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`;
- artifact-set identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`;
- artifact-set SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`.

BM25, E5, Graph, Hybrid/RRF, ContextBuilder, ranking, dataset, protocol, schemas,
artifacts, metrics, and Formal results are unchanged.

## Verification State

- P0 Provider foundation: `33 passed`;
- V3.1.4 reliability: `28 passed`;
- related targeted: `98 passed`;
- LLM: `6 passed`;
- production: `198 passed`;
- experiments: `240 passed`;
- release/architecture: `24 passed`;
- full: `1010 passed` (baseline 968);
- archive validator and four deterministic Formal CSV checks: PASS;
- CPython 3.10 UI smoke: `NOT EXECUTED / REQUIRED IN FINAL QA`.

## Authoritative Navigation

- [Documentation index](docs/README.md)
- [Development index](docs/development/README.md)
- [QA index](docs/qa/README.md)
- [Release index](docs/release/README.md)
- [Scope Freeze](docs/development/V3_1_4_Reliability_Stabilization_Scope.md)
- [Development Report](docs/development/Development_Report_V3_1_4.md)
- [Machine-readable release state](docs/release/release_state.json)

## Immediate Roadmap

1. DeepSeek Final QA executes targeted/full checks and CPython 3.10 Gradio build smoke.
2. Only a real PASS evidence file can authorize the separate C1/tag/C2 release flow.
3. No tag or push occurs in the implementation phase.
4. V3.2 remains `NOT STARTED` until separately scoped and authorized.
