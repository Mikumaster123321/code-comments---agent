# V3.1.0 Phase 6 — Annotation Protocol Clarification Addendum A

## 1. Status and Identity

- Addendum ID: `v3.1-phase6-protocol-addendum-a`
- Addendum version: `v1`
- Status: **CLARIFIED / FROZEN**
- Effective date: `2026-09-22`
- Applies to: `docs/experiments/Experiment_Protocol_V3_1_0.md`
- Supersedes only: the second-human reviewer requirement in Section 5.4 and the
  corresponding reviewer/adjudicator interpretation

This addendum is normative. It resolves an operational conflict between the frozen
protocol's second-reviewer language and the fact that the project has one available
human annotator. It does not reopen or otherwise reinterpret the experiment protocol.

## 2. Frozen Annotation Contract

The annotation contract is:

```text
primary_annotator_id: wang
second_human_annotator: ABSENT
review_method: delayed_blinded_self_review
minimum_review_delay_hours: 48
```

Ground-truth relevance is produced by one human annotator. No second person is
represented as having annotated, reviewed, or adjudicated the records.

## 3. Required Workflow

For every query covered by the Section 5.4 review requirement:

1. `wang` performs the initial annotation from the frozen query and frozen source
   evidence. The record is `drafted`.
2. At least 48 hours elapse before review begins.
3. During review, `wang` sees only the query and frozen source evidence. The initial
   relevance grade, rationale, and judgment are masked until the delayed judgment is
   complete. Evaluated retrieval rankings remain unavailable.
4. `wang` records a new, independent-in-time delayed judgment.
5. Only then is the delayed judgment compared with the initial annotation.
6. Any disagreement in relevance, identity, or span sets `ambiguity_flag=true` and
   requires an `adjudication_note` that preserves the disagreement and resolution.
7. Any material relevance, identity, or span correction requires a ground-truth
   version bump and a new canonical ground-truth hash. Prior affected formal results,
   if any, are invalid for that result namespace under the existing protocol.

An agreement may set `ambiguity_flag=false` and leaves `adjudication_note` null. The
review delay, masking confirmation, initial judgment, delayed judgment, comparison,
and any adjudication are retained in the annotation audit evidence.

## 4. Reviewer and Adjudicator Semantics

The existing ground-truth schema remains usable with these frozen meanings:

- `primary_annotator_id = wang` identifies the sole human annotator.
- `reviewer_id = wang` means **delayed blinded self-review**. It does not mean or
  imply second-person review.
- `adjudicator_id = null` when the initial and delayed judgments require no
  adjudication.
- `adjudicator_id = wang` when `wang` resolves a recorded disagreement after the
  delayed comparison.
- `annotation_status = reviewed` means the delayed blinded self-review completed
  without adjudication; `annotation_status = adjudicated` means a recorded
  disagreement was resolved; `frozen` retains the existing final freeze meaning.

The annotation audit record must identify `review_method` as
`delayed_blinded_self_review`, record a delay of at least 48 hours, and carry the
`ambiguity_flag` and `adjudication_note` semantics above. These audit fields clarify
the existing `annotation_audit.jsonl` evidence; they do not change retrieval truth,
metrics, or ranking behavior.

## 5. Independent Model/Data Audit Boundary

Later Independent QA may use an independent model to perform:

- manifest validation;
- hash validation;
- leakage audit;
- masked sample review; and
- dataset consistency audit.

An AI/model audit is independent QA evidence, not a human second annotator. It cannot
be recorded as second-human annotation, and it cannot be used to calculate or claim
human inter-annotator agreement.

## 6. Inter-Annotator Agreement and Thesis Limitation

Human inter-annotator agreement is **NOT AVAILABLE / NOT CLAIMED** because only one
human annotator participates. No IAA statistic may be fabricated or inferred from the
initial-versus-delayed self-review comparison or from an AI/model audit.

The thesis must disclose under **Threats to Validity / Annotation Limitations** that:

- ground-truth relevance was annotated by a single human annotator;
- a delayed blinded self-review after at least 48 hours was used to reduce consistency
  bias; and
- no second-human annotation or human inter-annotator agreement exists.

Delayed self-review mitigates but does not eliminate single-annotator subjectivity or
shared-bias risk.

## 7. Preserved Protocol Scope

Only the reviewer requirement and its associated semantics are clarified. The
following remain unchanged:

- RQ1–RQ4 and the formal experiment matrix;
- dataset composition and size;
- the fixed 72-query allocation;
- metrics, K values, and `top_k`;
- Hybrid weights and Graph configuration;
- the pinned E5 identity and runtime;
- File, Symbol, and Chunk baseline contracts;
- failure and degraded-mode policy; and
- all leakage, artifact, reproducibility, and claim-discipline requirements except
  where they refer to the superseded second-human reviewer assumption.

In particular, the self-repository path-filter remains exactly as Section 3.2
defines it: tracked production and test source are both eligible for the corpus, and
tracked test source is recorded with `path_role=test`. Tests are not excluded based
on prior chat summaries.

## 8. Research Boundary at Freeze

- Phase 6.0.1: **ANNOTATION PROTOCOL CLARIFICATION COMPLETED**
- Annotation Protocol: **CLARIFIED / FROZEN**
- Phase 6.2: **ALLOWED BUT NOT STARTED**
- Formal dataset/query/ground truth: **NOT CREATED**
- Formal RQ1–RQ4: **NOT STARTED**
- Phase 6.3: **NOT STARTED**
- V3.2: **NOT STARTED**
