# V3.1.0 Experiment Evidence Index

本页是 V3.1.0 冻结实验合同、Reference、Dry Run、Formal 结果与论文素材的导航入口。
历史合同和 artifact schema 均保持原样；本页不改变任何实验身份或结论。

发布与工程全局导航见 [V3.1.0 Documentation Index](../release/README.md) 和
[Final Development Report](../development/Development_Report_V3_1_0.md)。当前版本状态
是 **RELEASE DOCUMENTATION READY FOR DEEPSEEK FINAL QA**，不是 Released。

## 方法与数据合同

- [Experiment Protocol](Experiment_Protocol_V3_1_0.md)
- Addenda：[A](Experiment_Protocol_Addendum_A_V3_1_0.md)、[B](Experiment_Protocol_Addendum_B_V3_1_0.md)、[C](Experiment_Protocol_Addendum_C_V3_1_0.md)、[D](Experiment_Protocol_Addendum_D_V3_1_0.md)
- [Dataset / Query / Ground Truth Specification](Dataset_Query_GroundTruth_Specification_V3_1_0.md)
- [Reference Lifecycle Engineering Specification](Reference_Lifecycle_Engineering_Specification_V3_1_0.md)
- Amendments：[1](Reference_Lifecycle_Engineering_Specification_Amendment_1_V3_1_0.md)、[2](Reference_Lifecycle_Engineering_Specification_Amendment_2_V3_1_0.md)、[3](Reference_Lifecycle_Engineering_Specification_Amendment_3_V3_1_0.md)、[4](Reference_Lifecycle_Engineering_Specification_Amendment_4_V3_1_0.md)、[5](Reference_Lifecycle_Engineering_Specification_Amendment_5_V3_1_0.md)

## Reference 与 Dry Run

- [Reference Approval](reference_approval/e89ce78f4c7b27754b52cab1b9217b349f5e7a382423bd75eb44a2a1deafb5d8.json)
- [Phase 6.2 Closure](reference_approval/phase62_closure.json)
- [DryRunReceiptV2](audits/dry_run_receipts/8383eb1c0e45ca68927cecc5170a18a0ae56cc62dcbf2e5b3ff53448073fff3e/record.json)
- [English Dev Dry Run artifact set](audits/phase63_english_dev/artifact_set.json)
- [Phase 6.3 Dry Run report](../development/Development_Report_V3_1_0_Phase_6_3_English_Dev_Dry_Run.md)

## Formal RQ1–RQ4

- [Formal artifact set](audits/phase64_formal_english_test/artifact_set.json)
- [Formal Results report](../development/Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)
- [Formal Results Interpretation](Formal_Results_Interpretation_V3_1_0.md)
- [RQ1–RQ4 main CSV](Formal_Result_Table_RQ1_RQ4_V3_1_0.csv)
- [Extended metrics CSV](Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv)
- [ContextBuilder diagnostics CSV](Formal_ContextBuilder_Diagnostics_V3_1_0.csv)
- [Figure data CSV](Formal_Figure_Data_A_D_V3_1_0.csv)
- [Thesis materials index](../development/Thesis_Materials_V3_1_0_Formal_Results.md)
- [Release Notes](../release/Release_Notes_V3_1_0.md)

Formal artifact-set canonical identity：
`acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`。
Artifact-set file SHA-256：
`2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`。
Formal execution revision：
`2749969cd3a2d4d6e1e8d81160eebd5fb360879b`。

独立 Formal Results QA 的结论元数据为 **PASS WITH NON-BLOCKING NOTES**，
Critical 0、validity-blocking Medium 0。仓库未收到独立 reviewer 的逐字原文，
因此不存在可链接的 standalone Formal QA 原文档案；这一来源限制已明确记录在
[Formal Results Interpretation](Formal_Results_Interpretation_V3_1_0.md) 与
[Thesis materials index](../development/Thesis_Materials_V3_1_0_Formal_Results.md)。

## 状态边界

- Formal English Test：48/48 Query
- Frozen configurations：17/17
- Query-config pairs：816/816，全部 success
- RQ1–RQ4：`COMPLETED`
- V3.1.0 release commit / tag / push：`NOT CREATED / NOT CREATED / NO`
- V3.2 Multi-Agent Collaboration：`NOT STARTED`
