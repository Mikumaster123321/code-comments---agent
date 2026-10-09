# V3.1.4 Release Notes

Status: **RELEASE CANDIDATE / AWAITING FINAL QA**

V3.1.4 is the final reliability and maintainability stabilization version before the
planned V3.2 Multi-Agent Collaboration phase. It is not released, has no tag, and has
not been pushed by this implementation task.

## Highlights

- closes P0 Provider credential crossover with provider-scoped precedence and atomic
  switching;
- limits `OPENAI_API_KEY` fallback to OpenAI and Custom/OpenAI-compatible providers;
- lazily constructs Provider clients and keeps startup/import network-free;
- disables SDK retries and makes generation one application/transport attempt with an
  explicit timeout;
- avoids automatic duplicate-cost generation after ambiguous failures;
- reports cooperative cancellation as `Cancelled` after in-flight calls finish;
- adds centralized source/upload/batch/ZIP count, size, ratio, traversal, and symlink
  guards;
- correctly classifies all-failed and partial batch files and cleans batch-owned
  intermediates/failed partial packages;
- adds redacted structured local diagnostics and `javac` path sanitization;
- preserves workspace output language/rewrite state and rejects unknown future
  workspace versions;
- records the Pre-V3.2 stable, legacy-compatible, internal, operational, and
  Frozen-Formal interface boundary.

## Intentional behavior changes

These are production-behavior-sensitive reliability changes, not pure refactors:

1. an empty key on a cross-Provider switch no longer reuses the old Provider key;
2. generation failures are not automatically retried, including ambiguous timeouts;
3. normal generation no longer inherits the SDK's implicit long timeout/retry policy;
4. cancellation is cooperative and ends in `Cancelled`, not `Idle`;
5. oversized or dangerous intake is rejected with a stable reason;
6. an all-symbol-failed batch file is a failure and is not emitted as a normal empty
   result.

## Compatibility

Provider IDs/default models, Processor five-tuples, progress frames, batch two-tuples,
workspace public signatures, `CancelToken`, `ui.CUSTOM_CSS`, valid download/ZIP naming,
code-maintenance public values, Project Intelligence facades, and release schema v2
remain compatible. No Agent/Planner/Router/Memory API is introduced.

## Runtime support

CPython 3.10 is supported/recommended and remains the Ubuntu CI runtime. CPython 3.11,
3.12 core, standard 3.13 UI, and Windows are best-effort unless separately tested.
Anaconda Python 3.13.5 is unsupported for UI/bare pytest on the known host because of
the reproducible debugging/IPython `rlcompleter` SIGSEGV.

Tested implementation-host versions: Anaconda Python 3.13.5, Gradio 6.27.0, OpenAI SDK
1.109.1, pytest 8.3.4. The required CPython 3.10 `create_ui()` smoke could not run
locally because no 3.10 interpreter is installed; CI and independent Final QA must
record the actual Python patch, Gradio version, and build result.

## Verification

P0 Provider foundation `33 passed`; V3.1.4 reliability `28 passed`; related targeted
`98 passed`; LLM `6 passed`; production `198 passed`; experiments `240 passed`;
release `24 passed`; full `1010 passed`. Archive validator and four deterministic
Formal CSV checks passed.

Formal execution revision, artifact identity, and artifact SHA-256 remain:

- `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`;
- `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`;
- `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`.

## Remaining release gate

Independent DeepSeek Final QA is **NOT YET EXECUTED**. The expected evidence path is
`docs/qa/V3_1_4_Final_Release_QA.md`; this implementation does not create a placeholder
PASS. After actual Final QA, the separately authorized release flow may create C1,
annotated tag `v3.1.4`, C2 identity closure, and remote verification. Until then the
state remains `RELEASE_CANDIDATE / AWAITING FINAL QA`.
