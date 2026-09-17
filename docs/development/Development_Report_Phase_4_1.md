# V3.0 Phase 4.1 — Provider / BYOK Foundation

## Background

Phase 4.1 establishes user-owned model configuration before the V3.0 RC1 gate. The
product policy is **BYOK — Bring Your Own Key**: an official release does not embed the
project developer's third-party LLM API key. Each user supplies the Provider, Model,
and Credential used for their own requests.

The existing application already supported multiple OpenAI-compatible providers, but
its active Provider, Model, credential, and client were process-level mutable state.
That behavior was retained for the Gradio compatibility surface while a task-scoped
core was introduced underneath it.

## Capability

User-Owned Model Configuration

## Technical Implementation

Provider / BYOK Foundation

The implementation separates durable, displayable model configuration from runtime
credentials and constructs one provider/client context for each task:

```text
ProviderRegistry
    + ModelConfig (credential-free)
    + RuntimeCredential (runtime-only)
              |
              v
    TaskScopedLLMProvider
              |
              v
     one request or task

Legacy Gradio configuration
              |
              v
  Legacy Compatibility Bridge
              |
              v
 future task-scoped contexts
```

## Existing Architecture Problem

Before Phase 4.1, `config.py` maintained `_active_provider`, `_active_model`,
`_active_api_key`, `_active_base_url`, and `_active_client` as shared mutable process
state. `llm_service.py` reread the active client and model while executing requests and
retries. A Provider switch from another UI interaction could therefore affect work
that had already started.

This design also combined model selection and credential concerns in the same active
state. It did not provide an explicit configuration contract suitable for future
session isolation or a safe boundary between ordinary configuration and secrets.

## New Architecture

Phase 4.1 adds four focused contracts:

- `ModelConfig`: immutable, deterministic, credential-free model selection;
- `RuntimeCredential`: a redacted, non-ordinary-serializable runtime secret wrapper;
- `ProviderRegistry`: read-only metadata lookup and explicit provider construction;
- `TaskScopedLLMProvider`: a fixed `ModelConfig` and client pair reused by one task.

The legacy configuration API remains available through a compatibility bridge.
`switch_provider()`, `set_api_key()`, active getters, and the Gradio controls configure
the context captured by future tasks. They are not the state source for an already
running task.

## ModelConfig

`ModelConfig` contains only:

- `provider_id`;
- `model`;
- `base_url`.

It is a frozen data class. Construction normalizes the Provider id and base URL, and
`to_dict()` produces deterministic ordinary configuration data. It has no API-key or
credential field, so its representation, equality behavior, and serialization do not
carry a secret.

## RuntimeCredential

`RuntimeCredential` exists only at the client-construction boundary. Its `repr()` and
`str()` values are always redacted, it exposes no `to_dict()`, and pickle-style
serialization is rejected. The raw value is supplied to the SDK client factory at
runtime and is not written to workspace configuration or project documentation.

Phase 4.1 does not claim encrypted in-memory storage. The contract is separation and
non-persistence, not a Keychain or Vault implementation.

## ProviderRegistry

`ProviderRegistry` is derived from the repository's existing Provider metadata. It
supports:

- DeepSeek;
- OpenAI;
- Azure OpenAI;
- Alibaba DashScope / Qwen;
- Moonshot / Kimi;
- Custom OpenAI-compatible endpoints.

The Registry exposes supported Provider metadata, default models, base URLs,
customizable-base-URL policy, and pricing metadata. Given a `ModelConfig`, runtime
credential, and client factory, it constructs an independent task-scoped provider.

No Provider was added for Phase 4.1. The Registry does not select, score, benchmark,
route, or fall back between models. Those responsibilities remain outside this phase;
the future Router belongs to V3.3.

## Task Isolation

A task captures its `TaskScopedLLMProvider` once at entry. The captured provider owns
the task's fixed configuration and client reference. Later legacy global Provider
switches configure only future tasks and cannot replace the model, base URL, client, or
credential already in use by the running task.

Offline tests construct Task A with one Provider, model, base URL, and credential and
Task B with a different OpenAI-compatible configuration. Interleaved and concurrent
calls remain isolated, including their client and credential boundaries.

## LLM Service Migration

The LLM service accepts an explicit provider for:

- Python docstring generation;
- Java Javadoc generation;
- Python and Java translation;
- Python and Java summaries;
- API-key/model ping;
- retry execution;
- cost estimation.

The retry path captures a provider before its first attempt and reuses that same
provider for every retry. Explicit-provider calls do not reread legacy active state.
Provider failures are converted to sanitized messages containing stable Provider/model
identity and exception type rather than raw exception text.

## Processor Migration

The existing Processor and Gradio behavior remain compatible. The following paths now
accept or capture one task-scoped provider at their entry boundary:

- synchronous Python processing;
- synchronous Java processing;
- Python and Java progress generators;
- batch and batch-progress processing;
- preflight ping and estimation;
- Python and Java analysis/summary paths.

Worker threads receive the captured provider explicitly. A concurrent legacy switch
therefore cannot change the client used by another in-flight Processor task.

## Credential Security

The Phase 4.1 security boundary guarantees:

- `ModelConfig` is credential-free;
- `RuntimeCredential` representations are redacted;
- ordinary credential serialization is unavailable;
- provider/client representations do not expose the credential;
- workspace persistence continues to use a strict allowlist and drops credential and
  provider runtime objects;
- sanitized request and client-construction errors exclude raw exception messages;
- test credentials are obviously fake values;
- `code_maintenance/` remains independent of Provider, Credential, OpenAI SDK, and LLM
  modules.

No test sends a real provider or network request.

## Initial Testing

The initial Phase 4.1 implementation was committed as
`9f2d1517d9cfb72895cb322b2352fd0e2bb3ef12`
(`feat(v3): add BYOK provider foundation`).

- Phase 4.1 tests: **13 passed**;
- complete pytest suite: **123 passed**;
- offline LLM-contract smoke: **6 passed**;
- real API, network request, or real credential: **none**.

Coverage included configuration immutability, credential redaction and serialization,
Registry metadata, Task A/B client and credential isolation, concurrent calls, legacy
compatibility, explicit LLM-service use, retry isolation, Processor capture, workspace
persistence, and the `code_maintenance/` dependency boundary.

## DeepSeek Independent QA

The initial DeepSeek verdict was **PASS WITH ISSUES**:

- Critical: **0**;
- Medium: **1**;
- M1: legacy Provider updates could partially commit scalar state before provider/client
  construction succeeded.

The core BYOK policy, task isolation, credential safety, persistence boundary, and
architecture direction passed. M1 was directed for Phase 4.1.1 correction before the
Documentation Gate could close.

## Phase 4.1.1 Post-QA Hardening

Phase 4.1.1 is part of this Phase 4.1 report rather than a separate development phase
report. Commit `f28e3dbad1a16a5d4ec32e95fdfea7c7f1fbfeb4`
(`fix(v3): make legacy provider updates atomic`) corrected M1 with a build-first,
commit-second update sequence.

The compatibility bridge now builds candidate `ModelConfig`,
`TaskScopedLLMProvider`, and client values in local variables. Only after all
construction succeeds does it commit every related active scalar, client, and provider
inside the same `RLock` critical section.

The contract applies uniformly to:

- `switch_provider()`;
- `set_api_key()`;
- `set_custom_base_url()`.

The frozen update semantics are:

```text
success = atomic full commit
failure = no state mutation
```

Failure no longer requires rollback because no authoritative state is changed before
the candidate is fully built. Consecutive failures do not accumulate drift, a new task
after failure captures the unchanged authoritative context, and a later successful
switch commits the complete new context.

## Directed Retest

The DeepSeek directed retest returned **PASS**:

- `switch_provider()` atomicity: **PASS**;
- `set_api_key()` atomicity: **PASS**;
- `set_custom_base_url()` atomicity: **PASS**;
- consecutive failures: **PASS**;
- failed switch followed by task capture: **PASS**;
- failure followed by success: **PASS**;
- concurrent readers and writer: **PASS**;
- secret-safety regression: **PASS**;
- complete BYOK regression: **PASS**.

Final validation:

- Phase 4.1 tests: **19 passed**;
- complete pytest suite: **129 passed**;
- offline LLM-contract smoke: **6 passed**;
- Final Verdict: **PASS**;
- Retest Again: **Not Required**.

## Technical Debt

The following DeepSeek Low findings remain explicitly deferred:

- L1: preflight footer price display can reflect the later global Provider;
- L2: `TaskScopedLLMProvider` has a redacted representation but no dedicated
  serialization-defense method;
- L3: base URL validation is intentionally minimal and does not validate full URL
  shape;
- L4: some public compatibility/provider APIs are currently unused;
- L5: malformed Registry metadata can surface a raw `KeyError`;
- N1: `get_models_for_provider()` reads the custom model name without the active-state
  lock.

The legacy Gradio future-task Provider configuration also remains process-level for
compatibility. These observations do not invalidate task capture or the final Phase
4.1 QA verdict.

## Security Limitations

Phase 4.1 deliberately does not implement:

- OS Keychain integration;
- Vault;
- Secret Service;
- encrypted credential storage;
- credential databases;
- IDE credential-configuration UI.

Secure credential storage and its IDE UI remain V3.4 work. Phase 4.1 provides a safe
runtime boundary and non-persistence guarantees only.

## Next

Phase 4.1 and Phase 4.1.1 are complete, Final QA is **PASS**, and the Documentation
Gate is closed. The project may proceed to **V3.0 RC1**. This report does not start or
complete RC1.
