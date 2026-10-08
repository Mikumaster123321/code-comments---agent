# V3.1.2 Release Notes

<!-- release-state: V3.1.2 RELEASE_CANDIDATE -->

**Status:** Release Candidate / Pre-Release

**Version:** `3.1.2`

**Theme:** Language / UX / Output Quality

**Branch:** `v3.1.2-dev`

**Tag / remote publication:** Not created / not published

V3.1.2 is an implementation-complete maintenance candidate awaiting independent Final Release QA. It improves the existing Gradio comment-generation experience without changing retrieval, ranking, Formal artifacts or research claims.

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

The current Anaconda Python 3.13.5 host terminates during Gradio import through IPython/rlcompleter. `create_ui` smoke is therefore **HOST LIMITATION**, not PASS and not an observed business-code regression. Final QA should repeat the Gradio build smoke in CPython 3.10.

## Formal boundary

Execution revision `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`, artifact identity `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`, and SHA-256 `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` are unchanged. Retrieval ranking impact and Formal result impact are both NO.

## Release gate

This file intentionally does not claim RELEASED. Remaining steps are independent Final Release QA, reviewed release commit, annotated `v3.1.2` tag, main sync, GitHub/Gitee branch and tag publication, and remote verification. V3.2 remains NOT STARTED.
