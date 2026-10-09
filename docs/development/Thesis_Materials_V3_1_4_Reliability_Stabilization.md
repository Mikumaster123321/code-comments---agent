# V3.1.4 Thesis Materials — Reliability Stabilization

## Version position

V3.1.4 is the final engineering-maintenance release before the planned V3.2
Multi-Agent Collaboration phase. Its contribution is not a new retrieval algorithm or
a new model-quality result. It strengthens the runtime conditions under which the
existing software-maintenance capabilities can be reproduced, diagnosed, cancelled,
and evolved without accidental compatibility breakage.

Release status: **RELEASED** (independent Final Release QA PASS).

## Engineering problem

The pre-implementation audit identified a P0 credential-scope defect: when a user
changed Provider while the UI key field was empty, the new Provider could inherit the
previous active Provider's runtime key. Several vendor definitions also treated
`OPENAI_API_KEY` as a generic fallback. This could combine one vendor endpoint with
another vendor's credential. The audit also found implicit SDK-plus-application retry
multiplication, import-time client construction, cancellation copy that exceeded the
SDK's real interrupt capability, incomplete archive/resource guards, all-failed batch
files counted as success, unconsumed temporary downloads, silent workspace field loss,
and user-visible `javac` temporary paths.

## Engineering contributions

### Credential isolation

Credential precedence is now scoped to the candidate Provider: explicit UI credential,
then provider-specific environment credential, then unconfigured. Cross-Provider
switches clear the previous runtime key before candidate construction.
`OPENAI_API_KEY` belongs only to OpenAI and Custom/OpenAI-compatible configurations.
Candidate construction is atomic: failure leaves the prior active Provider/model/
client state coherent.

### Runtime robustness

Provider client construction is lazy, so importing configuration, processor, or
Project Intelligence creates no client and sends no network request. Runtime support
is no longer expressed as an ambiguous “Python 3.10+” promise. CPython 3.10 is the
supported/recommended baseline; later versions have explicit best-effort boundaries,
and the known Anaconda 3.13.5 UI/bare-pytest SIGSEGV is classified as unsupported on
that host. CI keeps Ubuntu and CPython 3.10 and adds import and UI-build smoke steps.

### Failure and cost handling

The OpenAI-compatible SDK retry owner is disabled (`max_retries=0`). Normal generation
performs one application attempt and one transport attempt with an explicit 90-second
client timeout. Preflight is one low-cost, one-token request with a six-second timeout.
Authentication, permission, invalid request/model, not-found, rate limit, timeout,
connection, response loss, and other ambiguous failures are not transparently retried.
This avoids silently duplicating a generation request that may already have incurred
Provider cost.

### Cancellation semantics

Cancellation is cooperative: queued futures are cancelled, new stages stop, already
running SDK calls finish naturally, and only then does the UI show `Cancelled`.
Completed partial results remain available. The contract explicitly avoids claiming
immediate network interruption or guaranteed token/cost savings.

### Resource lifecycle and batch correctness

Central defaults bound a single source (2 MiB), upload (25 MiB), batch count (200), ZIP
members (1,000), aggregate uncompressed content (100 MiB), and per-member compression
ratio (100:1). ZIP traversal, absolute path, symlink, count, size, and ratio violations
receive stable rejection reasons. All-symbol failure is no longer counted as file
success or written as a normal empty annotated source. Partial success remains
packaged with accurate status. Batch-owned per-file downloads and failed partial ZIPs
are cleaned, while final UI downloads remain valid under the OS temporary lifecycle.

### Diagnostics and compatibility stabilization

Structured local diagnostics use an opaque operation ID and an allow-list of stage,
Provider/model, attempt, duration, and stable error category. They exclude credentials,
prompt, source, raw Provider response, reasoning, and user-visible absolute paths.
Workspace schema v1 now retains `output_lang` and `rewrite_existing`; unknown future
versions fail closed and failed atomic saves remove `.tmp`.

The Pre-V3.2 contract classifies current surfaces as Stable, Legacy-Compatible,
Internal, Experimental/Operational, or Frozen-Formal. It preserves Provider IDs,
task-scoped Provider values, Processor/batch tuple shapes, workspace helpers,
`ui.CUSTOM_CSS`, Project Intelligence facades, and the frozen Formal boundary without
inventing future Agent APIs.

## Verification evidence

- P0 credential/provider foundation: `33 passed`;
- V3.1.4 reliability tests: `28 passed`;
- related targeted regression: `98 passed`;
- LLM contracts: `6 passed`;
- production: `198 passed`;
- experiments: `240 passed`;
- release/architecture: `24 passed`;
- full offline regression: `1010 passed` (baseline: 968);
- V3.1.0 archive validator: PASS;
- four deterministic Formal CSV checks: PASS.

The implementation host has Anaconda Python 3.13.5 and no CPython 3.10 interpreter.
The required CPython 3.10 Gradio `create_ui()` smoke is therefore **NOT EXECUTED in
this implementation phase** and must be recorded by CI/independent Final QA. No PASS
is inferred from historical V3.1.3 evidence.

## Formal research immutability

V3.1.4 changes no retrieval ranking, BM25, E5, Graph, Hybrid/RRF, ContextBuilder,
dataset, protocol, artifact, metric, or Formal result.

- execution revision:
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- artifact-set identity:
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- artifact-set SHA-256:
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

All three remained unchanged under archive and deterministic-export checks.

## Thesis claim boundary

The defensible contribution is Engineering Reliability, Runtime Robustness, Failure
Handling, Credential Isolation, Resource Lifecycle, Compatibility Stabilization, and
Pre-Multi-Agent Engineering Readiness. The evidence does not establish a production
SLA, uptime improvement, statistically significant reliability increase, lower
latency, improved retrieval/model quality, multi-tenant security, or completed
Multi-Agent capability.
