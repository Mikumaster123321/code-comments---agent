# V3.1.2 Development Report

<!-- release-state: V3.1.2 RELEASED -->

## 1. Summary

- **Version:** 3.1.2
- **Theme:** Language / UX / Output Quality
- **Status:** RELEASED
- **Branch / point:** `v3.1.2-dev` from `2036cb6c82860b9bf8229ecac0f4d4add420855d`
- **Scope Freeze:** `139833f`
- **Prompt Contract:** `2192293`, completed by `d12d800`
- **Tag / push:** `v3.1.2` / Pending（本轮仅本地 finalize）
- **V3.2:** NOT STARTED

V3.1.2 is an engineering, UX/HCI, and model-output-quality maintenance release. It does not alter retrieval or frozen Formal results.

## 2. Audit and frozen scope

The pre-implementation audit verdict was **READY FOR SCOPE FREEZE**, P0 = 0, baseline = 922 passed. The seven items V312-UX-01, LANG-02, PROVIDER-03, ERR-04, OUT-05, PROMPT-06, and TEST-07 were frozen before executable changes. Prompt behavior was separately frozen before prompt edits.

## 3. Implementation

- UI: independent Output Language, relevant style visibility, minimal rewrite checkbox, collapsed provider settings, run states, disabled idle Cancel, empty states, Copy restoration.
- Provider: applied versus verified status, help for required/optional key, environment fallback, Base URL, Azure and Custom behavior.
- Errors: local validation before ping, stable localized code mapping, safe UI messages, failed-run output clearing, raw exception removal from user-visible logs.
- Output: localized Python/Java API docs, Diff, Python quality/type analysis, style table headings, status and empty presentation.
- Prompt: stable source/doc delimiters, untrusted-data instruction, target language plus technical-name preservation, bounded language-neutral summary, translation/rewrite split, short-Javadoc contract.
- Cleanup: fail closed on empty, invalid fence, residual quote/comment wrapper, extra preface, traceback, secret-looking value, absolute path and control text.
- Workflow: release metadata finalized from 3.1.2 RELEASE_CANDIDATE to RELEASED; baseline tag is immutable V3.1.1.

## 4. UX/HCI contribution

The UI now separates three user intents that were previously conflated: interface comprehension, generated natural language, and parser language. State copy distinguishes configuration mutation from network evidence and distinguishes a failed current run from a previous success. Progressive disclosure and language-relevant controls reduce initial choice density without removing capability.

## 5. Backward compatibility

Processor return tuples remain five elements. New `rewrite_existing` arguments are optional trailing parameters with `True` defaults. Provider/model IDs, routing, BYOK, Python/Java parsing, downloads, batch ZIP naming, session persistence and Markdown anchors remain compatible. Documentation presentation now intentionally follows Output Language.

## 6. Test evidence

| Validation | Result |
| --- | ---: |
| Targeted V3.1.2 + LLM contracts | 35 passed |
| Processor/provider directed regression | 27 passed |
| LLM profile | 6 passed |
| Production profile | 198 passed |
| Experiments profile | 240 passed |
| Full profile | 951 passed |

No real provider request, real user key, or external model download occurred. The full count is above the 922 baseline with zero unexpected failures.

## 7. Prompt-sensitive changes

All prompt changes follow [V3_1_2_Prompt_Output_Contract.md](V3_1_2_Prompt_Output_Contract.md). Golden assertions check boundaries, language target, technical identifier preservation, summary structure, translation modes and Java minimal semantics. Mock outputs test valid wrappers and hostile/invalid response forms. Manual three-language review remains part of independent Final QA.

## 8. Formal immutability

- execution revision `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- artifact identity `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- file SHA-256 `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`
- retrieval/ranking impact: NONE
- Formal result impact: NONE

## 9. Known environment issue

On the current Anaconda Python 3.13.5 host, importing Gradio enters IPython/rlcompleter and terminates with SIGSEGV. This reproduces before UI construction and is recorded as **HOST LIMITATION**. Business-code compilation, source-level UI contracts and all 951 repository tests pass. Independent Final Release QA subsequently ran `create_ui` under CPython 3.10.20 with gradio 6.27.0, where the Gradio build smoke passed (`Blocks`, 106 blocks).

## 10. Release readiness

Implementation, independent Final Release QA and the documentation package are complete. The lifecycle is RELEASED with annotated tag `v3.1.2`. The reviewed release commit, main synchronization and GitHub/Gitee publication are recorded with remote target verification Pending（本轮仅本地 finalize）.
