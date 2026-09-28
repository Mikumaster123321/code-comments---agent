# V3.1.0 Phase 6.2 Final Closure

- PHASE 6.2 FINAL VERDICT：**CLOSED**。readiness、审批/关闭链、关闭后 Dry Run 资格、专项与全量回归全部 PASS。
- ROOT CAUSE FIX：**PASS**。根因是 **LIFECYCLE STAGING / VALIDATOR ORDERING BUG**：上一轮把 post-approval/post-closure 的 `validate_formal_eligibility` 当成 pre-approval readiness。OPEN Gate 返回 `current_gate_conflict` 是正确拒绝，不能据此倒置审批顺序。
- 初始 HEAD：`61cbc0db166e1577068101ffbe92b3b58e38e152`；分支 `v3.1.0-dev`。最终原子提交为包含本报告的 Git commit，避免把提交身份写入自身。未 push、未 tag。

## 生命周期修复与权限边界

`ReferenceApprovalRequest` 只携带 dataset/query/source Draft/reference、方法与工程身份、prerequisite 和 resolution 绑定；没有 approval、decision、closure 或执行开关。新增 `validate_reference_approval_readiness(repository_root, request) -> None`，只在合法 OPEN/pre-approval 状态核验完整证据包，成功不签发 `ValidatedExecutionInputs`。

两个入口共用 `_validate_reference_package`，保留原 dataset/query/draft/reference、冻结校验和、preregistration、12 条 Java audit、来源和 session、原文 hash、Resolution、Final Data QA 绑定与审批时间检查。中文 prerequisite 另显式验证 methodology review 身份绑定；物化 preregistration JSON 的 canonical identity 与原有 D 派生身份一致。

顺序是：readiness → Reference Approval / Approval Decision → Phase62 Closure / Documentation Decision → CLOSED Gate → `validate_formal_eligibility`。后者仍是唯一执行授权入口，保留 Approval、Decision、Closure、Documentation Decision、closed Gate、配置、代码、冻结运行环境，以及 FORMAL 专用 DryRunReceipt 的全部检查。没有为未提交工作区增加授权模式。

为同时满足“所有验证先通过再做唯一主仓库 commit”和“权威加载器只读已提交字节”，在仓库外建立临时验证副本，先以 OPEN 的已提交候选证据快照实际运行 readiness，再以 CLOSED 的已提交候选快照实际运行原 post-closure validator；这些临时测试快照不进入主仓库历史，不是发布或实验。主仓库仅在全量回归通过后原子提交。Gate 使用既有 `6.2B.6 / COMPLETED` 表达总 Gate CLOSED，没有创建新子阶段。

## 真实审查归档与四项 Low

完整 Grok 4.7 原文从任务“毕业设计选题建议”中用户粘贴的 message `d009823e-2fa9-4413-892a-14d47d9b5708` 找回；审查日期 2026-09-28，输入包 commit 为初始 HEAD，包 raw SHA-256 `ac86ceeeb9f4cac880689e7f3bd373be9d7a231c46e732c063f8116c25b05d58`。全文按工具返回文本的 UTF-8 字节归档，未从摘要补造、未改写 reviewer 身份。

Grok verdict **PASS WITH NON-BLOCKING NOTES**；Critical / validity-blocking Medium / non-blocking Medium / Low = **0 / 0 / 0 / 4**；建议 **ELIGIBLE TO PROCEED**。12 条中文判定及逐条 note 从该原文表格确定性提取，仅去除表格外层与填充空白，note 内容及 Markdown 转义原样保留。12/12 的 natural_independent_query 与 semantic_alignment 都是 PASS，translation_artifact_risk 都是 LOW，汇总 PASS。没有重新语义审查。

独立 Data QA 从同一任务的用户附件导出中唯一 `# FINAL INDEPENDENT DATA QA VERDICT:` 标题至文件结尾按原字节提取，保留完整 Final Answer。原导出 hash、起始 byte offset、归档来源与限制见 provenance；没有把中途思考或摘要当最终结论。Final QA 为 **PASS WITH NON-BLOCKING NOTES / ELIGIBLE**，Critical 与两类 Medium 均 0，Low 4。原文未声明 QA reviewer 的准确模型身份，因此没有推断成 DeepSeek R1 或 Claude。其显式要求的后续审查身份绑定在本轮完成；不声称外部 reviewer 曾签署后来才生成的 hash，也没有重新跑外部 QA。`completed_at` 表示确定性归档完成时间，原方法论审查保留日期精度。

| Low | 处理与保留的事实 |
| --- | --- |
| L-GT-01 | 72/72 `annotation_status=drafted`、`reviewed_at=null`；没有 completed delayed blind review / human IAA。Reference approval 不回写 GT。 |
| L-AUDIT-01 | `et-bl-ja-01`、`et-fl-ja-02` 保留 empty reviews、unavailable model verdict、execution CANNOT_ASSESS、response_contract_failure；`reply_complete=true` 仅代表 Final Answer 捕获完整。 |
| L-RES-01 | Approval 与 AuditSet 显式绑定两个既有关闭的 Resolution；不回写原始执行记录。 |
| L-ZH-01 | 中文正式 artifact 绑定 methodology review identity；Final Data QA 再绑定两项及候选 Reference、Java AuditSet。 |

四项仍为 **NON-BLOCKING LOW**。原始审查文字中的历史状态保留在原文；当前身份与归档状态以正式 records 为准。

## 正式 identities

| Artifact | Canonical identity |
| --- | --- |
| `preregistration` | `ddf93e9b0be6aae76dfbabef5f2dd55b12126252c54504e5bade3aa34150fa74` |
| `java_evidence_audit_set` | `054288894760683312c9b3acd7280e4516669c320bad5bb3abafe9133c7fa494` |
| `methodology_review` | `9920c292dbd5f46fc4acbc57ed63a6c9227bb9dbf96b049fa8653dc69e7358fb` |
| `chinese_coverage_audit` | `a2c3c7f60c0f80dc323e41fda5278c1ddf5ab378d10e28234513b56cf5091a98` |
| `final_data_qa` | `e16d79a93c119a52d60437da97f5223bd8d7828f5e8cdba269f1187db7eff517` |
| `resolution_set` | `70508a9636519ff42713bf2e5dc1bfc4a035efdc1a5f11d007ad9500be0e7580` |
| `reference_approval` | `e89ce78f4c7b27754b52cab1b9217b349f5e7a382423bd75eb44a2a1deafb5d8` |
| `approval_decision` | `f2f545821527ae9a042d6a11f408f909cafc742178f566eda1acd57264a6f784` |
| `phase62_closure` | `a8c7db46188caddaa5421821a2863399c600c912b33d1b4fc5025f3b316156c4` |
| `documentation_decision` | `bca0d6ffc7eb895d8956d48d9954a6aad94f213876b2a02b5ca02596700141e1` |

Resolution identities：

- `1680c6463324907a8f39e11f8a1e5b52ff79a79c71ea628078eeed9d89b8bc37`
- `ac39e3072674ef7740eb53a194c8b2cc00bca3edf73ce8529ed25344faa26b1d`

所有新 lifecycle records 均经正式 schema 构造、canonical serialize、写入、磁盘重载及 identity 重算，并有独立 raw SHA-256 sidecar。已提交验证副本中的 `RepositoryAuthority` 又完整验证同一原文与身份链。Approval 与 Closure 的 repository provenance 指向已审查初始提交；本轮实验代码身份在执行入口独立验证，未使用自引用提交 hash。

## 数据完整性与实验边界

Query 72（English test/dev/Chinese = 48/12/12）；GT **72/72 drafted**；Evidence **134**；Grade 2/1 = **72/62**。Java **12/12 executed**、**10/12 structured-valid**、模型 SUPPORTS **10**、执行 CANNOT_ASSESS **2**。两条源码决议仍为 `SUPPORTED_BY_FROZEN_SOURCE`、`source_verification/closed`、`gt_or_grade_changed=false`。这不代表 12 个模型 SUPPORTS，也不能外推为全部 English/Python/Chinese GT 的独立标注。

Dataset hash `164994a826fe51936d5fcb012a8d102967c33110787405fd3b0f7972efe8ade7`；Query hash `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`；Draft GT hash `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87`；Reference hash `d3d5f54f8256b2dadd151f26cd0f1f7674c1c62fa464846fb13bc5c295dc8f04`。Query/GT/Grade/rationale/span、prepared inputs、raw replies、Protocol/Addenda、Dataset Specification 全部未改。

Phase 6.2：**CLOSED**。Phase 6.3 English Dev Dry Run：**ALLOWED BUT NOT STARTED**。Formal RQ1–RQ4：**NOT STARTED**；formal execution eligibility 为 false，未生成 DryRunReceipt 或研究结果。V3.2 未开始。

## 验证

- 初始全量基线：`python -m pytest -p no:debugging`，**798 passed**。
- prepared verifier：**PASS**，12 个准确输入、23 项证据、完整冻结源码、12 个历史空白模板。
- 真实 candidate `validate_reference_approval_readiness`：**PASS**，返回 None；没有执行能力。
- Approval / Decision / Closure / Documentation Decision schema、磁盘重载与完整已提交 authority 链：**PASS**。
- 真实 post-closure `validate_formal_eligibility(purpose=DRY_RUN)`：**PASS**；FORMAL 请求按预期因 Gate 未开放而拒绝。资格校验不是执行；BenchmarkRunner/Retriever/E5 调用 0、Query 执行 0。
- 运行环境为实际恢复的 CPython **3.12.14**、torch **2.8.0**、transformers **4.56.2**，CPU/float32；仅从本机已有缓存离线恢复，未下载模型或调用 API。环境变量及 socket audit hook 禁止验证进程联网；运行证据见 `docs/experiments/audits/phase62_final/closure_validation.json`。未做性能或真实模型推理结论。
- 专项：lifecycle/eligibility/reference/dataset/benchmark + offline LLM smoke，**243 passed**（其中 LLM smoke 6）。
- 新增 **15** 项离线回归；证明 readiness 无执行 authority、不能替代审批、缺审查/错误 identity/缺 required resolution/未关闭 resolution/错中文绑定均拒绝，原最终入口仍要求全部后续审批 artifacts。既有 draft、legacy booleans、Gate-only、缺 receipt、错误 runtime/code 等拒绝测试保留。
- 全量候选回归：`python -m pytest -p no:debugging`，**813 passed**。不 skip、不 xfail、不删测试、不放宽断言。既有两项“尚无批准/当前 OPEN”的仓库状态断言迁移为检查真实 CLOSED lineage、批准绑定与仍未开放 FORMAL，原有 OPEN/legacy 拒绝测试保留。

## 文件范围与后续

修改 `experiments/reference.py`、`experiments/eligibility.py`、`experiments/__init__.py`、`tests/test_experiment_reference_lifecycle.py`、`PROJECT_CONTEXT.md`、`docs/experiments/current_gate.json` 及本报告。新增正式归档位于 `docs/experiments/audits/phase62_final/` 与 `docs/experiments/reference_approval/`；原有 resolutions 与 execution records 不变。生产 processor/UI/providers/Retrieval 不变，用户原有 `docs/thesis/` 未读取、列举其内容、修改、暂存或提交。

唯一主仓库提交消息：`close(v3.1): complete phase 6.2 reference gate`。下一允许动作是另行执行 Phase 6.3 English Dev Dry Run，并在入口重新核验提交态代码、配置和运行环境；本任务不执行该动作。
