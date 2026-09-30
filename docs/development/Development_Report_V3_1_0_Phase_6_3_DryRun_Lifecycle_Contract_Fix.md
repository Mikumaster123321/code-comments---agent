# V3.1.0 Phase 6.3 DryRun Lifecycle + Receipt Contract Fix 执行报告

## 判定与边界

本轮只修合同、校验实现和离线合成测试。正式 English Dev Dry Run `0/12`，正式矩阵执行 `0/17`，English Test `0`，Chinese `0`；正式 `DryRunReceipt` **NOT CREATED**，Formal RQ1–RQ4 **NOT STARTED**。Phase 6.2 维持 **CLOSED**；Phase 6.3 维持 **ALLOWED BUT NOT STARTED**。

初始分支 `v3.1.0-dev`，初始 HEAD `59aed8c68dffe7d1dfc788d9bc71401062622373`。原有未跟踪 `docs/thesis/` 未读取内容、未修改、未暂存。

## 两个根因

1. `RepositoryAuthority` 从 HEAD 加载并要求工作树字节一致；未提交的 receipt 不能被正式 validator 看见。此前流程把 FORMAL validator PASS 放在第一次提交 receipt 前，形成提交时序不可能条件。
2. `DryRunReceipt` v1 只有单项 `config_identity`；原 FORMAL validator 却将其与 `experiment_family_identity` 比较。单项 family 相容性不等于 17 项 Dry Run matrix 的完整覆盖。另有 `formal_execution_eligible` 导航布尔值的自依赖：receipt 已提交而 gate 尚未更新时，FORMAL validator 会先拒绝。

## 修复

- 保留 HEAD 作为正式 authority。未来先提交 17 项 Dry Run artifact set 与 v2 receipt；从新 HEAD 重载、运行 FORMAL validator；PASS 后才更新 gate/navigation 并作第二次原子提交。
- `CurrentGateIndex` 的 eligibility 布尔值只作状态展示；validator 继续要求已关闭 Phase 6.2 gate、选定 Approval 及完整 Closure 证据链，但不从 `formal_execution_eligible` 或 `dry_run_eligible` 布尔值取得授权。增加 Phase 6.3 导航状态的 schema 允许值。
- 新增 `DryRunConfigurationSet`，按冻结矩阵 C1–C17 的 `matrix_run_id` 规范排序，绑定每项 family 与 Dry Run config identity；缺项、重复、未知、多项均失败。没有修改冻结配置。
- 新增 `DryRunArtifactSet`，绑定 12 个冻结 English Dev query ID、17 个 run 的 manifest/aggregate/raw 原始字节 hash、Approval/dataset/query/Reference/runtime/code identity、`dry_run`/`english_dev`、204 覆盖与零 English Test/Chinese 计数。
- 新增 `DryRunReceiptV2`，绑定 artifact set 与矩阵 identity、204 覆盖、协议及提交态确定性/泄漏证据。正式收据采用内容身份目录与 SHA-256 sidecar；v1 仍可历史反序列化，但 FORMAL 不接受它。
- FORMAL validator 从 HEAD 验证 receipt/证据身份、17 个 run 的文件 hash 与配置、12×17 唯一覆盖、每条 raw 结果的 English Dev split/query 身份、成功状态和零降级。Phase 6.2 Approval/Closure、冻结输入、runtime、执行代码及目的/population 原有门槛仍执行。DRY_RUN 与 FORMAL 的授权入口仍分离。

确定性证据记录 17 项、204 个 query 比较范围及零排名不一致；validator 核对其提交态字节、交叉身份和结论。正式执行时仍须由独立 Phase 6.3 QA 审核该比较的生成过程；本轮没有生成真实比较或结果。

合同详见 `docs/experiments/Reference_Lifecycle_Engineering_Specification_Amendment_3_V3_1_0.md`。原冻结工程规范及其 SHA-256 未改。

## 验证

- 修改前基线：`python -m pytest -p no:debugging`，**825 passed**。
- 生命周期专项：`python -m pytest -p no:debugging tests/test_experiment_reference_lifecycle.py -x -q`，**104 passed**。合成临时 Git 仓库覆盖未提交收据拒绝、已提交重载、v1 单项拒绝、精确 17/17 成功、16/17/重复/额外失败、English Test/Chinese 混入、204 覆盖缺口、确定性失败、gate 布尔值不授权、Phase 6.2 不能绕过，以及 DRY_RUN/FORMAL 分离。
- 最终全量回归：`python -m pytest -p no:debugging`，**839 passed**。
- 所有测试为离线合成或既有离线回归；未请求真实 Provider、模型推理或外部 API。

## 后续动作

本合同修复提交后，另行执行 Phase 6.3 English Dev 正式 Dry Run，并按先 artifact/receipt 提交、后 FORMAL validator、最后 gate 更新的两提交顺序推进。本报告不是 Dry Run PASS 或正式 RQ 放行记录。
