# V3.1.0 Phase 6.2 独立方法论审查包 v1

- 状态：**READY FOR EXTERNAL METHODOLOGY REVIEW；未收到审查结论**。
- 输入边界：只读；不得修改 Query、GT、Grade、prepared input 或冻结源码，不运行正式 RQ，也不根据预期检索成绩选择标签。
- 建议审查角色：按 `AGENTS.md`，由 Claude 最高可用 Opus 高推理承担主要方法论审查；Grok 4.7 可独立交叉审查。此处没有代替任何外部审查。
- 身份：Phase 6 Protocol、Addenda A–D 与 Dataset Specification 的方法论 manifest identity 为 `733eb5fe73fd6993fed2d2736c5285532a5db2f14c56f68a2b4061adfa51c32e`；工程规范 v1 原始 SHA-256 为 `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045`。审查回复须同时写明本文件的 Git 路径、版本、提交 SHA 与原始文件 SHA-256，避免审错版本。

## 目的与方法

Phase 6.2 为 72 条固定 Query 建立可复核的 dataset、query 与 specification-anchored reference 身份，之后才可审批 English-dev Dry Run。构造依据是 [Experiment Protocol](Experiment_Protocol_V3_1_0.md)、[Addendum D](Experiment_Protocol_Addendum_D_V3_1_0.md) 和 [Dataset Specification](Dataset_Query_GroundTruth_Specification_V3_1_0.md)。数据包括 English test 48、English dev 12、Chinese coverage 12；六类任务各有固定配额。Python 是主实验语言，Java 用于覆盖验证。72 条旧 v1 GT 保持 `drafted`，由事先规格锚点与等级机械材料化；另有独立 Reference 内容身份 `d3d5f54f8256b2dadd151f26cd0f1f7674c1c62fa464846fb13bc5c295dc8f04`，尚未批准。没有逐条人类标注、延迟盲审或 human IAA。

Addendum D 预注册的 Java evidence audit 选择每类 English-test Query 字典序前两条，恰好为全部 12 条 English-test Java Query。当前 12/12 已执行，其中 10 条结构有效且模型 verdict 为 `SUPPORTS`；`et-bl-ja-01` 与 `et-fl-ja-02` 为执行级 `response_contract_failure`，模型 verdict 不可用。依据 [Amendment 2](Reference_Lifecycle_Engineering_Specification_Amendment_2_V3_1_0.md)，两条仍记 `CANNOT_ASSESS`，不修复或采纳非法回复。本轮分别依据冻结源码、JavaAdapter、prepared evidence 与未改动 GT 做了 [源码核验 1](audits/source_resolution/et-bl-ja-01.json) 和 [源码核验 2](audits/source_resolution/et-fl-ja-02.json)，均为 `SUPPORTED_BY_FROZEN_SOURCE`；对应 `ResolutionRecord` 为 `source_verification/closed`。该结果只核查已有证据是否支撑当前 reference，不改变 GT/Grade，也不声称模型转为 `SUPPORTS`。

中文覆盖的 12 条均为 Python，六类任务各 2 条，身份、配额、现有证据和机械泄漏检查通过。中文集合仅用于单独覆盖分析，不能并入 English test 主结果或调参。Addendum D §8 要求的 12 条“非机械直译”独立语义审查尚未预注册和执行；因此中文正式审批前置条件仍未完成。最终独立 Data QA 也尚未签发 PASS。详见 [Final Closure 准备报告](../development/Development_Report_V3_1_0_Phase_6_2_Final_Closure.md)。

## 请审查的问题与回执

1. specification-anchored reference 作为 72 条 Query 的固定操作性参考，是否足以支持限定为“相对该参考的系统间比较”的 RQ1–RQ4 解释？请指出遗漏真实相关证据和未列入即按零分的构念效度影响。
2. 48/12/12 的用途分离、Grade 2/1/0 与泄漏控制是否足以避免 dev/test/中文信息混用？请检查 12 条 Java 便利样本的选择及其外推限制。
3. 两条执行失败保留 `CANNOT_ASSESS`、只通过冻结源码解决既有证据支撑问题的处理是否符合 Addendum D §6 与 Amendment 2？
4. 中文非机械直译的独立语义审查和最终独立 Data QA 在批准前还需提供什么可追溯证据？请将任何方法论缺陷按 Critical、影响效度的 Medium 或 Low 标明。
5. 论文限制是否充分：本审计既不是 full external annotation，也不是 48 条 English test 的代表性质量估计；不能推断 Python/Chinese 的全面独立验证，不能声称外部项目泛化。

请以 `PASS`、`QUESTIONS` 或 `CANNOT_ASSESS` 给出总体结论，并逐条给出来源位置、理由、严重度、是否需要决议。回执记录审查者/模型显示身份、实际时间、输入文件路径与版本及 SHA-256、完整原始回复及 SHA-256、可得平台来源与限制、输出身份和每个问题的 resolution status。`QUESTIONS` 或 `CANNOT_ASSESS` 不得自动转为 PASS；任何影响方法或标签的决定须先进入 Git 跟踪的决议/规格，再由后续流程使用。本包及这些问题是预注册审查输入，不代表审查已发生。
