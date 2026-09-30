# V3.1.0 Phase 6.2B.1 开发报告

## Documentation Gate Closure（后续记录）

以下记录 implementation commit `df5a85bb0af9dcf0809f78fc1c0484d6d040cbf5` 之后的状态迁移；下方原实施证据及当时 QA PENDING 的判断保留其历史语义。

- 原 Independent QA：**PASS WITH LOW NOTES**，Critical / Medium / Low **0 / 0 / 2**，80/80 独立 probes PASS，历史全量回归 755 passed。Low-1 为独立 session 证明强度，Low-2 为凭据扫描覆盖范围；两项均未解决，分别移交 6.2B.2 Evidence Capture Proof 与真实 capture/publication hygiene。
- 首次 Documentation Closure 因 `CurrentGateIndex` 无法表示 `6.2B.2 / ALLOWED BUT NOT STARTED` 而 STOP；这是另一个 Medium 文档门禁 blocker，不改变原 QA verdict。6.2B.1.1 hardening commit `16ad2ac3392289362c0003ef94737348bbe877f8` 修复了状态矩阵，其[实施报告](Development_Report_V3_1_0_Phase_6_2B_1_1.md)保持独立。
- 后续独立 Directed Retest：**PASS WITH EXISTING LOW NOTES**；新 Critical / Medium / Low **0 / 0 / 0**，既有 Low 2；29/29 独立 probes PASS，专项 205 passed，全量 775 passed，prepared verifier PASS。M-CurrentGate **CLOSED / RESOLVED**。两轮仓库外 probes 均为先前 QA 的报告结果，本次文档收口未重跑。
- 第二次 Documentation Closure 在更新未提交的 `current_gate.json` 后运行 Git-backed 测试，触发预期的 `artifact_worktree_mismatch`，按当时 STOP 规则撤销改动。上层随后明确裁决事务顺序：先建立候选文档提交，再在候选 HEAD 上验证；不修改 loader、测试或 fail-closed 保护。
- 候选文档提交 `85d864ba21c676c144612e5f4c418cc64420cfa9` 的 post-commit 专项回归暴露另一个历史测试断言：它要求仓库当前阶段永远是 `6.2B.1`（204 passed / 1 failed），而合法导航现为 `6.2B.2`。上层批准 forward-only 迁移该断言，保留候选提交和 `artifact_worktree_mismatch` 保护。迁移后专项 **205 passed**、prepared verifier **PASS**、全量 **775 passed**；无实现或研究规格修改。
- [正式 QA 收口报告](../qa/QA_Report_V3_1_0_Phase_6_2B_1.md)分别记录两轮 QA、两个 Low、失败候选与后继迁移的验证。整条 forward-only 提交链经 prepared verifier、targeted/full regression 与仓库安全检查 PASS 后，Documentation Gate **CLOSED**、Phase 6.2B.1 **COMPLETED**、Phase 6.2B.2 **ALLOWED BUT NOT STARTED**。
- 整体 Phase 6.2 仍 **OPEN**：正式 Java audit **0/12**，Reference Approval、Phase 6.2 Closure、Dry Run Receipt 均 **NOT CREATED**；Phase 6.3 **BLOCKED / NOT STARTED**，Formal RQ1–RQ4 与 V3.2 **NOT STARTED**。`current_gate.json` 只是导航，Dry Run/Formal eligibility 均为 false。

## 状态与边界

- 实施结论：**IMPLEMENTED / INDEPENDENT QA PENDING**。本报告不是独立 QA 结论、Reference Approval、Phase 6.2 Closure 或正式实验结果。
- 起点：`v3.1.0-dev`，HEAD `8f931f73bf4b0630dff5e679104fbc025132cafa`；tracked diff 与 staging 均为空，用户已有 `?? docs/thesis/` 保持原样，未读取或暂存其内容。
- 工程规格：`Reference_Lifecycle_Engineering_Specification_V3_1_0.md` v1，原始文件 SHA-256 `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`。Protocol、Addenda A–D、Dataset Specification、72 Query、72 Draft GT、134 evidence 和 12 个 prepared package 均未修改。
- 阶段状态：正式 Java audit **0/12**，Reference Approval **NOT CREATED**，Phase 6.2 **OPEN**，Phase 6.3 **BLOCKED / NOT STARTED**，Formal RQ1–RQ4 **NOT ELIGIBLE / NOT STARTED**，V3.2 **NOT STARTED**。

## 实施内容

1. `experiments/reference.py` 新增独立的不可变 Reference、EvidenceAudit 执行记录与集合、Erratum、Resolution、typed prerequisite、Approval、Phase62Closure、DocumentationDecision 和 DryRunReceipt 合同。Reference 从现有 Draft 确定性派生，保留 query/evidence 身份，不写入历史审阅字段。语义身份由显式 `identity_record()` 计算；`approved_at`、路径及时间出处不进入批准语义身份，完整文件仍由 raw SHA-256 保护。
2. Evidence Audit 将 prepared 输入与实际执行分开，记录原始发送/回复字节、可见 thinking/final、独立会话及上下文证据、UI 模型名称、用户提供别名、不可得元数据、时间来源、逐证据 verdict 与 grade observation。逐项 verdict 决定 overall；grade observation 不修改 Reference。Erratum/Resolution 只能追加，不覆盖原始回复。
3. `experiments/eligibility.py` 以 Git HEAD 中的确切已提交字节为权威，验证 sidecar checksum、冻结数据、方法与工程身份、Reference 派生关系、预登记的 12 个 Java ID、12 个接受执行记录及会话独立性、Chinese coverage、methodology review、final QA、决议、独立 Phase 6.2 closure、Dry Run receipt、purpose/population、配置族、运行时和代码 commit。任一条件缺失时不颁发 `ValidatedExecutionInputs`。
4. Runner 对 Dry Run/Formal 只接受 validator 签发的输入，并在检索开始前重新验证；`allow_formal` 和历史两个 gate boolean 无授权效力。Synthetic 路径继续用于基础设施及 degraded 行为测试。新增 Reference/批准身份的 metadata 字段只承担 provenance，旧配置及 metadata 的原有序列化身份保持不变。
5. 现有 artifact writer 扩展 append-only 原子目录发布、raw blob SHA-256 与 secret scan。`current_gate.json` 仅作导航；它不能自行证明批准。CI checkout 使用完整历史，并预检冻结 self-repository commit `12391233daa2149ead4f451e920b2e0d8a1a6beb`，缺失即失败。

## 历史测试冲突裁决与迁移

旧测试 `test_runner_phase61_formal_execution_gate_and_degraded_formal_guard` 同时承担“旧布尔 gate 可让 FORMAL 成功”和 degraded 结果合同验证。根据用户明确的 STOP Resolution，前一成功预期已经退休；保留它会违反冻结规格。

- `test_legacy_boolean_formal_bypass_is_rejected_before_retrieval`：`allow_formal=True`、两个旧布尔值为真、匹配的 runtime metadata 与 synthetic strategy 均不能启动 Formal retrieval；无 validated authority 不产生结果。
- `test_synthetic_degraded_result_keeps_provenance_and_metrics`：在 SYNTHETIC 路径保留 degraded 状态、失败来源、结果状态及 recall metric 的回归保护。
- Legacy Formal Test Conflict：**RESOLVED**。Historical formal-success expectation：**RETIRED**。Legacy boolean deserialization compatibility：**PRESERVED**。Legacy boolean authorization power：**REMOVED FROM NEW AUTHORITATIVE FORMAL PATH**。Degraded behavior coverage：**PRESERVED UNDER SYNTHETIC / NON-FORMAL PATH**。

## 离线验证与独立 QA 入口

基线：`python -m pytest -p no:debugging` 为 **722 passed**。当前主机普通 `python -m pytest` 在 Anaconda Python 3.13 debugging plugin 初始化时崩溃，故使用禁用该插件的等价离线命令；测试不调用真实 LLM/provider，也不使用真实密钥。

新增测试以独立临时 Git 仓库构造完整 synthetic authority DAG，不在正式 `docs/experiments/` 发布任何完成的 audit/approval/closure/receipt。定向攻击覆盖：Draft GT/旧 gate boolean 绕过、缺失/待批/伪造 approval、无 closure 或 receipt、gate 篡改、未提交/变更文件、路径逃逸、原始字节差异、prepared 与 executed 混淆、11/12 不完整集合、共享会话、verdict/alias/retry 错误、数据/方法/决议/QA/运行时/代码/配置不匹配，以及不受哈希种子和顺序影响的语义身份。独立 QA 应审查这些 fixture 的断言强度，并对真实 authority 继续保持 fail closed。

独立 QA 预注册攻击面（A–X）：

| 类别 | 重点 |
| --- | --- |
| A–D | Draft truth 绕过；旧 boolean 绕过；调用者伪造 approval；approval identity 篡改 |
| E–H | Reference identity 篡改；dataset/query/source Draft 不一致；prerequisite 缺失；12 audit 不完整 |
| I–L | prepared 冒充 executed；共享会话；原始输入/回复 hash 篡改；overall 与逐证据 verdict 矛盾 |
| M–P | Erratum 覆盖原始回复；grade observation 污染 truth；current gate 伪造资格；RunMetadata 伪造权威 |
| Q–T | closure 缺失；Dry Run receipt 缺失；身份依赖循环；凭据与隐私泄漏 |
| U–X | 绝对路径/主机依赖；哈希种子与输入顺序；覆盖/半成品发布；旧数据和配置兼容回归 |

验证命令：`python -m pytest -p no:debugging`，**755 passed**（基线 722；新增专项 32；历史测试职责拆分使原文件净增 1）；`python -B docs/experiments/evidence_audit/prepared/verify_prepared.py`，**PASS**（12 个 prepared 输入、23 项 evidence、冻结源字节）；`git diff --cached --check`，**PASS**。全量回归包含 Phase 6.2 94、Phase 6.1 53、Phase 5 48、Phase 4 37、Phase 3.2 10、Phase 3.1 12、Phase 2 14、Phase 1 41 和离线 LLM smoke 6 项，全部通过。100 次确定性输入顺序扰动与 `PYTHONHASHSEED=1/7/31` 测试也通过。Commit SHA 以本阶段交付摘要为准。本报告不提前宣称独立 QA PASS。后续需独立 QA 与 directed retest，之后才可考虑 6.2B.2。任何真实 audit、批准、闭环、Dry Run 或 Formal RQ 都仍须按冻结规格另行取得权威证据。
