# V3.1.0 Phase 6.1 — Benchmark Infrastructure Development Report

## 1. Final Status

- Phase 6.1 — Benchmark Infrastructure: **COMPLETED**
- Phase 6.1.1 — Benchmark Evidence Integrity Hardening: **COMPLETED**
- Initial Independent QA: **FAIL / BLOCKED**
- Directed Retest: **PASS WITH LOW NOTES**
- Final Phase 6.1 QA: **PASS FOR PHASE 6.1 WITH LOW NOTES**
- Final Critical / Medium / Phase blocker: **0 / 0 / 0**
- Phase 6.1.2: **NOT REQUIRED**
- Documentation Gate: **CLOSED**
- Phase 6.2: **ALLOWED BUT NOT STARTED**
- Formal RQ1–RQ4: **NOT STARTED**
- V3.2: **NOT STARTED**

This report closes only the Phase 6.1 benchmark-infrastructure gate. It does not create
the formal dataset, queries, or ground truth; run the pinned real-E5 benchmark; execute
RQ1–RQ4; start Phase 6.2; or change production behavior.

## 2. Gate Input and Scope

The final documentation gate was evaluated on:

- branch: `v3.1.0-dev`;
- hardened implementation HEAD:
  `38822ffa008f908a911c242b93040b296df5c945`;
- initial implementation commit:
  `e4319cab3113706611ce38157087fe80f4d7c2b9`;
- protocol source of truth:
  `docs/experiments/Experiment_Protocol_V3_1_0.md`;
- the Phase 6.1 implementation and tests;
- Initial Independent QA findings;
- Phase 6.1.1 hardening changes; and
- Directed Retest evidence.

The pre-gate working tree was clean except for the user's existing untracked
`docs/thesis/` directory. This documentation gate changes only this report, the final
QA report, and `PROJECT_CONTEXT.md`. It does not change `experiments/`,
`project_intelligence/`, tests, requirements, the frozen experiment protocol, or
`docs/thesis/`.

## 3. Protocol Fidelity

Protocol drift is **0**. The frozen
`docs/experiments/Experiment_Protocol_V3_1_0.md` was not modified in response to QA.
Phase 6.1.1 corrected implementation behavior so it conformed to the pre-existing
rules; it did not relax or rewrite the rules to fit the implementation.

The protocol boundaries remain intact:

- formal dataset: **NOT CREATED**;
- formal query set: **NOT CREATED**;
- formal ground truth: **NOT CREATED**;
- formal real-E5 benchmark: **NOT RUN**;
- formal RQ1–RQ4: **NOT RUN / NOT STARTED**; and
- formal execution remains forbidden until the later Phase 6.2 and Phase 6.3 gates
  satisfy the frozen protocol.

## 4. Evolution of Phase 6.1

The complete development and validation sequence is:

```text
Initial Implementation
  -> Independent QA: FAIL / BLOCKED (Critical 4, Medium 7, Low 3)
  -> Phase 6.1.1 Benchmark Evidence Integrity Hardening
  -> Directed Retest: PASS WITH LOW NOTES
  -> Final QA: PASS FOR PHASE 6.1 WITH LOW NOTES
  -> Documentation Gate: CLOSED
```

The Initial Independent QA result is retained as material engineering evidence. The
initial implementation was not accepted merely because its ordinary tests passed:
four correctness-critical evidence-integrity defects and seven medium contract gaps
had to be fixed before the gate could close.

## 5. Initial Implementation

Phase 6.1 introduced isolated experiment-only infrastructure under `experiments/`:

- immutable benchmark, metric, hybrid, graph, file, chunk, and semantic
  configuration contracts;
- deterministic configuration identity and canonical credential-free serialization;
- strict dataset, query, ground-truth, runtime, result, and artifact schemas;
- frozen experiment-only File and Character Chunk lexical baselines;
- unit-aware mapping from canonical source evidence to File, Symbol, and Chunk truth;
- Recall@1/5/10, MRR@10, nDCG@5, Precision@5, and Hit Rate@5;
- failed-query denominator preservation;
- per-query raw evidence and macro/stratified aggregate records;
- a strategy-driven runner skeleton with Phase 6.1 formal-execution guards; and
- append-only artifact publication with checksums.

The implementation did not alter the production Phase 1–5 retrieval contracts. The
File and Chunk baselines remain experiment-only, fake semantic mode remains
synthetic-test-only, and no real provider or model was invoked by validation.

## 6. Initial Independent QA — FAIL / BLOCKED

Initial Independent QA reported **4 Critical, 7 Medium, and 3 Low** findings. The
gate remained open and Phase 6.2 remained blocked. The Critical and Medium findings
were treated as required correctness work rather than documentation exceptions.

### 6.1 Critical Findings and Final Resolution

#### C1 — Strategy-controlled ground-truth denominator

The initial runner could allow a Strategy's returned candidates to narrow the mapped
ground-truth universe. That made a missed relevant item disappear from the Recall
denominator.

Final behavior: the truth universe is built independently from the Strategy through
authoritative dataset evidence. Strategy output can retrieve or miss truth, but it
cannot define truth. The directed example has two relevant identities and one
retrieved identity, so Recall is exactly `1 / 2 = 0.5`.

Status: **CLOSED / RESOLVED**.

#### C2 — Manifest was not an effective runtime evidence boundary

The initial manifest metadata did not fully constrain the source and candidate
evidence consumed by a run.

Final behavior: the authoritative manifest/evidence registry validates the runtime
path set, file content hashes, candidate population, Symbol identity, source spans,
ground-truth references, and project ownership. Missing, stale, duplicate, or
out-of-manifest evidence fails closed instead of entering metric calculation.

Status: **CLOSED / RESOLVED**.

#### C3 — Population pooling could contaminate reported coverage

The initial aggregation path could pool English test, English dev, and Chinese
coverage records into an overall aggregate.

Final behavior: each run binds one explicit population. English test, English dev,
and Chinese coverage are isolated and carry separate roles and filters. Dev and
coverage evidence cannot enter the primary English-test denominator.

Status: **CLOSED / RESOLVED**.

#### C4 — Artifact publication trusted caller-supplied aggregates

The initial writer could accept an aggregate supplied by its caller without proving
that it matched raw evidence.

Final behavior: raw per-query evidence is the Source of Truth. Before publication,
the writer recomputes and validates raw SHA-256, run status, counts, metrics, and
strata. Any mismatch is rejected. Publication uses an atomic append-only path, so a
partially published or caller-corrupted aggregate cannot be accepted as a completed
run.

Status: **CLOSED / RESOLVED**.

### 6.2 Medium Findings and Final Resolution

| Finding | Final contract | Status |
| --- | --- | --- |
| M1 — matrix/config binding | Every formal matrix run ID is bound to its frozen strategy, retrieval unit, semantic mode, Graph state, and signal set. Mislabelled configurations fail closed. | **CLOSED / RESOLVED** |
| M2 — formal gate/runtime validation | Formal execution requires explicit Phase 6.2/6.3 gate evidence plus frozen runtime, offline, model-cache, dependency, commit, and fingerprint validation. | **CLOSED / RESOLVED** |
| M3 — run status | `SUCCESS`, `FAILED`, and `INVALID` semantics are derived from raw outcomes; failed queries remain zero-valued evidence and degraded formal semantic evidence becomes invalid. | **CLOSED / RESOLVED** |
| M4 — authoritative rank/order | Explicit unique positive ranks are authoritative; input tuple order cannot silently redefine ranking, and invalid ranks fail the query/run contract. | **CLOSED / RESOLVED** |
| M5 — privacy sanitization | Failure and artifact surfaces use safe codes and credential/source-marker rejection; caller exception text and sensitive values cannot enter canonical artifacts. | **CLOSED / RESOLVED** |
| M6 — semantic schema validation | Dataset language/counts, immutable tuples, numeric types, hashes, spans, result status, and related semantic invariants are checked strictly. | **CLOSED / RESOLVED** |
| M7 — reproducibility/performance schema | Offline flags, formal-gate evidence, performance counts/timings, cache condition, dimensions, checksum uniqueness, and deterministic metadata are validated and serialized. | **CLOSED / RESOLVED** |

## 7. Phase 6.1.1 Hardening Outcome

Phase 6.1.1 hardened the evidence chain from frozen inputs through metrics and final
publication:

```text
Frozen manifest + runtime evidence registry
  -> authoritative candidate and truth universe
  -> explicit population and matrix binding
  -> ranked raw per-query evidence
  -> recomputed status, metrics, counts, and strata
  -> verified SHA-256
  -> atomic append-only publication
```

This design makes the raw evidence boundary auditable. A Strategy supplies ranked
retrieval observations; it does not control dataset membership, ground truth,
population denominators, aggregate values, or artifact integrity.

## 8. Directed Retest Evidence

The repository-external independent probe suite passed **41 / 41** checks:

| Probe group | Passed |
| --- | ---: |
| C1/C2 | 8 |
| C3/C4 | 10 |
| M1–M7 | 16 |
| Extra defensive checks | 7 |
| **Total** | **41** |

These are independent probes, not repository pytest tests, and are not included in
the `607 passed` full-regression count.

Determinism evidence also passed:

- **120 input permutations** produced deterministic results; and
- cross-process runs under `PYTHONHASHSEED=1`, `7`, and `31` remained deterministic.

The Directed Retest found no new Critical or Medium issue and returned
**PASS WITH LOW NOTES**.

## 9. Residual Defensive Low

One non-blocking defensive Low remains: some future UUID-like version or run
identifiers could receive stricter canonical validation.

This does not change current formal experiment correctness, does not weaken the
authoritative evidence chain, and is not a Phase blocker. It is recorded for future
hardening. Phase 6.1 deliberately does not change code merely to reduce the Low count
to zero.

## 10. Regression Evidence

All validation remained offline and credential-free. No real model, formal query,
formal ground truth, formal benchmark, network LLM request, or provider credential was
used.

| Validation slice | Result |
| --- | ---: |
| Phase 6.1 benchmark infrastructure | **31 passed** |
| Phase 5 Hybrid Retrieval + ContextBuilder | **48 passed** |
| Phase 4 Graph Expansion + Incremental Indexing | **37 passed** |
| Phase 3.2 local embedding adapter | **10 passed** |
| Phase 3.1 embedding core | **12 passed** |
| Phase 2 lexical baseline | **14 passed** |
| Phase 1 corpus | **41 passed** |
| Offline LLM-contract smoke | **6 passed** |
| Full regression | **607 passed** |

On the current host, the documented Anaconda Python 3.13 debugging-plugin import
defect causes the unmodified `python -m pytest` command to segfault before test
execution. The established host-compatible invocation
`python -m pytest -p no:debugging` completed with **607 passed**. This is the existing
host issue documented by the project, not a repository test failure.

## 11. Final Gate Decision

The complete evidence supports the following final decision:

- Final Phase 6.1 QA: **PASS FOR PHASE 6.1 WITH LOW NOTES**;
- Final Critical: **0**;
- Final Medium: **0**;
- Phase blocker: **0**;
- C1–C4: **CLOSED / RESOLVED**;
- M1–M7: **CLOSED / RESOLVED**;
- Phase 6.1.2: **NOT REQUIRED**;
- Phase 6.1: **COMPLETED**; and
- Documentation Gate: **CLOSED**.

Phase 6.2 is now **ALLOWED BUT NOT STARTED**. This authorization does not start the
phase and does not authorize a formal RQ run. Under the frozen protocol, formal
RQ1–RQ4 execution remains unavailable until the Phase 6.2 gate is closed and the
Phase 6.3 dev-only Dry Run records PASS.

