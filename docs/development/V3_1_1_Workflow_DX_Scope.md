# V3.1.1 Workflow & Developer Experience Scope Freeze

## 1. Decision

- **Version:** V3.1.1
- **Theme:** Workflow & Developer Experience Optimization
- **Baseline:** released `v3.1.0` at
  `8813e4c2fb0dc07f38c2013d520441bf399dcbc4`
- **Status:** SCOPE FROZEN / IMPLEMENTATION AUTHORIZED
- **Research boundary:** V3.1.0 Formal RQ1–RQ4 history remains frozen.
- **V3.2:** NOT STARTED

V3.1.1 is a maintenance release for reproducible developer workflows,
environment diagnostics, safer validation, and release consistency. It does not
add retrieval capability or change research results.

## 2. Frozen Change Items

### V311-DX-01 — Unified Python developer command hub

**Problem:** Developer entry points are distributed across README snippets,
standalone scripts, and import-level APIs.

**Acceptance criteria:** Add `scripts/dev.py` with discoverable, explicit-exit-code
commands for doctor, project smoke, test profiles, model checks, experiment/archive
validation, and release checks. It must resolve the repository independently of the
current working directory, avoid `shell=True`, and perform no automatic Git writes,
model downloads, Formal executions, or network access by default.

**Expected files:** `scripts/dev.py`; developer-workflow tests; concise README usage.

**Test requirements:** Help and dispatch, cwd independence, stdout/stderr behavior,
exit-code propagation, safe subprocess arguments, and secret redaction.

**Backward compatibility:** Additive; all existing commands remain supported.

**Formal impact:** **NO**.

### V311-DX-02 — Runtime and test-environment doctor

**Problem:** Core, optional E5, and historical Formal environments are easy to
confuse, and some hosts fail before pytest collection during plugin initialization.

**Acceptance criteria:** Report Python, platform, core/optional dependency
availability, pytest, Git, repository root, branch, and HEAD. Report relevant
environment variables only as set/unset. Probe ordinary pytest in an isolated
subprocess and recommend `-p no:debugging` only when the observed probe fails.
Historical CPython 3.12.14, torch 2.8.0, transformers 4.56.2, CPU float32 must be
described as frozen experiment metadata, not a core-runtime requirement.

**Expected files:** developer command/helper and developer-workflow tests.

**Test requirements:** Available/missing/mismatched dependencies, pytest probe
success/failure, Git diagnostics, redaction, and safe recovery output.

**Backward compatibility:** Diagnostic-only and read-only.

**Formal impact:** **NO**.

### V311-DX-03 — Offline-first E5 preflight and lightweight smoke

**Problem:** The existing Phase 3.2 validator enters a heavyweight validation path
without a lightweight cache/revision diagnosis, and its resource reporting is not
portable to platforms without the POSIX `resource` module.

**Acceptance criteria:** Add a read-only, offline, no-download model preflight for
`intfloat/multilingual-e5-base` revision
`d128750597153bb5987e10b1c3493a34e5a4502a`, dimension 768. Check pinned optional
dependencies, explicitly supplied or standard local cache snapshots, required
files, dangling symlinks, resolved revision, and repository-internal cache risk.
An explicit `--smoke` may embed one query and one document only. The existing full
validator must degrade resource metrics to unavailable rather than fail at import.

**Expected files:** `scripts/dev.py`, minimal portability changes to
`scripts/validate_phase32_real_model.py`, and workflow tests.

**Test requirements:** Missing dependencies/cache/files, wrong revision, dangling
symlink, repository-internal cache, fake 768-dimensional smoke, no-network behavior,
and unavailable resource metrics.

**Backward compatibility:** Existing E5 provider semantics and full validator entry
remain unchanged.

**Formal impact:** **NO**.

### V311-DX-04 — Stable test profiles

**Problem:** Important V3.1.0 test groups are long file lists remembered from
historical execution context rather than stable repository commands.

**Acceptance criteria:** Provide `test llm`, `test production`, `test experiments`,
`test full`, and `test release` from one file-list source of truth. Preserve pytest
exit codes and support simple argument passthrough such as `--collect-only`, `-k`,
and `-x`. The V3.1.0 counts 198/240/892 are audit baselines, never future pass
thresholds.

**Expected files:** developer command/helper, workflow tests, and optionally the
existing CI workflow after local stability is proven.

**Test requirements:** Profile mapping, collection, passthrough, failure propagation,
and equivalence between the full profile and the legacy full command.

**Backward compatibility:** Existing direct pytest commands remain valid.

**Formal impact:** **NO**.

### V311-DX-05 — Read-only experiment/archive validator

**Problem:** Archive validation and execution eligibility require several low-level
APIs and manually supplied identities; stable validator failure codes lack a concise
developer-facing explanation.

**Acceptance criteria:** Compose existing schemas and validators to provide
`archive-v3.1.0` validation plus a read-only purpose preflight. Verify the frozen
execution/archive ancestry, artifact-set SHA-256 and canonical identity, 17 configs,
48 English Test queries, 816 query-config pairs, protected artifact immutability,
and deterministic Formal CSVs. The CLI may explain expected/actual/recovery but must
not copy or alter frozen protocol rules, write receipts/artifacts, or run a benchmark.
Correctness checks in workflow/export/model validation must remain active under
`python -O`.

**Expected files:** developer command/helper,
`scripts/export_formal_thesis_tables.py`, and workflow tests.

**Test requirements:** Valid archive, wrong identity/hash/ancestry, validator-code
explanation, zero writes, and optimized-Python failure on corrupted inputs.

**Backward compatibility:** Existing experiment APIs and frozen failure schemas are
unchanged.

**Formal impact:** **NO**.

### V311-DX-06 — Release preflight and version/document consistency gate

**Problem:** V3.1.0 was correctly tagged and pushed while tracked release documents
still described an unreleased candidate state.

**Acceptance criteria:** Add a read-only release check with explicit PREPARING,
RELEASE_CANDIDATE, and RELEASED states. Check branch/HEAD, tracked and staged state,
protected-path staging, version metadata, stable document sentinels, Formal
immutability, CSV validation, and tag state. Remote checks occur only with explicit
`--remote`, discover configured remotes, and use read-only operations. The command
must never stage, commit, tag, push, fetch, rewrite prose, or mutate history.

**Expected files:** developer command/helper, release-workflow tests, minimal release
metadata/sentinels if required, and release documentation.

**Test requirements:** Version/state mismatches, protected staged path, absent and
wrong-target tags, remote-disabled default, remote failure, and release-state
transitions in temporary repositories.

**Backward compatibility:** Read-only and additive.

**Formal impact:** **NO**.

## 3. Non-goals

- No retrieval semantic changes.
- No ranking changes.
- No Formal rerun or replacement.
- No Query, Ground Truth, Grade, Formal metric, interpretation, or artifact changes.
- No frozen schema or protocol identity changes.
- No directory restructuring.
- No end-user UX or prompt rewrite.
- No Multi-Agent work and no V3.2 implementation.
- No automatic Git write operations, tag overwrite, force push, or push.
- No model or model-revision change.
- No model download or repository-local model cache creation.

## 4. Quality Gate

Implementation may proceed only within the six items above. Completion requires
workflow tests, production and experiment profiles, full regression through both the
new and legacy entries, optimized-Python validator coverage, unchanged frozen Formal
identity/SHA-256, Critical 0, and validity/release-blocking Medium 0.
