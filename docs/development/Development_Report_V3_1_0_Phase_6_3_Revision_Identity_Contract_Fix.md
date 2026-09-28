# V3.1.0 Phase 6.3 Revision Identity Contract Fix 开发报告

## 根因与修正

前一轮 Dry Run 预检发现同一 run manifest 的 `self_repository_commit` 在 runner 中被要求等于冻结语料提交 `12391233daa2149ead4f451e920b2e0d8a1a6beb`，却在 FORMAL receipt validator 中被要求等于执行代码提交。两者本来不同，正式结果无法同时满足。根因是将 corpus/source revision 与 execution/code revision 混为一谈。

本轮按 [Amendment 4](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_4_V3_1_0.md) 将两者明确分开。新 run manifest 使用 `revision_schema_version=v2` 与 `corpus_revision`、`execution_revision`；artifact set 使用 schema `v2`；`DryRunReceiptV2` 使用修订 schema `v2.1`。FORMAL 资格分别核验冻结 dataset source revision、执行代码 revision、17 个 run 的一致性，以及 receipt 在执行提交之后的 Git 归档提交。旧 manifest 可按 corpus-only 语义读取，但不能取得 FORMAL 资格；旧 receipt 形状亦不能冒充新 provenance。

## 范围与状态

只修改 benchmark provenance schema、runner/eligibility 校验与 synthetic 测试。冻结数据、Reference、配置、指标和实验方法未变。本轮不运行正式 English Dev、English Test、Chinese 或 Formal RQ；不创建 DryRunReceiptV2，不更新 Formal gate。

新增 11 项 synthetic/offline 安全测试，覆盖 corpus 与 execution revision 不同仍合法、两种错误版本和混合 run 版本拒绝、旧 manifest 的 corpus-only 读取和 FORMAL 拒绝、旧 receipt 形状拒绝、receipt 字段互换拒绝、执行提交与 Commit A 归档提交不同仍合法、归档早于执行和归档后检索代码变化拒绝，以及导航布尔值不能绕过版本校验。受影响的 benchmark/production/lifecycle 专项为 `177 passed`，后补的 3 项定向测试亦通过；完整回归为 `850 passed`。测试没有真实 E5 推理、网络请求、正式 query 执行或 Formal RQ 执行。

提交消息：`fix(v3.1): separate corpus and execution revisions`。本轮不 push、不 tag；下一步是在新的已提交 HEAD 上重新核对正式 Dry Run 入口，然后另行执行 English Dev Dry Run。
