# V3.0 Phase 4.1 — Provider / BYOK Foundation QA Report

## Final Verdict

**PASS**

The initial DeepSeek independent review returned **PASS WITH ISSUES**, with zero
Critical and one Medium finding. Phase 4.1.1 corrected the legacy Provider partial
commit defect in commit `f28e3dbad1a16a5d4ec32e95fdfea7c7f1fbfeb4`. The directed
retest passed every atomicity, concurrency, secret-safety, and BYOK regression probe.
Another retest is **Not Required**.

```text
Initial DeepSeek QA: PASS WITH ISSUES
    -> Critical: 0
    -> Medium: 1
    -> M1 legacy Provider atomicity
Phase 4.1.1 fix: f28e3dbad1a16a5d4ec32e95fdfea7c7f1fbfeb4
DeepSeek directed retest:
    -> switch_provider atomicity PASS
    -> set_api_key atomicity PASS
    -> set_custom_base_url atomicity PASS
    -> consecutive failure PASS
    -> failed switch -> new task PASS
    -> failure -> success PASS
    -> concurrency PASS
    -> secret safety PASS
    -> BYOK regression PASS
Final Verdict: PASS
```

## Review Scope

The QA cycle covered:

- `ModelConfig` immutability, normalization, deterministic equality, and safe ordinary
  serialization;
- `RuntimeCredential` runtime-only behavior, representation redaction, and
  non-serialization;
- `ProviderRegistry` metadata and explicit provider/client construction;
- Task A/B configuration, client, base-URL, and credential isolation;
- interleaved and concurrent task-scoped calls;
- retry isolation from mutable legacy active state;
- Processor entry-point capture and worker propagation;
- workspace credential exclusion;
- sanitized failure reporting;
- legacy Provider update success and failure atomicity;
- the `code_maintenance/` Provider/LLM/Credential-free dependency boundary;
- absence of Router, Agent, fallback, scoring, and real network behavior.

The review did not expand scope into secure credential storage, multi-user accounts,
Router policy, Provider additions, IDE integration, or RC1 implementation.

## Environment and Versions

| Item | Result |
|---|---|
| Branch | `v3.0.0-test1` |
| Initial Phase 4.1 implementation | `9f2d1517d9cfb72895cb322b2352fd0e2bb3ef12` |
| Phase 4.1.1 atomicity fix | `f28e3dbad1a16a5d4ec32e95fdfea7c7f1fbfeb4` |
| Initial Phase 4.1 tests | 13 passed |
| Initial full suite | 123 passed |
| Final Phase 4.1 tests | 19 passed |
| Final full suite | 129 passed |
| Offline LLM-contract smoke | 6 passed |
| Real network/provider calls | None |

Validation used `python -m pytest -p no:debugging`, consistent with the documented
Anaconda Python 3.13 debugging-plugin workaround. Project test configuration was not
changed.

## Initial QA

- Verdict: **PASS WITH ISSUES**;
- Critical: **0**;
- Medium: **1**;
- Required fix: **M1 — legacy Provider atomicity**.

The initial implementation otherwise satisfied the core BYOK policy and safety
requirements.

## Core BYOK Security Results

| Contract | Result |
|---|---|
| Credential leakage | **0** |
| Task A/B isolation | **PASS** |
| Retry isolation | **PASS** |
| Processor capture | **PASS** |
| Workspace persistence remains credential-free | **PASS** |
| `code_maintenance/` dependency boundary | **PASS** |
| No Router / Agent implementation | **PASS** |

The tests use obvious fake values only. No valid-looking credential, real provider
request, or network call is part of the QA evidence.

## M1 — Legacy Provider Atomicity

### Finding

`switch_provider()`, `set_api_key()`, and `set_custom_base_url()` could mutate active
scalar fields before `ModelConfig`, `TaskScopedLLMProvider`, and the SDK client were
successfully rebuilt. If configuration or client construction failed, legacy getters
could report the candidate Provider or model while `_active_llm_provider` and
`_active_client` still represented the previous context.

This violated the required authoritative-state invariant and could affect the context
captured by a future task.

### Phase 4.1.1 Fix

The fix uses build-first, commit-second semantics. Candidate scalar values remain local
while `ModelConfig`, provider, and client construction run. After successful
construction, all related scalar fields, the task-scoped provider, and client are
committed within one `RLock` critical section.

The resulting contract is:

```text
success = atomic full commit
failure = no state mutation
```

The same helper boundary is used by all three legacy update entry points. Failure does
not require rollback because active state has not yet been mutated.

## Directed Retest

| Probe | Result |
|---|---|
| `switch_provider()` client-creation failure preserves all state | **PASS** |
| `set_api_key()` rebuild failure preserves all state | **PASS** |
| `set_custom_base_url()` rebuild failure preserves all state | **PASS** |
| Consecutive different failures do not accumulate drift | **PASS** |
| Failed switch followed by new task captures authoritative state | **PASS** |
| Failure followed by success commits complete new state | **PASS** |
| Concurrent readers never observe a partial committed state | **PASS** |
| Failure messages and provider representations exclude test secrets | **PASS** |
| Existing BYOK foundation regression | **PASS** |

The final repository evidence is:

- Phase 4.1 tests: **19 passed**;
- complete pytest suite: **129 passed**;
- offline LLM-contract smoke: **6 passed**;
- real network calls: **none**;
- real credentials: **none**.

## QA Traceability

During the DeepSeek directed retest, one intermediate QA probe reported a failure
because the probe's own trigger condition was incorrect. Investigation isolated the
result to the probe rather than the product implementation. After correcting the
probe, all directed cases passed.

The intermediate false failure is retained here for audit traceability, but it is not
classified as a product bug and does not change the final verdict.

## Deferred Low and Notes

The following observations remain recorded and unfixed:

- L1: preflight footer price display can reflect later global Provider state;
- L2: no dedicated serialization-defense method on `TaskScopedLLMProvider`;
- L3: base URL shape validation remains minimal;
- L4: some public Provider APIs are unused;
- L5: malformed Registry metadata can raise raw `KeyError`;
- N1: unlocked custom-model read in `get_models_for_provider()`;
- legacy Gradio future-task Provider configuration remains process-level;
- secure credential storage and IDE credential UI remain deferred to V3.4.

These are Low or future-work observations. They do not reopen M1 and do not block RC1.

## Final Assessment

- Initial verdict: **PASS WITH ISSUES**;
- Initial Critical: **0**;
- Initial Medium: **1**;
- M1: **PASS**;
- Final Critical: **0**;
- Final Medium: **0**;
- Phase 4.1 regression: **19 passed**;
- Full regression: **129 passed**;
- Offline LLM smoke: **6 passed**;
- Final Verdict: **PASS**;
- Retest Again: **Not Required**.

## Next Gate

Phase 4.1 and Phase 4.1.1 QA are closed. The project may proceed to **V3.0 RC1**. This
QA report does not start or complete RC1.
