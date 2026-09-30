# V3.1.0 Phase 6.1 — Final QA Report

## Verdict

**PASS FOR PHASE 6.1 WITH LOW NOTES**

- Initial Independent QA: **FAIL / BLOCKED**
- Initial Critical / Medium / Low: **4 / 7 / 3**
- Phase 6.1.1: **HARDENING COMPLETE**
- Directed Retest: **PASS WITH LOW NOTES**
- New Critical / Medium: **0 / 0**
- Final Critical / Medium: **0 / 0**
- Phase blocker: **0**
- Residual defensive Low: **1**
- Phase 6.1.2: **NOT REQUIRED**
- Phase 6.1: **COMPLETED**
- Documentation Gate: **CLOSED**

## 1. QA Scope and Evidence

This final QA closes the benchmark-infrastructure gate at hardened HEAD
`38822ffa008f908a911c242b93040b296df5c945` on branch `v3.1.0-dev`.

Evidence reviewed:

- frozen `docs/experiments/Experiment_Protocol_V3_1_0.md`;
- Phase 6.1 initial implementation at
  `e4319cab3113706611ce38157087fe80f4d7c2b9`;
- Initial Independent QA findings;
- Phase 6.1.1 hardening at
  `38822ffa008f908a911c242b93040b296df5c945`;
- repository-external Directed Retest results; and
- targeted and full offline regression results.

No production code, experiment implementation, tests, dependencies, frozen protocol,
or thesis documents were modified by this final documentation gate.

## 2. Initial QA Result

Initial Independent QA returned **FAIL / BLOCKED** with **4 Critical, 7 Medium, and 3
Low** findings. The result is retained without dilution. Phase 6.1 could not close and
Phase 6.2 could not begin until the evidence-integrity defects were corrected and
independently retested.

## 3. Critical Finding Closure

| Finding | Initial risk | Directed final evidence | Status |
| --- | --- | --- | --- |
| C1 | Strategy output could shrink the ground-truth denominator. | Truth is independent of Strategy. With 2 relevant identities and 1 retrieved identity, Recall is **0.5**. | **CLOSED / RESOLVED** |
| C2 | Manifest metadata did not fully constrain runtime evidence. | Authoritative registry verifies path/hash/candidate/Symbol/span/ground-truth/project consistency and fails closed. | **CLOSED / RESOLVED** |
| C3 | English test, dev, and Chinese coverage could be pooled. | Explicit population binding isolates English test, English dev, and Chinese coverage. | **CLOSED / RESOLVED** |
| C4 | Artifact writer trusted caller-provided aggregates. | Writer treats raw evidence as Source of Truth, recomputes/validates aggregate and SHA-256, rejects mismatches, and publishes atomically. | **CLOSED / RESOLVED** |

## 4. Medium Finding Closure

| Finding | Final QA result | Status |
| --- | --- | --- |
| M1 — matrix/config binding | Frozen matrix labels cannot be attached to incompatible strategies, units, semantic modes, or Graph configurations. | **CLOSED / RESOLVED** |
| M2 — formal gate/runtime validation | Formal mode fails closed without the required Phase 6.2/6.3, runtime, commit, offline, cache, and dependency evidence. | **CLOSED / RESOLVED** |
| M3 — `SUCCESS`/`FAILED`/`INVALID` status | Status is derived and validated from raw outcomes; failed and invalid evidence cannot be presented as success. | **CLOSED / RESOLVED** |
| M4 — authoritative rank/order | Explicit rank is authoritative and permutation-invariant; duplicate or invalid rank input is rejected. | **CLOSED / RESOLVED** |
| M5 — privacy sanitization | Sensitive exception/source/credential material is rejected or reduced to safe failure codes before artifact serialization. | **CLOSED / RESOLVED** |
| M6 — semantic schema validation | Cross-field types, identities, counts, languages, spans, hashes, statuses, and immutability constraints are validated. | **CLOSED / RESOLVED** |
| M7 — reproducibility/performance schema | Runtime/offline state, formal gates, counts, timings, cache condition, dimensions, and checksum uniqueness are explicit and validated. | **CLOSED / RESOLVED** |

## 5. Independent Directed Retest

Repository-external independent probes: **41 passed**.

| Group | Passed |
| --- | ---: |
| C1/C2 | 8 |
| C3/C4 | 10 |
| M1–M7 | 16 |
| Extra | 7 |
| **Total** | **41** |

The probe count is deliberately separate from pytest. It is not part of the full
`607 passed` repository regression.

Determinism checks passed for:

- **120 input permutations**; and
- `PYTHONHASHSEED=1`, `7`, and `31`.

Result: **deterministic**. No new Critical or Medium finding was identified.

## 6. Protocol Fidelity and Research Boundary

- Protocol drift: **0**.
- `Experiment_Protocol_V3_1_0.md`: **UNCHANGED**.
- Hardening target: **implementation**, not the frozen rules.
- Formal dataset: **NOT CREATED**.
- Formal query set: **NOT CREATED**.
- Formal ground truth: **NOT CREATED**.
- Formal real-E5 benchmark: **NOT RUN**.
- Formal RQ1–RQ4: **NOT RUN / NOT STARTED**.
- Phase 6.2: **ALLOWED BUT NOT STARTED**.
- V3.2: **NOT STARTED**.

Phase 6.1 closure allows Phase 6.2 dataset/query/ground-truth work to begin in a later
task. It does not authorize formal RQ execution; the frozen protocol still requires a
closed Phase 6.2 gate and a passing Phase 6.3 Dry Run first.

## 7. Residual Low

One defensive Low remains: future UUID-like version or run identifiers may benefit
from stricter canonical validation.

The current accepted identifiers and authoritative evidence chain preserve formal
experiment correctness. The observation is non-blocking and deferred to future
hardening; no code change is justified merely to make the Low count zero.

## 8. Regression Results

| Suite | Result |
| --- | ---: |
| Phase 6.1 | **31 passed** |
| Phase 5 | **48 passed** |
| Phase 4 | **37 passed** |
| Phase 3.2 | **10 passed** |
| Phase 3.1 | **12 passed** |
| Phase 2 | **14 passed** |
| Phase 1 | **41 passed** |
| Offline LLM smoke | **6 passed** |
| Full regression | **607 passed** |

The current Anaconda Python 3.13 host reproduces the already documented pytest
debugging-plugin interpreter crash before collection completes. The established
host-compatible command `python -m pytest -p no:debugging` passed all **607** tests.
All validation was offline: no real model, model download, provider API, network LLM
request, credential, formal query, formal ground truth, or formal benchmark was used.

## 9. Final Gate Matrix

| Gate item | Final state |
| --- | --- |
| C1–C4 | **CLOSED / RESOLVED** |
| M1–M7 | **CLOSED / RESOLVED** |
| New Critical / Medium | **0 / 0** |
| Final Critical / Medium | **0 / 0** |
| Phase blocker | **0** |
| Residual Low | **1, defensive and non-blocking** |
| Phase 6.1.2 | **NOT REQUIRED** |
| Final Phase 6.1 QA | **PASS FOR PHASE 6.1 WITH LOW NOTES** |
| Phase 6.1 | **COMPLETED** |
| Documentation Gate | **CLOSED** |
| Phase 6.2 | **ALLOWED BUT NOT STARTED** |
| Formal RQ1–RQ4 | **NOT STARTED** |
| V3.2 | **NOT STARTED** |

