# V3.1.0 Phase 6.2 — Dataset / Query / Ground Truth Specification

## 1. Status, authority, and scope

- Specification version: `v3.1-phase6-dataset-spec-v1`
- Status: **FROZEN**
- Phase 6.2.0: **COMPLETED / SPECIFICATION FROZEN**
- Dataset, query set, and ground truth: **NOT CREATED**
- Phase 6.2A: **ALLOWED BUT NOT STARTED**
- Phase 6.2 Gate: **OPEN**
- Phase 6.3 and formal RQ1–RQ4: **NOT STARTED / NOT ALLOWED**

This document is the complete repository Source of Truth for Phase 6.2A materialization.
It freezes the concrete dataset, fixture, query, evidence-authoring, leakage, identity,
and validation decisions beneath the research method frozen by
`Experiment_Protocol_V3_1_0.md` and the annotation workflow clarified by
`Experiment_Protocol_Addendum_A_V3_1_0.md`.

**Incremental fixture correction:** Addendum B at
`docs/experiments/Experiment_Protocol_Addendum_B_V3_1_0.md` supersedes only
the historical incremental SnapshotDiff and embedding-document counts in Sections
3.4 and 13. Within that scope, Addendum B is the latest normative authority;
the original figures below remain as the frozen historical record.

Authority order is:

1. the frozen Experiment Protocol plus Addendum A;
2. this corrected and final Dataset Specification; and
3. historical review notes and `PROJECT_CONTEXT.md`.

The Protocol defines the research method and global experiment rules. Addendum A
defines the single-annotator review contract. This specification defines the concrete
Phase 6.2 dataset, fixture, query, and truth-authoring decisions. It does not redefine
metrics, K values, Hybrid weights, production Graph behavior, the E5 identity, or the
formal research questions.

Design provenance: Grok 4.7 Phase 6.2 Dataset / Query / Ground Truth Review, followed
by Grok 4.7 Specification Correction; cross-audit by GPT-5.6 Sol; repository
materialization by Codex. This is design/review provenance, not empirical evidence.

## 2. Dataset identity and frozen self-repository

Primary dataset identity:

| Field | Frozen value |
| --- | --- |
| `dataset_id` | `v3.1-phase6-dataset-v1` |
| `version` | `v1` |
| `protocol_version` | `v3.1-phase6-protocol-v1` |
| Self project ID | `self-code-comments-agent` |
| Self source kind | `self_repository` |
| Self source revision | `12391233daa2149ead4f451e920b2e0d8a1a6beb` |
| Self fixture hash | `null` |

Only Git-tracked regular `.py` and `.java` files recognized by the existing
`ProjectScanner`/adapter boundary at the frozen commit are eligible. Production and
test source are both included; files below `tests/` have `path_role=test`, and all
other eligible files have `path_role=production`. The frozen commit's root
`.gitignore` and scanner exclusions apply. Symlinks, untracked content, Phase 6 code,
`experiments/`, `tests/test_experiment_benchmark_infrastructure.py`, and every file
introduced after the frozen commit are excluded. In particular, untracked
`docs/thesis/` content is never part of the corpus.

Each self-repository file hash is `SHA-256(raw Git blob bytes)`, not a Git object ID
and not a working-tree hash. Manifest paths are repository-relative POSIX paths. The
frozen commit has zero eligible source files excluded by scanner/root `.gitignore`
and zero eligible symlinks. Non-source tracked files such as Markdown, environment
examples, workflows, `.gitignore`, `pytest.ini`, and requirements files are outside
the adapter boundary.

### 2.1 Frozen statistics

Phase 6.2A must recompute these values from the frozen commit and stop on any mismatch;
it must never change the filter to make the figures fit.

| Statistic | Frozen value |
| --- | ---: |
| Python files | 72 |
| Java files | 0 |
| Production files | 44 |
| Test files | 28 |
| Symbols | 1233 |
| Classes | 190 |
| Methods | 377 |
| Functions | 666 |
| Zero-symbol files | 8 |
| File baseline documents | 72 |
| Chunk baseline documents | 857 |
| Symbols longer than 1200 characters | 151 |
| Symbols overlapping at least two chunks | 747 |

All 72 source files use LF line endings. The eight zero-symbol files are:

- `Java/__init__.py`
- `Py/__init__.py`
- `admin_operations/__init__.py`
- `code_maintenance/__init__.py`
- `credits/__init__.py`
- `main.py`
- `managed_access/__init__.py`
- `project_intelligence/__init__.py`

They remain part of the File and Chunk baselines.

## 3. Fixture projects

The primary dataset adds three versioned fixtures:

- `fixture-py-route-ledger`
- `fixture-py-intake-queue`
- `fixture-java-desk-queue`

The separate engineering fixture `fixture-py-incremental-delta` belongs to dataset
`v3.1-phase6-incremental-v1` and is not part of the 72-query primary dataset or the
RQ1–RQ4 aggregate. Fixture source revisions are `fixture-v1`. Fixture design is
domain/maintenance behavior first and query sampling second; query bookkeeping must
not create extra APIs or symbols.

For each fixture, `fixture_hash` is the canonical SHA-256 over records sorted by
relative path, where each record contains `path`, `language`, and the file's raw-byte
SHA-256. Filesystem timestamps, absolute paths, and random UUIDs are forbidden inputs.

### 3.1 `fixture-py-route-ledger`

Required files, symbols, and behavior:

- `route_ledger/__init__.py`: no symbol.
- `route_ledger/models.py`: `RouteStatus`, `RouteStatus.label`, `RouteEntry`,
  `RouteEntry.remaining_stops`, `RouteEntry.mark_closed`, and `validate_entry`.
  `mark_closed` changes the status to closed without clearing remaining stops;
  `remaining_stops` returns the remaining count; `validate_entry` rejects an empty ID.
- `route_ledger/policy.py`: `StopPolicy`, `StopPolicy.can_close`,
  `StopPolicy.counts_as_open`, and `StopPolicy.allows_skip`. `can_close` is true only
  when remaining stops equal zero; `counts_as_open` is false for closed or skipped
  state; `allows_skip` permits a stop to be marked skipped.
- `route_ledger/store.py`: `MemoryRouteStore`, `save`, `load_all`, and `delete`.
  Storage is an in-memory dictionary and `save` replaces by ID.
- `route_ledger/service.py`: `RouteService`, `open_route`, `add_stop`, `close_route`,
  and `reopen`. `close_route` calls `can_close`, then `mark_closed`, then `save`.
  Statement-level `import route_ledger.store` and `import route_ledger.policy` must
  exist.
- `route_ledger/report.py`: `RouteReport`, `count_open_stops`, `summarize`, and
  `closed_count`. The planted defect is that `count_open_stops` checks only
  `remaining_stops > 0` and does not call `counts_as_open`, so a closed route can be
  counted as open.
- `route_ledger/notify.py`: `RouteNotifier`, `notify_closed`, and `format_message`.
  `notify_closed` formats a message only for closed state.
- `tests/test_route_service.py`: `test_closed_route_is_not_open` and
  `test_skipped_stop_is_not_open`; these express expected behavior and are not the
  defective implementation.

### 3.2 `fixture-py-intake-queue`

Required files, symbols, and behavior:

- `intake_queue/__init__.py`: no symbol.
- `intake_queue/envelope.py`: `Envelope`, `Envelope.declared_checksum`, and
  `compute_checksum`; the checksum is computed from ID plus body.
- `intake_queue/rules.py`: `IntakeRules` and `IntakeRules.accepts`; a declared
  checksum different from `compute_checksum` is rejected.
- `intake_queue/parser.py`: `IntakeParser`, `normalize_payload`, `reject_reason`, and
  `last_record_included`. The LF-normalized `normalize_payload` source span is
  1500–1800 characters and overlaps chunks `(0,1200)` and `(1000,...)`.
  `reject_reason` lies wholly in offset `[0,700)`. `last_record_included` starts at
  offset 1400 or later and shares no chunk with `reject_reason`. The planted defect
  drops the last record when a payload has no trailing newline.
- `intake_queue/dispatcher.py`: `Dispatcher`, `enqueue`, and `dispatch_ready`; only an
  envelope accepted by `IntakeRules.accepts` enters the send queue.
- `intake_queue/audit.py`: `IntakeAudit.record`, recording rejected envelope ID plus
  reason.
- `tests/test_intake.py`: `test_last_line_without_newline_is_kept`, asserting that a
  final line without a newline is retained.

The following withdrawn query-only APIs are forbidden:
`IntakeAudit.rejected_ids`, `IntakeAudit.append_reason`, `IntakeRules.reason_code`,
and `Dispatcher.pending_ids`.

### 3.3 `fixture-java-desk-queue`

Every file has one top-level public class. Wildcard imports, static imports,
`extends`, `implements`, enums, and nested classes are forbidden. Overloads use
different parameter types, have different `semantic_disambiguator` values, and use
`fallback_line=null`. Every `package.Type` must resolve uniquely.

- `src/com/desk/model/Ticket.java`, package `com.desk.model`: `Ticket`, constructor
  `Ticket(String,String)`, `id`, `title`, `isOpen`, `markClosed`, and `statusLabel`.
- `src/com/desk/model/DeskClock.java`: `DeskClock` and `minutesUntil`.
- `src/com/desk/store/TicketFolder.java`: exact import `com.desk.model.Ticket`;
  `TicketFolder`, `put`, and `find`. `find` returns a detached copy.
- `src/com/desk/notify/DeskMail.java`: `DeskMail` and `render`.
- `src/com/desk/audit/DeskAudit.java`: exact import `com.desk.model.Ticket`;
  `DeskAudit` and `recordOpen`.
- `src/com/desk/service/DeskQueue.java`: exact imports of `Ticket`, `DeskClock`,
  `TicketFolder`, `DeskMail`, and `DeskAudit`; symbols `DeskQueue`,
  `openTicket(String,String)`, `openTicket(String,String,String)`, `closeTicket`,
  `notifyOwner`, `listOpen`, and `minutesLate`.

The two-argument `openTicket` constructs a `Ticket`, calls `put`, and calls
`recordOpen`; the three-argument overload also saves a free-text note. `closeTicket`
calls `markClosed` on the detached copy returned by `find` but does not put it back.
`listOpen` counts every ticket in the folder without calling `isOpen`. `notifyOwner`
always calls `render` without checking open state. `minutesLate` calls
`DeskClock.minutesUntil`. `statusLabel` returns only open/closed. `isOpen` is true
only when status is open.

### 3.4 `fixture-py-incremental-delta`

**Addendum B supersedes the incremental counts below:**
`docs/experiments/Experiment_Protocol_Addendum_B_V3_1_0.md`.

Base symbols are `Bin`, `Bin.put`, `Bin.remove`, `checksum`, `Shelf`, `Shelf.add`, and
`Shelf.drop`. The update must produce exactly:

- changed: `Bin.put`, `Shelf.add`, `checksum` (3);
- added: `Bin.count`, `Shelf.label` (2); and
- removed: `Bin.remove`, `Shelf.drop` (2).

The later formal E5 incremental experiment expects five new embedding calls. Phase
6.2A validates only fixture structure and must not run E5 to validate that count.

## 4. Query population and identity

The query set version is `v3.1-phase6-queries-v1`. There are exactly 72 queries:

| Population | Total | Python | Java | Per task |
| --- | ---: | ---: | ---: | ---: |
| English test | 48 | 36 | 12 | 8 |
| English dev | 12 | 10 | 2 | 2 |
| Chinese coverage | 12 | 12 | 0 | 2 |

Each of `symbol_lookup`, `feature_localization`, `dependency_questions`,
`bug_localization`, `maintenance_tasks`, and `cross_file_understanding` has 12
queries: 8 English test, 2 English dev, and 2 Chinese coverage. Project allocation is
`self-code-comments-agent=32`, `fixture-py-route-ledger=13`,
`fixture-py-intake-queue=13`, and `fixture-java-desk-queue=14`.

IDs use `{split}-{task}-{lang}-{nn}`, with split `et|ed|zh`, task
`sl|fl|dq|bl|mt|cf`, and language `py|ja`. Every ground-truth ID is
`gt-{query_id}`. In the tables below, all evidence not explicitly marked Grade 1 is
Grade 2; an empty Grade 1 cell means that no Grade 1 evidence is frozen. Evidence
anchors are resolved against the named project's real adapter output. Resolution by
qualified name must be unique; zero or multiple matches are a specification conflict
and require STOP, not substitution. Where a path is stated, it is mandatory.

Task mapping: `sl=symbol_lookup`, `fl=feature_localization`,
`dq=dependency_questions`, `bl=bug_localization`, `mt=maintenance_tasks`, and
`cf=cross_file_understanding`.

### 4.1 English test — self repository

| Query ID | Query text | Grade 2 evidence | Grade 1 evidence | Notes |
| --- | --- | --- | --- | --- |
| `et-sl-py-01` | Where is the symbol tokenize used to split a lexical query into terms? | `project_intelligence/lexical.py::tokenize` | — | — |
| `et-sl-py-02` | Where is compare_snapshots? | `code_maintenance/snapshot.py::compare_snapshots` | — | — |
| `et-sl-py-03` | Find expand_graph, which walks project relations under an explicit node budget. | `project_intelligence/graph_expansion.py::expand_graph` | — | — |
| `et-sl-py-04` | Find the scan method that walks the tree and applies ignore rules. | `code_maintenance/scanner.py::ProjectScanner.scan` | — | — |
| `et-fl-py-01` | A corpus build stops because the bytes on disk no longer match the recorded digest. Where is that comparison made while reading source? | `CorpusBuilder._read_source` | `CorpusSnapshotMismatchError` | — |
| `et-fl-py-02` | Where does a blank or punctuation-only query become an empty lexical hit list? | `BM25Index.search` | `tokenize` | `InvalidLexicalQueryError` is unjudged. |
| `et-fl-py-03` | After a managed provider call succeeds, where is the reserved credit usage finally settled? | `ManagedAccessService._finalize_success` | `ManagedAccessService.invoke` | — |
| `et-fl-py-04` | Where is the credit price of a completed token usage computed from the pricing policy? | `TokenPricingPolicy.price_usage` | `TokenPricingPolicy._price` | — |
| `et-dq-py-01` | Which analysis walks import edges to report cycles and files with too many outgoing targets? | `DependencyTool.analyze` | `_strongly_connected_components` | — |
| `et-dq-py-02` | Which code reads Python import and from-import statements before they are turned into graph targets? | `_python_imports` | `_canonicalize_python_target` | — |
| `et-dq-py-03` | Which lookup binds a Java package and top-level type name to exactly one source file? | `ProjectGraphBuilder._java_type_lookup` | `_java_package`; `_java_imports` | Grade 1 anchors are module functions, not builder methods. |
| `et-dq-py-04` | When an administrator grants or adjusts credits, which service method writes the ledger, and which on-disk ledger appends the transaction? | `AdminCreditService._apply` | `SQLiteCreditLedger._append_transaction` | Cross-file mapping probe. |
| `et-bl-py-01` | Incremental index update rejects the operation because the previous index identity is stale. Where is that rejection? | `RetrievalIndex.update` | `RetrievalIndexIdentity.for_snapshot` | — |
| `et-bl-py-02` | An uploaded archive contains an entry whose path escapes the destination directory. Where is that entry rejected? | `processor.py::_extract_zip_safe` | — | — |
| `et-bl-py-03` | A charge is refused because the account balance cannot cover it. Where is that refusal decided for the in-memory ledger? | `InMemoryCreditLedger.charge` | `InsufficientCreditsError` | — |
| `et-bl-py-04` | Newly annotated Java source fails a structural check before it is accepted. Where is that check? | `processor.py::_verify_java_annotated_code` | `_is_valid_java` | — |
| `et-mt-py-01` | The decimal form used for token prices must change. Which helper produces that canonical decimal, and which method applies it while pricing? | `TokenPricingPolicy._canonical_decimal` | `TokenPricingPolicy._price` | — |
| `et-mt-py-02` | Context assembly must drop lower-priority snippets once the character budget is exhausted. Which builder enforces that, and which package object rejects an inconsistent snippet collection? | `ContextBuilder.build` | `ContextPackage.__post_init__` | — |
| `et-mt-py-03` | An administrator grant must keep the operator reason with both the stored admin operation and the ledger note. Which grant entry point and persistence paths must stay consistent? | `AdminCreditService.grant` | `AdminCreditService._record_from_row`; `SQLiteCreditLedger._append_transaction` | — |
| `et-mt-py-04` | The structural bonus must treat containment as weaker than an import, and the relation names live in the graph model. Where are both sides of that change? | `hybrid.py::_graph_signal` | `GraphRelationKind` | — |
| `et-cf-py-01` | How does a snapshot symbol become a retrieval document whose text hash matches the extracted source range? | `CorpusBuilder._document` | `CorpusBuilder.build`; `RetrievalDocument.__post_init__` | — |
| `et-cf-py-02` | How do a term-ranking score and a vector score become one ordered result when either score may be absent? | `HybridRetriever.fuse` | `_lexical_normalization`; `_semantic_normalization` | — |
| `et-cf-py-03` | How does a snapshot difference become a plan of added, removed, and replaced symbols, and which index method applies that plan? | `SnapshotDiff` | `IncrementalIndexPlan.from_diff`; `RetrievalIndex.update` | — |
| `et-cf-py-04` | How are file-to-symbol containment edges and class-to-method containment edges both recorded while the graph is built? | `ProjectGraphBuilder._add_symbols` | `ProjectGraphBuilder._add_class_containment` | — |

### 4.2 English test — Python fixtures

| Query ID | Project | Query text | Grade 2 evidence | Grade 1 evidence | Notes |
| --- | --- | --- | --- | --- | --- |
| `et-sl-py-05` | `fixture-py-route-ledger` | Where is mark_closed? | `RouteEntry.mark_closed` | — | — |
| `et-fl-py-05` | `fixture-py-route-ledger` | Where is the rule that refuses to finish a route while unfinished stops remain? | `StopPolicy.can_close` | `RouteEntry.remaining_stops` | — |
| `et-dq-py-05` | `fixture-py-route-ledger` | Which store operation writes the saved route record, and which type represents that record? | `MemoryRouteStore.save` | `RouteEntry` | — |
| `et-bl-py-05` | `fixture-py-route-ledger` | A route that has already been closed is still included in the open-stop total. Which report calculation causes that, and which policy already knows a closed route is not open? | `RouteReport.count_open_stops` | `StopPolicy.counts_as_open`; `test_closed_route_is_not_open` | — |
| `et-mt-py-05` | `fixture-py-route-ledger` | A skipped stop must not keep the route open. Which policy decision allows the skip, and which open-count rule must honor it? | `StopPolicy.allows_skip` | `StopPolicy.counts_as_open`; `RouteReport.count_open_stops`; `test_skipped_stop_is_not_open` | — |
| `et-cf-py-05` | `fixture-py-route-ledger` | What must the closer, the in-memory store, and the summary report do before a route with no remaining work is treated as closed? | `RouteService.close_route` | `StopPolicy.can_close`; `MemoryRouteStore.save`; `RouteReport.summarize` | Cross-file mapping probe. |
| `et-sl-py-06` | `fixture-py-intake-queue` | Where is compute_checksum? | `compute_checksum` | — | — |
| `et-fl-py-06` | `fixture-py-intake-queue` | Where is an intake body normalized before its declared checksum is judged, including the long normalization routine? | `IntakeParser.normalize_payload` | `IntakeRules.accepts` | Grade 2 span ≥1500 characters and overlaps ≥2 chunks. |
| `et-dq-py-06` | `fixture-py-intake-queue` | Which rule decides that an envelope may be queued, and which function supplies the checksum it compares? | `IntakeRules.accepts` | `compute_checksum` | — |
| `et-bl-py-06` | `fixture-py-intake-queue` | The last intake record disappears when the payload has no trailing newline. Which parser decision drops it, and which nearby explanation string is produced for a rejected record? | `IntakeParser.last_record_included` | `IntakeParser.reject_reason`; `test_last_line_without_newline_is_kept` | `last_record_included` and `reject_reason` are in `parser.py` but share no chunk; `normalize_payload` is unjudged. |
| `et-mt-py-06` | `fixture-py-intake-queue` | Rejected envelopes must be audited with their reason. Which audit writer and which dispatcher handoff must be updated together? | `IntakeAudit.record` | `Dispatcher.enqueue` | — |
| `et-cf-py-06` | `fixture-py-intake-queue` | How does a ready envelope move from checksum acceptance to the send queue and then into the audit log? | `Dispatcher.dispatch_ready` | `IntakeRules.accepts`; `IntakeAudit.record` | — |

### 4.3 English test — Java fixture

All rows use project `fixture-java-desk-queue`.

| Query ID | Query text | Grade 2 evidence | Grade 1 evidence | `graph_note` |
| --- | --- | --- | --- | --- |
| `et-sl-ja-01` | Where is isOpen? | `Ticket.isOpen` | — | `contains` |
| `et-sl-ja-02` | Find the openTicket method that also stores a free-text note. | `openTicket(String,String,String)` | `openTicket(String,String)` | `contains` |
| `et-fl-ja-01` | Where is the message text for a ticket owner produced? | `DeskMail.render` | `DeskQueue.notifyOwner` | `imports_exact_unique` |
| `et-fl-ja-02` | Where is a ticket switched into the closed state? | `Ticket.markClosed` | — | `contains` |
| `et-dq-ja-01` | Which folder operation stores a ticket, and which type is stored? | `TicketFolder.put` | `Ticket` | `imports_exact_unique` |
| `et-dq-ja-02` | Which queue operation asks the clock how many minutes remain, and which clock method answers? | `DeskQueue.minutesLate` | `DeskClock.minutesUntil` | `imports_exact_unique` |
| `et-bl-ja-01` | The open-ticket count includes tickets that are already closed. Which count causes that? | `DeskQueue.listOpen` | `Ticket.isOpen` | `contains` |
| `et-bl-ja-02` | Closing a ticket changes a copy that is never written back, so the stored ticket stays open. Which closer and which lookup return that detached copy? | `DeskQueue.closeTicket` | `TicketFolder.find` | `imports_exact_unique` |
| `et-mt-ja-01` | A waiting label must be introduced without treating it as open or closed. Which method currently returns only the two existing labels? | `Ticket.statusLabel` | — | `contains` |
| `et-mt-ja-02` | Owner notification must stay silent for a closed ticket. Which queue method always renders text today, and which renderer supplies that text? | `DeskQueue.notifyOwner` | `DeskMail.render` | `imports_exact_unique` |
| `et-cf-ja-01` | How does opening a ticket without a note store it and record that opening? | `openTicket(String,String)` | `TicketFolder.put`; `DeskAudit.recordOpen` | `imports_exact_unique` |
| `et-cf-ja-02` | How is a stored ticket found and then given a lateness value from the clock? | `TicketFolder.find` | `DeskQueue.minutesLate`; `DeskClock.minutesUntil` | `imports_exact_unique` |

### 4.4 English dev

English dev exists only for runner, schema, identity, and Phase 6.3 Dry Run. Its
results may not change Hybrid weights, Graph configuration, Chunk size/overlap, K,
test truth, or the E5 model.

| Query ID | Project | Query text | Grade 2 evidence | Grade 1 evidence | `graph_note` |
| --- | --- | --- | --- | --- | --- |
| `ed-sl-py-01` | `fixture-py-intake-queue` | Where is declared_checksum? | `Envelope.declared_checksum` | — | — |
| `ed-sl-ja-02` | `fixture-java-desk-queue` | Where is the DeskClock type? | `DeskClock` | — | `contains` |
| `ed-fl-py-01` | `self-code-comments-agent` | Which service method returns the final context package for one maintenance query? | `RetrievalService.retrieve` | — | — |
| `ed-fl-py-02` | `fixture-py-route-ledger` | Where does a new route record first get created? | `RouteService.open_route` | — | — |
| `ed-dq-py-01` | `fixture-py-route-ledger` | Which store operation returns every saved route? | `MemoryRouteStore.load_all` | — | — |
| `ed-dq-ja-02` | `fixture-java-desk-queue` | Which audit operation records a newly opened ticket, and which service method calls it? | `DeskAudit.recordOpen` | `openTicket(String,String)` | `imports_exact_unique` |
| `ed-bl-py-01` | `self-code-comments-agent` | Corpus building rejects a file whose language no longer matches the snapshot. Where is that language check? | `CorpusBuilder._validate_files` | — | — |
| `ed-bl-py-02` | `fixture-py-intake-queue` | A checksum mismatch is still queued. Where should that acceptance decision have stopped it? | `Dispatcher.enqueue` | `IntakeRules.accepts` | — |
| `ed-mt-py-01` | `self-code-comments-agent` | The on-disk credit tables are created in one schema initializer. Where is it? | `SQLiteCreditLedger._initialize_schema` | — | — |
| `ed-mt-py-02` | `fixture-py-route-ledger` | Where is the count of already closed routes produced? | `RouteReport.closed_count` | — | — |
| `ed-cf-py-01` | `self-code-comments-agent` | How does a class symbol become the parent of the methods nested inside its source range? | `ProjectGraphBuilder._add_class_containment` | — | — |
| `ed-cf-py-02` | `fixture-py-intake-queue` | How does a rejection explanation produced while parsing become part of the audit record? | `IntakeParser.reject_reason` | `IntakeAudit.record` | — |

### 4.5 Chinese coverage

Chinese coverage is a separate Python-only population. It is not pooled into the
English test aggregate and cannot tune formal test configuration. Underlying Symbol
overlap with English is allowed, but each query requires delayed-review confirmation
that it is not a mechanical translation.

| Query ID | Project | Query text | Grade 2 evidence | Grade 1 evidence |
| --- | --- | --- | --- | --- |
| `zh-sl-py-01` | `self-code-comments-agent` | 请定位 canonicalize_graph。 | `canonicalize_graph` | — |
| `zh-sl-py-02` | `fixture-py-route-ledger` | 请定位 validate_entry。 | `validate_entry` | — |
| `zh-fl-py-01` | `self-code-comments-agent` | 账户退款时，退回金额在内存账本里被记成一笔正向流水。这段入账逻辑在哪里？ | `InMemoryCreditLedger.refund` | `validate_integer_amount` |
| `zh-fl-py-02` | `fixture-py-intake-queue` | 审核员要查看某次拒绝最终写进日志的记录动作。编号和拒绝原因在哪个操作里一起保存？ | `IntakeAudit.record` | — |
| `zh-dq-py-01` | `fixture-py-route-ledger` | 路线被正式关闭后，谁负责发出关闭通知，通知文字又由谁拼出来？ | `RouteNotifier.notify_closed` | `RouteNotifier.format_message` |
| `zh-dq-py-02` | `fixture-py-intake-queue` | 解析结果准备进入发送队列时，哪个入队操作接收它，而前面的哪条规则决定它是否可以进入？ | `Dispatcher.enqueue` | `IntakeRules.accepts` |
| `zh-bl-py-01` | `self-code-comments-agent` | 重新打开上次保存的本地工作区时失败。恢复工作区内容的读取逻辑在哪里？ | `load_workspace` | `save_workspace` |
| `zh-bl-py-02` | `fixture-py-route-ledger` | 重新打开一条已经关闭的路线后，剩余停靠数没有按关闭前的规则复原。复原入口在哪里？ | `RouteService.reopen` | — |
| `zh-mt-py-01` | `self-code-comments-agent` | 长时间批处理需要能够中途停止。表示取消状态的类型在哪里，哪一个带进度的批处理入口必须观察它？ | `CancelToken` | `process_batch_with_progress` |
| `zh-mt-py-02` | `fixture-py-intake-queue` | 需要调整拒绝说明的生成规则。解析器里负责产生这段拒绝说明的位置在哪里？ | `IntakeParser.reject_reason` | — |
| `zh-cf-py-01` | `fixture-py-route-ledger` | 从新增一个停靠，到内存记录被覆盖保存，中间经过哪几处代码？ | `RouteService.add_stop` | `MemoryRouteStore.save` |
| `zh-cf-py-02` | `fixture-py-intake-queue` | 一个 envelope 的声明校验值和根据正文重新计算出的校验值分别在哪里取得？ | `Envelope.declared_checksum` | `compute_checksum` |

## 5. Query and ground-truth record contracts

`queries.jsonl` uses the existing `QueryRecord` contract with at least `query_id`,
`query_set_version`, `split`, `language`, `task_type`, `dataset_id`, `project_id`,
`query_text`, `ground_truth_id`, `authoring_source`, and `notes`. Records are UTF-8,
LF, have no blank lines, and are sorted lexicographically by `query_id`.
`authoring_source` is `self_repository` for the self project and `fixture` otherwise.
Each Java table value is preserved in `notes` exactly as
`graph_note=contains` or `graph_note=imports_exact_unique`; a missing table value does
not authorize inferring another Graph relation.

Ground-truth version is `v3.1-phase6-truth-v1` until a real relevance, identity, or
span correction requires a bump. There is exactly one existing `GroundTruthRecord`
per query, sorted by `query_id`; the schema must not be expanded unless the frozen
Protocol requires it. Each Grade 1/2 `EvidenceRecord` contains:

- all six `SymbolId` fields: `language`, `relative_path`, `qualified_name`, `kind`,
  `semantic_disambiguator`, and `fallback_line`;
- zero-based, end-exclusive Unicode-code-point `start_offset` and `end_offset` over
  LF-normalized source;
- adapter-consistent `start_line` and `end_line`;
- relevance `1` or `2`; and
- a source-grounded rationale.

Grade 2 is directly required/best evidence; Grade 1 is useful supporting evidence;
Grade 0 is used only for an explicitly adjudicated near-negative or negative. Recall,
MRR, Precision, and Hit Rate treat Grade ≥1 as relevant; nDCG uses 2/1/0. Unlisted
symbols remain unjudged and map to zero; the corpus must not be exhaustively labeled
Grade 0.

A Grade 1/2 rationale must identify frozen commit or fixture hash, relative path,
qualified name, line/source range, and at least one source-verifiable behavior. A
bare opinion or bare `IMPORTS`/`CONTAINS` statement is invalid. If a Graph relation is
mentioned, the same rationale must also give a source line/range and behavior.

## 6. Corrected leakage policy

1. English dev and English test Grade 2 primary targets are disjoint. An unavoidable
   real maintenance overlap must be an explicit audited exception; no API may be
   invented to avoid it.
2. Natural Grade 1 supporting-evidence overlap within or across splits is allowed but
   recorded in the leakage audit.
3. Chinese coverage may share underlying Symbols with English, but is not a mechanical
   translation, is not pooled into the English aggregate, and is not used for tuning.
4. Any dev/test/coverage query pair with token Jaccard greater than 0.55 fails. Tokens
   are lowercase alphanumeric words of length at least three. Chinese mechanical
   translation cannot be decided by Jaccard alone and requires a
   `not_mechanical_translation` delayed-review field.
5. Test truth may never adjust weights, Graph configuration, Chunk configuration, K,
   the E5 model, or labels.

For every non-`symbol_lookup` query, `query_text` must not contain any relevant
evidence's qualified name, relative path, or semantic disambiguator, and must not
contain the Grade 2 simple symbol name. No query may contain a manifest path, Java
package prefix, or answer path such as `src/com/desk`. `symbol_lookup` may contain a
simple name but not a relative path or Java package prefix. A query cannot reproduce
40 or more consecutive characters from a rationale. Fixture comments cannot contain
a query ID or reproduce 40 or more consecutive characters from any query. Query,
notes, and fixture source cannot contain experiment-bookkeeping terms such as `bm25`,
`embedding`, `hybrid`, `ndcg`, `rrf`, or `grade`, except when a frozen legitimate code
entity itself requires the term.

## 7. Multi-relevant quotas

The English-test set must satisfy these mechanical minimums without changing domain
behavior or relevance merely to meet a quota:

| Task | Multi-relevant requirement | Cross-file requirement |
| --- | ---: | ---: |
| `dependency_questions` | ≥6/8 | ≥5/8 |
| `maintenance_tasks` | ≥6/8 | ≥5/8 |
| `cross_file_understanding` | ≥6/8 | ≥5/8 |
| `bug_localization` | ≥5/8 | ≥3/8 |
| `feature_localization` | ≥4/8 | ≥3/8 |
| `symbol_lookup` | ≤2/8 | none |

`et-sl-ja-02` is the allowed multi-relevant symbol-lookup query.

## 8. RQ1 truth derivation and probes

Authoritative truth is Symbol-level. File truth is relevant when the file contains a
relevant Symbol, with the file grade equal to the maximum evidence grade in the file.
Chunk construction is fixed at 1200 Unicode code points with 200 overlap and 1000
stride. A chunk is relevant only for a non-empty span overlap:

```text
max(chunk_start, symbol_start) < min(chunk_end, symbol_end)
```

Endpoint contact is not overlap. Chunk grade is the maximum grade of overlapping
evidence. A large Symbol crossing multiple chunks remains one Symbol truth and is not
split into multiple Symbol evidence records.

Phase 6.2A mechanically verifies:

- `et-fl-py-06`: `IntakeParser.normalize_payload` is at least 1500 characters and
  overlaps at least two chunks;
- `et-bl-py-06`: `last_record_included` and `reject_reason` are both in `parser.py`
  but share no chunk;
- cross-file evidence for `et-cf-py-05`, `et-dq-py-04`, and `et-bl-ja-02` spans at
  least two paths;
- File and Chunk grades use maximum evidence grade; and
- endpoint contact is not overlap.

## 9. Java RQ boundary

All 12 English-test Java queries enter the fixed RQ1, RQ2, RQ3, and RQ4 denominator.
For RQ3, `CONTAINS` interpretation is limited to `et-sl-ja-01`, `et-sl-ja-02`,
`et-fl-ja-02`, `et-bl-ja-01`, and `et-mt-ja-01`. `IMPORTS` interpretation is limited
to rows whose `graph_note=imports_exact_unique`:

- `et-fl-ja-01`
- `et-dq-ja-01`
- `et-dq-ja-02`
- `et-bl-ja-02`
- `et-mt-ja-02`
- `et-cf-ja-01`
- `et-cf-ja-02`

Wildcard, static, unresolved external imports, `CALLS`, and `INHERITS` are forbidden
as authoritative Graph truth or relevance rationale. Phase 6.2A validates that the
fixture has no wildcard/static imports, `extends`, `implements`, or nested classes;
that every `package.Type` is unique; and that every Java truth Symbol comes from real
adapter output. The two Java dev queries exist only for Phase 6.3 Dry Run and never
enter a formal RQ aggregate.

## 10. Annotation protocol and limitations

The authoritative Addendum A contract is:

| Field | Value |
| --- | --- |
| `primary_annotator_id` | `wang` |
| second human annotator | `ABSENT` |
| `review_method` | `delayed_blinded_self_review` |
| minimum delay | 48 hours |
| human IAA | `NOT AVAILABLE / NOT CLAIMED` |

Phase 6.2A creates only records with `annotation_status=drafted`, a truthful
`created_at`, `reviewed_at=null`, `reviewer_id=wang` under the Addendum's future
delayed-self-review semantics, and `adjudicator_id=null`. It must not fabricate a
future review time, elapsed delay, second person, or frozen status. Once timestamps
enter a canonical hash, they cannot be silently changed.

Phase 6.2B begins only after a real delay of at least 48 hours. `wang` first sees only
the query and frozen source evidence, not the initial grade/rationale/judgment or any
evaluated ranking, and records a new independent-in-time judgment before comparison.
The audit uses `review_role=delayed_blinded_self_review`, `reviewer_id=wang`, and
`second_annotator=absent`. Agreement may become a freeze candidate. A disagreement in
relevance, Symbol identity, or span sets `ambiguity_flag=true` and requires an
`adjudication_note`; an actual relevance/identity/span correction bumps both
`ground_truth_version` and `ground_truth_hash`. With no adjudication,
`adjudicator_id=null`; with adjudication, `adjudicator_id=wang`.

Independent model/data audit may check manifests, hashes, leakage, masked samples,
and dataset consistency. It is not human annotation, cannot substitute for a second
human, and cannot produce human IAA.

Frozen limitations to disclose are:

- one human annotator and no human IAA; delayed blinded self-review mitigates but does
  not remove subjectivity;
- fixture-design bias and fixed heuristics;
- self-repository author-familiarity bias;
- some Python from-imports become external targets under the current Graph behavior;
- Java uses a limited lightweight parser/adapter;
- zero-symbol files remain in the File baseline;
- Graph is not an independent retriever, File/Chunk mapping and candidate-pool limits
  affect construct validity; and
- the primary dataset is Python-heavy, Java is fixture-only, only one E5 model is
  frozen, and no external open-source project is required.

Reproducibility evidence must retain the frozen commit, fixed E5 revision, CPU
baseline, explicit truncation, and Java-parser limitation. A future external project
requires a separate dataset ID, manifest, query/truth set, and results; it may not be
silently pooled into this 72-query aggregate.

## 11. Phase 6.2A artifact layout

Phase 6.2A creates exactly the relevant materialized artifacts below, not during this
documentation freeze:

```text
docs/experiments/datasets/v1/manifest.json
docs/experiments/datasets/v1/identity.json
docs/experiments/datasets/v1/authoring_audit.json
docs/experiments/datasets/v1/fixtures/route-ledger/**
docs/experiments/datasets/v1/fixtures/intake-queue/**
docs/experiments/datasets/v1/fixtures/desk-queue/**
docs/experiments/datasets/v1/incremental/manifest.json
docs/experiments/datasets/v1/incremental/base/**
docs/experiments/datasets/v1/incremental/update/**
docs/experiments/queries/v1/queries.jsonl
docs/experiments/ground_truth/v1/ground_truth.jsonl
docs/experiments/ground_truth/v1/annotation_audit.jsonl
docs/experiments/datasets/v1/checksums.sha256
tests/test_phase62_dataset_contract.py
```

No `docs/experiments/runs/` or formal result artifact is created in Phase 6.2A.

## 12. Hash and identity rules

Phase 6.2A reuses `experiments.serialization.canonical_hash` or an exactly equivalent
Protocol-defined implementation:

- `dataset_hash`: existing `DatasetManifest` canonical identity;
- `query_set_hash`: canonical hash of `QueryRecord.to_record()` values sorted by
  `query_id`;
- `ground_truth_hash`: canonical hash of `GroundTruthRecord.to_record()` values sorted
  by `query_id`; and
- `path_manifest_hash`: canonical hash of the authoritative project/path manifest.

`identity.json` additionally records raw-byte SHA-256 for the Protocol, Addendum A,
and this Dataset Specification; raw-byte SHA-256 for authoring audit; the path
manifest hash; self frozen commit; `retrieval_runs_before_freeze=0`; and all
dataset/query/truth versions. `checksums.sha256` covers the raw bytes of every formal
Phase 6.2 delivery artifact.

## 13. Mechanical validation contract

**Addendum B supersedes the incremental `3/2/2` validation count below:**
`docs/experiments/Experiment_Protocol_Addendum_B_V3_1_0.md`.

`tests/test_phase62_dataset_contract.py` remains offline and validates at least:

- 72 total queries; 48/12/12 populations; 8/2/2 per task; test 36 Python/12 Java,
  dev 10 Python/2 Java, and coverage 12 Python/0 Java;
- unique query and ground-truth IDs, one query to one truth, no orphan query/truth,
  and valid project membership (with the incremental dataset excluded from queries);
- every truth has relevant evidence, grades are in 0/1/2, all Grade 1/2 evidence has
  full SymbolId/span/rationale, and no duplicate authoritative evidence exists;
- every path belongs to its project manifest; every Symbol and all six ID fields match
  real adapter output; all spans are valid and within LF-normalized source;
- self hashes match frozen Git blob bytes, fixture hashes match their canonical
  identity, and every GT path belongs to the manifest;
- corrected leakage rules, explicit audits for permitted Grade 1 and Chinese-English
  overlap, near-duplicate rejection, and Chinese
  `not_mechanical_translation` review field;
- multi-relevant and cross-file quotas;
- File/Symbol/Chunk mapping and the named RQ1 probes;
- Java restrictions and real adapter identities, excluding `CALLS`/`INHERITS` truth;
- canonical dataset/query/truth/protocol/Addendum/specification/audit/path hashes and
  checksums; and
- incremental changed/added/removed counts of 3/2/2.

Invalid duplicates, identities, spans, path/project relationships, or orphans fail
closed; silent deduplication is forbidden.

## 14. Authoring audit and no-retrieval boundary

`authoring_audit.json` records at least:

```text
retrieval_runs_before_freeze: 0
primary_annotator_id: wang
second_human_annotator: absent
review_method: delayed_blinded_self_review
minimum_delay_hours: 48
human_IAA: not_available_not_claimed
created_at: <truthful timestamp>
reviewed_at: null
annotation_status: drafted
```

It also records single-annotator, self-repository author-bias, Python from-import
externalization, Java lightweight-parser, and zero-symbol File-baseline limitations.

During Phase 6.2A and 6.2B authoring, BM25, Semantic, Hybrid, Graph ranking, RRF, and
formal E5 retrieval results must not influence wording, relevance, fixture behavior,
or evidence. `retrieval_runs_before_freeze` remains zero. Adapter parsing, manifest
construction, File/Chunk construction, schema validation, and hashing are allowed.

## 15. Phase boundaries and freeze criteria

Phase 6.2A materializes the dataset, fixtures, 72 queries, draft ground truth,
hashes, and mechanical tests. Its result is **DRAFTED**, not frozen, and it does not
close Phase 6.2. Phase 6.2B performs the real ≥48-hour delayed blinded self-review.
Only after the delay, all ambiguity/adjudication work, independent data QA,
mechanical validation, and final hash checks may annotation become frozen and the
Phase 6.2 Gate close.

The final Phase 6.2 Gate requires all of:

1. this specification frozen;
2. all Phase 6.2A artifacts materialized;
3. 72-query validation passed;
4. all GT Symbol/span/hash checks passed;
5. leakage audit passed;
6. multi-relevant quotas passed;
7. Java boundaries passed;
8. RQ1 mapping probes passed;
9. a real delay of at least 48 hours;
10. delayed blinded self-review completed;
11. every ambiguity/adjudication recorded;
12. Independent Data QA passed;
13. final hashes/checksums consistent;
14. `retrieval_runs_before_freeze=0`; and
15. no formal RQ result exists.

Phase 6.3 is not allowed until that gate closes. Its Dry Run uses only English dev,
never English test or Chinese coverage for tuning. Formal RQ1–RQ4 remain unavailable
until Phase 6.3 Dry Run passes. Fake embeddings never provide formal semantic-quality
evidence; English test remains sealed until Phase 6.4; Chinese remains separate.

Dataset design does not prove that Symbol beats File/Chunk, E5 beats BM25, Graph
improves Recall, Hybrid beats a single strategy, or RAG improves maintenance quality.
Unfavorable outcomes—including E5 not beating BM25, Graph helping only some tasks,
Hybrid helping only some tasks, or Symbol not being best for every query—must remain
admissible and must not trigger dataset redesign.

## 16. Phase 6.2A execution entry

A future Phase 6.2A executor must read only the frozen Protocol, Addendum A, this
specification, and `PROJECT_CONTEXT.md`, then materialize the artifacts above. It must
not depend on ChatGPT, Grok, Claude, or other chat history, or on a manually copied
older prompt. If those repository documents are insufficient or conflict, execution
must stop rather than guess.
