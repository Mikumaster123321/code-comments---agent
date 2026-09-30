# V3.1.0 Phase 6.3 Dry Run Lifecycle 与 Receipt 合同修正

- 版本：`v1`
- 范围：Phase 6.3 合同与实现；本文件不记录任何正式 Dry Run 结果。
- 上游冻结文档及其原始字节身份保持不变。此修正只限定未来 Dry Run 收据与 FORMAL 资格的接线方式。

## 授权顺序

`RepositoryAuthority` 只读取与 Git HEAD 完全一致的正式 artifact。工作树中的收据不能作为授权。未来 Phase 6.3 分两个提交阶段：

1. 在已关闭的 Phase 6.2 authority 下执行 English Dev Dry Run，物化 17 个 run 的原始结果、汇总、manifest、矩阵 artifact set、确定性和泄漏检查证据，以及 `DryRunReceiptV2`；提交这套正式 artifact。这是第一次原子提交。
2. 从新 HEAD 重载，运行 `validate_formal_eligibility(purpose=FORMAL)`。PASS 后更新 `current_gate.json` 和导航状态，使 Formal RQ 标为 `ALLOWED BUT NOT STARTED`；再提交 gate 更新。这是第二次原子提交。

不得要求 FORMAL validator PASS 后才首次提交 receipt。正式资格始终来自 HEAD 中的 Approval、Decision、Phase 6.2 Closure、Receipt 及其交叉身份校验。`current_gate.formal_execution_eligible` 是导航/状态元数据，不能单独产生权限，也不能成为 FORMAL validator 的前置布尔条件。DRY_RUN 资格只依赖其自身的 Phase 6.2 合同，不要求收据。

## 矩阵与 artifact set

`DryRunConfigurationSet` v1 的 `configurations` 按冻结 `FROZEN_MATRIX_IDS` 顺序保存 17 个三元组：`(matrix_run_id, experiment_family_identity, dry_run_config_identity)`。其位置依次对应 C1–C17，使用冻结的具体 `matrix_run_id` 作机器身份，不另造配置。构造和读取时拒绝缺项、重复、未知、多项；输入顺序规范化为冻结顺序，身份是整个规范记录的 `canonical_hash`。validator 从正式请求的冻结配置机械派生 English Dev 的 17 项，并验证该身份；单项配置 hash 与 family hash 不互换。

`DryRunArtifactSet` v1 绑定 Approval、dataset、query set、Reference、配置集合、runtime、执行时的仓库 HEAD / 代码 commit，`mode=dry_run`、`split=english_dev`、12 个冻结 English Dev query ID，以及 17 个 `DryRunArtifactRef`。artifact 提交会产生新 HEAD，因此 set 中的执行 commit 不能等于包含自身的提交；validator 用 `verify_execution_code` 检查两者之间的 `experiments/` 代码未变。每个 ref 绑定正式 run 的 manifest、aggregate、raw 路径和原始字节 SHA-256。协议粒度为每配置 12 个 query 结果，覆盖量严格为 `12 × 17 = 204`。set 中的 English Test 和 Chinese 计数必须为零。validator 从 HEAD 重读三个文件，逐项核对 hash、配置身份、运行 ID、split、query 身份、状态及覆盖唯一性。run 文件固定在 `docs/experiments/runs/<run_id>/`，以免任意路径替代正式结果。

## Receipt v2 与证据

`DryRunReceiptV2` 是 17 项整体 PASS 收据，绑定 artifact-set 身份与路径、配置集合身份、204 覆盖、Approval/dataset/query/Reference/runtime/code/protocol 身份，以及确定性和泄漏检查证据的路径与原始字节 SHA-256。收据由 append-only lifecycle writer 保存为 `docs/experiments/audits/dry_run_receipts/<identity_hash>/record.json` 并带原始字节 SHA-256 sidecar；validator 重算规范 identity 并核对路径。证据必须是 HEAD 中已提交的 JSON，`status=pass`，并绑定同一 artifact-set、矩阵身份和全部 17 个 raw run hash。确定性证据要求 `comparison_scope=all_17_configurations`、`compared_query_count=204`、`observed_rank_mismatches=0`；泄漏证据要求 English Test 与 Chinese 执行计数均为零。它们记录检查结论，正式签发前应由独立的 Phase 6.3 QA 审核；validator 负责提交态、交叉身份及实际 raw split/coverage 的机器核验，不把简单布尔值当作独立授权。

旧 `DryRunReceipt` v1 保持原 schema 可反序列化以读取历史记录；FORMAL 资格只接受 v2，旧单配置 receipt 不得替代完整矩阵。失败或尚未验证的 Dry Run 不产生 PASS 收据。`DryRunReceiptV2` 不能绕过 Phase 6.2 Approval/Closure、冻结输入、runtime 或代码校验。

本修正未执行 English Dev、English Test、Chinese 或 Formal RQ；正式 DryRunReceipt 仍未创建。
