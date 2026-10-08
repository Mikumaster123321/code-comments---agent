# PROJECT_CONTEXT History Through V3.1.2

Archive status: `HISTORICAL DOCUMENTATION / SNAPSHOT`

This file preserves the complete root `PROJECT_CONTEXT.md` body that existed at the
V3.1.3 branch point before current/history separation. The archived wording is kept
as historical evidence and is not current release-state authority.

Return to the [current root PROJECT_CONTEXT](../../PROJECT_CONTEXT.md) or the
[development documentation index](README.md).

---

# Project Context

<!-- release-state: V3.1.2 RELEASED -->

## Project

毕业设计：《基于大语言模型与多智能体协同的软件代码智能维护系统设计与实现》。项目正从 **Code Comments Agent** 渐进演进为智能软件代码维护系统；现有 Gradio 应用必须持续可用。

## Current State

- V3.1.2 Language / UX / Output Quality：**RELEASED**。
  Branch `v3.1.2-dev` 从 authoritative main
  `2036cb6c82860b9bf8229ecac0f4d4add420855d` 创建；Scope Freeze commit `139833f`，
  Prompt Output Contract commits `2192293` / `d12d800`。七项冻结工作 V312-UX-01 至
  V312-TEST-07 均完成：task-first UI、UI/Output/Programming Language 分离、Provider
  applied/verified 语义、本地验证优先与安全错误、现有结构化输出三语 presentation、
  prompt data/output contract、离线合同测试。targeted + LLM contracts `35 passed`，
  production `198 passed`，experiments `240 passed`，full `951 passed`。当前 Anaconda
  Python 3.13.5 的 Gradio import 因 IPython/rlcompleter 发生宿主 SIGSEGV，create_ui
  smoke 记录为宿主 HOST LIMITATION；Independent Final Release QA 已在 CPython 3.10.20
  （gradio 6.27.0）下重测 create_ui build smoke，结果为 PASSED（`Blocks`，106 blocks）。
  lifecycle 为 `RELEASED`；annotated tag `v3.1.2`，发布身份记录见
  `docs/release/release_state.json`。V3.2：**NOT STARTED**。

- V3.1.2 文档包已准备：Scope Freeze、Prompt Output Contract、Thesis Materials MD +
  UTF-8 standalone TXT、Development Report、Pre-Release Notes、README / Version History、
  PROJECT_CONTEXT 与 release index。下一步是 DeepSeek V4.1 Flash Independent Final
  Release QA；通过后才允许 reviewed release commit、annotated tag、main sync、GitHub / Gitee
  publication 与 remote verification。

- V3.1.0 + V3.1.1 Post-Release Documentation Closure：**COMPLETED**。两个版本均已具备
  README / Version History、Thesis Materials MD + UTF-8 TXT、Development Report、
  Release Notes、PROJECT_CONTEXT 与 release index 入口；永久版本文档合同已固化在
  `docs/release/Version_Documentation_Contract.md`。本次闭环仅修改 tracked documentation，
  不改变 retrieval、ranking、Formal artifact、Query/GT/Grade 或既有 tag。V3.2 为
  **NOT STARTED**。

- V3.1.1 Workflow & Developer Experience Optimization：**FULLY RELEASED**。Release
  commit C1 为 `683479da2fd3b72c17cba3f03101bc23e275f40b`，annotated tag `v3.1.1`
  指向 C1，final release-record HEAD C2 为
  `0238cc0bd5254ac782aa3981cdc755d5a59c498e`；GitHub / Gitee branch 与 tag 已 push
  并完成 remote verification。六项冻结工作均已完成：统一 Python developer command hub、runtime/test
  doctor、offline-first E5 preflight、稳定 test profiles、只读 experiment/archive
  validator、release consistency gate。新增 workflow/release 测试 `30 passed`；production
  `198 passed`；experiments `240 passed`；统一 full 与 legacy full 均为 `922 passed`。
  当前 host 的普通 pytest 在 plugin initialization 阶段异常，`-p no:debugging` 是通过
  subprocess probe 得出的环境 workaround，不改变测试语义。Critical 0；
  validity/release-blocking Medium 0。

- V3.1.0 Project Intelligence / RAG：**RELEASED**。Release commit
  `8813e4c2fb0dc07f38c2013d520441bf399dcbc4`，tag `v3.1.0`；branch 与 tag 已 push
  并完成 remote verification。发布基线完整回归 `892 passed`。Formal archive commit
  `c3ee6ec1b7aa28c2539d2fe849d1f25268807677`
  是当前 HEAD 的祖先；冻结 Formal run / artifact 未改变，归档后仅增加从 artifact
  确定性导出的论文 CSV 与解读材料。artifact-set canonical identity / file SHA-256 仍为
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` /
  `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`。
  V3.1.1 不改变 retrieval、ranking、Query/GT/Grade、Formal artifact、metrics 或
  interpretation。V3.1.2 为 **RELEASED**；V3.2：
  **NOT STARTED**。

- V3.1.0 Formal Results Interpretation 与论文实验素材准备：Formal Results QA
  **PASS WITH NON-BLOCKING NOTES**，Critical 0、validity-blocking Medium 0，
  Thesis Result Interpretation **ELIGIBLE**；用户提供的 Claude Sonnet 5
  Interpretation 判定为 **ACCEPT — CLAIM-BOUNDED**。正式解读档案依据已冻结
  Formal 报告起草并标注原文未提供；RQ1–RQ4 主表、扩展表、ContextBuilder 表和
  Figure A–E 数据均从 Formal artifact 自动提取并逐项校验。V3.1 experiments
  **COMPLETE**；该结果随 V3.1.0 正式发布并保持冻结。V3.2 **NOT STARTED**。

- V3.1.0 Phase 6.4 Formal RQ1–RQ4 Execution：基于 execution revision
  `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` 与冻结 corpus revision
  `12391233daa2149ead4f451e920b2e0d8a1a6beb`，English Test 48/48 × 17/17
  配置 = 816/816 unique query-config 全部 success，failed/invalid/degraded 均为 0；
  English Dev 0、Chinese 0。8 条代表路径共 384 条 Query 的 ranking/score/metric/
  identity 确定性比较 mismatch 为 0，RQ4 diagnostic serialization mismatch 为 0。
  两个 Weighted Hybrid run 的 `context-diagnostic-v1` 均已物化并完成引用、hash、
  canonical identity 和磁盘重载校验；Formal artifact-set canonical identity 为
  `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`，
  file SHA-256 为 `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`。
  正式结果与全部分群、辅助指标及 ContextBuilder diagnostics 见
  `docs/development/Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md`。
  正式归档后的相关专项回归 `240 passed`，全量回归 `892 passed`。
  结果归档提交并从新 HEAD 完成 post-commit reload 后，Formal execution 与
  RQ1–RQ4 均为 `COMPLETED`；V3.2 保持 `NOT STARTED`。`current_gate.json` 保留为
  Phase 6.3 authority 导航记录，因全部 Formal authority binding 明确绑定其冻结
  SHA-256，不在结果归档中改写。

- V3.1.0 Phase 6.4 Formal 前置 RQ4 Context Diagnostic Artifact Fix：上一轮基于 execution revision `5a462c70c2b10b96f6ec71314bda2b9990da0bb7` 的 Formal attempt 虽执行 English Test 48/48 × 17/17 = 816/816 且 384 次代表路径确定性比较通过，但两个冻结 RQ4 Weighted Hybrid run 未 materialize Protocol §7.5/§9.4 要求的 ContextBuilder diagnostics，artifact set 因此撤回且从未提交。修复现将 production `ContextPackage` 只读传入 runner，为两个适用配置生成 canonical `context_diagnostics.json`，在 aggregate、manifest output checksum 和 run checksum 中绑定并支持严格重载；缺失、损坏、wrong-config 或 namespace 混用 fail closed，非适用配置保持 `null`。诊断接线不参与 ranking 或 metrics。失败 attempt 的未跟踪产物已按记录 identity 后移除；无 Formal result 发布。专项回归 `240 passed`，全量回归 `892 passed`。Phase 6.3 仍 CLOSED；Formal successful execution `0/48`、配置 `0/17`、artifact set `NONE`、RQ1–RQ4 `NOT COMPLETED`。详见 `docs/development/Development_Report_V3_1_0_Phase_6_4_RQ4_Context_Diagnostic_Artifact_Fix.md`。

- V3.1.0 Formal Execution 前置 Git ancestry 合同修复：Amendment 5 明确区分 Dry Run execution revision `f0f4d2da169a071c71a6099c1d106fc3fec23299`、DryRunReceipt archive commit `ae063161a98cc0d88aafd7fffea8e81cbc57f335` 与后续 Formal execution revision，并要求按此顺序构成 Git 祖先链（允许相等）。FORMAL validator 继续将 receipt、artifact set、17 个 Dry Run manifest/aggregate 绑定原 Dry Run revision；Formal 请求单独绑定实际执行代码提交。修复前全量基线 `877 passed`；生命周期/身份/安全/生产接线专项 `211 passed`，修复后全量回归 `881 passed`。Phase 6.2/6.3 仍 CLOSED；正式 English Test `0/48`、配置 `0/17`、query-config `0/816`，Formal artifacts **NONE**，RQ1–RQ4 **NOT STARTED**。归档修复提交后仍须从新 HEAD 重载 RepositoryAuthority 并以该 HEAD 验证 FORMAL 资格；未执行 Formal benchmark。

- Phase 6.3 Final Closure：English Dev Dry Run 的 Commit A 为 `ae063161a98cc0d88aafd7fffea8e81cbc57f335`；从该新 HEAD 重新加载 RepositoryAuthority 后，`validate_formal_eligibility(purpose=FORMAL)` **PASS**，DryRunReceiptV2 的 Git 归档提交等于 Commit A，而 execution revision 仍为 `f0f4d2da169a071c71a6099c1d106fc3fec23299`。Phase 6.3 **CLOSED**（`current_gate.json` v1 以 `current_phase=6.3`、`phase_status=COMPLETED` 表示终态）；Formal experiment execution **ALLOWED BUT NOT STARTED**；Formal RQ1–RQ4 **NOT STARTED**。English Test 与 Chinese 正式执行均为 0；V3.2 **NOT STARTED**。Formal 运行入口仍须重新验证全部已提交 authority、runtime 和 receipt。

- Phase 6.3 English Dev Dry Run 归档阶段：当前 execution revision `f0f4d2da169a071c71a6099c1d106fc3fec23299`、冻结 corpus revision `12391233daa2149ead4f451e920b2e0d8a1a6beb` 下，12/12 English Dev Query × 17/17 冻结配置 = 204/204 unique query-config 结果均 success；English Test 0、Chinese 0。17 项完整确定性复跑零不一致；artifact-set identity `08f753fe7e9cb24e29a38baa5057005203f09524d0d94a48c4fbd98c19c8715b`，DryRunReceiptV2 identity `8383eb1c0e45ca68927cecc5170a18a0ae56cc62dcbf2e5b3ff53448073fff3e`，磁盘重载、hash、schema 与指标复核 PASS。两处旧 runs-directory 测试已迁移；直接相关 `147 passed`、生产执行/生命周期/安全专项 `154 passed`、全量回归 `877 passed`。本条记录仅为 Commit A 的 Dry Run QA 归档事实：Phase 6.3 尚待从归档 HEAD 验证 FORMAL 后关闭，Formal RQ1–RQ4 **NOT STARTED**。详见 `docs/development/Development_Report_V3_1_0_Phase_6_3_English_Dev_Dry_Run.md`。

- Phase 6.3 前置 Credential Scanner False-Positive Fix：`metric_inputs` 中合法 `RuntimeCredential` symbol identity 误判已修复；结构化 credential 字段和真实 secret 值继续 fail closed。遗留的单项 RQ1-FILE 未提交局部产物已记录 identity/字节 SHA-256 并清理，不计作完整 Dry Run。序列化/runner/生产执行/lifecycle 定向 `206 passed`，全量回归 `877 passed`。正式 English Dev `0/12`、Matrix `0/17`、DryRunReceiptV2 `NOT CREATED`、Formal RQ1–RQ4 `NOT STARTED`；Phase 6.3 仍为 `ALLOWED BUT NOT STARTED`。详见 `docs/development/Development_Report_V3_1_0_Phase_6_3_Credential_Scanner_Fix.md`。

- Phase 6.3 Corpus / Execution Revision Identity Contract Fix：已确认此前 blocker 是将冻结 self-repository corpus revision 与 benchmark execution revision 混用。Amendment 4 将新 run manifest、artifact set 和 DryRunReceiptV2 分别绑定两种 revision；receipt 的归档提交从已提交 Git 历史派生。合同修复与安全测试已完成，全量回归 `850 passed`。正式 Dry Run 仍为 English Dev `0/12`、Matrix `0/17`、Query-config `0/204`，DryRunReceiptV2 未创建，Formal RQ1–RQ4 `NOT STARTED`。

- Phase 6.3 Dry Run Lifecycle + Receipt Contract Fix：合同与实现已完成；生命周期专项 `104 passed`，全量回归 `839 passed`（原基线 `825 passed`）。正式 Dry Run 尚未执行，English Dev `0/12`、Matrix `0/17`、English Test `0`、Chinese `0`，正式 `DryRunReceipt` 未创建，Formal RQ1–RQ4 `NOT STARTED`。修正合同见 `docs/experiments/Reference_Lifecycle_Engineering_Specification_Amendment_3_V3_1_0.md`。未来正式执行按 artifact/receipt 提交、从新 HEAD 验证 FORMAL、验证通过后更新 gate 的顺序进行。

- 最新 Phase 6.2 状态：**CLOSED**；Reference Approval 与 Closure 已物化验证；Phase 6.3 **ALLOWED BUT NOT STARTED**；Formal RQ1–RQ4 **NOT STARTED**。Phase 6.3 前置接线真实 E5 与生产 benchmark 最小烟测 **PASS**，全量回归 **825 passed**；本节较早阶段条目保留历史状态，以后文 Final Approval Sequencing Fix + Closure、前置接线记录及 `current_gate.json` 为当前权威索引。

- Current Version: `3.1.2`
- Current branch: `v3.1.2-dev`
- V3.1.0 / V3.1.1 documentation closure: `COMPLETED`
- Version Documentation Contract: `ACTIVE`
- V3.1.1: `FULLY RELEASED`
- V3.1.1 release commit / tag:
  `683479da2fd3b72c17cba3f03101bc23e275f40b` / `v3.1.1`
- V3.1.1 final release-record HEAD: `0238cc0bd5254ac782aa3981cdc755d5a59c498e`
- V3.1.1 GitHub / Gitee branch and tag publication: `VERIFIED`
- V3.1.1 theme: Workflow & Developer Experience Optimization
- V3.1.1 scope: V311-DX-01 through V311-DX-06 `COMPLETE`
- V3.1.1 tests: workflow/release `30`; production `198`; experiments `240`;
  full / legacy full `922`
- V3.1.1 Formal impact: `NONE`; V3.1.0 identity/SHA unchanged
- V3.1.2: `RELEASED`
- V3.1.2 scope: V312-UX-01 through V312-TEST-07 `COMPLETE`
- V3.1.2 tests: targeted + LLM contracts `35`; production `198`; experiments `240`; full `951`
- V3.1.2 Prompt contract: `docs/development/V3_1_2_Prompt_Output_Contract.md`
- V3.1.2 Formal impact: `NONE`; V3.1.0 identity/SHA unchanged
- V3.1.2 tag: `v3.1.2`
- V3.1.0: `RELEASED`
- V3.1.0 release commit / tag:
  `8813e4c2fb0dc07f38c2013d520441bf399dcbc4` / `v3.1.0`
- V3.1.0 theme: Project Intelligence / RAG
- V3.1.0 Phase 0.0 — Development Baseline Gate: `COMPLETED`
- V3.1.0 Phase 0 — Architecture & Research Design: `COMPLETED`
- V3.1.0 Architecture: `FROZEN`
- V3.1.0 Research Methodology: `FROZEN`
- V3.1.0 Phase 0 Documentation Gate: `CLOSED`
- V3.1.0 Phase 0 Blocking Issues: `0`
- V3.1.0 Core Research Questions: RQ1–RQ4
- V3.1.0 Phase 1 — Corpus & Symbol Content Model: `COMPLETED`
- V3.1.0 Phase 1.1 — Corpus Integrity Hardening: `COMPLETED`
- V3.1.0 Phase 1 Documentation Gate: `CLOSED`
- V3.1.0 Phase 1 Final QA: `PASS WITH LOW NOTES`
- V3.1.0 Phase 1 Final Critical / Medium: `0 / 0`
- V3.1.0 Phase 1 M1 / M2 / L1: `RESOLVED / RESOLVED / RESOLVED`
- V3.1.0 Phase 1 architecture: `FROZEN`
- V3.1.0 Phase 1 Corpus & Symbol Content Model: `IMPLEMENTED`
- V3.1.0 Phase 1 primary retrieval unit: `Symbol`
- V3.1.0 Phase 1 snapshot: `UNCHANGED`
- V3.1.0 Phase 1 SymbolId: `UNCHANGED`
- V3.1.0 Phase 1 source text: `CorpusBuilder`
- V3.1.0 Phase 1 freshness: `content hash validation`
- V3.1.0 Phase 1 build: `offline/read-only/atomic`
- V3.1.0 Phase 1 tests: `41 passed`; full regression: `455 passed`
- V3.1.0 Phase 1 deferred Low: Java exotic separators; broad `ValueError` parse
  category; pre-hardening snapshot compatibility; hostile `str` subclass
- V3.1.0 Phase 1 next: `COMPLETED; transitioned to Phase 2`
- V3.1.0 Phase 2 — Lexical Baseline / BM25: `IMPLEMENTED / HARDENING COMPLETE`
- V3.1.0 Phase 2 implementation: deterministic stdlib-only BM25 over immutable
  Phase 1 `RetrievalDocument` values; embedding, graph, hybrid, and service layers
  remain deferred
- V3.1.0 Phase 2 Independent QA: `PASS WITH ISSUES`; Critical `0`; Medium `1 initially`
- V3.1.0 Phase 2 M1 public config mutability: `RESOLVED BY PHASE 2.1`
- V3.1.0 Phase 2 Directed Retest: `PASS WITH LOW NOTES`
- V3.1.0 Phase 2 Final QA: `PASS FOR PHASE 2 WITH LOW NOTES`; Final Critical / Medium `0 / 0`
- V3.1.0 Phase 2.2: `NOT REQUIRED`
- V3.1.0 Phase 2 Documentation Gate: `CLOSED`
- V3.1.0 Phase 2 tokenizer: `code-lexical-v1`; BM25 `k1=1.5`, `b=0.75`
- V3.1.0 Phase 2 lexical input: exactly one `qualified_name` plus one `source_text`
- V3.1.0 BM25: `IMPLEMENTED / DETERMINISTIC / OFFLINE`
- V3.1.0 Embedding: `NOT STARTED`
- V3.1.0 Graph Retrieval: `NOT STARTED`
- V3.1.0 Hybrid: `NOT STARTED`
- V3.2: `NOT STARTED`
- V3.1.0 branch base / synchronized `main`: `381708bb5cd57f9c15a8755416434ede5a337824`
- V3.1.0 baseline before Phase 2: `455 passed`; Phase 2 full regression: `463 passed`;
  offline LLM-contract smoke: `6 passed`
- V3.1.0 Phase 2.1 hardening validation: lexical `14 passed`; Phase 1 corpus `41
  passed`; offline LLM-contract smoke `6 passed`; full regression `469 passed`; no
  real API, Credential, or network request was used
- V3.1.0 Phase 2.1 current-project corpus smoke: `913 documents indexed` (working
  tree smoke only; not a retrieval-quality claim)
- V3.1.0 RQ2 fairness entry contract: lexical and future embedding retrieval use the
  same text input, exactly one `qualified_name` plus one `source_text`
- V3.1.0 Phase 3 entry contract: fake/hash embeddings are tests-only; formal semantic
  comparison requires a separately reviewed real model with fixed version, dimension,
  normalization, license, reproducibility, and runtime/hardware evidence
- V3.1.0 current baseline before Phase 3.1: `469 passed`; Phase 0 and Phase 1 are completed/frozen,
  Phase 2 is completed with Final QA `PASS WITH LOW NOTES` and Documentation Gate
  `CLOSED`
- V3.1.0 Phase 3: `COMPLETED`; Phase 3.0 Documentation Freeze is `CLOSED`
- V3.1.0 Phase 3.0 Selection Review: `COMPLETED`
- V3.1.0 Phase 3.0 Selection: `FROZEN`
- V3.1.0 Phase 3.0 Primary / Backup: `FROZEN`
- V3.1.0 Phase 3.0 RQ2/RQ4 fairness: `FROZEN`
- V3.1.0 Phase 3.0 failure ownership: `FROZEN`
- V3.1.0 Phase 3.1: `COMPLETED`
- V3.1.0 Phase 3.1 implementation: stdlib-only immutable embedding contracts,
  credential-free deterministic fingerprints, validated/l2-normalized vectors,
  deterministic fake query/document provider, and exact in-memory cosine
  `SemanticIndex` over Phase 1 `RetrievalDocument` values
- V3.1.0 Phase 3.1 tests: `12 passed`; full regression after implementation:
  `481 passed`; offline LLM-contract smoke: `6 passed`; no real model, model
  download, ML dependency, network inference, or API request was used
- V3.1.0 Phase 3.1 Independent QA: `PASS WITH LOW NOTES`; Critical `0`; Medium
  `0`; Phase blocker `0`; Phase 3.1.1 `NOT REQUIRED`
- V3.1.0 Phase 3.1 Intermediate Documentation Gate: `CLOSED`
- V3.1.0 formal Phase 3.1 corpus smoke: `976 documents` across `51 contributing
  files`; Phase 2 reference `913`; corrected growth `+63`, removed `0`
- V3.1.0 corpus-count correction: prior `971` implementation smoke was replaced
  by the independent-QA `976` evidence; this is a smoke-count correction, not a
  CorpusBuilder regression
- V3.1.0 Phase 3.1 real model: superseded by Phase 3.2 local adapter validation;
  fake provider remains tests-only and provides no semantic-quality evidence
- V3.1.0 Phase 3 Independent QA: `PASS WITH LOW NOTES`
- V3.1.0 Phase 3 Final QA: `PASS FOR PHASE 3 WITH LOW NOTES`
- V3.1.0 Phase 3 Final Critical / Medium / Phase blocker: `0 / 0 / 0`
- V3.1.0 Phase 3 Documentation Gate: `CLOSED`
- V3.1.0 Semantic Embedding Foundation: `FROZEN FOR V3.1`
- V3.1.0 Phase 3.2: `IMPLEMENTED / HARDENING COMPLETE`
- V3.1.0 Phase 3.2 Initial Independent QA: `FAIL / BLOCKED` (Critical `1`,
  Medium `2`, Low `7`)
- V3.1.0 Phase 3.2.1: `IMPLEMENTED / HARDENING COMPLETE`; C-1 `CLOSED / RESOLVED`;
  M-1 `CLOSED / RESOLVED`; Directed Retest `PASS WITH LOW NOTES`
- V3.1.0 Phase 3.2.2: `NOT REQUIRED`
- V3.1.0 Phase 3 overall Gate: `CLOSED`
- V3.1.0 Phase 3.2 runtime: `transformers==4.56.2` + `torch==2.8.0`,
  isolated Python 3.12.14 optional environment; `requirements.txt` unchanged
- V3.1.0 Phase 3.2 real model: `intfloat/multilingual-e5-base`, frozen revision
  `d128750597153bb5987e10b1c3493a34e5a4502a`, dimension `768` verified,
  tokenizer/model revision consistency verified, CPU float32 baseline validated
- V3.1.0 Phase 3.2 validation: explicit offline entry point; 100-repeat
  determinism and single/batch consistency passed; audited HEAD corpus `1003`
  and post-hardening working-tree corpus `1020`; corrected truncation evidence
  `79 / 7.7451%` on the post-hardening tree (median `144`, p99 `2321`); no
  vectors or model cache committed
- V3.1.0 Phase 3.2 audited token evidence: `1003 documents`, `78 truncated`,
  `7.7767%`; post-hardening: `1020 documents`, `79 truncated`, `7.7451%`,
  min `19`, median `144`, p90 `415`, p95 `627`, p99 `2321`, max `8886`, max
  dropped `8374`
- V3.1.0 Phase 3.2 prior `1002 documents / 0 truncated / 0.00%` evidence:
  `INVALID INITIAL EVIDENCE` due to tokenizer backend truncation-state
  diagnostic contamination; superseded by the audited and post-hardening evidence
- V3.1.0 Phase 3 final validation: adapter `10 passed`; Phase 3.1 `12 passed`;
  Phase 2 `14 passed`; Phase 1 `41 passed`; offline LLM smoke `6 passed`; full
  regression `491 passed`; no real API, credential, or network request used
- V3.1.0 Phase 4 — Graph Expansion + Index Identity / Incremental Indexing:
  `COMPLETED`
- V3.1.0 Phase 4 Initial Independent QA: `PASS WITH NON-BLOCKING FINDINGS`
- V3.1.0 Phase 4.1 Hardening: `COMPLETED`
- V3.1.0 Phase 4 Directed Retest: `PASS WITH LOW NOTES`
- V3.1.0 Phase 4 F1 — graph traversal direction contract:
  `CLOSED / RESOLVED`
- V3.1.0 Phase 4 F2 — incremental unchanged lookup complexity:
  `CLOSED / RESOLVED`
- V3.1.0 Phase 4 Final QA: `PASS FOR PHASE 4 WITH LOW NOTES`
- V3.1.0 Phase 4 Final Critical / Medium / Phase blocker: `0 / 0 / 0`
- V3.1.0 Phase 4.1.1: `NOT REQUIRED`
- V3.1.0 Phase 4 Documentation Gate: `CLOSED`
- V3.1.0 Phase 4 index identity: immutable, deterministic, credential-free
  `RetrievalIndexIdentity` over project ID, authoritative Snapshot content hash,
  retrieval-config hash, and optional Embedding fingerprint
- V3.1.0 Phase 4 incremental indexing: deterministic `SnapshotDiff` add/delete/
  replace/reuse semantics; unchanged semantic vectors are reused without Provider
  calls; fingerprint/config changes fail closed and require rebuild; the public
  immutable `IncrementalIndexPlan` tuple contract is unchanged and unchanged
  membership is tested through a per-update set (average `O(1)` per document instead
  of `O(N)`)
- V3.1.0 Phase 4 full-rebuild equivalence: document/content identity, BM25 ranking,
  exact semantic ranking, metadata, and index identity covered by offline tests
- V3.1.0 Phase 4 Graph Expansion: deterministic bidirectional neighborhood traversal
  over frozen `CONTAINS` / `IMPORTS` only, with hop, per-seed, global, cycle, duplicate,
  provenance, unsupported-node, and target-graph guards
- V3.1.0 Phase 4 traversal direction: `CONTAINS` / `IMPORTS` stay directed in
  `ProjectGraph`; the expansion layer records explicit `GraphTraversalDirection`
  (`FORWARD` = `edge.source → edge.target`, `REVERSE` = `edge.target → edge.source`)
  in `GraphExpansionProvenance`; direction is retrieval provenance only and no new
  `GraphRelationKind` is introduced
- V3.1.0 Phase 4 structural context nodes: `PROJECT` / `FILE` structural nodes may have
  `document=None` and still consume expansion budget; this is documented behavior, not
  a correctness defect
- V3.1.0 Phase 4 exclusions: no Hybrid Retrieval, score fusion/RRF, ContextBuilder,
  final RetrievalService facade, persistent cache, Vector DB, ANN, Agent, or Router;
  no RQ3 conclusion is claimed; RQ3 must later ablate `(relation, direction)` pairs
  rather than a merged `IMPORTS` signal
- V3.1.0 Phase 4 implementation tests: `37 passed`; Phase 3.2 `10 passed`;
  Phase 3.1 `12 passed`; Phase 2 `14 passed`; Phase 1 `41 passed`; offline LLM
  smoke `6 passed`; full regression `528 passed`; no real model, model download,
  credential, API, or network request was used
- V3.1.0 Phase 4 Directed Retest performance evidence: 5,000 Symbols incremental
  `~0.1059s` versus full rebuild `~0.1152s` (ratio `~0.919`); 10,000 Symbols
  incremental `~0.2158s` versus full rebuild `~0.2332s` (ratio `~0.926`); doubling
  produced `~2.038x` incremental scaling and did not show stable `O(N^2)` behavior;
  this is engineering evidence, not a formal thesis performance result
- V3.1.0 Phase 4 deferred Low: direct manual `GraphExpansionProvenance`
  construction has no `__post_init__` validation for invalid direction values;
  authoritative `expand_graph()` emits only `FORWARD` / `REVERSE`, so production
  expansion is unaffected; future defensive hardening only
- V3.1.0 Phase 4 expected-graph behavior: semantically equal graphs with different
  tuple order are accepted through canonical comparison; genuinely different graphs
  fail closed; frozen `ProjectGraph` / `Snapshot` contracts remain unchanged
- V3.1.0 Phase 4 reports: `docs/development/Development_Report_V3_1_0_Phase_4.md`
  and `docs/qa/QA_Report_V3_1_0_Phase_4.md`
- V3.1.0 Phase 5 — Hybrid Retrieval + ContextBuilder: `COMPLETED`
- V3.1.0 Phase 5 Independent QA: `PASS WITH LOW NOTES`
- V3.1.0 Phase 5 Final QA: `PASS FOR PHASE 5 WITH LOW NOTES`
- V3.1.0 Phase 5 Final Critical / Medium / Low: `0 / 0 / 6`
- V3.1.0 Phase 5 Phase blockers: `0`
- V3.1.0 Phase 5.1: `NOT REQUIRED`
- V3.1.0 Phase 5 Directed Retest: `NOT REQUIRED`
- V3.1.0 Phase 5 Documentation Gate: `CLOSED`
- V3.1.0 Phase 5 implementation: deterministic candidate union by authoritative
  `SymbolId`; explainable Weighted Score Fusion over normalized BM25, normalized
  cosine, and fixed relation/direction/hop Graph signals; optional deterministic
  weighted RRF comparison; lexical-only, semantic-only, Hybrid-without-Graph,
  Hybrid-with-Graph, and Graph-focused configurations remain independently ablatable
- V3.1.0 Phase 5 normalization: BM25 scores use safe branch-maximum normalization;
  cosine scores use fixed `[-1, 1] -> [0, 1]` normalization with finite clamping;
  missing branch components are `0`; fusion weights are explicit, finite,
  non-negative, and need not sum to one because final scores are ranking-relative
- V3.1.0 Phase 5 Graph integration: Phase 4 expansion candidates and immutable
  `(relation, direction, hop)` provenance are preserved; Graph signal is isolated in
  the Hybrid layer and never mutates original BM25 or Semantic scores
- V3.1.0 Phase 5 degraded mode: standalone Semantic failure remains explicit;
  Hybrid may return a complete lexical-only result only when the lexical branch is
  active, with `degraded=True`, a stable `degradation_reason`, and failure provenance
- V3.1.0 Phase 5 ContextBuilder: deterministic SymbolId deduplication, Hybrid-rank/
  seed-adjacent Graph ordering, `RetrievalDocument.source_text`-only source assembly,
  explicit character budget, deterministic oversized-snippet truncation, and
  observable `truncated` metadata
- V3.1.0 Phase 5 V3.2 boundary: immutable `RetrievalQuery` and `ContextPackage`, plus
  `RetrievalService.retrieve(query) -> ContextPackage`, are the recommended future
  Agent consumption boundary; V3.2 Agent runtime remains `NOT STARTED`
- V3.1.0 Phase 5 RRF: `IMPLEMENTED AS OPTIONAL COMPARISON`; Weighted Fusion remains
  the default primary strategy
- V3.1.0 Phase 5 implementation validation: `48 passed`; Phase 4 `37 passed`;
  Phase 3.2 `10 passed`; Phase 3.1 `12 passed`; Phase 2 `14 passed`; Phase 1
  `41 passed`; offline LLM smoke `6 passed`; full regression `576 passed`
- V3.1.0 Phase 5 Independent QA probes: `243 / 243 passed` (fusion `77/77`,
  normalization extremes `19/19`, context `48/48`, service `52/52`, scope `21/21`,
  determinism `9/9`, performance `17/17`); these are probes, not pytest tests
- V3.1.0 Phase 5 final real-corpus QA evidence: `1233 RetrievalDocuments`, `131 files`,
  `1233 symbols`; the earlier `1232 documents` value remains implementation-time
  evidence, and the natural growth is not a CorpusBuilder regression
- V3.1.0 Phase 5 final performance evidence: median `HybridRetriever.retrieve`
  `~13.981 ms`; median end-to-end `RetrievalService.retrieve` `~13.959 ms`; synthetic
  fusion for `N=100/1000/5000` `~0.391/3.920/20.435 ms`; deep `top_k=N` fusion
  `~0.723/7.318/36.799 ms` and ContextBuilder `~0.240/2.402/12.252 ms`; no obvious
  `O(N^2)` observed; engineering smoke evidence only, not a formal RQ4 result
- V3.1.0 Phase 5 Context semantics: `ContextPackage.hits` are final ranked Hybrid
  hits, while `ContextSnippet` values are the actually rendered budgeted context;
  Graph-only snippets use `hybrid_rank=None`, and hits/provenance may be unrendered
- V3.1.0 Phase 5 deferred Low: clamp-comment wording; exception-chain traceback
  privacy; hits versus rendered snippets; possibly unrendered Graph provenance;
  implementation/QA corpus and latency drift; public fake-provider export; all six are
  non-blocking
- V3.1.0 Phase 5 research boundary: no claim that Hybrid beats BM25 or Embedding,
  that Graph improves Recall, that RQ4 is answered, or that RAG improves maintenance;
  formal RQ1–RQ4 conclusions remain Phase 6 benchmark/ablation work
- V3.1.0 Phase 5 reports: `docs/development/Development_Report_V3_1_0_Phase_5.md`
  and `docs/qa/QA_Report_V3_1_0_Phase_5.md`
- V3.1.0 Phase 6: `STARTED`
- V3.1.0 Phase 6.0 — Experiment Protocol Documentation Freeze:
  `COMPLETED / PROTOCOL FROZEN`
- V3.1.0 Phase 6.0.1 — Annotation Protocol Clarification:
  `ANNOTATION PROTOCOL CLARIFICATION COMPLETED`
- V3.1.0 historical human Annotation Protocol: `CLARIFIED / FROZEN` by Addendum
  A (`v1`) at
  `docs/experiments/Experiment_Protocol_Addendum_A_V3_1_0.md`
- V3.1.0 historical Addendum A human annotation path: single primary annotator
  `wang`; second human annotator `ABSENT`; review method
  `delayed_blinded_self_review`; minimum delay `48 hours`
- V3.1.0 Phase 6 reviewer/adjudicator semantics: `reviewer_id=wang` denotes delayed
  blinded self-review, not second-person review; `adjudicator_id=null` without
  adjudication and `adjudicator_id=wang` when a recorded disagreement is adjudicated
- V3.1.0 Phase 6 independent model/data audit may validate manifests, hashes, leakage,
  masked samples, and dataset consistency, but is not a human second annotator and
  cannot produce human inter-annotator agreement
- V3.1.0 historical Addendum A annotation limitation: its single-human and
  delayed-review claims apply only if that human path is actually completed. The
  user-approved Addendum D specification-anchored path below does not inherit those
  completion or mitigation claims; no per-query human review or human IAA occurred
- V3.1.0 Experiment Protocol: `FROZEN` at
  `docs/experiments/Experiment_Protocol_V3_1_0.md`
- V3.1.0 formal RQ1–RQ4: `NOT STARTED`
- V3.1.0 Phase 6.1 — Benchmark Infrastructure: `COMPLETED`
- V3.1.0 Phase 6.1 Initial Independent QA: `FAIL / BLOCKED`
- V3.1.0 Phase 6.1 Initial QA findings: Critical `4`; Medium `7`; Low `3`
- V3.1.0 Phase 6.1.1 — Benchmark Evidence Integrity Hardening: `COMPLETED`
- V3.1.0 Phase 6.1.1 C1–C4: `CLOSED / RESOLVED`
- V3.1.0 Phase 6.1.1 Medium findings M1–M7: `CLOSED / RESOLVED`
- V3.1.0 Phase 6.1 Directed Retest: `PASS WITH LOW NOTES`
- V3.1.0 Phase 6.1 Final QA: `PASS FOR PHASE 6.1 WITH LOW NOTES`
- V3.1.0 Phase 6.1 Final Critical / Medium / Phase blocker: `0 / 0 / 0`
- V3.1.0 Phase 6.1 residual defensive Low: `1`; future UUID-like version/run
  identifiers may receive stricter canonical validation; non-blocking
- V3.1.0 Phase 6.1.2 — Annotation Lifecycle Schema Hardening:
  `COMPLETED`
- V3.1.0 Phase 6.1.2 root cause: `GroundTruthRecord` required `reviewed_at` to be a
  non-empty timestamp and therefore could not represent the frozen pre-review
  `drafted` annotation state
- V3.1.0 Phase 6.1.2 resolution: `drafted` records support `reviewed_at=null` and
  reject review/adjudication evidence; `reviewed`, `adjudicated`, and `frozen`
  records require a valid review timestamp at least 48 hours after `created_at`, in
  accordance with the Addendum A lifecycle
- V3.1.0 Phase 6.1.2 validation: annotation lifecycle / Phase 6.1 benchmark
  infrastructure `47 passed`; Phase 5 `48 passed`; Phase 4 `37 passed`; Phase 3.2
  `10 passed`; Phase 3.1 `12 passed`; Phase 2 `14 passed`; Phase 1 `41 passed`;
  offline LLM-contract smoke `6 passed`; full regression `623 passed`; no dataset,
  query, ground-truth artifact, Retriever/E5 call, network request, or formal RQ run
  was performed
- V3.1.0 Phase 6.1.2 Directed Retest: `NOT PASS`; new Critical `0`; new Medium `1`
- V3.1.0 Phase 6.1.2 original drafted/null schema blocker: `CLOSED / RESOLVED`
- V3.1.0 Phase 6.1.3 — Annotation Lifecycle Consistency Hardening:
  `COMPLETED`
- V3.1.0 Phase 6.1.3 M-1 root cause: `annotation_status=reviewed` could retain a
  non-null `adjudicator_id`, contradicting the frozen Addendum A meaning that review
  completed without adjudication
- V3.1.0 Phase 6.1.3 resolution: `reviewed` rejects every non-null
  `adjudicator_id`; `adjudicated` still requires one; `frozen` continues to allow
  either null or non-null adjudication provenance; generic identity remains outside
  schema scope
- V3.1.0 Phase 6.1.3 implementation commit:
  `675bf0d5c78bba10577d639dc5e39fcd2df0a877`
- V3.1.0 Phase 6.1.3 Independent Directed Retest: `PASS WITH LOW NOTES` on
  `675bf0d5c78bba10577d639dc5e39fcd2df0a877`; repository-external probes
  `69 passed / 0 failed`; new Critical / Medium `0 / 0`
- V3.1.0 Phase 6.1.3 M-1: `CLOSED / RESOLVED`; final Critical / Medium `0 / 0`;
  Phase 6.1.4 `NOT REQUIRED`
- V3.1.0 Phase 6.1.3 residual non-blocking Low: generic schema leaves the frozen
  `wang` reviewer/adjudicator identity check to the Phase 6.2 dataset contract;
  `_timestamp` exception `__cause__` may retain malformed input. The earlier Phase
  6.1 UUID v7 shape / `RunMetadata.run_id` validation note also remains non-blocking
- V3.1.0 Phase 6.1.3 validation: annotation lifecycle / Phase 6.1 benchmark
  infrastructure `52 passed`; Phase 5 `48 passed`; Phase 4 `37 passed`; Phase 3.2
  `10 passed`; Phase 3.1 `12 passed`; Phase 2 `14 passed`; Phase 1 `41 passed`;
  offline LLM-contract smoke `6 passed`; full regression `628 passed`; no dataset,
  query, ground-truth artifact, Retriever/E5 call, network request, or formal RQ run
  was performed
- V3.1.0 Phase 6.1.3 QA closure report:
  `docs/qa/QA_Report_V3_1_0_Phase_6_1_3.md`
- V3.1.0 Phase 6.1 Documentation Gate: `CLOSED`
- V3.1.0 Phase 6.1 implementation: isolated experiment-only infrastructure in
  `experiments/` for immutable deterministic benchmark configuration identity,
  strict dataset/query/ground-truth and result contracts, canonical credential-free
  serialization, append-only run artifacts, reproducibility metadata, frozen File
  and Character Chunk lexical baselines, unit-aware truth mapping, retrieval metrics,
  aggregate strata, and a strategy-driven benchmark runner skeleton
- V3.1.0 Phase 6.1 metrics: Recall@1/5/10, MRR@10, nDCG@5 with grade 2/1/0 gains,
  Precision@5 with a fixed denominator, and Hit Rate@5; failed queries remain in the
  denominator with zero quality metrics
- V3.1.0 Phase 6.1 oracle: independent hand-calculated synthetic metric fixture under
  `tests/fixtures/experiments/`; expected values are not generated by implementation
  metric helpers
- V3.1.0 Phase 6.1 baseline boundary: File identity/text and deterministic 1200/200
  Unicode-code-point Chunk identity/text are experiment-only; production Symbol
  retrieval behavior and Phase 1–5 public contracts are unchanged
- V3.1.0 Phase 6.1 semantic safety: fake semantic mode is explicit and test-only;
  formal semantic configuration requires the frozen real-E5 fingerprint; provider
  failure never substitutes fake embeddings; degraded semantic output invalidates a
  formal run; formal execution remains disabled by default in the runner skeleton
- V3.1.0 Phase 6.1.1 validation: infrastructure/hardening `31 passed`; Phase 5 `48 passed`;
  Phase 4 `37 passed`; Phase 3.2 `10 passed`; Phase 3.1 `12 passed`; Phase 2
  `14 passed`; Phase 1 `41 passed`; offline LLM-contract smoke `6 passed`; full
  regression `607 passed`; no real model, formal query, formal ground truth, formal
  benchmark, network LLM request, or credential was used
- V3.1.0 Phase 6.1 Directed Retest independent probes: `41 passed` (`8` C1/C2,
  `10` C3/C4, `16` M1–M7, `7` extra); not included in pytest `607 passed`
- V3.1.0 Phase 6.1 determinism: `120` input permutations and `PYTHONHASHSEED`
  `1 / 7 / 31` passed deterministically
- V3.1.0 Phase 6.1 protocol drift: `0`; frozen
  `docs/experiments/Experiment_Protocol_V3_1_0.md` unchanged
- V3.1.0 Phase 6.1 formal dataset/query/ground truth: `ABSENT / PHASE 6.2 NOT STARTED`
- V3.1.0 Phase 6.1 formal benchmark: `NOT RUN`; no RQ1–RQ4 result or conclusion exists
- V3.1.0 Phase 6.1 reports: `docs/development/Development_Report_V3_1_0_Phase_6_1.md`
  and `docs/qa/QA_Report_V3_1_0_Phase_6_1.md`
- V3.1.0 Phase 6.2.0 — Dataset Specification Documentation Freeze:
  `COMPLETED / SPECIFICATION FROZEN`
- V3.1.0 Dataset Specification: `AVAILABLE IN REPOSITORY` at
  `docs/experiments/Dataset_Query_GroundTruth_Specification_V3_1_0.md`
- V3.1.0 Phase 6.2 research specification source: Grok 4.7 review + corrected
  specification + GPT-5.6 Sol cross-audit; these are design/review provenance, not
  empirical evidence
- V3.1.0 Phase 6.1.3 annotation-lifecycle blocker: `LIFTED / RESOLVED`;
  the earlier Phase 6.2A `blocker=LIFTED` was the correct historical state
- V3.1.0 later Phase 6.2A materialization attempt:
  `STOPPED ON NEW INCREMENTAL FIXTURE SPECIFICATION CONFLICT`; no dataset,
  query, or ground-truth artifact was created
- V3.1.0 Grok 4.7 Incremental Fixture Semantics methodology review: `COMPLETED`;
  this is review provenance, not formal experiment evidence
- V3.1.0 Phase 6 Incremental Fixture SnapshotDiff Semantics Addendum B:
  `FROZEN` at `docs/experiments/Experiment_Protocol_Addendum_B_V3_1_0.md`;
  raw-byte SHA-256 `34406b3dad94cf21c3422176cedd7b94221f18518b82c97e8c061e52b3972a5d`
- V3.1.0 Incremental Fixture Specification Conflict:
  `CLOSED / RESOLVED BY ADDENDUM B`; direct edit set `3 changed / 2 added /
  2 removed`; enclosing symbol effect `Bin / Shelf`; authoritative SnapshotDiff
  `5 changed / 2 added / 2 removed / 0 unchanged`
- V3.1.0 incremental fixture embedding contract: `7` new documents from
  `changed ∪ added`; `embed_documents` is one batch of seven texts; removed and
  unchanged require zero new document embeddings
- V3.1.0 Addendum B scope: production parser, SymbolId, Snapshot, SnapshotDiff,
  RetrievalIndex, and hashing `UNCHANGED`; RQ1–RQ4 methodology `UNAFFECTED`;
  Protocol + Addendum A + Addendum B govern, with Dataset Specification subordinate
  to Addendum B only for the corrected incremental fixture counts
- V3.1.0 Phase 6.2A blocker after Addendum B (historical):
  `LIFTED AGAIN AFTER ADDENDUM B`
- V3.1.0 subsequent Phase 6.2A failed materialization attempt: `STOPPED`;
  Query wording / leakage policy conflict `IDENTIFIED`; this was separate from
  the resolved Addendum B incremental conflict
- V3.1.0 invalid Phase 6.2A draft history: `34` untracked artifacts under
  `docs/experiments/datasets/v1/`, `docs/experiments/queries/v1/`, and
  `docs/experiments/ground_truth/v1/` were discarded before this documentation
  correction; `INVALID / NOT AUTHORITATIVE / NOT COMMITTED / NOT REUSABLE`;
  no Phase 6.2 dataset-contract test was created, and `docs/thesis/` was untouched
- V3.1.0 Query Leakage Methodology Review: `COMPLETED`; Multi-token Clarification:
  `COMPLETED`; the earlier uncommitted `len(tokenize(simple_name)) == 1` proposal
  was rejected because the frozen tokenizer retains identifier components
- V3.1.0 Phase 6 Query Leakage Control Addendum C: `FROZEN` at
  `docs/experiments/Experiment_Protocol_Addendum_C_V3_1_0.md`;
  raw-byte SHA-256 `3a3e125b1245206ec49fe22c59cd95b625a7ec28d4c75f10dcc361770f238c79`
- V3.1.0 Addendum C corrected queries: `4` — originally authorized
  `et-bl-py-01`, `et-bl-py-03`, `et-mt-py-03`, plus `et-cf-py-01` explicitly
  authorized by the user after full-table validation found `_document -> document`;
  the fourth replacement uses `retrieval unit`; all IDs, Grade-1/2 anchors,
  allocation, and the 72-query count remain unchanged
- V3.1.0 Addendum C leakage rule: extract
  `simple_name = qualified_name.rsplit(".", 1)[-1]`, use frozen `code-lexical-v1`,
  fail closed on empty tokens, and prohibit `tokenize(simple_name)[0]` in
  `tokenize(query_text)` for non-`symbol_lookup`; `FULL IDENTIFIER TOKEN ONLY`;
  compound component tokens `ALLOWED BY THIS GATE`; manual allowlist `NONE`;
  no single-token-count requirement or NLP / ordinary-English exception
- V3.1.0 Addendum C validation: `8` tokenizer examples verified; all `4` old texts
  fail and all replacements pass this token gate; frozen table `72` queries,
  `12` lookup exemptions, `60` non-lookup targets, `39` multi-token simple names,
  `0` remaining full-identifier-token failures after replacements; full regression
  `628 passed`; this is documentation/tokenizer evidence, not Dataset/GT validation
  or a formal RQ result
- V3.1.0 current Protocol reference-updated SHA-256:
  `214360ac17633db7d77caec2ea2a135bf4372a773f9343b2fcb91bff8ee4e341`;
  current Dataset Specification reference-updated SHA-256:
  `4e72ceb84f06df361e10a24a6ab273ed3f6eba4d3649b96177a810c6a0c30a92`;
  all original and earlier reference-updated hashes remain recorded in Addenda B/C
- V3.1.0 current Source of Truth: Protocol + Addenda A/B/C +
  [Addendum D](docs/experiments/Experiment_Protocol_Addendum_D_V3_1_0.md).
  D supersedes only its enumerated human-review/reference-approval scope for the
  72-query specification-anchored method, including a scoped exception to Phase 0
  Architecture Decision §18's human-primary GT sentence; independent methodology
  review is still required before formal reference approval. A remains historical
  for old v1 fields; B/C and all unaffected Protocol/Specification clauses continue.
  Production,
  tokenizer, infrastructure/tests, RQ1–RQ4 and frozen retrieval configuration are
  unchanged
- V3.1.0 Query Leakage Conflict: `CLOSED / RESOLVED BY ADDENDUM C`
- V3.1.0 Phase 6.2A blocker: `LIFTED AFTER ADDENDUM C`
- V3.1.0 Phase 6.2A — Dataset / Query / Ground Truth Draft Materialization:
  `COMPLETED`; clean regeneration from the frozen Git specification plus Addenda
  A/B/C, beginning at `e97a0e03afeaf2a16127c81577f9ef0760db3611`; discarded drafts
  were not restored or reused
- V3.1.0 Phase 6.2 dataset/query/ground truth: `DRAFTED / DRAFTED / DRAFTED`;
  primary manifest has `4` projects, `93` files and `1299` symbols; the independent
  incremental fixture is excluded from this dataset and its query population
- V3.1.0 Phase 6.2 annotation: `MECHANICAL MATERIALIZATION COMPLETE / DRAFTED`;
  Codex mechanically materialized the user-authorized frozen relevance decisions
  and source-grounded rationales, with protocol-designated annotator `wang` and
  future self-reviewer `wang`; no second human, completed review, or human IAA is
  represented; `reviewed_at=null`, `adjudicator_id=null`
- V3.1.0 Phase 6.2 successful draft `created_at`:
  `2026-09-23T04:00:42.357095+00:00`; delayed review clock `STARTED`;
  earliest allowed review `2026-09-25T04:00:42.357095+00:00` (exactly 48 hours);
  Delayed Blinded Self-Review `PENDING`, not automatically executed or scheduled
- V3.1.0 Phase 6.2A frozen self-repository recomputation: Python/Java `72/0`,
  production/test `44/28`, symbols `1233` (class/method/function `190/377/666`),
  zero-symbol files `8`, File/Chunk documents `72/857`, symbols over 1200 chars
  `151`, multi-chunk symbols `747`; source is raw blobs from the frozen commit,
  with scanner/root-ignore agreement, not the working tree
- V3.1.0 Phase 6.2A primary fixtures: route-ledger `8 files / 28 symbols`,
  intake-queue `7 / 15`, desk-queue `6 / 23`; required defects preserved;
  Java exact local imports `7`, unique top-level types `6`, distinct overload
  signatures with no fallback identity; no wildcard/static imports, inheritance,
  enums, or nested classes
- V3.1.0 Phase 6.2A incremental evidence: base/update each `3 files / 7 symbols`;
  direct edit set `3/2/2`; production SnapshotDiff `5/2/2/0`, including enclosing
  `Bin` and `Shelf`; future changed-plus-added batch `7` documents / `1` call;
  actual embedding calls `0`
- V3.1.0 Phase 6.2A actual query distribution: English test/dev/Chinese `48/12/12`,
  every task `8/2/2`; Python/Java `36/12`, `10/2`, `12/0`; project allocation
  self/route/intake/Java `32/13/13/14`; Addendum C corrections `4/4` verified;
  non-lookup targets `60`, multi-token targets `39`, leakage failures `0`
- V3.1.0 Phase 6.2A truth: `72` records, `134` evidence items; grades 2/1/0
  `72/62/0`; all six SymbolId fields, source spans, raw hashes, and rationale
  provenance verified against real adapter output; no orphan or duplicate evidence
- V3.1.0 Phase 6.2A English-test multi-relevant/cross-file actual counts, each out
  of 8: lookup `1/0`, feature `7/4`, dependency `8/5`, bug `7/5`, maintenance
  `7/5`, cross-file `8/6`; Grade-1 overlap audit `23` symbol groups,
  Chinese-English overlap audit `7` groups; all `2556` query pairs pass Jaccard
  threshold `0.55`; Chinese non-translation judgment remains pending delayed review
- V3.1.0 Phase 6.2A RQ1 mechanical probes: normalization symbol `1689` characters
  overlaps chunks `[0,1200)` and `[1000,1917)`; rejection explanation `[20,141)`
  and final-record decision `[1834,1916)` share no chunk; all three named
  cross-file probes pass; File/Symbol/Chunk maximum-grade mapping and endpoint
  non-overlap verified without retrieval; Java test subsets CONTAINS/IMPORTS `5/7`
- V3.1.0 Phase 6.2A dataset hash:
  `164994a826fe51936d5fcb012a8d102967c33110787405fd3b0f7972efe8ade7`
- V3.1.0 Phase 6.2A query-set hash:
  `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`
- V3.1.0 Phase 6.2A drafted truth hash:
  `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87`
- V3.1.0 Phase 6.2A path-manifest hash:
  `9adddbc3e69716b899352185d22b15df74b9c03e6d25aac9857a958fe7c33978`;
  identity records all five frozen document hashes and the authoring-audit hash;
  `checksums.sha256` verifies all `34` formal data files other than itself
- V3.1.0 Phase 6.2A validation: new offline dataset contract `94 passed`;
  Phase 6.1/lifecycle `52`, Phase 5 `48`, Phase 4 `37`, Phase 3.2 `10`,
  Phase 3.1 `12`, Phase 2 `14`, Phase 1 `41`, offline LLM smoke `6`;
  full regression `722 passed` from baseline `628 passed`, with
  `python -m pytest -p no:debugging`
- V3.1.0 Phase 6.2A authorized scope extension: the user explicitly approved
  migration of `test_no_formal_dataset_truth_or_result_artifacts_were_added` in
  `tests/test_experiment_benchmark_infrastructure.py`; the test is retained,
  allows only drafted GT, rejects completed review/adjudication/freeze, and keeps
  runs forbidden; no test was deleted/skipped and Phase 6.1 still has `52` tests
- V3.1.0 Phase 6.2A authoring `retrieval_runs_before_freeze=0`; no authoring
  Retriever/Graph ranking, E5 inference, network call, Dry Run or formal RQ run;
  existing offline regression tests retain their synthetic/stub retrieval checks;
  production, experiment infrastructure, dependencies, frozen research documents,
  AGENTS/CLAUDE and user `docs/thesis/` content remain unchanged
- V3.1.0 Phase 6.2A Independent Draft Data QA: DeepSeek V4.1 Flash reply summary
  `PASS WITH LOW NOTES`, reported Critical / Medium `0 / 0`; QA Documentation
  Closure `CLOSED` at `docs/qa/QA_Report_V3_1_0_Phase_6_2A_Independent_Draft_Data.md`
  for the draft report only. Current repository verification independently matched
  dataset/query/truth hashes, 34 raw checksums, 72 drafted GT and 72 drafted audit
  entries; offline Phase 6.2 contract `94 passed`, full pytest `722 passed`, both
  exit code 0 with `-p no:debugging`. The repository-external `probe1`–`probe9`
  scripts/raw outputs were not supplied or archived; their detail remains attributed
  to the DeepSeek reply, not to this repository execution.
- V3.1.0 Phase 6.2A Independent Draft Data QA Low notes: L1 blinded masking and
  L2 Chinese non-translation/semantic judgments remain Phase 6.2B human work;
  L3 compliant cross-record reuse, L4 corrected QA-probe error, and L5 single-human
  annotation/no human IAA are observations or methodology limits, not confirmed
  dataset defects. The reply's displayed escaped end marker was not authenticated
  against an original message record; remote push state was not checked. Current
  identity field `retrieval_runs_before_freeze=0` and absent run artifacts do not
  establish historical absence of temporary/untracked retrieval activity.
- V3.1.0 Phase 6.2 Gate: `OPEN`
- V3.1.0 historical single-judge LLM silver reference proposal:
  `PROPOSED / NOT EFFECTIVE / NO LABELING AUTHORIZED`，见
  [非生效 Addendum D 候选提案](docs/experiments/PROPOSED_NOT_EFFECTIVE_NO_LABELING_AUTHORIZED_Addendum_D_Single_Judge_Silver_Reference_V3_1_0.md)。
  它不是当前执行路径，不与正式 D 并行生效。
- V3.1.0 Phase 6.2 formal Addendum D: user-approved
  `specification-anchored reference` method + preregistered limited TraeWork
  `DeepSeek-V4.1-Flash` evidence audit, not full silver or human blind review;
  Addendum D raw-byte SHA-256
  `2e276bbcc63a75ce12760d3728894860a9a7328bd040fd21c6ba2ce27c160375`;
  12 English-test IDs are the first two lexicographic IDs in each of six task types
  and are all Java. Addendum D method/preregistration is tracked; independent
  methodology review, actual 12 audits, Chinese non-translation verification,
  reference approval/schema/runner Gate migration and final independent Data QA
  remain pending. No LLM evidence audit or formal retrieval has run.
- V3.1.0 Addendum D independent contract QA: user-provided reply reports
  `PASS WITH NOTES`; the raw probes/full reply are not archived in Git, and its
  documentation closure remains a separate pending decision.
- V3.1.0 Phase 6.2 Java evidence audit inputs: `PREPARED / NOT EXECUTED` at
  [evidence_audit/prepared](docs/experiments/evidence_audit/prepared/README.md).
  All 12 preregistered English-test Java queries have individually hashed prompts,
  complete cited frozen fixture files and blank execution records; no model call,
  evidence judgment, Python/Chinese audit or GT change occurred. This preparation
  does not approve the reference or close the Phase 6.2 Gate.
- V3.1.0 Phase 6.2B under Addendum D: `PENDING`; next steps are the preregistered
  12-item evidence audit, independent source checks for doubts, bounded Chinese
  non-translation review, provenance/reference approval implementation, final Data
  QA and explicit Gate decision. Old ≥48-hour human self-review is not the new route;
  Phase 6.2 is not completed
- V3.1.0 Phase 6.2B blinded review preparation:
  `PREPARATION COMPLETE / NOT REVIEWED`;
  `docs/experiments/blind_review/` contains a reproducible GT-free query/source bundle
  generator, 72-query blank second-judgment packet, blinded reviewer instructions,
  and operator-only preparation/comparison procedure. The verified bundle contains
  all 93 frozen source files, no GT/audit/ranking file or query-specific candidate
  selection; blank packet raw-byte SHA-256 is
  `eb031f55870a35e74824454cdae9fd6d2ab5654e1906a1205761b4658678f095`.
  Same-account access to the full repository remains an actual masking limitation;
  under the historical A path only a separate GT-free bundle could be handed to
  `wang`; future human behavior could not be certified by preparation checks
- V3.1.0 Phase 6.2B blinded review preparation independent QA:
  `PASS WITH LOW NOTES`; its Documentation Closure is `CLOSED` at
  `docs/qa/QA_Report_V3_1_0_Phase_6_2B_Blinded_Review_Preparation.md`. The
  existing external bundle passed current read-only verification for 72 unique
  Query and 93 frozen source files with blank judgments and no symlinks; offline
  Phase 6.2 contract `94 passed`, full regression `722 passed`. DeepSeek's
  37 independent assertions and separate byte-identical regeneration are reply
  claims without archived raw scripts/outputs. Actual GT-free delivery and human
  masking remain unproven; this closure does not complete the human review,
  final Data QA, or Dataset Freeze; this preparation remains historical under D
- V3.1.0 Phase 6.3: `BLOCKED / NOT STARTED`
- V3.1.0 formal RQ1–RQ4: `NOT STARTED`
- V3.1.0 Phase 6 self-repository dataset commit:
  `12391233daa2149ead4f451e920b2e0d8a1a6beb`
- V3.1.0 Phase 6 formal test rule: once formal test results exist, they must not be
  used to tune parameters within the frozen protocol version
- V3.2 Multi-Agent: `NOT STARTED`
- Claude Phase 3.0 Semantic Embedding Selection Review: `COMPLETED / READ-ONLY`;
  verdict `APPROVE WITH NON-BLOCKING OPEN QUESTIONS`; architecture blocker `0`;
  research-methodology blocker `0`
- Phase 3.0 selection summary: primary `intfloat/multilingual-e5-base` (revision
  `d128750597153bb5987e10b1c3493a34e5a4502a`, dimension `768`, L2 normalization,
  cosine similarity, query instruction `query: `, document instruction `passage: `;
  English main benchmark with a Chinese coverage set); backup
  `BAAI/bge-base-en-v1.5`; core requirements remain unchanged and real-model
  dependencies are optional
- Historical Audit Remediation P1: `RESOLVED`; this is a documentation/contract
  clarification only. Deferred audit items are P2: V3.0.0 formal release-gate
  evidence, V3.0.0 Thesis Development Report, and tracked V3.0.1 Thesis
  Development Report; P3: CorpusBuilder optional canonical tie-key hardening
- Historical pre-release state used `3.0.1` metadata until V3.1.0 Release Engineering;
  current release metadata is `3.1.0`.
- Previous release: V3.0.1 `RELEASED / FROZEN`
- V3.0.1: `RELEASED`
- Status: `V3.0.1 Final / Stable Release`
- V3.0.1 Final Release Gate: `PASS`
- V3.0.1 Core Feature Freeze: `COMPLETED`
- V3.0.1 RC1.1 — Release Engineering Gate: completed (`PASS`)
- V3.0.1 RC1.1 Release Blockers: `0`
- V3.0.1 RC1.2 — Repository Hygiene Audit: completed
  (`PASS WITH CLEANUP RECOMMENDED`)
- V3.0.1 RC1.2 Release Blockers: `0`
- V3.0.1 Final baseline: `414 passed`
- V3.0.1 RC1.3 — Product Documentation: completed
- Product Documentation: `UPDATED`
- README: `V3.0.1 Stable Release`
- Release Notes: `docs/release/Release_Notes_V3_0_1.md`
- V3.0.1 RC1.4 — Full-System Release QA: completed (`PASS`)
- V3.0.1 RC1.4 Release Blockers: `0`
- V3.0.1 RC1.4 Product Critical / Product Medium: `0 / 0`
- V3.0.1 RC1.4 clean-environment baseline: `414 passed` under CPython 3.10.20
- V3.0.1 RC1.4 QA artifact:
  `docs/qa/QA_Report_V3_0_1_RC1_4_Full_System_Release.md`
- V3.0.1 RC1.5 — Claude Final Release Review: completed
  (`APPROVE WITH NON-BLOCKING NOTES`)
- V3.0.1 RC1.5 Release Blockers: `0`
- V3.0.1 Final Release Blockers: `0`
- V3.0.1 Product Critical / Product Medium: `0 / 0`
- Admin UI: `SKIPPED FOR V3.0.1`
- Phase 5: `SKIPPED FOR V3.0.1`
- V3.0.2 commercial track: `DEFERRED`
- No release fix or directed retest is required.
- Next: V3.1.0 Phase 3.1 — Embedding Core Architecture
- Phase 0 — Architecture & Scope Gate: completed
- Phase 0.0 — Development Baseline: completed
- Claude Phase 0 Architecture Review: completed
- V3.0.1 Architecture Decision: frozen
- Phase 0.1 — Architecture Decision Documentation: completed
- DeepSeek Phase 0 Architecture Consistency Review: `PASS WITH ISSUES`
  (Critical 0, Medium 0, Low 4, Blocking 0)
- Phase 0 Documentation Hardening: completed (O-1 through O-4 resolved)
- Phase 0 Final Documentation Gate: `CLOSED`
- V3.0.0: released / frozen
- V3.0.0 tag: annotated tag `v3.0.0` resolves to final release commit
  `2b2b0cb103264f7ac278f35c19a1dc0b02196dc8`
- V3.0.0 tracked Thesis-Oriented Development Report: missing; Documentation Backlog
- V3.0.1 tracked Thesis-Oriented Development Report: missing; a pre-existing untracked
  local candidate is preserved outside the Phase 0.0 commit and requires a separate
  Documentation Task before it becomes repository evidence
- Development baseline tests: `129 passed` with the documented current-host
  `python -m pytest -p no:debugging` workaround; ordinary pytest reproduces the known
  Anaconda Python 3.13.5 debugging-plugin / `rlcompleter` segmentation fault
- Offline LLM-contract smoke: `6 passed`; no real API, credential, or network LLM
  request was used
- Import smoke: core runtime and V3 modules passed; direct `ui` import remains blocked
  on this Anaconda Python 3.13.5 host by the documented `gradio` segmentation fault
- V3.0.1 Phase 1 — Credits Domain: completed
- V3.0.1 Phase 1 Initial QA: `PASS WITH ISSUES` (Critical 0, Medium 3,
  Low 10, Blocking 0)
- V3.0.1 Phase 1.1 — Credits Domain Post-QA Hardening: completed; production Credits
  behavior unchanged
- Phase 1.1 freezes the privileged-operation boundary (M1), idempotency payload
  contract (M2), and Phase 2 SQLite atomic-commit requirement (M3).
- Phase 1.1 validation: Credits `66 passed`; full suite `195 passed`; offline
  LLM-contract smoke `6 passed`. No real API, Credential, network, Provider, LLM, UI,
  SQLite, or `managed_access/` work was used.
- V3.0.1 Phase 1 DeepSeek Directed Retest: `PASS WITH ISSUES` (Critical 0,
  Medium 0, Blocking 0; 3 non-blocking Low observations; 13/13 independent probes
  passed). M1 and M2 are closed; M3 is closed for Phase 1 and frozen as a Phase 2
  entry contract. No further Phase 1 retest is required.
- V3.0.1 Phase 1 Final QA: `PASS`.
- V3.0.1 Phase 1 Documentation Gate: `CLOSED`.
- Phase 1 reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_1.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_1.md`.
- Directed-retest Low disposition: L1 remains a Phase 2 structural-guard requirement;
  L2 is resolved by separating the V3.0.0 and V3.0.1 test baselines; L3 is resolved by
  the version-qualified Development and QA reports.
- Phase 1 QA Low findings remain deferred: `history_of` object-reference hardening,
  transaction-ID collision enforcement, private-container exposure, integer upper
  bounds, the global `RLock`, note normalization, hostile `str` subclasses, and
  validation-helper duplication.
- V3.0.1 Phase 2 — Managed Access Foundation: completed. It adds frozen
  `LLMAccessMode` and credential-free `LLMAccessContext`, a small `ManagedProvider`
  port, configurable positive-integer `FlatPricingPolicy`, SQLite-backed managed
  request state, and `ManagedAccessService` orchestration.
- Phase 2 request state is `RESERVED -> SUCCEEDED` on Provider and accounting success,
  or `RESERVED -> FAILED` on a Provider failure. `FINALIZATION_FAILED` is the limited
  reconciliation state for Provider success followed by accounting failure; its active
  reservation is retained and replay never invokes the Provider again.
- Managed request identity is `(normalized account_id, normalized request_id)`. A
  SHA-256 payload fingerprint detects reuse with a different credential-free model
  selection, prompt, or flat price. `SUCCEEDED` replay returns completion metadata but
  does not fabricate or persist the original Provider response; `FAILED` is terminal.
- `SQLiteCreditLedger` implements the Phase 1 `CreditLedger` contract using the Python
  standard library. `USAGE` and `REFUND` transaction append plus idempotency identity
  are committed in one SQLite transaction. Failure injection verifies rollback both
  after transaction append and after idempotency write, with no orphan record.
- Phase 2 uses active managed reservations rather than a new `TransactionType`.
  Available Credits are derived as ledger balance minus `RESERVED` and
  `FINALIZATION_FAILED` reservations. Provider calls run outside SQLite write
  transactions. Final `USAGE` plus `SUCCEEDED` state is committed atomically.
- Platform credentials remain inside the injected server-side Provider implementation.
  They do not enter access context, managed request/result, credit transactions,
  SQLite, logs, or public service representations. The Managed service public surface
  exposes no ledger, `grant`, `refund`, or `adjust` operation.
- Phase 2 validation: SQLite ledger `27 passed`; Managed Access `35 passed`; original
  Credits regression `66 passed`; BYOK Provider regression `19 passed`; full suite
  `257 passed`; offline LLM-contract smoke `6 passed`. All Provider tests used offline
  stubs; no real API, credential, or network request was used.
- V3.0.1 Phase 2 Initial DeepSeek QA: `PASS WITH ISSUES` (Product Critical 0,
  Product Medium 0, Release Blocker 0); full suite `257 passed`; independent probes
  `167/167 passed`. The Phase 2 product architecture passed independent validation.
- V3.0.1 Phase 2.1 — Managed Access Post-QA Regression Hardening: completed. C1 adds
  deterministic multi-service concurrency coverage over independent SQLite connections
  and service locks. C2 freezes the Provider-success/process-interruption window as a
  persistent `RESERVED` state requiring manual reconciliation and forbidding automatic
  Provider retry. C3 exercises actual `commit()` failure for both ledger idempotency and
  Managed finalization boundaries.
- Phase 2.1 L1 is resolved by requiring exactly one row for
  `RESERVED -> FINALIZATION_FAILED`; illegal transitions from `SUCCEEDED`, `FAILED`, or
  `FINALIZATION_FAILED` now raise `ManagedAccessError` instead of succeeding silently.
- Phase 2.1 also freezes restart behavior for terminal `FAILED` and
  `FINALIZATION_FAILED` requests, flat-price payload conflicts, and fixed-seed
  InMemory/SQLite ledger parity as formal regressions.
- Phase 2.1 validation: SQLite ledger `29 passed`; Managed Access `44 passed`; original
  Credits regression `66 passed`; BYOK Provider regression `19 passed`; full suite
  `268 passed`; offline LLM-contract smoke `6 passed`. All tests remained offline and
  used only fake credentials and Stub Providers.
- V3.0.1 Phase 2 DeepSeek Directed Retest: `PASS` (Product Critical 0,
  Product Medium 0, Release Blocker 0; independent probes `186/186 passed`). C1
  multi-service concurrency, C2 Provider-success crash-window safety, C3 commit-boundary
  atomicity, and L1 rowcount consistency are closed. No double charge, double Provider
  call, partial SQLite commit, reservation loss, Credential leak, or BYOK regression
  was found. No further production fix or directed retest is required.
- V3.0.1 Phase 2 Final QA: `PASS`.
- V3.0.1 Phase 2 Documentation Gate: `CLOSED`.
- Phase 2 reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_2.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_2.md`. Phase 2.1 is included in the Phase 2 reports.
- V3.0.1 Phase 3 — Usage Metering + PricingPolicy: completed. It adds immutable,
  Credential-free `UsageRecord`, `PricingContext`, and `ManagedProviderResponse`
  contracts plus a minimal `PricingPolicy` Protocol for reservation quotes and actual
  usage pricing. Zero-total-token usage is rejected; input-only and output-only usage
  remain valid.
- `TokenPricingPolicy` uses synthetic `Decimal` Credit rates per 1,000 tokens and
  converts the final amount to integer Credits with `ROUND_CEILING`. Floats, `bool`,
  negative values, NaN, Infinity, and an all-zero rate configuration are rejected.
  Stable versioned policy identities participate in Managed request payload identity.
- Token-priced Managed requests require an explicit provider/model/token-limit
  `PricingContext`. The priced limits form the pre-Provider reservation upper bound.
  Actual usage must match the provider and model, remain within the declared limits,
  and price to `0 <= actual_credits <= reserved_credits`.
- Provider success with missing, malformed, mismatched, over-limit, or over-reservation
  usage transitions to `FINALIZATION_FAILED`, retains the reservation, and is never
  automatically reinvoked. Successful reconciliation records only the actual `USAGE`
  charge; unused reservation capacity is released without a compensating refund.
- Phase 3 persists Credential-free usage metadata and final Credits in `managed_usage`.
  The `USAGE` transaction, Credit idempotency record, usage metadata, final Credits,
  and `SUCCEEDED` transition share one SQLite transaction. Phase 2 databases migrate
  in place, preserve existing ledger/request data, and retain compatible flat-price
  replay behavior.
- `FlatPricingPolicy` implements the new `PricingPolicy` contract while preserving the
  Phase 2 behavior: reservation equals final Credits, usage remains optional, and
  legacy string Provider responses remain supported. BYOK, UI, processor, and Provider
  foundation files remain unchanged.
- Phase 3 validation: Usage/Pricing and Managed token flow **55 passed**; original
  Managed Access regression **44 passed**; SQLite ledger **29 passed**; Credits
  regression **66 passed**; BYOK Provider regression **19 passed**; offline
  LLM-contract smoke **6 passed**; full suite **323 passed**. All tests were offline and
  used only synthetic rates, fake credentials, and Stub Providers.
- V3.0.1 Phase 3 Initial DeepSeek QA: `PASS WITH ISSUES` (Critical 0, Medium 1,
  Release Blocker 0). M1 found that token-price arithmetic depended on the ambient
  Decimal context and could undercharge under low precision. QA also verified that the
  Phase 3 core architecture passed and identified the recoverable SQLite migration
  autocommit window for immediate hardening.
- V3.0.1 Phase 3.1 — Pricing Determinism & Migration Hardening: completed. Token
  pricing now uses a dynamically sized local Decimal context with fixed
  `ROUND_CEILING`, independent of caller precision and rounding, while policy identity
  canonicalization no longer performs context-sensitive Decimal normalization.
- Phase 3.1 places all Managed schema changes, policy-identity backfill,
  `managed_usage` creation, and legacy usage initialization inside one
  `BEGIN IMMEDIATE` transaction. Real SQLite failure injection after the first
  alteration, during backfill, before usage-table creation, and during legacy usage
  initialization proves that DDL and data changes roll back together before a normal
  reopen completes the migration.
- Phase 3.1 regression coverage includes ambient Decimal precision/rounding matrices,
  large Decimal rates and token counts, a faithful Phase 2 schema fixture, five
  idempotent migration reopens, existing usage-metadata preservation, privacy scans of
  logical rows/dumps/database sidecars, zero-cost finalization atomicity, and Flat/Token
  request-identity conflicts in both directions.
- Phase 3.1 validation: Phase 3 pricing, token-flow, and hardening tests **75 passed**;
  original Managed Access regression **44 passed**; SQLite ledger **29 passed**;
  Credits regression **66 passed**; BYOK Provider regression **19 passed**; offline
  LLM-contract smoke **6 passed**; full suite **343 passed**. No real API, Credential,
  or network LLM request was used.
- V3.0.1 Phase 3 DeepSeek Directed Retest: `PASS` (Product Critical 0, Product
  Medium 0, Release Blocker 0; independent probes `137/137 passed`). M1 ambient
  Decimal-context determinism is resolved and the previous L1-L6 observations are
  closed. Evidence includes 11 precision settings by 8 rounding modes with zero drift,
  9,000 reservation cases with zero invariant violation, four atomic-migration failure
  points with complete rollback, 20 reopens with zero drift, and zero privacy-marker
  occurrences.
- Phase 3 Final QA: `PASS FOR PHASE 3`. No further production fix or directed retest
  is required. L7 initialization connection-close structure and L8 proactive validation
  of a malformed pre-existing `managed_usage` table remain Low, non-blocking, and
  deferred for future hardening.
- Phase 3 contracts are frozen: `UsageRecord`; `PricingPolicy`; Phase 2-compatible
  `FlatPricingPolicy`; deterministic `TokenPricingPolicy`; local Decimal pricing with
  `ROUND_CEILING`; reservation upper bounds; actual reconciliation;
  `FINALIZATION_FAILED` fail-closed behavior; provider/model integrity; private usage
  persistence; atomic finalization; atomic Phase 2-to-Phase 3 migration; and request
  fingerprint/pricing-policy identity.
- V3.0.1 Phase 3 Documentation Gate: `CLOSED`. The combined Phase 3 and Phase 3.1
  reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_3.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_3.md`.
- V3.0.1 Phase 4 — Admin Operations Surface: completed. It adds a trusted
  server-side `AdminCreditService` with immutable `AdminOperationContext` and
  `AdminOperationRecord` values plus the minimal `GRANT` and `ADJUSTMENT`
  `AdminOperationType` values.
- Phase 4 administrative operation identity is `(normalized actor_id, normalized
  operation_id)`. Exact replay returns the persisted audit record without another
  Credit mutation, while any change to operation type, normalized account, amount,
  or normalized non-empty reason raises `AdminOperationConflictError`.
- Phase 4 persists normalized administrative audit metadata in
  `admin_credit_operations`. Each `ADMIN_GRANT` or `ADJUSTMENT` Credit transaction
  and its immutable admin audit row share one `BEGIN IMMEDIATE` SQLite transaction;
  failure injection and commit-failure coverage prove all-or-nothing rollback and
  safe retry.
- `AdminCreditService.balance()` and `history()` expose only an integer balance and
  immutable Credit transaction tuple. The service does not return a `CreditLedger`,
  and `ManagedAccessService` continues to expose no grant, adjust, refund, ledger, or
  Admin service capability.
- Phase 4 validation: Admin Operations **51 passed**; Phase 3 pricing/token-flow and
  hardening **75 passed**; Managed Access **44 passed**; SQLite ledger **29 passed**;
  Credits **66 passed**; BYOK Provider **19 passed**; offline LLM-contract smoke
  **6 passed**; full suite **394 passed**. No real API, Credential, Provider-network,
  or network LLM request was used.
- Phase 4 Initial DeepSeek QA: `PASS WITH ISSUES` (Critical 0, Medium 1, Low 3,
  Release Blocker 0). M-1 demonstrated that hostile `str` subclasses could bypass
  Admin actor/operation normalization and create a duplicate Grant. The Phase 4 core
  idempotency, atomicity, audit, foreign-key, concurrency, restart, migration, and
  Credential-boundary behavior passed independent validation.
- V3.0.1 Phase 4.1 — Admin Identity & Persistence Hardening: completed. The Admin
  boundary now accepts only exact built-in strings before trimming actor ID,
  operation ID, account ID, and reason, so caller-defined `strip`, equality, hash,
  string conversion, and representation behavior cannot influence Admin identity,
  replay comparison, or SQLite keys. Normal built-in whitespace normalization is
  unchanged.
- Phase 4.1 adds an Admin persistence guard for SQLite signed 64-bit Credit amounts.
  Out-of-range grants and adjustments raise `InvalidCreditAmountError` before any
  write and leave the operation identity reusable. Executable regression coverage
  also verifies `PRAGMA foreign_keys = 1` on the service connection and rejects an
  audit row whose Credit transaction does not exist.
- Phase 4.1 validation: Admin Operations **71 passed**; Phase 3 pricing/token-flow and
  hardening **75 passed**; Managed Access **44 passed**; SQLite ledger **29 passed**;
  Credits **66 passed**; BYOK Provider **19 passed**; offline LLM-contract smoke
  **6 passed**; full suite **414 passed**. All validation remained offline and used no
  real API, Credential, Provider-network, or network LLM request.
- V3.0.1 Phase 4 DeepSeek Directed Retest: `PASS` (Product Critical 0, Product
  Medium 0, Release Blocker 0; independent assertions `159 passed`; full suite
  `414 passed`). M-1 is resolved: hostile actor/operation subclasses are rejected
  before caller-defined identity behavior, with zero additional writes and zero
  hostile-method executions. Exactly-once replay, multi-service concurrency, restart,
  foreign-key enforcement, five atomic rollback boundaries, and Credential privacy
  passed independent validation. No further production fix or directed retest is
  required.
- Phase 4.1 resolves M-1 and hardens L-1 SQLite integer-range validation. L-2
  close-after-use exception wrapping remains deferred. Cumulative SQLite `SUM(amount)`
  overflow from multiple individually valid transactions remains a non-blocking member
  of the existing integer-upper-bound technical-debt family; it can make the affected
  account query fail but does not corrupt data, duplicate a Grant, break atomicity, or
  affect other accounts.
- Phase 4 contracts are frozen: `AdminOperationContext`, `AdminOperationType`,
  `AdminOperationRecord`, `AdminCreditService`, exact built-in string identity,
  `(actor_id, operation_id)` idempotency, Credit plus audit atomicity, foreign-key
  enforcement, grant/adjustment semantics, the Managed privileged boundary, refund
  non-exposure, and the Admin SQLite signed-64 amount guard.
- V3.0.1 Phase 4 Final QA: `PASS FOR PHASE 4` (Critical 0, Medium 0, Release
  Blocker 0). Phase 4 Documentation Gate: `CLOSED`. The combined Phase 4 and Phase 4.1
  reports are recorded as
  `docs/development/Development_Report_V3_0_1_Phase_4.md` and
  `docs/qa/QA_Report_V3_0_1_Phase_4.md`.
- Phase 4 does not expose `refund()`. Admin UI is `SKIPPED FOR V3.0.1` and remains a
  possible future enhancement. Optional Phase 5 Payment Interface Reservation is
  `SKIPPED FOR V3.0.1`; Payment, recharge, and `PURCHASE` remain unimplemented and may
  be reconsidered for V3.0.2 or a future commercial enhancement.
- V3.0.1 RC1.2 Repository Hygiene Audit: `PASS WITH CLEANUP RECOMMENDED` with
  Release Blockers `0`; no tracked generated artifact, secret, local-path leak, empty
  file, byte-duplicate file, dead source module, or DELETE/MOVE candidate was found.
  Top-level `credits/`, `managed_access/`, and `admin_operations/` placement and all
  frozen dependency boundaries remain valid. Seven unused import bindings are a
  non-blocking P1 cleanup recommendation; canonical helper duplication, large source
  and test files, and continued `PROJECT_CONTEXT.md` growth remain P2 maintenance.
  No cleanup, README, Release Notes, business-code, test, package, tag, or push action
  was performed by the audit.
- V3.0.1 Phase 1 provides immutable `CreditAccount` and `CreditTransaction` domain
  objects, the minimal `CreditLedger` protocol, and a thread-safe
  `InMemoryCreditLedger`.
- The Phase 1 ledger is append-only and authoritative; integer Credit balances are
  derived from transaction records rather than a second authoritative balance store.
- `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT` are implemented with typed domain
  failures, failed-operation atomicity, `(account_id, request_id)` charge/refund
  idempotency, and same-account debit serialization under an `RLock`.
- Phase 1 remains fully offline and Provider-independent. It adds no Credential, LLM,
  Provider, UI, SQLite, network, pricing, or managed-access dependency.
- Phase 1 completion baseline: Credits `50 passed`; full suite `179 passed` with the documented
  current-host `python -m pytest -p no:debugging` workaround.
- V3.0.1 RC1.3 Product Documentation: completed. README records V3.0.1
  product capabilities and boundaries, and the release notes are recorded at
  `docs/release/Release_Notes_V3_0_1.md`.
- V3.0.1 RC1.4 Full-System Release QA: completed (`PASS`) with Release Blockers `0`,
  Product Critical `0`, Product Medium `0`, and a clean-environment baseline of
  `414 passed` under CPython 3.10.20. No release fix or directed retest is required.
- V3.0.1 RC1.5 Claude Final Release Review: completed
  (`APPROVE WITH NON-BLOCKING NOTES`) with Release Blockers `0`.
- V3.0.1 Final Release Gate: `PASS`; version `3.0.1` is released.
- Next: V3.1.0 Phase 3.0 Documentation Freeze, based on the completed Claude
  Semantic Embedding Selection Review.
- V3.0 roadmap:
  - Phase 0 — Engineering Baseline: completed
  - Phase 1 — Domain Core & Stable Symbol Identity: completed
  - Phase 2 — Processor Symbol Migration: completed
  - Phase 3.1 — Project Discovery / Project Scanner: completed
  - Phase 3.2 — Project Relationship Awareness / Project Graph: completed
  - Phase 3.2.1 — Graph Identity & Containment Hardening: completed
  - Phase 3.3 — Project Snapshot / State: completed
  - Phase 3.3.1 — Snapshot Post-QA Hardening: completed
  - V3 Core Architecture Review: frozen by the Phase 4 architecture decisions
  - Phase 4 — Project Analysis Engine: completed
  - Phase 4.0.1 — Analysis Engine Post-QA Hardening: completed
  - Phase 4 Documentation Gate: completed
  - Phase 4.1 — Provider / BYOK Foundation: completed
  - Phase 4.1.1 — Legacy Provider Atomicity Hardening: completed
  - Phase 4.1 Documentation Gate: completed
  - V3.0 RC1.1 — Release Engineering Gate: completed (`PASS WITH ISSUES`)
  - V3.0 RC1.2 — Repository Hygiene Gate: completed (`PASS WITH CLEANUP RECOMMENDED`)
  - V3.0 RC1.3 — Product Documentation & README V3: completed
  - V3.0 RC1.4 — Full-System Release QA: completed (`PASS`)
  - V3.0 RC1.5 — Claude Final Release Review: completed (`APPROVE WITH NON-BLOCKING NOTES`)
  - V3.0.0 — released
  - V3.0.1 Phase 0.0 — Development Baseline: completed
  - V3.0.1 Phase 0.1 — Architecture Decision Documentation: completed
  - V3.0.1 Phase 0 — Architecture & Scope Documentation Gate: completed
  - V3.0.1 Phase 1 — Credits Domain: completed
  - V3.0.1 Phase 1.1 — Credits Domain Post-QA Hardening: completed
  - V3.0.1 Phase 1 Documentation Gate: closed (`PASS`)
  - V3.0.1 Phase 2 — Managed Access Foundation + SQLite + flat pricing: completed
  - V3.0.1 Phase 2.1 — Managed Access Post-QA Regression Hardening: completed
  - V3.0.1 Phase 2 Documentation Gate: closed (`PASS`)
  - V3.0.1 Phase 3 — Usage Metering + token PricingPolicy: completed
  - V3.0.1 Phase 3.1 — Pricing Determinism & Migration Hardening: completed
  - V3.0.1 Phase 3 Documentation Gate: closed (`PASS`)
  - V3.0.1 Phase 4 — Admin Operations Surface: completed; Final QA `PASS FOR PHASE 4`
  - V3.0.1 Phase 4.1 — Admin Identity & Persistence Hardening: completed
  - V3.0.1 Phase 4 Documentation Gate: closed (`PASS`)
  - V3.0.1 RC1.1 — Release Engineering Gate: completed (`PASS`)
  - V3.0.1 RC1.2 — Repository Hygiene Audit: completed
    (`PASS WITH CLEANUP RECOMMENDED`)
  - V3.0.1 RC1.3 — Product Documentation: completed
  - V3.0.1 RC1.4 — Full-System Release QA: completed (`PASS`)
  - V3.0.1 RC1.5 — Claude Final Release Review: completed
    (`APPROVE WITH NON-BLOCKING NOTES`)
  - V3.0.1 Final Release Gate: completed (`PASS`)
  - V3.0.1 — Managed AI Access & Credits: released / stable
  - V3.0.2 — Commercial infrastructure enhancement track: deferred / optional
  - V3.1 — Project Intelligence / RAG: planned
  - V3.2 — Controlled Multi-Agent Collaboration: planned
  - V3.3 — Data-driven Multi-Model Router: planned
  - V3.4 — VS Code Integration: planned
- Released product version: `3.0.1`
- V3.0.0 Final Release Gate: `PASS`
- V3.0.1 Release Blockers: `0`
- V3.0.1 Product Critical / Product Medium: `0 / 0`
- V3.0.0 released test baseline: `129 passed`
- V3.0.1 final test baseline: `414 passed`
- Current V3.0.1 Admin Operations tests: `71 passed`
- Current V3.0.1 Managed Access tests: `44 passed`
- Current V3.0.1 Phase 3 Usage/Pricing, token-flow, and hardening tests: `75 passed`
- Current V3.0.1 SQLite ledger tests: `29 passed`
- Current V3.0.1 Credits tests: `66 passed`
- Current V3.0.1 BYOK Provider tests: `19 passed`
- Current offline LLM-contract smoke: `6 passed`
- Phase 3.1 QA: `PASS` (Critical 0, Medium 0, Low observations 8; 12 independent probes passed)
- Phase 3.2: `Completed`
- Phase 3.2.1 hardening: `Completed`
- Phase 3.2 QA: `Final PASS` (initial `PASS WITH ISSUES`; D1/D2 verified in retest)
- Graph identity contract: `Preserved by Phase 3.3.1`
- Phase 3.3: `Completed`
- Phase 3.3 QA: `PASS WITH ISSUES` (Critical 0; M1/M2 resolved in Phase 3.3.1)
- Phase 3.3.1 Snapshot Post-QA Hardening: `Completed`
- Phase 3.3 DeepSeek directed retest: `PASS` (M1 PASS; M2 PASS; Golden Hash PASS)
- Phase 3.3 Final QA: `PASS` (further retest not required)
- Phase 4: `Completed`
- Phase 4 Independent QA: `PASS WITH ISSUES` (Critical 0; M1/M2 resolved in Phase 4.0.1)
- Phase 4.0.1 M1 finding validation/isolation: `Resolved`
- Phase 4.0.1 M2 recursion-depth-dependent SCC: `Resolved`
- Phase 4 DeepSeek directed retest: `PASS` (M1 PASS; M2 PASS; caller-stack independence PASS; fan-out regression PASS; determinism PASS)
- Phase 4 Final QA: `PASS` (further retest not required)
- Phase 4 tests: `32 passed`
- Offline LLM-contract smoke: `6 passed`
- Phase 4.1: `Completed`
- Phase 4.1 BYOK foundation: immutable credential-free `ModelConfig`, redacted
  runtime-only `RuntimeCredential`, read-only `ProviderRegistry`, and task-scoped
  provider/client construction over the existing Provider set
- Phase 4.1 task isolation: processor, analysis, batch, progress, preflight, retry,
  and direct LLM-service paths can use one explicitly captured provider/client without
  rereading mutable legacy active state during the task
- Phase 4.1 legacy compatibility: existing `switch_provider()`, `set_api_key()`,
  active getters, and Gradio UI remain available as a bridge that configures future
  task contexts
- Phase 4.1 security: credentials are excluded from `ModelConfig`, ordinary
  serialization, workspace persistence, provider/client representations, and sanitized
  provider error messages
- Phase 4.1 Independent QA: `PASS WITH ISSUES` (M1 directed for Phase 4.1.1)
- Phase 4.1.1: `Completed`
- Phase 4.1.1 M1 legacy Provider atomicity: `Resolved`
- Legacy Provider update contract: success atomically commits the complete active state;
  failure leaves every active scalar, client, and task-scoped provider unchanged
- Phase 4.1 tests: `19 passed`
- Phase 4.1 DeepSeek Directed Retest: `PASS`
- Phase 4.1 Final QA: `PASS` (Critical 0, Medium 0; further retest not required)
- Phase 4.1 Documentation Gate: `CLOSED`
- BYOK foundation: `Completed`; workspace persistence and `code_maintenance/` remain
  Credential/Provider-free at their respective persistence and domain boundaries
- Release metadata source: `code_maintenance.__version__ = "3.0.1"`
- Python support: minimum and recommended `3.10`; CI validates Python 3.10
- RC1.1 clean install: `PASS` in a repository-external Python 3.13.7 virtual
  environment; install, import, startup, dependency, and 129-test gates passed
- RC1.1 host note: the existing Anaconda Python 3.13.5 installation segfaults while
  importing both `gradio` and `rlcompleter`; this is isolated from the clean
  environment and is non-blocking for the release
- RC1.1 security and portability checks: `PASS`; no tracked credential, workspace,
  cache, junk file, or production/user-document local absolute path was found
- RC1.2 repository hygiene: `PASS WITH CLEANUP RECOMMENDED`; Release Blockers `0`,
  no tracked delete candidate, and no directory restructuring approved for RC1
- V3.0.0 Feature Freeze: completed
- RC1.3 product documentation: completed; README V3 now records current product
  positioning, available capabilities, BYOK boundaries, V3.0.1 planned credits,
  installation and configuration, the permanent Version History policy, Python 3.10+
  support, and the 129-test RC baseline
- RC1.3 repository hygiene: completed; the RC1.2-approved narrow coverage and local
  workspace ignore rules were added without broad JSON or archive patterns
- RC1.4 full-system release QA: completed; verdict `PASS`, Release Blockers `0`,
  Medium `0`, Low `6` (all non-blocking)
- RC1.4 test baseline: `129 passed` in both the development environment and the
  repository-external clean virtual environment
- RC1.4 clean venv: `PASS`; install and `pip check` passed with no network failure and
  no repository dependency failure
- RC1.4 gates: clean install, README command validation, no-credential startup, BYOK
  user flow, legacy feature integration, V3 Core integration, provider isolation and
  security, version consistency and history, roadmap accuracy, repository hygiene,
  directory consistency, CI, and startup smoke all `PASS`
- RC1.5 Claude Final Release Review: completed; verdict
  `APPROVE WITH NON-BLOCKING NOTES`, Release Blockers `0`
- RC1.4 QA artifact: the RC1.5 review found the RC1.4 QA report missing from the
  repository; the report was recorded as `docs/qa/QA_Report_RC1_4_Full_System_Release.md`
  to close the Release QA Documentation Gate without changing product code, tests,
  README, or version metadata
- Final Release Gate: `PASS`; V3.0.0 is released with version `3.0.0`
- Current-host validation: Anaconda Python 3.13.5 retains the known interpreter /
  pytest debugging-plugin issue; `python -m pytest -p no:debugging` passes all 129 tests
- Standard-environment evidence: RC1.4 records `python -m pytest` with `129 passed`
  under standard CPython / clean venv; the host-specific issue is not a release blocker
- Current version: V3.0.1 — Managed AI Access & Credits (`RELEASED`; stable)

### V3.1.0 Phase 6.2B.0 — Reference Lifecycle Engineering Specification Freeze

- Recovery & Architecture Audit identified the main remaining Phase 6.2 obstacle as Addendum D evidence/approval engineering. Production Retrieval: **NO RESTRUCTURE REQUIRED**. The read-only architecture review selected **方案 B / Recommended Bounded Hardening**; neither a lasting Minimal Patch nor a large `experiments/` refactor is the implementation direction.
- Phase 6.2B.0: **COMPLETED / ENGINEERING SPECIFICATION FROZEN (v1)**. Repository Source of Truth: [Reference Lifecycle Engineering Specification](docs/experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md), version `v1`, raw-byte SHA-256 `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`. Its freeze commit is the Git commit containing this entry and the linked specification; the final commit ID is recorded in Git history rather than embedded into itself.
- The specification freezes separate `ReferenceRecord`, `EvidenceAuditRecord`, and `ReferenceApprovalRecord` contracts; a single authoritative formal-eligibility validator; deauthorization of legacy gate booleans; a future current-gate navigation index and minimal closure artifact; exact identity/raw-byte checksum rules; and append-only audit/erratum/approval publication. It does not alter Protocol/Addenda, the 72 Queries, 72 drafted GT records, or 134 evidence items, and creates no actual audit, approval or closure artifact.
- Phase 6.2B.1: **ALLOWED BUT NOT STARTED**. Formal Java Evidence Audit: **0/12 COMPLETED**. Reference Approval: **NOT CREATED / NOT APPROVED**. Phase 6.2 Gate: **OPEN**. Phase 6.3: **BLOCKED / NOT STARTED**. Formal RQ1–RQ4: **NOT STARTED**. V3.2: **NOT STARTED**.
- Current host baseline: ordinary `python -m pytest` still segfaults in the Anaconda Python 3.13 debugging plugin before test execution; `python -m pytest -p no:debugging` is the verified offline regression command for this host. This is a host issue, not a repository regression.

### V3.1.0 Phase 6.2B.1 — Reference Eligibility Hardening

- Phase 6.2B.1: **COMPLETED** after Documentation Gate closure. Implementation commit: `df5a85bb0af9dcf0809f78fc1c0484d6d040cbf5`; its former QA-pending status is historical. The frozen Engineering Specification v1 SHA-256 remains `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`.
- Separate immutable Reference, executed Evidence Audit, Erratum/Resolution, typed prerequisite, Reference Approval, Phase 6.2 Closure and Dry Run receipt contracts are implemented in `experiments/`; no real approval, closure, audit execution, receipt or formal benchmark result is published.
- `validate_formal_eligibility` is the single authoritative Dry Run/Formal entry. It reloads committed repository evidence and raw checksums; legacy `FormalGateEvidence` booleans remain readable but cannot authorize execution. Formal/Dry Run runner input must be validator-issued and is revalidated at entry. Synthetic infrastructure and degraded-behavior tests remain available.
- `docs/experiments/current_gate.json` is a navigation index only. Formal Java Evidence Audit: **0/12 COMPLETED**; Reference Approval: **NOT CREATED / NOT APPROVED**; Phase 6.2 Gate: **OPEN**; Phase 6.3: **BLOCKED / NOT STARTED**; Formal RQ1–RQ4: **NOT ELIGIBLE / NOT STARTED**; V3.2: **NOT STARTED**.
- The historical Formal success expectation based on `allow_formal=True` and two legacy booleans was retired under the explicit STOP resolution. Separate tests now protect fail-closed authorization and synthetic degraded result provenance/metrics. Original Independent QA: **PASS WITH LOW NOTES**, Critical / Medium / Low **0 / 0 / 2**, 80/80 independent probes and historical full regression 755 passed. Phase 6.2B.1 Documentation Gate: **CLOSED**; [QA closure report](docs/qa/QA_Report_V3_1_0_Phase_6_2B_1.md).

### V3.1.0 Phase 6.2B.1.1 — Current Gate Lifecycle Hardening

- Original Phase 6.2B.1 Independent QA on `df5a85bb0af9dcf0809f78fc1c0484d6d040cbf5`: **PASS WITH LOW NOTES**, Critical 0, Medium 0, Low 2, 80/80 independent probes; the two Low notes (independent-session proof strength and credential-scanner coverage) remain open and outside this hardening.
- A separate **Medium Documentation-Gate blocker** was found during closure: `CurrentGateIndex` v1 accepted only `6.2B.1` and lacked `ALLOWED BUT NOT STARTED`, preventing the next legal navigation state. Phase 6.2B.1.1 extends the strict v1 phase/status compatibility matrix to the frozen `6.2B.0`–`6.2B.6` lifecycle. The original v1 record remains readable; `current_gate` denotes the overall Phase 6.2 gate, while `phase_status` denotes the selected subphase. The index remains navigation only and does not grant approval, Dry Run or Formal authority.
- Hardening commit `16ad2ac3392289362c0003ef94737348bbe877f8` was **FIX IMPLEMENTED / PENDING DIRECTED RETEST** at the time. Subsequent independent Directed Retest: **PASS WITH EXISTING LOW NOTES**, 29/29 independent probes, new Critical / Medium / Low **0 / 0 / 0**, existing Low **2**, targeted 205 passed, full 775 passed, prepared verifier PASS. M-CurrentGate: **CLOSED / RESOLVED**. Both original Low notes remain unresolved and deferred.
- Phase 6.2B.1 Documentation Gate: **CLOSED**. Phase 6.2B.2: **ALLOWED BUT NOT STARTED**; next legal action is its one-query Evidence Capture Proof. Formal Java audit **0/12**, Reference Approval, Phase 6.2 Closure and Dry Run Receipt **NOT CREATED**. Phase 6.2 **OPEN**; Phase 6.3 **BLOCKED / NOT STARTED**; Formal RQ1–RQ4 and V3.2 **NOT STARTED**. The Engineering Specification v1 SHA-256 remains `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`.
- Forward-only closure validation: candidate commit `85d864ba21c676c144612e5f4c418cc64420cfa9` retained after its first post-commit regression exposed one stale repository-current `6.2B.1` assertion (204 passed / 1 failed). The test now checks committed `CurrentGateIndex` schema/lifecycle and navigation-only authority, retains legacy `6.2B.1` compatibility, and explicitly rejects changed worktree gate bytes. Targeted regression **205 passed**, prepared verifier **PASS**, full regression **775 passed**; the new test migration is a separate forward-only commit.

### V3.1.0 Phase 6.2B.2 — Raw Reply Boundary Clarification

- Raw Reply Boundary Ambiguity: **CLARIFIED / FROZEN** by [versioned Engineering Specification Amendment 1](docs/experiments/Reference_Lifecycle_Engineering_Specification_Amendment_1_V3_1_0.md), ID `v3.1-phase62b-raw-reply-boundary-a1`, version `v1`, raw-byte SHA-256 `5cf10c271268ac7cbcd45f718a3f519bb2783e115db51f4834ec010088d3dffa`. The original Engineering Specification v1 and Addendum D bytes remain unchanged.
- `raw_reply` is the complete platform-exportable final response. UI-visible Thinking that cannot be completely exported is recorded separately as `visible_thinking=unavailable` with an explicit visible-but-unexportable reason; it is not silently treated as absent or reconstructed. `reply_complete=true` covers the complete exportable Final Answer only and still requires raw bytes/hash, end marker, response-contract validation, and independent provenance checks.
- Existing schema expresses this boundary; no `experiments/` or test change is part of the clarification. The first user-reported `et-dq-ja-01` capture awaits validation under the frozen amendment and is **not materialized or counted** here. Phase 6.2B.2 is **ALLOWED BUT PROOF NOT YET COMPLETED**; `current_gate.json` retains its existing schema-valid `ALLOWED BUT NOT STARTED` navigation value. Formal Java Evidence Audit **0/12**; Reference Approval **NOT CREATED**; Phase 6.2 **OPEN**; Phase 6.3 **BLOCKED / NOT STARTED**; Formal RQ1–RQ4 **NOT ELIGIBLE / NOT STARTED**.
- Synthetic schema validation **PASS**; document-only full regression **775 passed** before and after clarification. [Development report](docs/development/Development_Report_V3_1_0_Phase_6_2B_2_Raw_Reply_Boundary.md) records scope and limits.

### V3.1.0 Phase 6.2 — Java Evidence 外部响应映射修复

- 根因：prepared input 冻结外部审查语义及顶层五字段，但不要求 DeepSeek 输出内部 `EvidenceReview.to_record()` 六字段；旧 eligibility loader 对 raw `evidence_reviews` 与 canonical reviews 做完全相等比较，导致 READY capture 系统性 `audit_reply_reviews_mismatch`。
- `experiments/reference.py` 以 exact 外部布局、严格类型、E 集合、prepared source/SymbolId/span/Grade 身份、verdict/overall/end marker 验证 raw JSON，确定性映射为 `EvidenceReview`；`experiments/eligibility.py` 用原始 bytes 重算并与内部记录及转录独立比较。未知布局 fail closed。原始 capture、冻结方法、prepared inputs、Dataset/Query/GT、Grade、检索及 Formal 授权链未变。
- 现有 capture manifest 的 **10/10 CAPTURE_READY** 原始回复通过 SHA-256、外部解析、身份交叉核对及内部 review 构造的只读 dry validation；这不是正式 EvidenceAudit materialization。另外两条 capture 仍为 BLOCKED。
- prepared verifier **PASS**；新增 19 个离线外部响应测试，相关生命周期文件 **71 passed**，全量回归 **794 passed**（此前 775）。[窄 Development Report](docs/development/Development_Report_V3_1_0_Phase_6_2_Java_Evidence_Response_Mapping.md) 记录字段映射与方法边界。
- Formal Java Evidence Audit **0/12**；Reference Approval、Phase 6.2 Closure、Dry Run Receipt **NOT CREATED**；Phase 6.2 **OPEN**；Phase 6.3 **BLOCKED / NOT STARTED**。下一动作：对现有 10 条 READY capture 重新执行 batch materialization；本轮不增加独立 QA。

### V3.1.0 Phase 6.2 — Java Evidence Batch Materialization RETRY

- 以 `a6cc001aad5f5c9588d46fa756b669bf06e6f075` 为初始 HEAD，现有 10 条 CAPTURE_READY 的 raw bytes/hash、prepared input、身份、strict external parser 和 deterministic normalization 重新验证均 PASS；未重新调用 DeepSeek，保留首份合格 capture 原 verdict（10 条均 `SUPPORTS`）。
- 正式 `EvidenceAuditRecord` append-only materialize **10/10**；真实 capture attempt 编号 1/2/3，失败历史单独按 hash/原因存档，不创建失败 completed audit；raw、external parsed、internal normalized、transcription、provenance 与 visible Final 分开留存，Thinking export unavailable 明示。由 72 条 drafted GT 派生候选 Reference content identity `d3d5f54f8256b2dadd151f26cd0f1f7674c1c62fa464846fb13bc5c295dc8f04`，不构成批准。
- prepared verifier **PASS**；10/10 磁盘重载及提交态 authority reload **PASS**；相关专项 **172 passed**、全量回归 **795 passed**（初始基线 794）。
- Formal Java Evidence Audit **10/12**；`et-bl-ja-01`、`et-fl-ja-02` 仍 **BLOCKED / NO FORMAL AUDIT**。Query 72、GT 72/72 drafted、Evidence 134，冻结原件和 prepared inputs 未改。Reference Approval、Phase 6.2 Closure **NOT CREATED**；Phase 6.2 **OPEN**；Phase 6.3 **BLOCKED / NOT STARTED**。详见 [Java Evidence 执行报告](docs/development/Development_Report_V3_1_0_Phase_6_2_Java_Evidence_Response_Mapping.md)。

### V3.1.0 Phase 6.2 — Final Two Java Evidence Audits Closure

- 合同裁决：**MINIMAL CLARIFICATION IMPLEMENTED**。Addendum D §§5–6 已将格式错误归入保守 `CANNOT_ASSESS`；工程 v1 缺少与模型 verdict 分离的执行失败表示。[Engineering Amendment 2](docs/experiments/Reference_Lifecycle_Engineering_Specification_Amendment_2_V3_1_0.md) ID `v3.1-phase62b-response-contract-failure-a2`、v1、raw-byte SHA-256 `611a6226337f11cba6d1d59dc8f89497d168eb5dcff02efb2f8ffb8375e051a5` 澄清了 v2 记录，不修改 Addendum D 或既有 v1 artifacts。
- `et-bl-ja-01` 第 4 次真实采集：完整 Final SHA-256 `c7cbc3d12b8b4f85aeb862570972605d3afa3d2081dcff137f9e2155d7c2cd56`，EvidenceAudit identity `76334e61be0bb3a08bafe8c7025d3ce61e67648b1cb150ccdfa7ea822e143323`；`et-fl-ja-02` 第 4 次真实采集：`e48cbf81c06e418e24ded5f344cb8937e7afce08fc5ece1daa47e466b1730e01`，identity `d8c74c81807533afe9169b2f5649f4ef557fdafed6804e2904a3e2feec23cd84`。两条 raw bytes 原样 append-only 保存；旧采集历史只按仓库外 manifest 记录，未补造旧正式 attempt。
- Java Evidence **12/12 EXECUTED**；合法结构化审查 **10/12**，模型 `SUPPORTS=10`、`QUESTIONS=0`；执行级 `CANNOT_ASSESS=2`，原因均 `response_contract_failure`，模型 verdict 均 unavailable，无伪造 `EvidenceReview`。这两条尚需 Addendum D §6 的独立源码核查，Reference Approval 不会将其误判为 SUPPORTS。
- Query **72**、GT **72/72 drafted**、Evidence **134**；冻结 Query/GT/Grade/rationale/span/prepared input 未变。Reference Approval、Phase 6.2 Closure **NOT CREATED**；Phase 6.2 **OPEN**，Phase 6.3 **BLOCKED / NOT STARTED**。下一步仅为 **Phase 6.2 Final Closure**，一并处理中文覆盖、方法论审查、独立 Data QA、Reference Approval 和 Closure。

### V3.1.0 Phase 6.2 — Final Approval Sequencing Fix + Closure

- Phase 6.2：**CLOSED**；Reference Approval / Approval Decision / Phase62 Closure / Documentation Decision 已按正式 schema 物化、重载并通过完整 authority 链验证。Phase 6.3 English Dev Dry Run：**ALLOWED BUT NOT STARTED**。Formal RQ1–RQ4：**NOT STARTED**，formal execution gate 仍为 false，DryRunReceipt 未创建。此前 OPEN/PENDING 条目均为历史阶段状态。
- 根因 **LIFECYCLE STAGING / VALIDATOR ORDERING BUG** 已修复：`validate_reference_approval_readiness` 在 OPEN 阶段校验独立 `ReferenceApprovalRequest`，成功返回 None，不签发执行能力；现有 `validate_formal_eligibility` 仍只在 Approval、Decision、Closure、Documentation Decision、closed Gate 及运行配置/代码/环境成立后签发 Dry Run 能力，FORMAL 仍另需 receipt。全部 evidence 检查共用同一实现，未放松 committed authority。
- 完整 Grok **4.7** 2026-09-28 外部审查原文已找回并归档，**PASS WITH NON-BLOCKING NOTES**，Critical / validity-blocking Medium / non-blocking Medium / Low = **0/0/0/4**，Reference recommendation **ELIGIBLE TO PROCEED**。12 条中文逐项原文机械归档，natural/alignment 全 PASS、translation risk 全 LOW；中文 artifact 绑定 methodology identity。既有独立 Data QA 完整 Final Answer 原字节归档，**PASS WITH NON-BLOCKING NOTES / ELIGIBLE**；其后续身份绑定明确记录为本轮物化，不伪称 reviewer 已签署未来 hash。
- 两条 Java execution-level `CANNOT_ASSESS` 的既有源码 Resolution 明确绑定；仍 empty reviews / unavailable model verdict / response_contract_failure，没有转成 SUPPORTS。GT 仍 **72/72 drafted**、`reviewed_at=null`，未完成 delayed blind review。四项 Low 的限制与处置全部保留，不阻断审批。Query **72**、Evidence **134**、Grade2/Grade1 **72/62**；Java **12 executed / 10 structured SUPPORTS / 2 execution CANNOT_ASSESS**。
- 真实 OPEN candidate readiness **PASS**；post-closure `validate_formal_eligibility(purpose=DRY_RUN)` **PASS**，实际 CPython 3.12.14 / torch 2.8.0 / transformers 4.56.2 离线环境；FORMAL 请求按预期拒绝。仅验证资格，未调用 BenchmarkRunner/Retriever/E5 或执行 Query。为保留提交态证据规则，提交前验证在仓库外临时 Git 副本完成；主仓库只做一次原子提交。
- 验证：初始基线 **798 passed**；prepared verifier **PASS**；专项含离线 LLM smoke **243 passed**；全量候选回归 **813 passed**。新增 15 项安全/生命周期测试；没有 skip/xfail/删测试/放宽断言。详见 [Final Closure report](docs/development/Development_Report_V3_1_0_Phase_6_2_Final_Closure.md)，全部正式 identities 与源文 provenance 均在 `docs/experiments/audits/phase62_final/`。
- 冻结 Protocol/Addenda/Specification、Query/GT/Grade/rationale/span、准备输入与 raw replies 不变；未重做 Java Audit、外部审查或独立 Data QA；`docs/thesis/` 未触碰。下一动作仅 **Phase 6.3 English Dev Dry Run**，本轮不执行，Formal RQ 与 V3.2 未开始。

### V3.1.0 Phase 6.3 Prerequisite — Frozen Benchmark Execution Wiring

- 已确认先前 `0/12` English Dev、`0/17` matrix execution 的工程缺口：`BenchmarkRunner` 仅接受注入的策略，尚无冻结 Dataset/Query/Reference 到生产检索组件的适配入口。新增 `experiments/execution.py`，从 manifest 校验的冻结源码重建 Snapshot/Corpus 与 File/Symbol/Chunk 候选，按既有 17 项 matrix 绑定调用生产 BM25、E5 adapter、Graph Expansion、Weighted/RRF 和 ContextBuilder，再交回原 Runner/metrics。File/Chunk 原有 BM25 基线改为复用生产计分核心；生产模块仍不导入 `experiments`。
- 冻结 17 项均能解析为可执行配置；合成样例已完成 File/Symbol/Chunk、Graph ON/OFF 与方向 pair、Weighted/RRF、稳定排序及 Runner→metrics 最小集成验证。上一轮相关定向测试 **362 passed**；本轮接线、embedding、runner/experiment 定向测试 **177 passed**，全量回归 **825 passed**。冻结 E5 同 commit `d128750597153bb5987e10b1c3493a34e5a4502a` 以 `EXACT_REVISION_DOWNLOAD` 恢复至仓库外 `/private/tmp/v31-e5-recovered-cache/`；snapshot **23 files / 0 dangling symlink**。既有 CPython 3.12.14、torch 2.8.0、transformers 4.56.2 环境在补足进程库路径后离线加载真实 `LocalE5EmbeddingProvider`，CPU float32 query/passage 均为 finite 的 768 维 L2 单位向量；合成查询经真实 E5、生产 `RetrievalIndex`、`ProductionBenchmarkStrategy`、`BenchmarkRunner` 和既有 metrics，`success`、`Recall@5=1.0`。离线 stub 测试只证明调用接线，不作为上述真实语义 smoke 的替代证据。
- 本前置工程未执行正式 English Dev Dry Run、English Test 或 Formal RQ；正式 matrix execution 仍 `0/17`，English Dev `0/12`，English Test `0`，`DryRunReceipt` **NOT CREATED**。Phase 6.2 继续 `CLOSED`；Phase 6.3 仍 **ALLOWED BUT NOT STARTED**；Formal RQ1–RQ4 仍 **NOT STARTED**。本轮前置接线验证已通过；下一动作才是另行执行 English Dev Dry Run。详见 [接线报告](docs/development/Development_Report_V3_1_0_Phase_6_3_Benchmark_Execution_Wiring.md)。

## Planned Version Roadmap

### V3.0.0 — Released

V3.0.0 is the released stable Project-level Maintenance Core Foundation. It contains
the completed V3 core and BYOK foundation.

### V3.0.1 — Managed AI Access & Credits

Status: **RELEASED / STABLE**. Core Feature Freeze is completed and the Final Release
Gate passed.
Phase 1 — Credits Domain, Phase 2 — Managed Access Foundation + SQLite + flat
pricing, Phase 3 — Usage Metering + PricingPolicy, Phase
3.1 hardening, Phase 4 — Admin Operations Surface, and Phase 4.1 Admin Identity &
Persistence Hardening are completed. The Phase 2
Documentation Gate is closed with Final QA `PASS`; Phase 3 Initial QA returned
`PASS WITH ISSUES`, Phase 3.1 resolved M1, the directed retest returned `PASS`, and the Phase
3 Documentation Gate is closed with Final QA `PASS FOR PHASE 3`. Phase 4 Initial QA
returned `PASS WITH ISSUES`; Phase 4.1 resolved M-1, the directed retest returned
`PASS`, and the Phase 4 Documentation Gate is closed with Final QA
`PASS FOR PHASE 4`. RC1.5 approved the release with non-blocking notes and Release
Blockers `0`.

V3.0.1 preserves BYOK while optionally allowing users without their own API
configuration to use platform-managed AI access. Released capabilities are:

- BYOK mode remains available;
- optional platform-managed AI access;
- `CreditAccount` and `CreditLedger` concepts;
- administrative credit grants;
- usage metering;
- a `PricingPolicy` abstraction.

Phase 1 supports `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT`. `PURCHASE` and
payment-provider integration remain outside Phase 1 and are interface reservations
rather than mandatory V3.0.1 integrations.

The platform Provider credential must never be delivered to a client or written into
a plugin, frontend, ordinary configuration file, or client package. Managed mode must
use this server-side boundary:

`Client -> Platform Backend -> Authentication / Credit Check -> Server-side Provider Credential -> LLM Provider`

### Later Planned Versions

- V3.0.2 — Commercial infrastructure enhancement track: **DEFERRED / OPTIONAL**
- V3.1.0 — Project Intelligence / RAG: **DEVELOPMENT STARTED**; Phase 0 Architecture
  and Research Methodology frozen; Phase 1 Documentation Gate closed; Phase 1
  completed and frozen; Phase 2 Lexical Baseline / BM25 completed with Final QA
  `PASS WITH LOW NOTES` and Documentation Gate `CLOSED`; Phase 3 is allowed but
  not started
- V3.2 — Controlled Multi-Agent Collaboration: **PLANNED**
- V3.3 — Data-driven Multi-Model Router: **PLANNED**
- V3.4 — VS Code Integration: **PLANNED**

## Current Architecture

Current domain: `Project`, `SourceFile`, `Symbol`, `SymbolId`, `AnalysisFinding`.

`PythonAdapter` and `JavaAdapter` reuse the existing parsers. `SymbolId` is:

`language + relative_path + qualified_name + kind + semantic_disambiguator`

For Java overloads, `semantic_disambiguator` uses the normalized parameter signature. `fallback_line` is collision fallback only. `content_hash` is not part of normal identity.

Processor concurrency results, errors, annotated-source backfill, Markdown document
association, and navigation anchors use `SymbolId` as their internal identity key.

`ProjectScanner` builds a read-only `ScanResult` containing the project, directories,
files, detected languages, applied ignore rules, metadata, per-file hashes, and a
deterministic aggregate project hash. It does not perform code analysis.

`ProjectGraphBuilder` builds a deterministic in-memory `ProjectGraph` from a
`ScanResult`. Graph nodes are `PROJECT`, `FILE`, `SYMBOL`, and `EXTERNAL_MODULE`;
relations are limited to `CONTAINS` and `IMPORTS`. Project, file, and symbol identities
reuse `Project.id`, `ProjectFile.relative_path`, and `SymbolId`. Python imports are
discovered with the standard AST, while Java package and import discovery remains
best-effort compatibility without a parser framework. Exact, unique local module/type
matches resolve to file nodes; all other import targets remain deterministic unresolved
external-module nodes.

Class containment is attributed with the existing symbol source ranges and the parent
class `SymbolId`, rather than treating a bare qualified class name as unique. Python
relative imports use their importer package context to produce canonical graph
identities before local resolution; imports without a reliable package context use a
deterministic unresolved-relative identity instead of a guessed module.

`SnapshotBuilder` builds an immutable in-memory `ProjectSnapshot` from a `ScanResult`
and the existing `ProjectGraph`. Snapshot file state uses normalized relative paths and
file content hashes; symbol state reuses `SymbolId` and `Symbol.content_hash`. Snapshot
content identity is a SHA-256 hash of an explicit canonical representation containing
the project identity, sorted file and symbol states, and sorted graph nodes and edges.
It excludes `created_at`, file mtimes, random values, object representations, and Python
hash values. `SnapshotDiff` compares snapshots from the same project root and reports
added, removed, changed, and unchanged files and symbols. Snapshot serialization is
limited to an in-memory `to_dict()` representation; no persistence layer exists.

`AnalysisEngine` is a deterministic service, not an Agent, over an existing
`ProjectSnapshot`. Each `AnalysisTool` is deterministic and read-only and consumes
only existing Snapshot/Graph state without reparsing source. The engine runs a small
ordered collection of tools, isolates each tool failure,
validates every returned `AnalysisFinding`, and canonically orders each tool's complete
output inside that tool's isolation boundary before final aggregation. A failed or
malformed tool produces a project-level `analysis.tool_failure` finding while the
remaining tools continue. Finding validation covers the string fields, integer line,
and optional `SymbolId` fields required by canonical ordering. Failure messages contain
only the stable tool id and exception type. The engine and tools do not scan, read
files, parse source, call adapters, use the network, or call an LLM.

Phase 4 provides `ComplexityTool`, `StructureTool`, and `DependencyTool`.
`ComplexityTool` reports direct method concentration per class from graph containment;
`StructureTool` reports per-file symbol density from snapshot symbol state; and
`DependencyTool` reports internal import cycles and high import fan-out from existing
`IMPORTS` edges. Dependency cycle detection uses deterministic iterative strongly
connected-component traversals and does not depend on Python's recursion limit. The
stable rule ids are `complexity.class_method_count`,
`structure.symbol_density`, `dependency.cycle`, `dependency.concentration`, and the
engine-owned `analysis.tool_failure`. Quality findings use `warning`; tool execution
failures use `error`.

`AnalysisFinding` scope conventions are: project-level findings use
`relative_path=""`, `line=0`, and `symbol_id=None`; file-level findings use the actual
relative path, an actual line or `0`, and `symbol_id=None`; symbol-level findings use
`Symbol.relative_path`, `Symbol.start_line`, and `Symbol.id`. Phase 4 keeps the existing
schema unchanged. Rule ids are deterministic, stable, lowercase machine-readable
dotted names.

`graph.py` owns the canonical graph node and edge ordering used by both
`ProjectGraphBuilder` and `SnapshotBuilder` through `canonicalize_graph()`; it is the
single source of truth for ProjectGraph canonical ordering. A graph built directly from
a scan is equal to the graph stored in its snapshot. Python parse boundaries skip
file-level symbol and import extraction on `SyntaxError` or `ValueError`, while
retaining the scanned file state and continuing to process other files.

`SourceFile.content_hash` hashes the entire file content. `Symbol.content_hash` hashes the
source slice returned for that symbol; neither hash is part of `SymbolId`.

## Known Debt and Boundaries

- The legacy Python parser does not extract nested functions or local classes inside functions.
- Java signature normalization is deterministic best-effort canonicalization for the
  parameter declarations currently needed by V3.0, not a complete Java compiler
  signature parser. The legacy regex parser guarantees only basic overload and
  parameter-declaration handling.
- V3.0 does not add RAG, Multi-Agent, Router, API, or VS Code integration; do not rewrite the Java parser. Migrate incrementally and keep Gradio working.
- Processor retains separate synchronous and progress-reporting pipelines; changes to
  processing stages must keep both paths behaviorally aligned.
- The legacy Java annotator is line-oriented: when several declarations share one
  physical line, their identities and documentation remain distinct, but generated
  Javadocs are inserted above the shared line rather than directly before each declaration.
- Project Scanner applies built-in rules, root `.gitignore`, and caller rules with a
  deterministic Gitignore-like subset. Nested ignore files and full Git ignore
  semantics are not implemented; symlinks are deliberately not followed.
- The Project Graph does not infer calls, references, inheritance, or wildcard/static
  import ownership. Python local resolution uses project-root module paths only; Java
  resolution requires an exact unique package/type match. Unmatched targets are
  unresolved rather than claimed to be third-party dependencies.
- Self-imports currently produce explicit self-loop `IMPORTS` edges. Star imports remain
  coarse targets such as `a.*`, and external-module nodes do not model package members.
- Python `src` layouts, `pyproject` packaging semantics, namespace-package semantics,
  installed packages, and complete import resolution remain deferred.
- Root `__init__.py` relative imports retain a narrow precision gap because the project
  root does not provide a reliable package name.
- `Project.id` depends on the resolved absolute project root path. The first Phase 3.3
  Snapshot version defaults to time-series comparison under the same project root.
- Phase 3.3 QA M3 remains deferred: case-sensitive absolute-path spelling can affect
  `Project.id`; resolving it would change the frozen project identity contract.
- Snapshot construction reads supported source files again to capture symbol content;
  Phase 3.3 QA M4 remains a known limitation because concurrent filesystem changes
  during a scan/build sequence are not made atomic.
- Phase 3.3 QA L1 remains deferred: validation of an explicitly supplied `graph=` checks
  its project node identity but does not exhaustively validate every node and edge.
- Phase 3.3 QA L2/L3 retain the current content semantics: a class symbol's content hash
  includes its method bodies, so a method-body edit can mark both method and class as
  changed.
- Low maintenance note: `graph.py` and `snapshot.py` retain duplicate
  `_symbol_id_record` and `_node_record` implementations. This remains deferred and was
  not changed by Phase 4.
- Snapshot comparison is state comparison by file and symbol identity/content hash; it
  does not provide semantic diffs, AST edit scripts, history, repositories, or storage.
- Function/method source size, cyclomatic complexity, oversized-file byte/line rules,
  and source-text style rules are deferred because `ProjectSnapshot` does not retain
  the required source ranges, file sizes, or source text. Phase 4 does not reread or
  reparse source and does not expand the frozen Snapshot contract for these metrics.
- Symbol-level Phase 4 findings that require `Symbol.start_line` are deferred for the
  same reason. The implemented class-method concentration rule is reported at file
  scope with line `0` and identifies the class in its deterministic message.
- A Phase 4 `StyleTool` is deferred because no reliable style rule can be proved from
  the current `ProjectSnapshot`, `FileState`, `SymbolState`, and `ProjectGraph` data
  without reading source text.
- Phase 4 QA Low / technical debt remains deferred: the
  `structure.symbol_density` rule id, Finding deduplication, duplicate tool-id
  enforcement, missing `tool_id` behavior, `_symbol_id_key` helper duplication, and
  `TYPE_CHECKING` import cleanup. R1 retains the hostile cross-tool `str` subclass
  final-sort edge case, and R2 retains the hostile mutable `tool_id` failure-report
  edge case. These items do not block Phase 4.1.
- Dependency semantics beyond imports, graph persistence/databases, RAG, and
  incremental graph updates remain outside the current implementation.
- Phase 4.1 provides only an in-memory runtime credential boundary. It does not provide
  Keychain, Secret Service, Vault, encryption, database persistence, or credential UI;
  secure IDE credential storage remains deferred to V3.4.
- The legacy Gradio Provider selection remains process-level state for compatibility.
  Each started task now captures an isolated provider/client, while per-session UI
  configuration state remains future work.
- Provider clients still use the existing OpenAI-compatible SDK surface. Phase 4.1 adds
  no Provider, automatic selection, fallback policy, benchmark, model scoring, or Router.
- Phase 4.1 QA Low issues remain deferred: preflight price-footer presentation (L1),
  a dedicated `TaskScopedLLMProvider` serialization guard (L2), broader `base_url`
  validation (L3), unused public Provider APIs (L4), and normalized Registry errors for
  malformed metadata instead of raw `KeyError` (L5).
- Phase 4.1 QA note N1 remains deferred: `get_models_for_provider()` reads the custom
  model name without acquiring the active-state lock.
- Phase 2 persistence and locking are single-process foundations, not distributed
  coordination. A stranded `RESERVED` request and `FINALIZATION_FAILED` request require
  reconciliation; Phase 2 intentionally provides no automatic retry or admin recovery
  workflow. The original Provider response is not persisted, so successful replay
  returns metadata only. Payment, Admin UI, and a production HTTP backend remain
  unimplemented.
- Phase 2 QA Low L2 remains deferred: a BYOK context with `account_id=""` continues to
  fail closed with the existing credit-domain exception type rather than a normalized
  Managed Access exception.
- Phase 2 QA Low L3 remains deferred: no
  `managed_requests(account_id, status)` performance index is added until managed
  request volume justifies it.
- Phase 2 QA Low L4 remains deferred with the Phase 1 integer-upper-bound observation:
  `FlatPricingPolicy` accepts any positive Python integer and has no artificial maximum.
- Phase 2 mutation-review coverage note remains deferred: the existing defensive
  `rowcount` guards for the `SUCCEEDED` update in `_finalize_success()` and the `FAILED`
  update in `_mark_provider_failed()` do not have direct mutation-targeted regressions.
  Their defensive branches are unreachable through the normal state machine and this
  is a Low coverage observation, not a product defect.

## Frozen Decisions

### V3.1.0 Development and Research Baseline

- V3.1.0 develops on `v3.1.0-dev` from synchronized stable `main`. V3.0.1 remains
  released and frozen; `v3.0.0`, `v3.0.1`, and previous development branches are not
  moved or automatically deleted.
- V3.1.0 targets Project Intelligence / RAG: project retrieval, context construction,
  and project understanding that can provide reliable project context to the future
  V3.2 Multi-Agent stage.
- V3.1.0 must support engineering implementation and thesis research: research
  questions, benchmark/dataset design, ground truth, baselines, quantitative metrics,
  ablation studies, and reproducible experiments. Architecture must answer both how
  retrieval works and how its effectiveness will be demonstrated.
- Phase 0 Architecture & Research Review must assess file-, symbol-, chunk-, and
  hybrid-level retrieval units; lexical/BM25-like, embedding, graph-aware, hybrid, and
  reranking strategies; and in-memory, standard-library/local, FAISS-like,
  Chroma-like, or other storage options. These are candidates, not frozen selections.
- Candidate metrics include Recall@K, Precision@K, MRR, Hit Rate@K, nDCG@K, context
  relevance, maintenance-task success, LLM answer correctness, and token/context cost.
  Metric applicability remains a Phase 0 decision.
- Phase 0 must decide the embedding provider boundary, local versus remote execution,
  BYOK/Managed relationship, offline testing, cache behavior, privacy, and
  determinism. No embedding implementation or dependency is part of Phase 0.0.
- V3.1 should reuse stable `SymbolId`, `ProjectScanner`, `ProjectGraph`,
  `ProjectSnapshot`, content hashes, and `SnapshotDiff`. Graph-assisted retrieval may
  use the frozen `CONTAINS` and `IMPORTS` relations, but any graph relation expansion
  requires a separate architecture review.
- `ProjectSnapshot`, content hashes, and `SnapshotDiff` are candidates for index
  identity, incremental indexing, change detection, and cache invalidation.
- `AnalysisEngine` remains a deterministic analysis service. It does not become a RAG
  engine, Agent runtime, or planner. The RAG layer remains separate, and its package
  name is not selected during Phase 0.0.
- V3.2 Multi-Agent Collaboration and V3.3 Multi-Model Router are not started. V3.1 may
  design a future consumption interface but does not implement Agent runtime, planner,
  collaboration, memory, or routing.
- V3.0.2 commercial enhancements remain deferred and optional. Admin UI, Payment,
  Recharge, and Auth/RBAC do not enter V3.1.
- Phase 0.0 adds no RAG package, embedding, vector database, retrieval dependency,
  Agent, Router, tree-sitter, ANTLR, JavaParser, source change, test change, or
  `requirements.txt` change.
- The research questions registered for Phase 0 are: retrieval-unit selection;
  comparative effectiveness of lexical, embedding, and graph-aware retrieval;
  hybrid versus single-strategy retrieval; Project Graph/Snapshot contribution;
  SnapshotDiff-based incremental indexing; and RAG-context impact on maintenance-task
  correctness and relevance. Phase 0.0 does not answer them.

### Release Documentation Policy

- Every formal release, including major, minor, and patch versions, must retain an
  accurate but concise README Version History entry. Feature releases record Version,
  Status, Major Updates, Phase Summary when needed, and Tests. Patch releases record
  Version, Status, Changes/Fixes, and Tests. README history excludes internal finding
  identifiers, probe counts, and directed-retest workflow detail.
- After every formal release, create a version-level Thesis-Oriented Development Report
  under `docs/thesis/`, named `V<major>_<minor>_<patch>_Thesis_Development_Report.md`
  (for example, `V3_1_0_Thesis_Development_Report.md`). It must
  reorganize evidence from real code, Development Reports, QA Reports, and release
  evidence into thesis-usable material rather than concatenate existing reports.
- The tracked V3.0.0 report is a Documentation Backlog item. The tracked V3.0.1 report
  is also pending; a pre-existing untracked local candidate must be handled only by a
  separate Documentation Task.

### V3.1.0 Frozen Architecture and Research Methodology

- V3.1.0 is a Project Intelligence / Retrieval-Augmented Context Layer for software
  maintenance, not a generic chatbot, document-QA demo, embedding wrapper, or Agent
  runtime.
- Core research questions are frozen as RQ1 File/Symbol/Chunk retrieval units, RQ2
  lexical versus semantic retrieval, RQ3 `CONTAINS`/`IMPORTS` graph contribution, and
  RQ4 Lexical + Embedding + Graph hybrid retrieval and signal ablation.
- The primary retrieval unit is Symbol and must reuse `code_maintenance.SymbolId`.
  File is secondary; Chunk is fallback only for oversized symbols,
  unsupported/no-symbol files, and documentation. Fixed-token chunking is not the
  default code unit.
- `ProjectSnapshot` remains a state/identity boundary and does not store source text.
  A separate Corpus Builder reads source through the project root and existing
  adapters, constructs future `RetrievalDocument` values, and must compare actual
  content hashes with snapshot-recorded hashes. Stale or missing content fails closed
  or requests a rebuild.
- BM25-style lexical retrieval is the deterministic, offline, explainable formal
  baseline and should prefer a standard-library implementation with no new retrieval
  dependency.
- Embeddings use an independent future `EmbeddingProvider` Protocol rather than
  `LLMProvider` or `TaskScopedLLMProvider`. Deterministic fake embeddings are permitted
  only for offline architecture/regression tests. Formal semantic RQ2/RQ4 experiments
  require a fixed real semantic model selected by a separate Phase 3 review, with
  version, dimension, normalization, license, feasibility, cost, and fingerprint
  recorded. Remote source-code embedding is never silently enabled.
- FAISS, Chroma, and a dedicated Vector DB are not required in V3.1. Exact similarity
  search with in-memory or lightweight local persistence is preferred. A future scale
  justification requires a new Architecture Review.
- Future `RetrievalIndexIdentity` includes project ID, snapshot content hash,
  retrieval-config hash, and optional embedding fingerprint. Any identity change
  invalidates silent reuse.
- `SnapshotDiff` maps added/add, removed/delete, changed/replace, and unchanged/reuse.
  Incremental results must equal a full rebuild. Incremental indexing is a Phase 4
  capability and secondary engineering performance experiment, not a Phase 2
  responsibility or core RQ.
- Graph-aware retrieval reads only frozen `CONTAINS` and `IMPORTS` relations. Expansion
  has hop, relation, per-seed, and global node budgets; unbounded traversal is
  prohibited. `max_hops = 1` is an implementation candidate, not a frozen numeric
  default.
- Weighted score fusion is the primary hybrid strategy for explainability and
  ablation. RRF is an optional comparison. Learned, LLM, and cross-encoder rerankers
  are deferred.
- Retrieval is separate from `ContextBuilder`, which owns deduplication, ordering,
  bounded graph context, snippets, and model-agnostic budget truncation. It does not
  own prompt templates, few-shot examples, or Agent planning.
- Future V3.2 code consumes `RetrievalService` and `ContextPackage`, not index,
  lexical, embedding, or graph internals. V3.2 and V3.3 remain not started.
- The future top-level production package is `project_intelligence/`. Allowed
  dependency direction is `project_intelligence -> code_maintenance`; the reverse is
  prohibited, and Project Intelligence does not strongly depend on Credits, Managed
  Access, or Admin Operations. Phase 0 creates no production package.
- `AnalysisEngine` remains deterministic analysis. `AnalysisFinding` may be retrieval
  metadata, but RAG does not control the engine lifecycle.
- Core tests remain offline with fake embeddings, fixture projects, fixed queries, and
  fixed ground truth. No real API, Credential, network embedding, or network LLM is
  used in regression tests.
- The primary benchmark combines this repository with manually constructed fixtures;
  an external open-source project is optional generalization evidence. Python is the
  main experiment language and Java is coverage validation.
- Benchmark queries cover symbol lookup, feature localization, dependency questions,
  bug localization, maintenance tasks, and cross-file understanding. Human annotation
  is primary ground truth; evaluated retrievers cannot generate their own truth.
- Primary metrics are Recall@K and MRR. Secondary metrics are nDCG@K, Precision@K, and
  Hit Rate@K. All strategies use the same dataset, query set, ground truth, `top_k`,
  and metric definitions.
- Core ablation is capped at Lexical only, Embedding only, Hybrid without Graph,
  Hybrid with Graph, and a Graph-focused variant. Deterministic retrieval is not
  repeated for meaningless variance statistics.
- Reproducibility records dataset/query/truth/config versions and hashes, embedding
  fingerprint, applicable seed, index identity, code commit, and output. Raw outputs,
  summaries, and paper-ready figures remain distinct; large indexes and caches are not
  committed.
- Engineering performance records full build time, incremental update time, query
  latency, index size, and context size with environment and dataset scope.
- Failure behavior is stale content -> reject/rebuild, missing source -> fail closed,
  corrupt index -> rebuild, and snapshot mismatch -> reject/rebuild. In standalone
  Phase 3 Semantic Retrieval, an embedding-provider failure becomes an explicit
  semantic retrieval error; Phase 5 Hybrid Retrieval may use a lexical-only fallback
  only when it marks degraded mode and strategy provenance. V3.1 does not create a
  complex retry framework.
- Failure ownership is layered: `EmbeddingProvider` reports provider/model failure;
  the Semantic Retriever converts it to a stable semantic retrieval error; the Phase
  5 Hybrid Retriever decides whether lexical fallback is permitted; and the future
  `RetrievalService` exposes final strategy/provenance.
- Frozen phase plan: Phase 0 Architecture & Research Design; Phase 1 Corpus & Symbol
  Content Model; Phase 2 Lexical BM25; Phase 3 Embedding Port & Semantic Retrieval;
  Phase 4 Graph-aware Retrieval + Index Identity + Incremental Indexing; Phase 5
  Hybrid Retrieval + Context Builder + RetrievalService; Phase 6 Evaluation Benchmark
  + Ablation + Reproducible Results; then RC.
- V3.1 explicitly defers Multi-Agent runtime/planner/memory/collaboration, Router/model
  routing, VS Code integration, LLM/cross-encoder reranking, autonomous patch and
  test-pass loops, required Vector DB infrastructure, Payment, Recharge, Admin UI,
  Auth/RBAC, and a production SaaS backend.
- V3.1 thesis contribution is the systematic maintenance-oriented integration and
  evaluation of stable symbol identity, project structure, hybrid retrieval, and
  context construction. It does not claim a new BM25, embedding, or graph algorithm.
- V3.1.0 Phase 0 Architecture and Research Methodology are frozen with no blocker. The
  Phase 0, Phase 1, and Phase 2 Documentation Gates are closed. Phase 1 and Phase 2
  are completed and frozen; Phase 3 is allowed but not started. Phase 2 owns BM25
  correctness, determinism, input-order independence, and corpus compatibility only;
  incremental indexing, incremental index consistency, and `SnapshotDiff` operations
  belong to Phase 4.

### Phase 3.3 Graph Identity Contract

- `PROJECT`, `FILE`, and `SYMBOL` identities continue to reuse `Project.id`, normalized
  relative paths, and `SymbolId`.
- Class containment uses existing symbol ranges to select the enclosing class and links
  through that class's `SymbolId`.
- Canonical Python import targets are used for both internal resolution and unresolved
  external-module identity.
- Phase 3.3 does not treat the current location-dependent `Project.id` as a portable
  cross-machine identity.

### BYOK / Credential & Provider Policy

- Official releases do not include a developer API key.
- Users configure their own Provider, Model, and Credential.
- API keys must not enter Git, ordinary configuration files, or logs.
- Phase 4.1 established the Provider/BYOK Foundation.
- `ModelConfig` is immutable ordinary configuration and remains credential-free.
- `RuntimeCredential` is runtime-only and excluded from ordinary serialization,
  workspace persistence, and non-redacted representations.
- `TaskScopedLLMProvider` is captured once per task; later legacy global switches do
  not alter an already-started task.
- Legacy Provider updates use atomic semantics: success commits the complete active
  state, while failure performs no active-state mutation.
- Workspace persistence remains credential-free, and `code_maintenance/` remains free
  of Provider, Credential, OpenAI SDK, and LLM dependencies.
- A future Router uses only providers already configured by the user.
- No secure credential store exists in Phase 4.1; the V3.4 IDE stage provides the
  secure credential-configuration UI.

### V3.0.1 Managed AI Access & Credits

- The access modes are `BYOK` and `MANAGED`. The frozen minimum contract for a future
  `LLMAccessContext` contains `mode: LLMAccessMode`, `model_config: ModelConfig`,
  `account_id`, and `request_id`. `account_id` and `request_id` are optional for BYOK
  and required for MANAGED. The context never owns a client, Provider,
  `TaskScopedLLMProvider`, `RuntimeCredential`, or any credential.
- The V3.0 BYOK architecture remains unchanged and independent of Credits: BYOK does
  not check or deduct Credits.
- Managed mode uses a process-local, backend-facing `ManagedAccessService`; V3.0.1 does
  not establish a production HTTP backend. The platform credential remains server-side
  and must not enter UI state, workspace data, ordinary configuration, credit records,
  logs, or `LLMAccessContext`.
- A Managed client or UI caller must never receive the platform `RuntimeCredential`,
  platform `TaskScopedLLMProvider`, raw Provider client, or platform API key. A future
  `ManagedAccessService` may return only safe results and safe usage/accounting metadata.
- `credits/` and `managed_access/` are new top-level peers of `code_maintenance/`.
  `managed_access/` may depend on `credits/` and existing Provider infrastructure.
  Reverse dependencies into `credits/`, dependencies from `code_maintenance/` to either
  new package, and Provider-infrastructure dependencies on `credits/` are prohibited.
- The credit ledger is append-only and authoritative. Phase 1 derives balance from the
  transaction sum, uses integer Credit units, and uses `Decimal` rather than `float` for
  real monetary values or costs.
- Every transaction amount is a nonzero integer: `ADMIN_GRANT > 0`, `USAGE < 0`,
  `REFUND > 0`, and `ADJUSTMENT` may be positive or negative but not zero.
- Phase 1 transaction types are `ADMIN_GRANT`, `USAGE`, `REFUND`, and `ADJUSTMENT`;
  `PURCHASE` is excluded. User identity is only an opaque `account_id: str`.
- Phase 1 implements immutable `CreditAccount` and `CreditTransaction` values, the
  minimal `CreditLedger` protocol, and a thread-safe `InMemoryCreditLedger`.
- Charge and refund operations are idempotent within their operation type by
  `(account_id, request_id)`; conflicting retries fail without mutating history or the
  idempotency index. Grants and safe adjustments append new audit records.
- `grant()`, `refund()`, and `adjust()` are privileged domain operations available only
  to trusted server-side or admin-side orchestration. They must not be exposed directly
  to a client, Gradio UI, Managed caller, or ordinary user-facing API; Phase 2
  `ManagedAccessService` must not expose these methods or a ledger object.
- Phase 1 `refund()` is a low-level positive accounting primitive. Its `request_id`
  identifies the refund operation rather than an original `USAGE`, and Phase 1 does
  not reconcile usage. Any Phase 2 user-facing or Managed refund must first identify
  the original `USAGE`, authorize the refund, and prevent repeated refund against the
  same authorized usage before internally calling `CreditLedger.refund()`.
- Idempotency lookup identity is `(operation_type, normalized account_id, normalized
  request_id)` for `USAGE` and `REFUND`, which have independent namespaces. A valid
  replay must preserve amount and exact note and returns the original transaction;
  changed amount or note raises `IdempotencyConflictError`. Note is a payload
  consistency field, not a lookup key, and Phase 2 retries must preserve it.
- The in-memory ledger uses an `RLock` so idempotency checks, balance prechecks, and
  appends share one critical section. All rejected operations preserve balance,
  history, and idempotency state.
- A `USAGE` charge is idempotent by `(account_id, request_id)`. The Phase 2 charging
  contract is per-account guarded charge-after-success: precheck balance, invoke the
  Provider, and charge only after success; Provider failure is not charged.
- Phase 1 uses the minimal `CreditLedger` Protocol and in-memory implementation and defines no
  `PricingPolicy`, flat pricing, token pricing, or cost conversion. It remains completely
  offline and must not import or call LLM or Provider infrastructure. Phase 2 adds
  standard-library SQLite and flat pricing. Phase 3 adds Provider/model/token-based
  `PricingPolicy` and freezes `Decimal` cost-to-integer-Credits conversion with
  `ROUND_CEILING`.
  No ORM, distributed database, distributed transaction, or hard-coded commercial
  exchange ratio is authorized.
- Phase 2 SQLite must atomically commit the ledger transaction append and idempotency
  record in one SQLite transaction. Partial commit in either direction is prohibited,
  and Phase 2 QA must verify all-or-nothing behavior with failure injection.
- Phase 2 entry requirements are implemented: Managed clients cannot access `grant`,
  `refund`, or `adjust`; no user-facing refund is exposed; SQLite transaction append
  and idempotency-record write are atomic; and retries preserve the complete
  idempotency payload contract. Failure injection covers rollback on both sides of the
  transaction/idempotency boundary.
- Phase 4 adds the trusted server-side `AdminCreditService` as the only administrative
  Credits entrypoint in this phase. It exposes `grant`, `adjust`, `balance`, and
  immutable Credit `history`, but no public refund and no ledger object. Admin identity
  is `(normalized actor_id, normalized operation_id)` and the complete business payload
  is conflict-checked on replay.
- Phase 4.1 freezes the Admin identity boundary to exact built-in strings before
  normalization and persistence. It also rejects amounts outside SQLite's signed
  64-bit INTEGER range before opening an Admin write and formally verifies that the
  service connection enforces the Admin audit foreign key.
- The Phase 4 `admin_credit_operations` audit row and corresponding Credit transaction
  commit atomically in one SQLite transaction. `BEGIN IMMEDIATE` serializes independent
  service connections so same-operation concurrency mutates exactly once and different
  operations retain balance safety. The admin schema migrates and reopens idempotently
  without changing existing ledger, Managed request, or usage data.
- The frozen V3.0.1 sequence is Phase 0 Architecture & Scope; Phase 1 Credits Domain and
  domain grant; Phase 2 Managed Access Foundation, SQLite, and flat pricing; Phase 3
  Usage Metering and token pricing; Phase 4 Admin Operations Surface; optional Phase 5
  Payment Interface Reservation; then RC. Phases 1 through 4.1 and the Phase 4
  Documentation Gate are completed. Optional Phase 5 is skipped for V3.0.1; RC1.1
  through RC1.5 and the Final Release Gate are completed, and V3.0.1 is released.
- The timeout case where a Provider succeeded but the caller observed a timeout remains
  an explicit known limitation; V3.0.1 does not build distributed transaction machinery.
- Phase 3 extends Flat Pricing into Usage Metering and `PricingPolicy` while preserving
  the Phase 2 reservation state machine, SQLite all-or-nothing atomicity,
  Managed request idempotency and payload identity, the server-side Credential
  boundary, and BYOK isolation from Credits and Managed Access.
- V3.0.1 is an engineering-completeness enhancement. After the
  `ADMIN_GRANT -> Managed AI -> USAGE -> Ledger` loop is complete, thesis priority moves
  to V3.1 RAG and V3.2 Multi-Agent rather than commercial expansion.

### V3.0.1 Report Naming Policy

- Starting with V3.0.1, new Development and QA report filenames must include the
  version, for example `Development_Report_V3_0_1_Phase_1.md` and
  `QA_Report_V3_0_1_Phase_1.md`.
- Do not create unversioned V3.0.1 report names such as
  `Development_Report_Phase_1.md` or `QA_Report_Phase_1.md`; this avoids collisions
  with V3.0 historical phases.

## Collaboration

- GPT-5.6 Sol: overall workflow control, cross-phase audit, and consistency across
  prompts, gates, thesis claims, and engineering evidence.
- Codex: repository implementation, testing, Git operations, and documentation
  materialization.
- DeepSeek R1: independent QA, directed retest, and adversarial verification; it
  does not overturn frozen architecture or methodology.
- Claude (highest available Opus model with high reasoning): preferred Primary
  Research Architecture & Methodology Reviewer for architecture research review,
  RQs and experiment protocols, dataset and ground-truth methodology, and
  methodological review of research results.
- Grok 4.7: normally the Independent Research Cross-Reviewer / Alternative
  Methodology Reviewer, covering independent review of Claude/GPT research design,
  dataset bias and leakage, threats to validity, negative results, and claim
  discipline.
- Grok 4.7 temporarily assumes Claude's Primary Research/Methodology Reviewer role
  only when the user explicitly states that Claude is currently unavailable. Grok
  never replaces Claude automatically. Once Claude is available again, the Primary
  role returns to Claude and Grok returns to independent cross-review.
- Formal prompts and execution reports should primarily use Simplified Chinese;
  precise English technical terms may be retained.
- An important external-model decision that determines code, formal experiment, or
  release behavior must be recorded in a Git-tracked specification or decision
  document before any later phase relies on it; chat history alone is not a
  repository Source of Truth.
- The user makes final decisions and acceptance.

After each phase, update only facts that changed in **Current State**, **Test Baseline**, or **Known Debt**.
