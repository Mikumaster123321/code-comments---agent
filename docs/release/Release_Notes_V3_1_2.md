# V3.1.2 Release Notes

<!-- release-state: V3.1.2 RELEASED -->

**Status:** Released

**Version:** `3.1.2`

**Theme:** Language / UX / Output Quality

**Branch:** `v3.1.2-dev`

**Annotated tag:** `v3.1.2`（指向 release commit）

**Remote publication:** Pending（本轮仅本地 finalize）

V3.1.2 is a maintenance release that improves the existing Gradio comment-generation experience without changing retrieval, ranking, Formal artifacts or research claims.

## Highlights

- Independent UI Language and Output Language, with Programming Language remaining separate
- Task-first layout, collapsed advanced Provider settings and language-relevant style controls
- Explicit Idle / Running / Success / Failure states and safe failed-run output clearing
- Provider settings-applied versus connectivity-verified semantics
- Local validation before any Provider ping
- Stable three-language user errors without raw provider payload, traceback, secret or local path
- Localized Python/Java API docs, Diff, analysis, status and empty states
- Restored Gradio Code Copy control
- Frozen prompt data boundary and target-language rules
- Translation-only versus translation-plus-style-rewrite selector
- Java minimal mode aligned to short Javadoc
- Strict response cleanup and 29 new offline contract tests

## Compatibility

Processor tuple shapes, existing default values, Provider/Model IDs, registry/routing, BYOK, Python/Java support, downloads, batch behavior, ZIP naming, workspace persistence and Markdown anchors remain supported. New public arguments are optional and default to prior rewrite behavior.

## Tests

- targeted V3.1.2 plus LLM contracts: 35 passed
- LLM profile: 6 passed
- production: 198 passed
- experiments: 240 passed
- full: 951 passed

No real Provider, real API key or model download was used.

## Host limitation

The Anaconda Python 3.13.5 host terminates during Gradio import through IPython/rlcompleter; that environment is recorded as **HOST LIMITATION**, not an observed business-code regression. Independent Final Release QA executed `create_ui` under CPython 3.10.20 with gradio 6.27.0, where the Gradio build smoke **PASSED** (`Blocks`, 106 blocks).

## Formal boundary

Execution revision `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`, artifact identity `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`, and SHA-256 `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` are unchanged. Retrieval ranking impact and Formal result impact are both NO.

## Release gate

V3.1.2 has passed independent Final Release QA. The reviewed release commit, annotated `v3.1.2` tag, main sync and GitHub/Gitee branch and tag publication are recorded with remote verification Pending（本轮仅本地 finalize）. V3.2 remains NOT STARTED.
