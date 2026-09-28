# V3.1.0 Phase 6.3 Corpus 与 Execution Revision 身份修正

- 版本：`v1`
- 范围：Phase 6.3 provenance identity；不改变冻结查询、Reference、配置矩阵、指标或实验方法。
- 本文件不记录正式 Dry Run 或 Formal RQ 结果。

## 三种 Git 身份

1. `corpus_revision` 是冻结 dataset manifest 中唯一 `self_repository` 项的 `source_revision`。当前值为 `12391233daa2149ead4f451e920b2e0d8a1a6beb`；CorpusBuilder、Snapshot 和 source evidence 均从该提交读取语料。该值不随 benchmark 执行代码提交变化。
2. `execution_revision` 是**实际运行 runner 时的 pre-run 代码 HEAD**，绑定 runner、retrieval、metrics 和 artifact writer。它不是随后归档 artifacts 的 Commit A。执行入口核验该提交是当前 HEAD 的祖先，且 `experiments/`、`project_intelligence/`、`code_maintenance/` 在该提交至当前 HEAD 之间没有已提交或工作树代码差异。
3. `receipt_archive_commit` 是当前可达 Git 历史中最近一次加入 receipt 路径、且该次字节与当前 HEAD 一致的提交。收据无法预先写入自身的 Commit A SHA，因此此身份由 `RepositoryAuthority` 在提交后派生，不写入 receipt。FORMAL 校验要求 `execution_revision` 是归档提交的祖先，且 receipt 及其证据与当前 HEAD 的已提交字节一致。Commit B 仅更新导航时，仍可从其 HEAD 读取 Commit A 的 receipt。

## 新 artifact 合同

- 新 run manifest 使用 `revision_schema_version=v2`，明确保存 `corpus_revision`、`execution_revision`、`mode` 和 `split`；不再输出顶层 `self_repository_commit` 或 `runner_code_commit`。runner 核验 corpus revision 等于冻结 dataset 的 source revision，execution revision 等于资格校验授予的实际代码提交。RunMetadata 的两个版本字段也明确分开。
- `DryRunArtifactSet` schema `v2` 分别绑定两种 revision。FORMAL validator 从 HEAD 重读全部 17 个 run manifest，要求每个 run 的 corpus revision 等于冻结 source revision、每个 execution revision 等于 artifact set、receipt 与获准执行提交；任一混用均拒绝。
- `DryRunReceiptV2` 的本次字段修订使用 schema `v2.1`，分别绑定 `corpus_revision` 和 `execution_revision`，并保留矩阵、12 个 English Dev ID、204 覆盖、determinism、leakage 与 Reference Approval 交叉校验。旧 `v2` 形状不会被解析为 `v2.1`。
- 已有 run manifest 若没有 `revision_schema_version`，其 `self_repository_commit` **只解释为 corpus revision**；其 execution revision 为 unavailable。该旧形状可读用于历史解释，但不能满足新的 FORMAL provenance。新格式同时出现旧字段也拒绝。

此修订只修复 provenance identity；Phase 6.3 English Dev Dry Run、DryRunReceiptV2 和 Formal RQ1–RQ4 仍未执行。
