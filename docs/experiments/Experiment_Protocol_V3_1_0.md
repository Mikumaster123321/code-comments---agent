# V3.1.0 Phase 6 — Experiment Protocol

## Freeze Status

**Phase 6.0: COMPLETED / PROTOCOL FROZEN**

- Protocol version: `v3.1-phase6-protocol-v1`
- Annotation clarification: Addendum A (`v1`), **CLARIFIED / FROZEN** at
  `docs/experiments/Experiment_Protocol_Addendum_A_V3_1_0.md`
- **Incremental fixture correction:** Section 10.3's historical `3/2/2`
  SnapshotDiff and `5` embedding-document expectations are superseded by
  `docs/experiments/Experiment_Protocol_Addendum_B_V3_1_0.md`.
- Self-repository dataset commit:
  `12391233daa2149ead4f451e920b2e0d8a1a6beb`
- Formal RQ1–RQ4: **NOT STARTED**
- Phase 6.1 — Benchmark Infrastructure: **ALLOWED BUT NOT STARTED**
- V3.2 Multi-Agent: **NOT STARTED**

This document is the authoritative V3.1.0 experiment contract. It freezes the
reviewed protocol before benchmark code, queries, ground truth, dry runs, or formal
results exist. A later phase may implement this protocol but may not reinterpret it
after seeing formal test results. Any material change requires a new versioned
protocol, an explicit reason, an independent review, and a fresh result namespace;
the original protocol and results remain preserved.

## 1. Scope and Evidence Boundary

Phase 6 evaluates retrieval quality and engineering performance over the completed
Phase 1–5 Project Intelligence implementation. It does not redesign the retrieval
architecture or begin V3.2.

The protocol covers:

- RQ1 File/Symbol/Chunk lexical retrieval units;
- RQ2 BM25 versus the pinned real E5 model;
- RQ3 Graph OFF versus ON and relation/direction ablations;
- RQ4 Lexical, Embedding, Hybrid without Graph, and Hybrid with Graph;
- a secondary RRF robustness comparison;
- retrieval metrics, separately reported context diagnostics, and engineering
  performance;
- a secondary incremental-index experiment; and
- reproducibility, failure, artifact, claim, and audit rules.

The following are not authorized by this freeze: a benchmark runner, metric
implementation, formal query set, ground truth, E5 benchmark execution, RQ1–RQ4 run,
production-code change, test change, dependency change, thesis-document change, or
V3.2 work.

## 2. Research Questions

### RQ1 — Retrieval unit

For maintenance-oriented lexical retrieval, how do File, Symbol, and fixed Character
Chunk units compare when the dataset, queries, tokenizer, BM25 parameters, `top_k`,
ground-truth evidence, and metrics are held constant?

The primary RQ1 comparison is **Lexical-only**. It does not use Embedding, Graph,
Hybrid fusion, or ContextBuilder to rank candidates.

### RQ2 — Lexical versus semantic retrieval

At the frozen Symbol unit, how does deterministic BM25 compare with the pinned real
`intfloat/multilingual-e5-base` model when both receive the same retrieval text and
Graph is OFF?

Fake/hash embeddings are not admissible evidence for RQ2.

### RQ3 — Graph contribution

For primary Weighted Hybrid retrieval, what is the contribution of bounded Graph
signals when Graph OFF and Graph ON use the same Lexical and real-E5 candidates,
weights, queries, ground truth, and `top_k`?

The secondary analysis isolates `CONTAINS/FORWARD`, `CONTAINS/REVERSE`,
`IMPORTS/FORWARD`, and `IMPORTS/REVERSE`. Direction remains retrieval provenance;
no new `GraphRelationKind` is introduced.

### RQ4 — Signal ablation

How do Lexical-only, Embedding-only, Weighted Hybrid without Graph, and Weighted
Hybrid with Graph compare under the frozen Symbol-level protocol?

Weighted Score Fusion is primary. RRF is secondary robustness evidence only and may
not replace or be pooled with the primary RQ4 results.

## 3. Dataset Contract

### 3.1 Composition

The primary dataset combines:

1. the repository at the exact commit
   `12391233daa2149ead4f451e920b2e0d8a1a6beb`; and
2. manually constructed, versioned Python and Java fixture projects.

The self-repository supplies realistic cross-file maintenance structure. Fixtures
supply controlled feature, dependency, bug, language, and unit-boundary cases that
must not be invented or modified in response to formal results. An external
open-source project is outside the primary matrix; if later approved as optional
generalization evidence, it must use a separate dataset ID, repository commit/tag,
license, selection reason, query set, ground truth, and aggregate tables.

Phase 6.2 freezes a manifest containing, for every project, dataset/project ID,
version, source kind, source commit or fixture hash, language, relative file list and
hashes, file count, symbol count, and applicable limitations. The aggregate dataset
hash is SHA-256 over a canonical UTF-8 JSON representation with sorted keys and
deterministically sorted records.

### 3.2 Self-repository path-filter policy

The self-repository source is checked out at the frozen commit in a clean worktree.
Only Git-tracked files at that commit are eligible; untracked files, including local
`docs/thesis/` content, are excluded.

The frozen filter is:

- include tracked regular `.py` and `.java` files recognized by the existing
  `ProjectScanner`/adapter boundary;
- include production and test source when tracked; path role is recorded so results
  can be reported without hiding test-source matches;
- apply the production scanner's built-in exclusions and the root `.gitignore` at the
  frozen commit;
- exclude `.git`, virtual environments, dependency/vendor trees, caches, build and
  coverage output, model caches, vector/index caches, generated experiment results,
  and every untracked path;
- do not follow symlinks; and
- normalize manifest paths to repository-relative POSIX form.

The Phase 6.2 manifest is authoritative. A path-set or file-hash mismatch at run time
fails closed; the runner must not silently absorb a changed working tree.

### 3.3 Fixture strategy

Fixtures are small, human-readable projects with deterministic source and no generated
answers. Collectively they must cover all six task types, Python and Java, File/Symbol/
Chunk mapping, overload/identity cases relevant to Java, graph directions, cross-file
imports, and queries whose wording is not an exact copy of a target identifier.

Each fixture has a purpose statement, language, file/symbol counts, source hashes, and
query IDs. Fixtures may be revised only before the Phase 6.2 freeze. Dev, test, and
Chinese-coverage queries may reuse a fixture project, but may not be paraphrases of
one another that reveal held-out answers.

### 3.4 Language and split policy

English test is the primary thesis-quality aggregate. English dev is used for runner,
schema, and dry-run validation and is never pooled into the primary test result.
Chinese is a separately labelled coverage set and is never merged into the English
primary aggregate.

Java is coverage validation under the documented lightweight Java-parser limits. It
is not represented as fully symmetric compiler-grade Java support.

## 4. Query Set

### 4.1 Task types

The six frozen task types are:

1. symbol lookup;
2. feature localization;
3. dependency questions;
4. bug localization;
5. maintenance tasks; and
6. cross-file understanding.

The set must not collapse into exact-name lookup. Feature, bug, maintenance, and
cross-file queries must require source or structural interpretation appropriate to
their category.

### 4.2 Fixed 72-query allocation

| Task type | English test Python | English test Java | English dev | Chinese coverage Python | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Symbol lookup | 6 | 2 | 2 | 2 | 12 |
| Feature localization | 6 | 2 | 2 | 2 | 12 |
| Dependency questions | 6 | 2 | 2 | 2 | 12 |
| Bug localization | 6 | 2 | 2 | 2 | 12 |
| Maintenance tasks | 6 | 2 | 2 | 2 | 12 |
| Cross-file understanding | 6 | 2 | 2 | 2 | 12 |
| **Total** | **36** | **12** | **12** | **12** | **72** |

The English dev language total is frozen at Python 10 and Java 2. Phase 6.2 assigns
the two Java dev queries to task types before any formal test result is visible; the
other ten dev queries are Python. This assignment and all query IDs are then hashed.

Therefore:

- English test: 48, exactly 8 per task type, Python 36 / Java 12;
- English dev: 12, exactly 2 per task type, Python 10 / Java 2;
- Chinese coverage: 12, exactly 2 per task type, Python 12; and
- total: 72.

### 4.3 Query schema

The canonical query-set record is JSONL with one record per query:

```text
query_id                 stable, unique string
query_set_version        version string
split                    english_dev | english_test | chinese_coverage
language                 python | java
task_type                one of the six frozen task types
dataset_id               frozen dataset identifier
project_id               frozen project/fixture identifier
query_text               exact text passed to all compared retrievers
ground_truth_id          linked annotation record identifier
authoring_source         self_repository | fixture
notes                    non-answer-bearing protocol note or null
```

The embedding adapter may add its frozen `query: ` model instruction internally;
the stored and BM25-visible `query_text` stays unchanged. Query records contain no
retriever score, rank, generated answer, hidden model hint, or result-derived label.

## 5. Ground Truth and Annotation

### 5.1 Canonical evidence model

Ground truth is human annotated independently of evaluated rankings. Graph facts and
source navigation may assist validation, but no evaluated retriever may generate,
select, or revise its own truth.

The canonical annotation unit is a source-evidence record. It identifies the relevant
file, optional `SymbolId`, and optional normalized source span. Unit-specific truth is
derived from this one evidence record under Section 6; separate ad hoc truth sets for
File, Symbol, and Chunk are prohibited.

### 5.2 Relevance grades

- `2` — directly necessary or best evidence for answering/localizing the query;
- `1` — useful supporting evidence that materially contributes to the task; and
- `0` — judged non-relevant for the query.

Grades `1` and `2` are relevant for Recall, MRR, Precision, and Hit Rate. nDCG retains
the graded values. Unjudged candidates are treated as grade `0` for metric
calculation and are retained for audit; they are not silently counted as relevant.

Every frozen query must have at least one grade-1-or-2 item. A query without relevant
truth fails the Phase 6.2 dataset gate rather than entering a metric denominator.

### 5.3 Ground-truth schema

Each canonical record contains:

```text
ground_truth_id
ground_truth_version
query_id
dataset_id
project_id
evidence[]:
  relative_path
  symbol_id | null
  start_offset | null
  end_offset | null
  start_line | null
  end_line | null
  relevance                 2 | 1 | 0
  rationale
annotation_status           drafted | reviewed | adjudicated | frozen
primary_annotator_id
reviewer_id
adjudicator_id | null
created_at
reviewed_at
```

`symbol_id`, when present, serializes all authoritative `SymbolId` fields. Offsets use
zero-based, end-exclusive positions in LF-normalized source. Timestamps are audit
metadata and are excluded from relevance decisions.

### 5.4 Annotation protocol

1. The primary annotator reads the frozen query and source and assigns evidence,
   grades, and rationale without retrieval rankings.
2. As clarified and frozen by **Annotation Protocol Clarification Addendum A (`v1`)**,
   the sole human annotator is `wang`; a second human annotator is absent. Every English
   test query and every grade-2 item receives a delayed blinded self-review by `wang`
   after at least 48 hours. Dev and Chinese coverage receive the same delayed blinded
   self-review for consistency.
3. The delayed reviewer sees only the query and frozen source evidence until a new
   judgment is recorded; the initial grade is revealed only for the subsequent
   comparison. Disagreements on relevance, identity, or span set an ambiguity flag and
   require an adjudication note before freeze. Any material correction requires a
   ground-truth version/hash bump. The final record never erases the disagreement or
   the fact that adjudication occurred.
4. Automated validation checks IDs, paths, spans, Symbol identities, allowed grades,
   duplicate evidence, and the existence of at least one relevant item.
5. Phase 6.2 freezes the query and truth hashes together. Later typo-only corrections
   require a version bump and audit note. A relevance change invalidates prior formal
   results for the affected result namespace.

`reviewer_id = wang` denotes delayed blinded self-review, not second-person review.
`adjudicator_id` is null when no adjudication occurs and `wang` when the recorded
disagreement is adjudicated. Independent model/data audit may validate manifests,
hashes, leakage, masked samples, and dataset consistency, but it is not human
annotation. Human inter-annotator agreement is unavailable and must not be claimed or
calculated from self-review or model audit. Addendum A is authoritative for the full
workflow, audit fields, reviewer/adjudicator semantics, and thesis limitation.

### 5.5 Leakage controls

- English test queries and truth are frozen before the first formal run.
- Dev results may validate infrastructure and presentation only; the weights, model,
  chunk policy, Graph budgets, metrics, and `top_k` are already frozen here.
- Annotators do not see evaluated rankings while drafting or reviewing truth.
- Test-query text and relevance labels do not enter index text, embedding text,
  lexical enrichment, Graph score, or configuration selection.
- No query is copied from a target signature or comment solely to guarantee a hit;
  unavoidable identifiers are documented.
- Near-duplicate dev/test/coverage queries are rejected during Phase 6.2 review.
- After any formal English-test result exists, parameters may not be tuned to that
  result. A changed parameter creates a new, explicitly exploratory protocol version
  and cannot replace the preregistered result.
- Failed, hard, or unfavorable queries remain in the denominator and raw output.

## 6. File, Symbol, and Chunk Fairness Mapping

These File and Chunk representations are experiment-only baselines. They do not
modify production `RetrievalConfig.retrieval_unit="symbol"`.

### 6.1 File baseline

- identity: normalized `relative_path`;
- source unit: the complete LF-normalized source file;
- indexed text:

```text
relative_path + "\n" + full_source
```

The grade of a File candidate is the maximum grade of canonical evidence in that
file.

### 6.2 Symbol baseline

- identity: authoritative `SymbolId`;
- source unit: Phase 1 `RetrievalDocument`;
- indexed text:

```text
qualified_name + "\n" + source_text
```

The grade of a Symbol candidate is the maximum grade of canonical evidence explicitly
attached to that Symbol or whose frozen evidence span lies inside the Symbol range.
Evidence that cannot be mapped reliably to a Symbol remains available to File/Chunk
but is not fabricated as Symbol truth.

### 6.3 Chunk baseline

- source: complete LF-normalized file source;
- size: 1200 characters;
- overlap: 200 characters;
- stride: 1000 characters;
- identity: `(relative_path, start_offset, end_offset)`;
- indexed text:

```text
relative_path + "\n" + chunk_text
```

Offsets count Unicode code points, are zero-based and end-exclusive, and refer to the
LF-normalized source. Chunks begin at offsets `0, 1000, 2000, ...`; `end_offset` is
`min(start_offset + 1200, len(source))`. A final non-empty partial chunk is retained;
empty chunks are not created. No line, token, AST, or whitespace boundary adjustment
is permitted.

The grade of a Chunk is the maximum grade of canonical evidence whose non-empty source
span overlaps the Chunk. Symbol-only evidence uses the frozen Symbol source span for
this mapping.

### 6.4 Shared lexical contract

All three RQ1 units use `code-lexical-v1`, BM25 `k1=1.5`, and `b=0.75`. They use the
same query text and `top_k=10`. The different identity prefix (`relative_path` versus
`qualified_name`) is part of the frozen unit representation and is reported as a
threat to construct validity, not hidden as identical input.

## 7. Metrics

### 7.1 Retrieval metric boundary

Retrieval metrics are calculated on the final ranked hits **before** ContextBuilder.
Only unique candidate identities count. Context metrics and diagnostics are reported
separately and never alter a retrieval rank or relevance grade.

The runner must emit per-query metric inputs and outputs so an independent audit can
recompute every aggregate.

### 7.2 K values and relevance

The frozen K values are `1`, `5`, and `10`; all runs use `top_k=10`.

For query `q`, let `R_q` be all grade-1-or-2 relevant identities under the active
unit mapping and let `H_q@K` be the first K unique ranked identities.

- `Recall@K = |R_q ∩ H_q@K| / |R_q|` for K in 1, 5, 10.
- `MRR` is reciprocal rank of the first grade-1-or-2 hit within the top 10; it is 0
  when none occurs.
- `Precision@5 = |R_q ∩ H_q@5| / 5`; a short result list retains denominator 5.
- `Hit Rate@5` is 1 when at least one relevant item occurs in the top 5, otherwise 0.
- `nDCG@5` uses gain `2^relevance - 1`, discount `log2(rank + 1)`, and the ideal
  ordering for the active unit truth. If ideal DCG is zero, dataset validation has
  failed because every query must have relevant truth.

Each reported aggregate is the macro arithmetic mean over the fixed query set. Raw
per-query values, counts, and language/task-type strata are also reported. No query is
weighted by its number of relevant items, and no micro/macro substitution is allowed.

### 7.3 Reporting hierarchy

- Primary: `Recall@5`, `MRR`.
- Also mandatory: `Recall@1`, `Recall@10`.
- Secondary in the main body: `nDCG@5`.
- Appendix: `Precision@5`, `Hit Rate@5`.

English test is the primary aggregate. Python/Java and six task-type slices accompany
it. Chinese coverage is a separate table. Dev is clearly labelled non-test evidence.

No composite score, weighted metric total, or post-hoc winner index may be created.

### 7.4 Failed-query denominator

A failed query remains in the denominator and receives `0` for retrieval metrics,
with `status`, `failure_type`, and `failure_stage` retained in raw output. Failure
counts are reported beside aggregates. This rule does not convert an invalid formal
run into valid evidence: Section 12 may additionally invalidate the whole run.

### 7.5 Context diagnostics

ContextBuilder is applied after ranking only where the matrix requests context output.
The fixed budget is `8000` characters. The separate context report contains:

- relevant-ground-truth evidence rendered / total relevant evidence;
- relevant ranked hits rendered / relevant ranked hits;
- `budget_used`, budget-utilization ratio, snippet count, and context characters;
- package/snippet truncation count and rate;
- ranked hits not rendered;
- Graph-only rendered snippets; and
- retained but unrendered Graph provenance count.

These are context diagnostics, not retrieval metrics. They are not pooled into
Recall, MRR, nDCG, or a composite score.

## 8. Frozen Runtime and Retrieval Configuration

### 8.1 Real E5 runtime

| Field | Frozen value |
| --- | --- |
| Model | `intfloat/multilingual-e5-base` |
| Revision | `d128750597153bb5987e10b1c3493a34e5a4502a` |
| Python | `3.12.14` |
| torch | `2.8.0` |
| transformers | `4.56.2` |
| Device/dtype | CPU / float32 |
| Dimension | 768 |
| Pooling | attention-mask-aware mean pooling |
| Normalization | L2 |
| Similarity | exact cosine |
| Query instruction | `query: ` |
| Document instruction | `passage: ` |
| Token policy | `512-token-explicit-truncation-v1` |

The model and tokenizer must resolve to the same frozen revision and run from a
verified local cache without network fallback during a formal run. The embedding
fingerprint and its deterministic hash are stored in every semantic-dependent run.

### 8.2 Truncation policy

The adapter applies explicit truncation to at most 512 total tokens, including special
tokens. It records untruncated total tokens, effective content limit, truncated flag,
and dropped-token count for every indexed document and query. Silent truncation is a
protocol failure.

Formal reports include truncated counts/rates overall and by dataset, language, and
split. A predeclared sensitivity table separates queries whose grade-2 or grade-1
relevant documents were truncated from queries whose relevant documents were not.
The main result remains the full fixed set; truncated queries are never removed.
Truncation evidence may motivate a future protocol but may not trigger a model,
chunking, or max-length change inside this result namespace.

### 8.3 Hybrid configuration

Primary Weighted Fusion uses:

```text
lexical_weight  = 1.0
semantic_weight = 1.0
graph_weight    = 0.25 when Graph ON, otherwise 0.0
top_k           = 10
```

BM25 normalization is branch maximum. Exact cosine is clamped to `[-1, 1]` and mapped
to `[0, 1]`. Missing components contribute zero. Weights need not sum to one because
the final score is ranking-relative.

RRF robustness runs use `rrf_k=60`, the same branch weights, dataset, query set,
ground truth, Graph configuration, and `top_k`. RRF remains secondary and is never
used to tune the Weighted result.

### 8.4 Graph configuration

Primary Graph ON uses:

```text
max_hops               = 1
relations              = CONTAINS + IMPORTS
max_expanded_per_seed  = 5
max_total_context_nodes = 30
```

The frozen score is `relation_factor * direction_factor / hop` with
`IMPORTS=1.0`, `CONTAINS=0.75`, `FORWARD=1.0`, and `REVERSE=0.8`. Multiple
provenances retain their deterministic tuple and use the maximum Graph signal.

The four secondary RQ3 pair runs keep every numeric setting fixed and admit exactly
one `(relation, direction)` signal. This experiment-side signal filter changes no
production `ProjectGraph` or relation kind.

## 9. Formal Experiment Matrices

### 9.1 RQ1 — Lexical retrieval unit

| Run | Unit | Lexical | E5 | Graph | ContextBuilder |
| --- | --- | --- | --- | --- | --- |
| RQ1-FILE | File | BM25 | OFF | OFF | OFF for retrieval metrics |
| RQ1-SYMBOL | Symbol | BM25 | OFF | OFF | OFF for retrieval metrics |
| RQ1-CHUNK | Chunk 1200/200 | BM25 | OFF | OFF | OFF for retrieval metrics |

### 9.2 RQ2 — Lexical versus real E5

| Run | Unit | Lexical weight | Semantic weight | Model | Graph |
| --- | --- | ---: | ---: | --- | --- |
| RQ2-BM25 | Symbol | 1.0 | 0.0 | none | OFF |
| RQ2-E5 | Symbol | 0.0 | 1.0 | pinned real E5 | OFF |

Both receive exactly one `qualified_name + "\n" + source_text` document input and
the exact same stored query text. The E5 adapter alone adds its required instructions.

### 9.3 RQ3 — Graph contribution

| Run | Fusion | L/S/G weights | Graph signals |
| --- | --- | --- | --- |
| RQ3-GRAPH-OFF | Weighted | 1.0 / 1.0 / 0.0 | none |
| RQ3-GRAPH-ON | Weighted | 1.0 / 1.0 / 0.25 | all four pairs |
| RQ3-CONTAINS-F | Weighted | 1.0 / 1.0 / 0.25 | CONTAINS/FORWARD only |
| RQ3-CONTAINS-R | Weighted | 1.0 / 1.0 / 0.25 | CONTAINS/REVERSE only |
| RQ3-IMPORTS-F | Weighted | 1.0 / 1.0 / 0.25 | IMPORTS/FORWARD only |
| RQ3-IMPORTS-R | Weighted | 1.0 / 1.0 / 0.25 | IMPORTS/REVERSE only |

The first two rows are the primary RQ3 comparison. The four pair rows are secondary
attribution, not a weight/hop grid search.

### 9.4 RQ4 — Signal ablation

| Run | Fusion | L/S/G weights | Graph |
| --- | --- | --- | --- |
| RQ4-LEXICAL | Weighted identity mode | 1.0 / 0.0 / 0.0 | OFF |
| RQ4-EMBEDDING | Weighted identity mode | 0.0 / 1.0 / 0.0 | OFF |
| RQ4-HYBRID-NO-GRAPH | Weighted | 1.0 / 1.0 / 0.0 | OFF |
| RQ4-HYBRID-GRAPH | Weighted | 1.0 / 1.0 / 0.25 | ON |

All four rows produce ranked-hit metrics before ContextBuilder. ContextBuilder then
runs with the fixed 8000-character budget for the two Hybrid rows and produces only
the separate context diagnostics in Section 7.5. Lexical-only and Embedding-only
context packages may be retained as appendix diagnostics but are not required for the
primary RQ4 conclusion.

### 9.5 RRF robustness

RRF repeats `RQ4-HYBRID-NO-GRAPH` and `RQ4-HYBRID-GRAPH` with `rrf_k=60`. It is
labelled secondary robustness evidence, appears in separate tables, and does not alter
the preregistered Weighted comparison or determine a winner.

## 10. Performance Protocol

### 10.1 Environment capture

Every timing record includes OS/build, CPU model and logical/physical core count, RAM,
power mode, Python implementation/version, `torch`/`transformers` versions, device,
dtype, thread-related environment, Git commit, dataset size, document count, vector
count/dimension, config hash, and whether caches were cold or warm. Network access is
disabled for model loading and inference.

### 10.2 Measurements

The formal engineering report records:

- full lexical index build time;
- full real-E5 embedding/index build time, with model-load time separated;
- incremental update time;
- per-query retrieval latency by configuration;
- ContextBuilder and end-to-end service latency separately;
- logical index payload size and process RSS delta, clearly distinguished; and
- context character size, snippet count, and truncation.

Quality results are deterministic and are executed once per frozen formal run.
Timing repetition exists only to characterize runtime noise: after five untimed warm-up
queries, each fixed query/configuration is timed 30 times in one declared order, and
median and p95 are reported with all samples preserved. Full-build and incremental
measurements use three clean measured runs when feasible; if the real-E5 cost prevents
three runs, one complete run is allowed only with an explicit limitation and may not
support a variance claim.

No process is silently mixed between cold and warm conditions. Millisecond fixture
results are not presented as production scalability or an SLA.

### 10.3 Incremental experiment

**Addendum B controls the incremental fixture counts in this section:**
`docs/experiments/Experiment_Protocol_Addendum_B_V3_1_0.md`. The `3/2/2`
SnapshotDiff and `5` embedding-document figures below remain historical text.

Incremental indexing is a secondary engineering experiment, not a fifth research
question. Phase 6.2 freezes a base fixture snapshot and one update with exactly:

- 3 changed Symbols;
- 2 added Symbols; and
- 2 removed Symbols.

The experiment compares incremental update with full rebuild of the final snapshot.
It must verify exact equality of index identity, ordered documents/content hashes,
BM25 ranks/scores, Semantic ranks/scores, and final retrieval results. With real E5,
new document embedding calls must equal changed plus added (`5`); removed and
unchanged Symbols produce zero document-embedding calls.

A separate deterministic 5,000/10,000-Symbol synthetic scaling probe may measure the
non-model update path and doubling ratio. Fake/precomputed vectors are allowed only
for this clearly labelled algorithmic engineering probe and cannot support semantic
quality or real-E5 latency claims. No absolute pass threshold is inferred from prior
Phase 4 smoke timings; stable O(N^2) behavior, result inequivalence, or unexpected
embedding calls fail the incremental experiment.

## 11. Artifact Layout and Schemas

### 11.1 Layout

The versioned artifact layout is:

```text
docs/experiments/
  Experiment_Protocol_V3_1_0.md
  datasets/v1/
    manifest.json
    fixtures/
  queries/v1/
    queries.jsonl
  ground_truth/v1/
    ground_truth.jsonl
    annotation_audit.jsonl
  configs/v1/
    *.json
  runs/<run_id>/
    run_manifest.json
    raw_results.jsonl
    aggregate_results.json
    context_results.jsonl
    performance.json
    checksums.sha256
  audits/
  figures/
```

Phase 6.0 creates only this protocol. Later phases create only the artifacts they own.
Large model files, vector indexes, embedding caches, temporary checkouts, and runtime
caches are never committed. Raw results, aggregates, audits, and paper-ready figures
remain distinct.

### 11.2 Raw result schema

Each `raw_results.jsonl` record contains at least:

```text
run_id, protocol_version, matrix_run_id
query_id, split, language, task_type, dataset_id, project_id
status, failure_type, failure_stage, degraded, degradation_reason
top_k, retrieval_config_hash, index_identity
ranked_hits[]:
  rank, candidate_identity, relative_path, symbol_id | null,
  start_offset | null, end_offset | null,
  raw_lexical_score | null, raw_semantic_score | null,
  normalized_lexical_score, normalized_semantic_score,
  graph_score, graph_provenance[], final_score, relevance
metrics:
  recall_at_1, recall_at_5, recall_at_10, mrr,
  ndcg_at_5, precision_at_5, hit_rate_at_5
latency_ns
```

Semantic-dependent records also link the embedding fingerprint and token diagnostics.
Raw records are append-only evidence. Corrections produce a new run ID; raw values are
never manually edited to improve a result.

### 11.3 Aggregate result schema

`aggregate_results.json` contains:

```text
run_id, protocol_version, matrix_run_id
dataset/query/ground_truth/config versions and hashes
code commit, embedding fingerprint, index identity
population filters and denominator count
success, failure, invalid, and degraded counts
macro metric values and per-task/per-language/per-split strata
context diagnostic summary references
performance artifact reference
raw_results_sha256
aggregation_implementation_version
aggregate_created_at
```

It must be reproducible solely from frozen inputs and raw results. Aggregate files do
not contain manually transcribed thesis numbers.

### 11.4 Reproducibility fields

Every run manifest records:

- protocol ID/version/hash;
- dataset ID/version/hash and complete path/file manifest hash;
- query-set version/hash;
- ground-truth version/hash;
- retrieval configuration records and hashes;
- self-repository and runner code commits plus dirty-state flag;
- embedding fingerprint, model/tokenizer repository and revision, cache artifact
  verification, dimension, instructions, normalization, similarity, and token policy;
- Python, dependency, OS, CPU, RAM, device, dtype, and thread settings;
- applicable random seeds and `PYTHONHASHSEED` (or explicit `not applicable`);
- index identity;
- UTC start/end time and run ID;
- raw/aggregate/context/performance checksums; and
- operator and independent-audit status.

Timestamps identify execution but never enter dataset, query, truth, configuration,
index, ranking, or metric identity.

## 12. Failure and Degraded-Mode Policy

- A failed query is retained and scored zero; it is never removed from a denominator.
- Stale/missing source, path/hash drift, Snapshot mismatch, corrupt index, config or
  fingerprint mismatch, malformed truth, and metric non-finiteness fail closed.
- A global E5 load, tokenizer, revision, dimension, or inference failure makes every
  affected semantic-dependent experiment **FAILED**.
- Fake/hash embeddings may not replace real E5 in RQ2, RQ3, RQ4, RRF, or formal
  semantic performance evidence.
- Production Hybrid may support a marked Lexical fallback, but a formal
  semantic-dependent benchmark may not present degraded fallback as a normal Hybrid
  result. Any `degraded=True` result makes that formal semantic-dependent run
  **INVALID / FAILED**. The raw degraded record is preserved for diagnosis.
- Partial completion may be shown as diagnostic evidence but cannot support the
  corresponding RQ conclusion.
- A rerun after infrastructure failure uses the exact same frozen inputs and config,
  receives a new run ID, links the failed run, and states why the rerun was necessary.

## 13. Claim Discipline

Results may support only comparisons directly executed under this frozen protocol.
Reports must distinguish association from causation, primary from secondary metrics,
English main results from Chinese coverage, Python from Java coverage, retrieval
quality from context diagnostics, and engineering timings from scalability claims.

The project may claim neither a novel BM25/embedding/graph algorithm nor general
superiority beyond the frozen dataset. Statistical significance is not manufactured
through repeated deterministic retrieval. Effect sizes are the transparent paired
per-query metric differences; optional paired uncertainty analysis, if later reviewed,
must be labelled supplemental and cannot redefine the primary metrics.

Negative, null, failed, and counterintuitive findings remain in the record. No metric,
query, task type, language, or run is suppressed because it weakens a preferred
conclusion. Formal test results may not be used to tune weights, Graph settings,
chunking, E5, `top_k`, ContextBuilder budget, or ground truth.

## 14. Threats to Validity

The final research report must discuss at least:

- **construct validity:** relevance grades and unit mapping may imperfectly represent
  maintenance usefulness; File/Chunk use path enrichment while Symbol uses qualified
  name enrichment; retrieval metrics do not measure final patch correctness;
- **internal validity:** single-annotator judgment, incomplete unjudged pools, query
  wording, truncation, parser limitations, Graph resolution, and implementation
  defects may affect rankings; delayed blinded self-review mitigates but does not
  eliminate single-annotator bias;
- **external validity:** one self-repository, constructed fixtures, Python emphasis,
  limited Java support, one real embedding model, CPU execution, and a modest corpus
  limit generalization;
- **conclusion validity:** 48 primary English test queries constrain precision of
  subgroup conclusions; deterministic results do not justify artificial repeated-run
  significance; multiple secondary slices increase cherry-picking risk; and
- **reproducibility validity:** local model cache, hardware/runtime variation, host
  timing noise, and future dependency availability may affect exact replication even
  with frozen revisions.

Mitigations are frozen manifests/hashes, paired queries, one canonical truth model,
at-least-48-hour delayed blinded self-review/adjudication, raw per-query results,
exact configs/fingerprints, separate coverage tables, explicit failures, and
independent Phase 6.5 model/data audit. The thesis must disclose that ground truth has
one human annotator and no second-human annotation or human inter-annotator agreement.

## 15. Phase 6 Subphases and Gates

| Subphase | Scope | Exit condition |
| --- | --- | --- |
| Phase 6.0 | Protocol Documentation Freeze | this protocol committed and state recorded |
| Phase 6.1 | Benchmark Infrastructure | runner/metrics/schema implementation independently validated, no formal data result |
| Phase 6.2 | Dataset / Query / Ground Truth Freeze | 72 queries, manifests, annotations, hashes, leakage review frozen |
| Phase 6.3 | Dry Run | dev-only execution, schema/metric recomputation, E5/runtime/failure checks PASS |
| Phase 6.4 | Formal Benchmark & Ablation | first formal RQ1–RQ4 run under exact frozen inputs |
| Phase 6.5 | Independent Result Audit + Research Documentation Gate | raw-to-aggregate recomputation, claim and reproducibility audit PASS |

The first formal RQ1–RQ4 run is forbidden until **Phase 6.3 Dry Run PASS** is recorded.
A dry run uses English dev only; it may not expose or execute the English test result.

## 16. Stop Conditions

Phase 6 work stops before a formal run when any of the following is true:

- protocol, dataset, query, ground-truth, config, or code hash is missing or mismatched;
- the self-repository is not the frozen commit or contains an absorbed untracked path;
- the 72-query allocation, language split, task-type split, or relevant-truth minimum
  is violated;
- annotation leakage, unresolved disagreement, invalid path/span/Symbol identity, or
  near-duplicate split leakage remains;
- Phase 6.1 or 6.2 gate is not closed, or Phase 6.3 Dry Run is not PASS;
- the pinned E5 runtime, revision, dimension, L2/cosine behavior, instructions, or
  truncation diagnostics cannot be reproduced;
- a fake provider, network fallback, silent truncation, degraded Hybrid result, or
  deleted failed query enters formal semantic evidence;
- metrics cannot be independently recomputed from raw hits and truth;
- ContextBuilder output is mixed into retrieval ranking metrics;
- non-finite score/metric, nondeterministic ranking, incremental/full-rebuild
  inequivalence, unexpected embedding calls, or stable O(N^2) update behavior appears;
- any formal test result has already been used to change parameters or labels without
  a new reviewed protocol version; or
- production code, tests, dependencies, thesis documents, V3.2, or another prohibited
  scope is changed as a shortcut around this protocol.

When stopped, preserve the failed artifact, record the reason, and return to the
owning subphase. Do not reinterpret a stop as a negative RQ result.

## 17. Freeze Declaration

This protocol freezes experiment interpretation before formal evidence exists.

- Phase 6.0: **COMPLETED / PROTOCOL FROZEN**
- Formal RQ1–RQ4: **NOT STARTED**
- Phase 6.1: **ALLOWED BUT NOT STARTED**
- V3.2: **NOT STARTED**
- Formal test results, once produced, may not be used for parameter tuning within this
  protocol version.
