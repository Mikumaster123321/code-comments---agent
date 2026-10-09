# V3.1.4 Reliability / Maintainability / Pre-V3.2 Stabilization Scope Freeze

发布门禁：V3.1.4 `IMPLEMENTATION / PRE-RELEASE`

## 1. Authority and status

- Version: `3.1.4`
- Status: `SCOPE FROZEN / IMPLEMENTATION AUTHORIZED / NOT RELEASED`
- Authoritative baseline and branch point:
  `7f6ac6ffe20991d47f094d271213f1d57d3c5efd`
- Development branch: `v3.1.4-dev`
- Baseline regression authority: `968 passed`
- Local host observation: bare `python -m pytest` on Anaconda Python 3.13.5
  terminates in pytest debugging-plugin initialization while importing
  `rlcompleter`; this host/runtime combination is not a supported UI or bare-pytest
  environment.
- P0: `P0-CRED-01 Provider credential crossover`
- V3.1.0 / V3.1.1 / V3.1.2 / V3.1.3:
  `RELEASED + DOCUMENTATION CLOSED`
- V3.2: `NOT STARTED`

This tracked document is the Source of Truth for V3.1.4 implementation scope. Chat
history does not extend it. V3.1.4 is the final reliability and compatibility
stabilization release before V3.2 Multi-Agent Collaboration. It does not introduce an
Agent API or create new retrieval-research evidence.

## 2. Frozen seven-item scope

### V314-CRED-01 — Provider-scoped credential ownership (`P0`, production-sensitive)

Credential selection belongs to the provider being constructed. Precedence is:

1. non-empty explicit UI credential for the **current candidate provider**;
2. that provider's specific environment credential;
3. no credential.

An empty UI value never inherits the previous active provider's runtime credential.
DeepSeek, Azure, Alibaba, Kimi, and OpenAI credentials are not shared with another
vendor. `OPENAI_API_KEY` may be a documented generic fallback only for the OpenAI and
Custom/OpenAI-compatible contracts; it is not a fallback for other vendors. Empty
values are treated as absent.

Provider switching is atomic. A fully valid candidate provider is constructed before
active state is committed. Construction failure preserves the previous coherent
active state; the implementation must never expose provider B with provider A's key.
Provider registry IDs, model IDs, and the BYOK product model remain unchanged.

Offline stub/factory tests must cover DeepSeek to Custom with an empty key, OpenAI to
DeepSeek with an empty key, Custom to OpenAI, provider-specific environment values,
the allowed generic OpenAI fallback, explicit UI override, an empty current-provider
credential, and construction failure. Tests assert the exact credential passed to
the client factory and make no real request.

This P0 is the first implementation gate. Its targeted tests must pass and its fix
must be committed independently before work continues on the remaining items.

### V314-RUNTIME-02 — Supported runtime, startup, dependency, and CI contract

The tracked support matrix is:

| Runtime / platform | V3.1.4 status |
|---|---|
| CPython 3.10 | `SUPPORTED / RECOMMENDED` |
| CPython 3.11 | `BEST-EFFORT / UNVERIFIED` |
| CPython 3.12 | `BEST-EFFORT CORE`; historical E5 evidence is not full UI certification |
| Standard CPython 3.13 | `BEST-EFFORT / UNVERIFIED UI` |
| Anaconda Python 3.13.5 | `UNSUPPORTED FOR UI / BARE PYTEST` on the known host because of a reproducible SIGSEGV |
| Ubuntu + CPython 3.10 | `SUPPORTED CI EVIDENCE` |
| macOS + CPython 3.10 | `SUPPORTED RELEASE-QA EVIDENCE` when the required smoke passes |
| Windows | `BEST-EFFORT` unless separately tested |

Importing `config.py`, `processor.py`, or `project_intelligence` must not make a
network request. Default Provider/client creation moves behind an explicit or lazy,
dependency-injection-friendly boundary. App startup must not load E5. E5 and Gradio
remain optional at their existing boundaries, and `javac` retains graceful
degradation. `pycodestyle` availability is reported by doctor/runtime diagnostics so
its user-visible effect is not a silent environment difference; it is not forced into
the core dependency set without demonstrated need.

Dependencies are not broadly upgraded or exact-pinned. Release QA records the tested
Python patch, Gradio, OpenAI SDK, and other material dependency versions. CI remains a
small Ubuntu/CPython 3.10 job with clear full-test, import/startup, and `create_ui()`
smoke steps; it uses no secret or real Provider request and does not globally disable
a debugging plugin because of the Anaconda host defect.

### V314-NET-03 — Explicit timeout and single-owner retry (`production-sensitive`)

Application code owns the retry decision; the SDK/transport retry count is explicitly
zero wherever application retry is available. Code and tests must state the maximum
application attempts and maximum transport attempts, preventing implicit multiplication
such as `3 x 3 = 9`.

Authentication, permission, bad request, invalid input, invalid model, not-found or
configuration failures, and prompt/validation errors receive no automatic retry.
Only contractually classified transient connection-establishment failures, HTTP 429,
and selected 5xx responses may receive a bounded retry when duplicate-cost risk is
acceptable. Broad `Exception` or broad `APIError` retry is forbidden.

Read timeout, response loss, and a reset after a request may have been sent are
ambiguous-cost failures. They do not transparently issue a second generation request;
the user receives a stable retryable error and decides whether to run again. Managed
Access retains its existing conservative no-automatic-Provider-retry behavior unless
a real failing test proves otherwise.

Tests assert exact client call counts. The operation contracts are:

| Operation | Timeout owner / semantics | Retry contract |
|---|---|---|
| preflight / ping | application supplies short bounded connect/read limits; request is low-cost and non-generative | at most one application attempt; zero SDK retries |
| normal generation | application supplies an explicit bounded request timeout instead of inheriting the SDK 600-second default | bounded classified retry only before send can be established; ambiguous post-send failures are not retried |
| Managed Access | existing service/provider boundary | keep current no automatic Provider retry |
| `javac` | subprocess operation timeout | no network retry |
| developer probes | command-specific bounded timeout | no Provider request unless explicitly named and stubbed in tests |

Exact numeric defaults are centralized and documented after auditing current product
operations; they are not presented as universally optimal values.

### V314-CANCEL-04 — Cancellation state and cost contract (`production-sensitive`)

Cancellation is cooperative and best-effort:

`Cancellation requested -> current blocking operation finishing -> Cancelled`.

The system stops submitting new work, cancels futures that have not started, observes
cancellation before the next stage, and allows an already running blocking SDK call to
finish when the SDK cannot safely interrupt it. Final state is `Cancelled`, never
`Idle`. Completed usable partial results may be retained according to the existing
product contract. UI and documentation must not promise immediate interruption or
immediate token/cost savings: a request already accepted by a Provider may continue
and may still incur cost. Provider SDK internals are not modified.

### V314-RESOURCE-05 — Intake, archive, batch, and temporary-resource reliability (`production-sensitive`)

This item covers only runtime/user intake, ZIP/archive handling, batch processing,
temporary downloads, and temporary lifecycle. It does not change ContextBuilder
budgets, retrieval `top_k`, Graph expansion, or Formal experiment limits.

Conservative defaults for single-source bytes, upload bytes, batch file count, ZIP
member count, aggregate uncompressed bytes, compression ratio, and any necessary
source/prompt preflight are centralized, configurable, documented, and derived from
current product use and memory/UX constraints. Rejections use stable reasons.

Existing zip-slip, absolute-path, parent-traversal, and nested-archive defenses remain.
ZIP symlinks are rejected; count, total-uncompressed-size, and compression-ratio limits
are enforced without materializing an archive bomb. Tests use small constructed
fixtures.

An internal typed outcome or equivalent explicit state distinguishes `SUCCEEDED`,
`SUCCEEDED_WITH_PARTIAL_SYMBOL_FAILURES`, `FAILED`, and, where existing behavior needs
it, `CANCELLED_WITH_RESULTS`. Public `process_code`, progress-frame, and batch tuple
shapes remain compatible. A file whose only/all symbols fail is not counted as fully
successful and is not packaged as a normal zero-byte annotated source. Partial counts,
failure reasons, and ZIP contents remain accurate.

Temporary ownership is explicit for single-source and Markdown downloads, batch
intermediates and staging directories, final and partial ZIPs, `javac`, lint,
workspace `.tmp`, and failure cleanup. Batch must clean ignored per-file download
temps created by `process_code()`. Final files returned to the UI remain valid after
the callback; their final lifecycle may remain the OS temp lifecycle for V3.1.4.
Intermediate, failed, abandoned, and partial-package resources are cleaned. Workspace
atomic `tmp + os.replace` remains, with `.tmp` cleanup on failure.

### V314-DIAG-06 — Structured local diagnostics and workspace recovery

Diagnostics use Python stdlib logging or the existing lightweight mechanism only. No
Sentry, OpenTelemetry backend, cloud logging, or analytics is introduced. Allowed
structured fields are opaque local `operation_id`, stage, provider/model IDs, attempt,
duration, and stable error category. API keys, credentials, full prompts, source code,
raw Provider responses, private reasoning, and user-visible absolute local paths are
never logged. Developer-only path detail, when necessary, remains separated from the
user-visible log and contains no secret. Operation IDs correlate preflight, generation,
batch, package, and failure only; they do not become agent tracing.

User-facing `javac` output removes temporary absolute paths while retaining a stable,
actionable reason. Workspace persistence includes the existing UI fields
`output_lang` and `rewrite_existing`. Known schema versions load; unknown future
versions fail closed with a stable explanation. No migration framework is added.

The current threat model is a localhost, single-user, desktop-style application, not a
multi-tenant web service. Process-global Provider settings and a shared per-OS-user
workspace remain acceptable under that model and are documented; V3.1.4 does not
rewrite the application into session-isolated multi-tenancy.

### V314-API-07 — Pre-V3.2 compatibility contract

Create
`docs/architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md` from actual references.
It classifies surfaces as `STABLE`, `LEGACY-COMPAT`, `INTERNAL`,
`EXPERIMENTAL / OPERATIONAL`, or `FROZEN-FORMAL`.

Candidate stable surfaces to verify include Provider registry IDs, `ModelConfig`,
`RuntimeCredential`, `TaskScopedLLMProvider`, public `code_maintenance` domain and
adapter contracts, `RetrievalService`, `RetrievalQuery`, `ContextPackage`, and project
domain representation. Candidate legacy-compatible surfaces include
`processor.process_code()` tuple shape, progress frames, batch tuple, `CancelToken`,
root workspace helpers, `ui.CUSTOM_CSS`, and legacy `config` globals. Compatibility
protects the public behavior without promising internal implementation permanence.

No `Agent`, `Planner`, `Critic`, `Router`, `Memory`, `AgentContext`, `AgentTool`, or
`Orchestrator` interface is created. This item records existing reusable capability;
it does not pre-design V3.2.

## 3. Backward compatibility and intentional behavior changes

V3.1.4 preserves Provider IDs and default models, Processor public tuples, progress
frames, the batch public tuple, workspace public signatures, `ui.CUSTOM_CSS`, valid
downloads and ZIP naming, Project Intelligence public contracts, the V3.1.3 release
schema v2/C1-tag-C2 architecture, and Formal identity.

The only intentional user-visible changes are: no cross-provider credential
inheritance; no retry of non-transient or ambiguous-cost requests; explicit bounded
timeouts; truthful cooperative-cancellation state/cost wording; rejection of oversized
or dangerous intake; accurate all-failed/partial batch classification; and
`Cancelled != Idle`. V314-CRED-01, V314-NET-03, V314-CANCEL-04, and V314-RESOURCE-05
are therefore production-behavior-sensitive, not pure refactors.

## 4. Formal and protected-path immutability

V3.1.4 does not change BM25, E5, Graph, Hybrid, RRF, ContextBuilder, retrieval ranking,
Formal dataset/protocol/artifacts/results, or experiment schemas.

- Formal execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- Formal artifact-set canonical identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Formal artifact-set file SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

These are `FROZEN-FORMAL` surfaces. V3.2 may not casually modify them.

`docs/thesis/` is user-protected: do not read, list, search, modify, move, stage, or
delete it. Only `git status` may observe its untouched/untracked state.

## 5. Verification contract

All new tests are offline and use mocks, stubs, subprocesses, or temporary directories.
They make no real Provider request, use no real credential, and do not materialize a
large archive bomb. Required coverage includes the credential crossover matrix,
credential environment precedence and switch atomicity; timeout/retry exception and
exact-attempt matrices; cancellation transitions and pending-future cancellation;
batch success/partial/all-failed/cancelled outcomes; temp and partial-ZIP cleanup;
ZIP count/size/ratio/symlink guards; workspace fields/version/temp cleanup; diagnostic
redaction/operation ID/`javac` path redaction; compatibility surfaces; import/startup;
and CI UI smoke.

Required validation is:

1. targeted V3.1.4 tests, with the credential P0 gate first;
2. `python scripts/dev.py test llm`;
3. `python scripts/dev.py test production`;
4. `python scripts/dev.py test experiments`;
5. `python scripts/dev.py test release`;
6. `python scripts/dev.py test full`, with at least 968 tests and zero unexpected
   failures;
7. `python scripts/dev.py experiment-validate archive-v3.1.0`;
8. deterministic Formal CSV checks and immutable revision/identity/SHA verification;
9. CPython 3.10 `import gradio` plus `create_ui()` smoke, recording the Python patch,
   Gradio version, and block-build result.

No test is deleted, broadly skipped, or weakened to satisfy the change.

## 6. Documentation and release boundary

Before independent Final QA, update README and Version History, runtime/reliability
contracts, the Pre-V3.2 Compatibility Contract, Markdown and independently readable
UTF-8 TXT Thesis Materials, Development Report, Release Notes, `PROJECT_CONTEXT.md`,
and documentation indexes. The Release Notes and current summaries may state only
`IMPLEMENTATION COMPLETE / AWAITING FINAL QA`, never `RELEASED`.

The expected independent evidence path is
`docs/qa/V3_1_4_Final_Release_QA.md`. This implementation does not fabricate that file
or claim a PASS. The V3.1.3 release architecture remains unchanged. This phase creates
local logical commits only: no tag, no push, and no formal desktop thesis-material
copy.

## 7. V3.2 non-goals

V3.2 is `NOT STARTED`. V3.1.4 does not add Multi-Agent collaboration, Agent routing,
planning, criticism, memory, tools, orchestration, multi-tenant sessions, a dependency
container, a config-system rewrite, large module migration, tree-sitter, ANTLR,
JavaParser, or new `rag`, `agents`, `router`, `api`, or `vscode` modules. It does not
expand this seven-item scope or convert maintenance evidence into claims of production
SLA, uptime, statistical reliability, or latency improvement.
