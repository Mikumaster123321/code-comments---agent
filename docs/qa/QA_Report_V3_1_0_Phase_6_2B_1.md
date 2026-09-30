# V3.1.0 Phase 6.2B.1 Independent QA 与 Documentation Gate Closure

## 结论与证据归属

本报告将已经完成的两轮独立 QA 写入 Repository Source of Truth。**Phase 6.2B.1 Documentation Gate：CLOSED；Phase 6.2B.1：COMPLETED；Phase 6.2B.2：ALLOWED BUT NOT STARTED。** 整体 Phase 6.2 Gate 仍 **OPEN**。本报告不构成 Reference Approval、Evidence Audit 执行、Phase 6.2 Closure、Dry Run 或 Formal 授权。

| QA 层 | 对象与角色 | Verdict | Findings | 仓库外独立 probes | 当时仓库验证 |
| --- | --- | --- | --- | --- | --- |
| 原 Phase 6.2B.1 Independent QA | `v3.1.0-dev`，implementation commit `df5a85bb0af9dcf0809f78fc1c0484d6d040cbf5`；Independent QA / Adversarial Auditor，READ-ONLY | **PASS WITH LOW NOTES** | Critical 0 / Medium 0 / Low 2 / Phase blocker 0 | **80/80 PASS**；default ×2、`PYTHONHASHSEED=7/31` 均 80/80 | full **755 passed**，0 skipped，0 xfailed；prepared verifier PASS |
| Phase 6.2B.1.1 CurrentGate Directed Retest | hardening commit `16ad2ac3392289362c0003ef94737348bbe877f8`；独立定向复测 | **PASS WITH EXISTING LOW NOTES** | New Critical 0 / New Medium 0 / New Low 0；Existing Low 2；M-CurrentGate **CLOSED / RESOLVED** | **29/29 PASS** | targeted **205 passed**；full **775 passed**；prepared verifier PASS |

80/80 和 29/29 属于两轮不同的独立 QA，**本次文档收口未重跑**，也不合并为一次 109-probe 运行。模型按用户提供的项目称谓记录为 **DeepSeek V4.1 Flash**；原始探针产物及其 checksum、会话 ID、精确 provider revision、token usage、finish reason 和 provider build ID 未随本轮材料提供，故 **not recorded / unavailable**，不推断。755 与 775 是不同代码提交上的历史回归；本次收口的重新运行另行记录。

冻结 Engineering Specification v1 原始字节 SHA-256 为 `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`，与 `experiments/eligibility.py` 的 `ENGINEERING_SHA256` 一致。研究方法权威仍为 Protocol、Addenda A–D 和 Dataset Specification；工程规格控制实现。`current_gate.json` 仅是导航索引，不是授权根。

## 原独立 QA 的 A–X 攻击面摘要

| 面 | 已核验的合同边界 |
| --- | --- |
| A Draft Truth Bypass | `drafted` GT 不能充当 Formal Reference。 |
| B Legacy Boolean Bypass | `allow_formal`、`phase_6_2_dataset_truth_frozen`、`phase_6_3_dry_run_passed` 仅兼容读取，不具 Formal 授权力。 |
| C Caller Fake Approval | 调用方伪造 Approval 或 lookalike 不能替代 validator-issued `ValidatedExecutionInputs`。 |
| D Approval Identity Tampering | Approval 语义身份及已提交原始字节必须匹配。 |
| E Reference Tampering | Reference 必须从冻结 Draft 确定性派生，改动使身份失配。 |
| F Cross-reference Mismatch | Dataset、Query、Draft、Reference、Audit、Approval 的交叉身份须一致。 |
| G Prepared vs Executed | prepared package 和空白记录不算 completed execution。 |
| H Independent Session | 共享 session 证据拒绝；剩余证明强度边界保留为 Low-1。 |
| I Raw Input Integrity | 实发输入须匹配 prepared 原始字节和 hash。 |
| J Raw Response Integrity | 原始回复按字节保存并校验。 |
| K Verdict Forgery | overall verdict 从逐项 verdict 推导，不能由调用方覆盖。 |
| L Grade Observation Pollution | 模型 grade observation 不改 Reference 或 Draft。 |
| M Erratum Immutability | 纠错走 append-only erratum/resolution，不覆盖 raw response。 |
| N Prerequisite Completeness | 中文核查、方法论审查、Final Data QA、决议及必要 resolution 不全则拒绝 Approval。 |
| O Audit Set Completeness | 需要准确预登记的 12 个有效 Java 执行；11/12 或错 ID 拒绝。 |
| P current_gate Forgery | gate 声明与底层 authority 不符时 fail closed。 |
| Q RunMetadata Forgery | metadata 声明不能替代 validator-issued capability。 |
| R Phase 6.2 Closure | Approval 后仍须独立真实 closure artifact。 |
| S Dry Run Receipt | Formal 前须有合格 Dry Run receipt；当前未创建。 |
| T Identity Cycle | Draft → Reference → Audit/审查 → Approval → Closure → Dry Run 的依赖不得循环。 |
| U Canonical Identity | 语义身份采用冻结 canonical projection；时间及文件出处另受保护。 |
| V Path Independence | 身份不能依赖绝对路径或主机位置；越界路径拒绝。 |
| W Serialization / Privacy | 严格 schema、raw hash 与模式驱动的凭据检查；剩余边界为 Low-2。 |
| X Atomicity / Append-only | 发布原子且不可覆盖；失败与重试可追溯。 |

原 QA 还核对了离线 LLM contracts **6 passed**、benchmark infrastructure **53 passed**、reference lifecycle **32 passed**、Phase 6.2 dataset contract **94 passed**。旧 formal-success 测试 `test_runner_phase61_formal_execution_gate_and_degraded_formal_guard` 已退役；`test_legacy_boolean_formal_bypass_is_rejected_before_retrieval` 与 `test_synthetic_degraded_result_keeps_provenance_and_metrics` 分别保护负向授权与 synthetic degraded 行为。

## Directed Retest 与保留的 Low

6.2B.1.1 修复了 `CurrentGateIndex` 不能表达 `6.2B.2 / ALLOWED BUT NOT STARTED` 的 Medium 文档门禁阻断。独立 Directed Retest 报告新 Critical / Medium / Low 均为 0，原两项 Low 仍在；旧 `6.2B.1` 记录可读，新导航状态可往返序列化，伪造 gate 不能取得 Dry Run 或 Formal authority。M-CurrentGate **CLOSED / RESOLVED** 不表示两项 Low 已解决。

- **Low-1：Independent-session proof strength，NON-BLOCKING / UNRESOLVED。** 当前可区分 raw evidence hash 及可用时的 platform session identity，但纯仓库数据无法密码学地证明 UI 会话真正独立；单字节变化即可产生新 hash。这不是当前 Formal bypass。**Deferred to Phase 6.2B.2 Evidence Capture Proof**：须留存 1 Query = 1 independent session 的 session provenance、时间隔离和平台/UI 证据或冻结合同允许的等价证明。
- **Low-2：credential/privacy scanner coverage，NON-BLOCKING / UNRESOLVED。** scanner 按声明的模式拒绝凭据；接受的 raw evidence 按原始字节存储，不静默改写。自由文本如 `api_key=...` 并非所有形式必然被捕获。此为 publication hygiene / defense-in-depth 边界，不是 authority 或 identity bypass。真实 Evidence Capture 和发布前须人工 privacy / credential review；**deferred to evidence capture/publication hygiene**。

## Documentation Gate 决策与剩余状态

本次按事务顺序先创建候选文档提交，再在其成为 HEAD 后执行 Git-backed authority 回归。候选提交本身不代表先验测试 PASS；首次回归暴露的历史测试断言由后继 forward-only 提交迁移。只有整条提交链的 prepared verifier、targeted/full regression、schema/authority 与 Git 安全检查全部通过，本报告的 Documentation Gate 结论才生效。`artifact_worktree_mismatch` 检查继续保留。

**Forward-only 验证沿革：**候选提交 `85d864ba21c676c144612e5f4c418cc64420cfa9` 的首次 post-commit prepared verifier PASS，专项回归为 204 passed / 1 failed。此前未提交 gate 字节引起的 `artifact_worktree_mismatch` 已消失；唯一失败是历史测试把 repository-current `current_phase` 硬编码为 `6.2B.1`。上层裁决保留该候选提交，并迁移测试以验证 Git 已提交字节、严格 schema、合法生命周期组合、无批准及无 Dry Run/Formal 授权；旧 `6.2B.1` 兼容记录另行构造验证，且新增对 gate 工作区字节不匹配的负向断言。迁移后四文件专项 **205 passed**，prepared verifier **PASS**，全量回归 **775 passed**。没有修改 `experiments/` 实现或放宽 `RepositoryAuthority`。此修正由后继 forward-only commit 记录，原 85d864b 的失败史不被改写。

72 Query / 72 GT / 134 evidence 保持冻结身份，72/72 GT 仍为 `drafted`。12 个 prepared Java 输入、23 项 prepared evidence 与 12 空白记录只是准备材料；正式 Java Evidence Audit **0/12 COMPLETED**。Reference Approval **NOT CREATED**；Phase 6.2 Closure artifact **NOT CREATED**；Dry Run Receipt **NOT CREATED**。Phase 6.2 **OPEN**；Phase 6.3 **BLOCKED / NOT STARTED**；Formal RQ1–RQ4 和 V3.2 **NOT STARTED**。`dry_run_eligible=false`、`formal_execution_eligible=false`。下一合法动作仅为 **Phase 6.2B.2 Evidence Capture Proof / ALLOWED BUT NOT STARTED**。
