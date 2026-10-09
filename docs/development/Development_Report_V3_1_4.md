# V3.1.4 Development Report

Status: `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`

## 1. Authority and audit

- authoritative main / branch point:
  `7f6ac6ffe20991d47f094d271213f1d57d3c5efd`;
- development branch: `v3.1.4-dev`;
- initial regression authority: `968 passed`;
- local bare-pytest observation: Anaconda Python 3.13.5 SIGSEGV in pytest debugging
  plugin / `rlcompleter` initialization;
- first implementation gate: `P0-CRED-01 Provider credential crossover`;
- scope authority:
  `docs/development/V3_1_4_Reliability_Stabilization_Scope.md`.

The scope document was committed before executable changes. Retrieval, Formal,
release-schema architecture, and `docs/thesis/` remained outside implementation.

## 2. V314-CRED-01 — CLOSED

The previous scalar active API key was inherited while selecting a new Provider when
the UI sent no key. Vendor metadata also allowed `OPENAI_API_KEY` to fall through into
DeepSeek, Azure, DashScope, and Moonshot.

The fix resets the candidate runtime key when Provider identity changes. The candidate
then uses its own explicit UI value, its provider-specific environment variable, or an
unconfigured placeholder required only to construct the offline OpenAI-compatible
client. `OPENAI_API_KEY` remains available to OpenAI and Custom only. Candidate
provider/client creation completes before active state is committed; construction
failure retains the prior state.

The offline matrix covers DeepSeek to Custom, OpenAI to DeepSeek, Custom to OpenAI,
provider-specific env, generic OpenAI env, explicit override, empty credential, and
construction failure. P0 targeted result: `33 passed`.

## 3. V314-RUNTIME-02 — COMPLETE

The runtime matrix is tracked in the runtime contract and README. CPython 3.10 is
supported/recommended. Later CPython versions and Windows are explicitly best-effort,
and the known Anaconda 3.13.5 UI/bare-pytest host is unsupported. The historical
CPython 3.12 E5 evidence is not presented as UI certification.

`config` no longer constructs a default client at import. Imports of `config`,
`processor`, and `project_intelligence` are network-free and do not load Gradio or E5.
Doctor reports optional `pycodestyle` availability and the active basic-lint fallback.
No dependency was broadly upgraded or exact-pinned. Implementation-host versions were
Python 3.13.5 (Anaconda), Gradio 6.27.0, OpenAI SDK 1.109.1, pytest 8.3.4.

CI remains Ubuntu/CPython 3.10 and adds named import/lazy-startup and `create_ui()`
build smokes before the full offline suite. It needs no secret.

## 4. V314-NET-03 — COMPLETE

Application generation attempts: `1`. Transport attempts per application attempt:
`1`. OpenAI-compatible SDK `max_retries`: `0`. The previous implicit application plus
SDK retry multiplication is removed.

Normal generation uses the client's explicit 90-second timeout. Preflight is a single
one-token request with a six-second request timeout. `javac` has a 15-second local
operation timeout. Authentication, permission, invalid request/model, configuration,
not-found, rate-limit, timeout, connection, response loss, and unexpected generation
failures receive no automatic second request. Ambiguous post-send failure is returned
to the user because a transparent retry could duplicate Provider cost. Managed Access
retry behavior was kept unchanged.

## 5. V314-CANCEL-04 — COMPLETE

The state contract is `Cancellation requested -> queued work cancelled -> in-flight
blocking calls finish -> Cancelled`. Executor shutdown cancels pending futures and
waits for already-running calls. The processor checks cancellation before further
translation, insertion, file, and batch stages. Completed partial results remain
available. UI status and README no longer describe cancellation as Idle or promise
immediate remote termination/token savings.

Known limitation: an SDK/HTTP call already running cannot be forcefully interrupted by
this application and may still incur Provider cost.

## 6. V314-RESOURCE-05 — COMPLETE

Central runtime defaults are 2 MiB single source, 25 MiB upload, 200 batch files,
1,000 ZIP members, 100 MiB aggregate uncompressed ZIP data, and 100:1 per-member
compression ratio. ZIP traversal/absolute paths, symlinks, member count, total size,
and ratio have stable rejection codes; nested ZIP contents are not recursively
processed.

Internal `BatchFileOutcome` distinguishes `SUCCEEDED`,
`SUCCEEDED_WITH_PARTIAL_SYMBOL_FAILURES`, `FAILED`, and
`CANCELLED_WITH_RESULTS`. Public tuple shapes are unchanged. An all-symbol failure now
increments failure, does not write an empty annotated file, and cannot produce a
normal success ZIP by itself.

Single-file final downloads remain UI/OS-temp owned. Batch consumes and deletes the
otherwise ignored per-file Markdown/source downloads. Batch staging, lint and javac
temps are helper-owned and cleaned. A failed partial ZIP is deleted. The returned final
ZIP remains valid for UI download and follows the OS temporary lifecycle. Workspace
atomic save cleans `.tmp` after failure.

## 7. V314-DIAG-06 — COMPLETE

`code_comments_agent.reliability` provides an opaque local operation ID, monotonic
duration, and stdlib logging allow-list. Allowed fields are operation/stage,
Provider/model IDs, attempt, duration, and stable error category. Credentials, full
prompts, source, raw responses, reasoning, and user-visible absolute paths are not
accepted by the logger. `javac` output replaces its temporary path with a stable
placeholder.

Workspace schema v1 now persists `output_lang` and `rewrite_existing`. A known version
loads; an unknown future version fails closed. The deployment threat model remains
localhost/single-user desktop style with process-global Provider state and one
OS-user workspace; this is not a multi-tenant claim.

## 8. V314-API-07 — COMPLETE

The tracked contract is
`docs/architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md`. Stable surfaces include
Provider IDs and task-scoped Provider values, code-maintenance domain/adapters, and
the Project Intelligence retrieval/context facade. Legacy-compatible surfaces include
Processor and progress tuples, batch tuples, `CancelToken`, workspace helpers,
`ui.CUSTOM_CSS`, and config globals. Internal implementation and operational tooling
are distinguished from Frozen-Formal surfaces. No future Agent API was created.

## 9. Test evidence

| Gate | Result |
|---|---:|
| P0 Provider foundation | `33 passed` |
| V3.1.4 reliability | `28 passed` |
| related targeted | `98 passed` |
| LLM contracts | `6 passed` |
| production | `198 passed` |
| experiments | `240 passed` |
| release/architecture | `24 passed` |
| full | `1010 passed in 331.73s` |
| archive-v3.1.0 validator | PASS |
| deterministic Formal CSV checks | 4/4 PASS |

Bare `python -m pytest` on the current Anaconda host still terminates before collection
in the debugging plugin. The developer command hub's previously documented local
`-p no:debugging` workaround produced the results above without changing test
semantics.

No CPython 3.10 interpreter is installed on the implementation host. CPython 3.10
Gradio `create_ui()` smoke is `NOT EXECUTED / REQUIRED IN CI AND FINAL QA`; no
historical result is reused as a current PASS.

## 10. Formal immutability

- execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`;
- artifact identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`;
- artifact SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`.

Archive reload and all deterministic CSV checks passed. No Formal file or behavior was
changed.

## 11. Release and known limitations

Release schema v2 and C1/tag/C2 design remain unchanged. Machine state is
`RELEASE_CANDIDATE`; the expected Final QA path is
`docs/qa/V3_1_4_Final_Release_QA.md`, which is intentionally absent until DeepSeek
Final QA executes. No tag or push occurred.

Known limitations: cooperative rather than forceful HTTP cancellation; final download
lifetime delegated to OS temporary storage; no multi-tenant session isolation; later
CPython/Windows runtimes are best-effort; no production SLA, uptime, latency, or
statistical reliability claim. V3.2 remains not started.
