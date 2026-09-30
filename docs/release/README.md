# V3.1 Documentation Index

<!-- release-state: V3.1.1 RELEASE_CANDIDATE -->

本页是 V3.1 Project Intelligence / RAG 与维护版本的发布、工程、研究和论文材料导航。
V3.1.0 已正式发布；V3.1.1 Workflow & Developer Experience Optimization 当前为
**RELEASE CANDIDATE / READY FOR DEEPSEEK FINAL QA**。V3.2 **NOT STARTED**。

## Start Here

- [Repository README](../../README.md) — 项目定位、当前能力、架构、评估摘要与 Version History
- [V3.1.0 Final Development Report](../development/Development_Report_V3_1_0.md) — Phase 0–6 工程与研究全程总结
- [V3.1.0 Release Notes](Release_Notes_V3_1_0.md) — 候选版本亮点、兼容性、限制与迁移说明
- [V3.1.0 Thesis Materials Package](../development/Thesis_Materials_V3_1_0_Formal_Results.md) — 可直接用于论文的事实、表格、图表计划与 claim boundary
- [V3.1.1 Scope Freeze](../development/V3_1_1_Workflow_DX_Scope.md) — 六项维护工作及 non-goals
- [V3.1.1 Development Report](../development/Development_Report_V3_1_1.md) — 实现、测试与兼容性证据
- [V3.1.1 Thesis Engineering Materials](../development/Thesis_Materials_V3_1_1_Workflow_DX.md) — workflow reproducibility 工程贡献
- [V3.1.1 Release Notes](Release_Notes_V3_1_1.md) — 命令、诊断、门禁与限制

## Architecture and Design

- [Architecture & Research Decision](../development/Architecture_Decision_V3_1_0.md)
- [Development Baseline Gate](../development/Development_Baseline_Gate_V3_1_0.md)
- [Semantic Embedding Selection](../development/Semantic_Embedding_Selection_V3_1_0.md)
- [Phase 1 — Corpus / Symbol](../development/Development_Report_V3_1_0_Phase_1.md)
- [Phase 2 — BM25](../development/Development_Report_V3_1_0_Phase_2.md)
- [Phase 3 — Embedding](../development/Development_Report_V3_1_0_Phase_3.md)
- [Phase 4 — Graph / Incremental](../development/Development_Report_V3_1_0_Phase_4.md)
- [Phase 5 — Hybrid / ContextBuilder](../development/Development_Report_V3_1_0_Phase_5.md)

## Protocol, Dataset, and Reference

- [Experiment Protocol](../experiments/Experiment_Protocol_V3_1_0.md)
- Protocol Addenda: [A](../experiments/Experiment_Protocol_Addendum_A_V3_1_0.md) · [B](../experiments/Experiment_Protocol_Addendum_B_V3_1_0.md) · [C](../experiments/Experiment_Protocol_Addendum_C_V3_1_0.md) · [D](../experiments/Experiment_Protocol_Addendum_D_V3_1_0.md)
- [Dataset / Query / Ground Truth Specification](../experiments/Dataset_Query_GroundTruth_Specification_V3_1_0.md)
- [Reference Lifecycle Engineering Specification](../experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md)
- Lifecycle Amendments: [1](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_1_V3_1_0.md) · [2](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_2_V3_1_0.md) · [3](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_3_V3_1_0.md) · [4](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_4_V3_1_0.md) · [5](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_5_V3_1_0.md)
- [Reference Approval](../experiments/reference_approval/e89ce78f4c7b27754b52cab1b9217b349f5e7a382423bd75eb44a2a1deafb5d8.json)
- [Phase 6.2 Closure](../experiments/reference_approval/phase62_closure.json)
- [Phase 6.2 Final Closure Report](../development/Development_Report_V3_1_0_Phase_6_2_Final_Closure.md)

## Dry Run and Formal Results

- [DryRunReceiptV2](../experiments/audits/dry_run_receipts/8383eb1c0e45ca68927cecc5170a18a0ae56cc62dcbf2e5b3ff53448073fff3e/record.json)
- [English Dev Dry Run artifact set](../experiments/audits/phase63_english_dev/artifact_set.json)
- [English Dev Dry Run report](../development/Development_Report_V3_1_0_Phase_6_3_English_Dev_Dry_Run.md)
- [Formal artifact set](../experiments/audits/phase64_formal_english_test/artifact_set.json)
- [Formal RQ1–RQ4 Results Report](../development/Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)
- [Formal Results Interpretation](../experiments/Formal_Results_Interpretation_V3_1_0.md)
- [Experiment Evidence Index](../experiments/README.md)

Independent Formal Results QA 的结论元数据为 **PASS WITH NON-BLOCKING NOTES**，
Critical 0、validity-blocking Medium 0。仓库没有收到可单独归档的 reviewer 逐字原文；
来源边界见 Formal Results Interpretation 与 Thesis Materials Package。

## Formal CSVs and Figure Data

- [RQ1–RQ4 Main Results](../experiments/Formal_Result_Table_RQ1_RQ4_V3_1_0.csv)
- [Extended Metrics and Slices](../experiments/Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv)
- [ContextBuilder Diagnostics](../experiments/Formal_ContextBuilder_Diagnostics_V3_1_0.csv)
- [Figure A–D Data](../experiments/Formal_Figure_Data_A_D_V3_1_0.csv)
- [Deterministic Export / Check Script](../../scripts/export_formal_thesis_tables.py)

## Frozen Formal Identity

| Item | Value |
| --- | --- |
| Result archive commit | `c3ee6ec1b7aa28c2539d2fe849d1f25268807677` |
| Execution revision | `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` |
| Artifact-set identity | `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` |
| Artifact-set file SHA-256 | `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` |
| Formal execution | 48/48 English Test × 17/17 configs = 816/816 success |

这些结果仅支持冻结 benchmark 上的 descriptive comparison。RRF 是 secondary
robustness comparison；不作 significant、best、winner、全面提升、外部泛化或下游
LLM 维护质量声明。

## Release Boundary

- V3.1.0：RELEASED
- V3.1.0 release commit：`8813e4c2fb0dc07f38c2013d520441bf399dcbc4`
- V3.1.0 tag：`v3.1.0`
- V3.1.0 push / remote verification：Completed
- V3.1.1：RELEASE CANDIDATE / Ready for DeepSeek Final Release QA
- V3.1.1 tag / push：Not created / No
- V3.2 Multi-Agent Collaboration：Not Started
