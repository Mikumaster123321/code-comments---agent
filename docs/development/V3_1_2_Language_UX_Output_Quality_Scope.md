# V3.1.2 Language / UX / Output Quality Scope Freeze

发布门禁：V3.1.2 RELEASED

## 1. Authority and status

- Version: `3.1.2`
- Status: `SCOPE FROZEN / IMPLEMENTATION AUTHORIZED / NOT RELEASED`
- Authoritative baseline: `2036cb6c82860b9bf8229ecac0f4d4add420855d`
- Development branch: `v3.1.2-dev`
- Audit verdict: `READY FOR SCOPE FREEZE`
- Audit P0 findings: `0`
- Baseline regression: `922 passed`
- V3.1.0 and V3.1.1: `RELEASED + DOCUMENTATION CLOSED`
- V3.2: `NOT STARTED`

This document is the tracked Source of Truth for V3.1.2 implementation scope. Chat
history does not extend the scope. The release is an Engineering, UX/HCI, and output
quality maintenance release; it does not create a new retrieval-research result.

## 2. Frozen change items

### V312-UX-01 — Task-first information architecture

Reorder and progressively disclose the existing Gradio controls so input and primary
actions are clear. Provider settings may be collapsed as advanced configuration, only
the programming-language-relevant comment-style control should be visible, and the UI
must distinguish idle, running, success, failure, and cancellation states. Existing
callbacks, public Processor tuple shapes, downloads, batch processing, session
persistence, and defaults remain compatible.

### V312-LANG-02 — Separate UI language and output language

Create independent UI Language and Output Language state for 中文, English, and 日本語.
On first load Output Language defaults to the initial UI Language. A later UI Language
change must not modify Output Language or trigger translation/rewrite of existing
docstrings, Javadocs, or comments. Documentation presentation follows Output Language
in V3.1.2. Programming Language remains an independent Python/Java selection.

### V312-PROVIDER-03 — Provider and model setup clarity

Preserve Provider IDs, Model IDs, Registry, routing, and BYOK behavior. Distinguish
"settings applied" from "connectivity verified": client construction alone never
claims that the API key, endpoint, Provider, or Model works. Only a successful explicit
preflight/ping may claim verified connectivity. Help copy must explain required versus
optional inputs, environment fallback, Base URL constraints, Custom Provider behavior,
and Azure-specific requirements without translating vendor model identifiers.

### V312-ERR-04 — Safe user-facing errors and run states

Perform local empty-input, supported-language, and obvious parser validation before
network connectivity checks. Add a small, local, testable stable-error-code to
three-language message mapping. User messages state what happened, what to do next,
and whether retry is appropriate. They must not expose traceback, raw Provider payload,
system prompt, secret/API key, local absolute path, or internal exception chains.
Failed runs clear the current run outputs so prior successful results cannot appear to
belong to the failed run.

### V312-OUT-05 — Localized structured output formatters

Improve only current real surfaces: Annotated Code, Diff, API Documentation, Code
Analysis, logs/status, and summary. Localize headings and empty states, keep Markdown
hierarchy and fences correct, restore Gradio code-copy capability, and improve long
content readability. API documentation formatters accept presentation/output language
while retaining anchors, identity, signatures, types, and download compatibility.
No new review semantics, severity, location, recommendation, evidence, or Project
Intelligence fields may be invented.

### V312-PROMPT-06 — Prompt and output contract hardening

This item is `MODEL-BEHAVIOR-SENSITIVE`. No prompt change is allowed until
`docs/development/V3_1_2_Prompt_Output_Contract.md` is tracked and frozen. The contract
must inventory prompts and classify PURE-COPY, FORMAT-ONLY, and
MODEL-BEHAVIOR-SENSITIVE changes; define source-code data boundaries, target output
language, summary structure, existing-comment translation/rewrite behavior, Java
minimal-style behavior, allowed wrappers, forbidden output, mock cases, golden cases,
and the manual review matrix.

### V312-TEST-07 — UX and output contract test layer

Add offline tests for UI/output-language independence, three-language terminology,
formatters, Markdown fences, empty states, copy configuration, Provider status
semantics, validation-before-ping, safe errors, no-secret/no-absolute-path/no-traceback,
failed-run cleanup, prompt golden contracts, mock Provider output, and Python/Java
formatting. Tests must not use a paid Provider, real credential, network LLM request,
or model download.

## 3. Prompt-sensitive boundary

Prompt wording that changes model interpretation, content selection, translation,
rewriting, or response validity is not UX copy. V312-PROMPT-06 must therefore be
specified and reviewed independently before implementation. In particular:

- source code is delimited data to analyze/transform, never an instruction source;
- identifiers, API names, types, exception names, and library identifiers are not
  translated;
- summary length uses a language-neutral structural contract rather than `200字以内`;
- translation of existing comments and style rewrite are explicitly distinguished,
  with backward-compatible defaults;
- Java minimal style is frozen as **short Javadoc**, because the existing annotator
  always emits `/** ... */` and changing to `//` would alter the insertion pipeline;
- empty or structurally unsafe model output is rejected rather than silently accepted.

## 4. Non-goals and deferred work

The following are outside V3.1.2:

- retrieval, ranking, BM25, E5, graph expansion, Hybrid, RRF, ContextBuilder, dataset,
  Query, Ground Truth, Grade, RQ result, or Formal interpretation changes;
- a new Code Review, Optimization/Refactoring, Project Intelligence, Evidence, or
  Context Gradio engine/surface;
- invented analysis semantics or fields not produced by current underlying logic;
- package or repository restructuring, large directory changes, or documentation
  system reorganization (`DEFER-V3.1.3`);
- generalized reliability, retry/timeout architecture, production observability, or
  public API freeze (`DEFER-V3.1.4`);
- Multi-Agent collaboration, routing, or approval architecture (`DEFER-V3.2`);
- Playwright, Selenium, a large UI framework, or a complete i18n framework.

## 5. Formal and retrieval immutability

V3.1.2 has `Retrieval ranking impact: NO` and `Formal result impact: NO`.

- Formal execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- Formal artifact-set canonical identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Formal artifact-set file SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

These identities and all Formal artifacts are frozen. V3.1.2 must not claim retrieval
quality, RQ, statistical-significance, or user-satisfaction improvement without new,
separately authorized evidence.

## 6. Backward-compatibility contract

The implementation retains Processor public signatures and return tuple shapes,
Provider and Model IDs, Registry/routing and BYOK behavior, download formats, ZIP
naming values, Markdown anchors, Python/Java support, batch behavior, and Formal
identity. Any optional parameter receives a compatible default.

## 7. Test plan

Required validation is:

1. targeted V3.1.2 contract tests;
2. `python scripts/dev.py test llm`;
3. `python scripts/dev.py test production`;
4. `python scripts/dev.py test experiments`;
5. `python scripts/dev.py test full` with at least 922 tests and no unexpected failure;
6. `python scripts/dev.py release-check --version 3.1.2` in pre-release mode;
7. Formal artifact identity and file SHA-256 recheck;
8. Gradio `create_ui` smoke under recommended CPython 3.10 where available.

The known Anaconda Python 3.13.5 Gradio/IPython/`rlcompleter` SIGSEGV is recorded as a
host limitation, not fabricated as a passing business-code smoke.

## 8. Documentation and release requirements

Before V3.1.2 Final QA, tracked documentation must include README and Version History,
Markdown and independently readable UTF-8 TXT Thesis Materials, Development Report,
pre-release Release Notes, PROJECT_CONTEXT, and the documentation/release index. The
permanent contract in `docs/release/Version_Documentation_Contract.md` remains binding.

The implementation phase created no tag and performed no push. The subsequent formal
release added documentation consistency QA, independent Final Release QA, a reviewed
release commit and the annotated `v3.1.2` tag; GitHub/Gitee branch and tag publication
with remote target verification remain Pending（本轮仅本地 finalize）. The status is now
`RELEASED`; the earlier `IMPLEMENTATION COMPLETE / AWAITING FINAL RELEASE QA` ceiling is
satisfied.
