# V3.1.4 Runtime and Reliability Contract

Status: `IMPLEMENTED / AWAITING FINAL QA`

## Runtime support

| Runtime / platform | Status |
|---|---|
| CPython 3.10 | `SUPPORTED / RECOMMENDED` |
| CPython 3.11 | `BEST-EFFORT / UNVERIFIED` |
| CPython 3.12 | `BEST-EFFORT CORE`; historical E5 evidence is not UI certification |
| standard CPython 3.13 | `BEST-EFFORT / UNVERIFIED UI` |
| Anaconda Python 3.13.5 | `UNSUPPORTED FOR UI / BARE PYTEST` on the known host |
| Ubuntu + CPython 3.10 | `SUPPORTED CI EVIDENCE` |
| macOS + CPython 3.10 | supported when release QA records the required smoke |
| Windows | `BEST-EFFORT` unless separately tested |

Importing `config`, `processor`, or `project_intelligence` creates no Provider client
and makes no network request. Provider client construction is lazy. App startup does
not load the optional E5 model/runtime. `pycodestyle` is optional and doctor reports
whether professional lint or the basic fallback is active.

## Provider request attempts and timeouts

- normal generation: one application attempt × one transport attempt;
- OpenAI-compatible SDK `max_retries`: `0`;
- normal generation client timeout: `90 seconds`;
- preflight/ping: one non-generative, one-token attempt with a `6 second` request
  timeout by default;
- `javac`: one local subprocess attempt with a `15 second` operation timeout;
- Managed Access: unchanged conservative no-automatic-Provider-retry policy.

Authentication, permission, invalid request/model/configuration, not-found, rate
limit, timeout, connection, response-loss, and other ambiguous failures are not
automatically retried for generation. This deliberately avoids an unobservable second
billable request when the first may have reached the Provider. A stable error lets the
user explicitly decide whether to run again. Numeric limits are conservative product
defaults, not universal performance optima.

## Credential contract

Credential precedence is explicit current-provider UI value, then the current
provider's environment variable, then unconfigured. Empty or missing UI input during
a cross-provider switch never inherits the previous Provider's runtime secret.
`OPENAI_API_KEY` is available only to OpenAI and Custom/OpenAI-compatible providers;
other vendors use their own named variables. Candidate construction precedes active
state commit, so failure leaves the previous coherent state intact.

## Cancellation and cost

Cancellation is cooperative:

`Cancellation requested -> queued work cancelled -> in-flight blocking calls finish -> Cancelled`.

No new stages or batch files start after cancellation is observed. Completed useful
partial results remain downloadable. The application cannot guarantee interruption of
an HTTP request already running inside the SDK, cannot guarantee immediate token
savings, and does not claim that a Provider will waive cost.

## Intake and archive limits

Defaults are centralized in `code_comments_agent.reliability.RuntimeLimits`:

| Boundary | Default |
|---|---:|
| single source | 2 MiB |
| uploaded file/archive | 25 MiB |
| batch source/upload count | 200 |
| ZIP members | 1,000 |
| aggregate ZIP uncompressed data | 100 MiB |
| per-member compression ratio | 100:1 |

ZIP traversal, absolute paths, symlinks, excessive count/size/ratio, and nested archive
recursion are rejected or excluded with stable local reasons. Tests construct small
metadata fixtures; they do not materialize an archive bomb. These are runtime intake
limits only and do not change retrieval or ContextBuilder budgets.

## Batch and temporary ownership

Internal batch outcomes distinguish success, partial-symbol failure, failure, and
cancelled-with-results. All-symbol failure is not counted as success and does not
produce a normal empty annotated source. Public tuples and ZIP naming remain unchanged.

- single-file final source/Markdown downloads: returned to UI; OS temporary lifecycle;
- batch per-file source/Markdown downloads: batch-owned intermediates, deleted after
  their contents are consumed;
- batch staging directory: batch-owned, deleted in `finally`;
- final/partial ZIP: final ZIP is returned to UI and follows OS temporary lifecycle;
  failed partial ZIP is deleted;
- `javac` and lint files: helper-owned, deleted after the check;
- workspace `.tmp`: workspace-owned, atomically replaced on success and deleted on
  failure.

## Diagnostics and workspace recovery

Developer diagnostics use stdlib logging and an allow-list: opaque `operation_id`,
stage, provider/model IDs, attempt, duration, and stable error category. Credential,
prompt, source, raw Provider response, private reasoning, and user-visible absolute
paths are excluded. `javac` user messages replace temporary paths with a stable
placeholder.

Workspace schema version `1` persists the existing UI fields including `output_lang`
and `rewrite_existing`. Unknown future versions fail closed; no migration framework is
introduced. The workspace is per OS user under the current localhost/single-user
threat model, not a multi-tenant storage claim.
