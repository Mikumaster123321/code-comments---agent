# V3.1.0 Phase 6.4 Formal 前置：RQ4 Context Diagnostic Artifact Fix

## 范围与结论

本轮只修复冻结 Protocol 已要求的 RQ4 ContextBuilder diagnostic artifact 接线，不执行 Formal benchmark，不发布 Formal result，不修改 Query、GT、Grade、检索排序、融合权重、BM25、E5、Graph、RRF、ContextBuilder 选择策略、8000 字符预算或指标公式。

上一轮基于 execution revision `5a462c70c2b10b96f6ec71314bda2b9990da0bb7` 的失败 Formal attempt 实际运行了 English Test 48/48、配置 17/17、query-config 816/816，并完成 8 条代表路径共 384 次确定性比较；但两个 RQ4 Weighted Hybrid run 没有 materialize Protocol 要求的 ContextBuilder diagnostics，`context_diagnostic_summary_reference` 为 `null`。因此该 attempt 已撤回且从未提交，Formal artifact set 未发布，RQ1–RQ4 仍未完成。

失败 attempt 的 17 个 raw run 集合身份为 `733ad4e5870002d2f587a16d1654dae8373ba885a12783d68964156a91f5950d`；确定性证据文件 SHA-256 为 `dbffce197b8110370198705d78a56b3abc8d5533da9f9f26d775b213d660c3af`；泄漏证据文件 SHA-256 为 `d4e338ba5e59eccce11a81f06efebd0ebca0e7037aa1e33bd936a2f24c491dcc`。曾生成后立即撤回的 artifact-set canonical identity 为 `7b38a0575bdf53b1f84a9906061ae91cfbf21a3cd36a557c8cdb527a5288cb47`。这些身份仅记录失败 provenance，不构成 Formal result。对应未跟踪 run/audit 目录已移除，没有 ranking 或 metrics 进入本次修复提交。

## 根因

`ProductionBenchmarkStrategy` 已对 `RQ4-HYBRID-NO-GRAPH` 与 `RQ4-HYBRID-GRAPH` 调用 production `ContextBuilder`，但只把返回的 `ContextPackage` 留在 strategy 的进程内字典。`StrategyResult` 没有把该 package 交给 runner；`BenchmarkRunner` 固定把 aggregate 的 `context_diagnostic_summary_reference` 设为 `null`；`write_run_artifacts` 也只写 manifest、aggregate 和 raw results。因此 ContextBuilder 的真实执行行为没有被 canonical serialization、run checksum 和 artifact reload 链绑定。

冻结 Protocol §7.5 和 §9.4 已明确要求两个 Weighted Hybrid row 在排名之后执行 ContextBuilder 并单独报告 diagnostics。本轮不新增方法学 Amendment。RRF 是独立的 secondary robustness 表，Protocol 未要求其产生 ContextBuilder diagnostics，因此其 reference 继续使用合法的 `null` 语义。

## 修复

production adapter 继续只调用现有 `project_intelligence.ContextBuilder`。它将真实 `ContextPackage` 作为只读 observation 交给 runner；diagnostic collection 发生在 Hybrid ranking 已完成后，不参与候选选择、打分、排序或 metric 计算。

每个适用 run 新增 `context_diagnostics.json`，schema 为 `context-diagnostic-v1`。artifact 顶层绑定：

- mode、split、run ID、matrix run ID、config identity；
- corpus revision、execution revision、index identity；
- artifact canonical identity；
- per-run summary 与按 query ID 排序的 per-query diagnostics。

per-query 记录绑定 query input identity 与 retrieval identity，并只保存 Protocol 冻结的诊断口径：相关 ground-truth evidence rendered/total、相关 ranked hits rendered/total、budget used/ratio、snippet count、context characters、package/snippet truncation、未渲染 ranked hits、Graph-only rendered snippets，以及 retained but unrendered Graph provenance count。artifact 不保存 source text、context text或向量。

适用 run 的 aggregate 将 `context_diagnostic_summary_reference` 绑定为 `context_diagnostics.json`；manifest `output_checksums` 和 run `checksums.sha256` 同时绑定该文件。loader 会重算文件 SHA-256、canonical artifact identity、summary、query/retrieval identity关联，并核对 manifest/aggregate 中的 mode、split、config、revision、index 和 run 绑定。缺失、损坏、wrong-config 或 namespace 混用均 fail closed。非适用配置不生成占位 artifact，reference 保持 `null`。

## 验证

最小 integration smoke 使用 synthetic fixture 和 deterministic fake embedding，仅验证 production 链路，不访问真实 E5、不执行 English Test：

`production Hybrid retrieval → production ContextBuilder → per-query diagnostics → context_diagnostics.json → aggregate reference → checksum/canonical identity reload`

两项 synthetic mirror 分别覆盖 RQ4 Hybrid No Graph 和 Hybrid Graph。对每项使用相同检索设置的 diagnostic-on 与 diagnostic-off 路径比较，ranked hits 和 metrics 完全相同。测试还覆盖缺失 diagnostic、损坏 checksum、错误 config 绑定、错误 namespace、确定性序列化、corpus/execution revision、非适用配置保持 `null`，以及 RRF/RQ3 不被扩展到本 artifact 合同。

- 修复前全量基线：`881 passed`。
- ContextBuilder、production execution、runner/artifact、identity/serialization/security、reference lifecycle/eligibility 专项：`240 passed`。
- 修复后全量回归：`892 passed`。

## 状态

Phase 6.3 继续 `CLOSED`。本修复提交完成并从新 HEAD 重新验证 FORMAL eligibility 之前，不存在成功 Formal execution。当前 Formal English Test successful execution 为 0/48，Formal matrix successful execution 为 0/17，Formal artifact set 为 `NONE`，RQ1–RQ4 为 `NOT COMPLETED`。

下一允许动作是在本修复提交的新 execution revision 上，从 0 完整重跑冻结 English Test 48 × 17 = 816 Formal benchmark。
