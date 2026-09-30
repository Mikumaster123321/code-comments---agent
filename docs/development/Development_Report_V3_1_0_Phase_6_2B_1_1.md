# V3.1.0 Phase 6.2B.1.1 Current Gate Lifecycle Hardening

## 后续 Directed Retest closure

下方 **FIX IMPLEMENTED / PENDING DIRECTED RETEST** 是 hardening 提交时的历史状态。对提交 `16ad2ac3392289362c0003ef94737348bbe877f8` 的后续独立 Directed Retest 已报告 **PASS WITH EXISTING LOW NOTES**：29/29 仓库外独立 probes PASS，新 Critical / Medium / Low **0 / 0 / 0**，原两项 Low 仍未解决；专项回归 205 passed，全量 775 passed，prepared verifier PASS。M-CurrentGate 现为 **CLOSED / RESOLVED**，允许重试 Phase 6.2B.1 Documentation Gate Closure。探针属于先前独立复测，本次文档收口未重跑。最终收口判断见 [Phase 6.2B.1 QA 报告](../qa/QA_Report_V3_1_0_Phase_6_2B_1.md)。

## Gate 与根因

- 起点：`v3.1.0-dev`，`df5a85bb0af9dcf0809f78fc1c0484d6d040cbf5`；tracked diff/staging 为空，用户的 `?? docs/thesis/` 受保护且未读取内部内容。
- 原 Phase 6.2B.1 Independent QA：`PASS WITH LOW NOTES`，Critical 0、Medium 0、Low 2、80/80 independent probes，适用于上述 commit。Low-1 independent-session proof strength 与 Low-2 credential-scanner coverage 均不在本轮处理范围。
- 本轮发现的 M-CurrentGate：**Medium / Documentation-Gate blocker**。Phase 6.2B.1 首次实现 `CurrentGateIndex` 时，把当时实施的 `6.2B.1` 收窄成唯一合法 `current_phase`，状态集合也缺少 `ALLOWED BUT NOT STARTED`。因此 Independent QA PASS 后无法通过 schema 合法表达 `6.2B.2`，阻断 Documentation Gate 的下一次导航更新。它不改变 Addendum D、Reference lifecycle 架构或 Formal authority。
- 结论：**FIX IMPLEMENTED / PENDING DIRECTED RETEST**。本轮仅修复状态表达能力；原 Documentation Gate STOP 的 schema 原因已解除，但 Documentation Gate 仍 **BLOCKED PENDING DIRECTED RETEST**，Phase 6.2B.2 仍 **NOT ALLOWED YET**。

## 合同与版本决策

`CurrentGateIndex` 集中采用不可变 phase → allowed statuses 矩阵。冻结工程规格 v1 的阶段为 `6.2B.0` 至 `6.2B.6`：前者可表示 `COMPLETED`；`6.2B.1` 支持历史 `IMPLEMENTATION IN PROGRESS`、`IMPLEMENTED / QA PENDING`、`CLOSED`，以及生命周期里的 `ALLOWED BUT NOT STARTED`、`QA PASS / DOCUMENTATION GATE PENDING`、`COMPLETED`；`6.2B.2` 至 `6.2B.6` 支持 `ALLOWED BUT NOT STARTED`、`IN PROGRESS`、`BLOCKED`、`COMPLETED`。未知 phase、status、非法组合、大小写和空格变体均被拒绝。

**Schema version 不升级，仍为 `v1`。** 此变更只扩大同一字段中可表达的冻结生命周期状态，没有改变字段、既有值的含义、`from_record`/`to_record` 形状或旧记录字节；旧 `6.2B.1 / IMPLEMENTED / QA PENDING` 与 `CLOSED` 仍可读取。`CurrentGateIndex` 没有权威语义身份；本轮未更改任何旧 artifact 的 canonical identity，也无需 migration。`current_gate=OPEN` 指整体 Phase 6.2 gate 尚未关闭；`phase_status=ALLOWED BUT NOT STARTED` 仅表示当前子阶段可开始，两者可同时成立。

合成导航记录 `6.2B.2 / ALLOWED BUT NOT STARTED / OPEN / approval=null / dry_run=false / formal=false` 现可构造、序列化、从已提交文件加载并通过 `validate_current_gate`。`next_allowed_action` 可以是 `Phase 6.2B.2 Evidence Capture Proof`。但这不创建 EvidenceAudit、Reference、Approval、Phase62Closure、DryRunReceipt 或 `ValidatedExecutionInputs`。缺少底层 authority 时，`validate_formal_eligibility` 仍拒绝 Formal；伪造 gate 的 eligibility、`COMPLETED`、`CLOSED` 和 approval identity 也不能授权。Formal validator 核心、Reference/Audit/Approval identity、Runner、artifact writer 均未修改。

仓库真实 `docs/experiments/current_gate.json` 保持原样，不在本轮推进到 `6.2B.2`。正式 Java audit 0/12；Reference Approval、Phase62Closure、DryRunReceipt 均不存在；72 GT 仍为 Draft。Phase 6.2 OPEN，Phase 6.3 BLOCKED / NOT STARTED，Formal RQ1–RQ4 NOT STARTED，V3.2 NOT STARTED。冻结 Engineering Specification v1 原始文件 SHA-256：`6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`。

## 验证与仓库范围

- 修改前基线：`python -m pytest -p no:debugging`，**755 passed**。本机普通 `python -m pytest` 在 Anaconda Python 3.13 的 pytest debugging plugin 初始化时段错误，故沿用仓库已记录的禁用该插件命令。
- 本轮新增 **20** 项测试：完整冻结 phase/status 矩阵、未知 phase/status 与大小写/空格拒绝、严格 bool/未知字段、旧记录读取、新状态的序列化和仓库加载、navigation-valid / authority-denied，以及伪造 gate 拒绝。`tests/test_experiment_reference_lifecycle.py`：**52 passed**；四个指定专项文件合计：**205 passed**；全量：**775 passed**。现有 `PYTHONHASHSEED=1/7/31` 语义身份回归仍在全量测试中通过；CurrentGateIndex 本身不定义权威 identity，本轮未新增 identity 算法。
- `python -B docs/experiments/evidence_audit/prepared/verify_prepared.py`：**PASS**，12 个精确预登记 Java 输入、23 项 evidence、冻结源字节与 12 个空白记录。未创建真实 formal artifact。
- 修改：`experiments/eligibility.py`、`tests/test_experiment_reference_lifecycle.py`、`PROJECT_CONTEXT.md`。新建：本报告。未修改 production Retrieval、其余 experiments 实现、Protocol/Addenda A–D、Dataset Specification、Engineering Specification v1、Dataset/Query/GT、prepared packages、requirements、`current_gate.json`；用户的 `docs/thesis/` 未读取内部内容、未修改、未暂存。

## Directed Retest 预注册

下一轮由 DeepSeek V4.1 Flash 独立复测以下范围；本轮实施侧测试不得称为 Independent Directed Retest：

1. `6.2B.1 / QA PASS / DOCUMENTATION GATE PENDING` 合法。
2. `6.2B.2 / ALLOWED BUT NOT STARTED` 合法。
3. 后者 `approval=null` 时导航合法。
4. 后者 `dry_run=false`。
5. 后者 `formal=false`。
6. Unknown phase 拒绝。
7. Unknown status 拒绝。
8. 非法 phase/status 组合拒绝。
9. 伪造 current gate eligibility 仍无法授权。
10. 旧 `6.2B.1` record 可读取。
11. 序列化 round-trip 稳定。
12. 如相关，检查 `PYTHONHASHSEED=1/7/31` 确定性。
13. Full regression。
14. Prepared verifier。
15. Repository safety：冻结文档、Query/GT/evidence/prepared、生产代码、requirements 和用户 `docs/thesis/` 未动。

仅当下一轮针对本 hardening 得到 Critical 0、Medium 0，M-CurrentGate 才可标记 `CLOSED / RESOLVED`，之后才可重试 Phase 6.2B.1 Documentation Gate Closure。本轮不得自行宣告独立 QA PASS 或关闭 Documentation Gate。
