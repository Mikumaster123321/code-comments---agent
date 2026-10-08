# V3.1 Documentation Index

<!-- release-state: V3.1.2 RELEASED -->

本页是 V3.1 Project Intelligence / RAG 与维护版本的发布、工程、研究和论文材料导航。
V3.1.0 已正式发布；V3.1.1 Workflow & Developer Experience Optimization 已正式发布
（**FULLY RELEASED**，tag `v3.1.1`）。V3.1.2 Language / UX / Output Quality 已正式发布
（**RELEASED**，tag `v3.1.2`）；V3.2 **NOT STARTED**。

## Start Here

- [Repository README](../../README.md) — 项目定位、当前能力、架构、评估摘要与 Version History
- [V3.1.0 Final Development Report](../development/Development_Report_V3_1_0.md) — Phase 0–6 工程与研究全程总结
- [V3.1.0 Release Notes](Release_Notes_V3_1_0.md) — 正式版本亮点、兼容性、限制与迁移说明
- V3.1.0 Thesis Materials：[MD](../development/Thesis_Materials_V3_1_0_Formal_Results.md) · [UTF-8 TXT](../development/Thesis_Materials_V3_1_0_Formal_Results.txt) — 论文事实、结果解释与 claim boundary
- [V3.1.1 Scope Freeze](../development/V3_1_1_Workflow_DX_Scope.md) — 六项维护工作及 non-goals
- [V3.1.1 Development Report](../development/Development_Report_V3_1_1.md) — 实现、测试与兼容性证据
- V3.1.1 Thesis Engineering Materials：[MD](../development/Thesis_Materials_V3_1_1_Workflow_DX.md) · [UTF-8 TXT](../development/Thesis_Materials_V3_1_1_Workflow_DX.txt) — workflow reproducibility 工程贡献
- [V3.1.1 Release Notes](Release_Notes_V3_1_1.md) — 命令、诊断、门禁与限制
- [V3.1.2 Scope Freeze](../development/V3_1_2_Language_UX_Output_Quality_Scope.md) — 七项冻结维护范围与 non-goals
- [V3.1.2 Prompt Output Contract](../development/V3_1_2_Prompt_Output_Contract.md) — 模型输入边界、语言、translation/rewrite 与 cleanup 合同
- [V3.1.2 Development Report](../development/Development_Report_V3_1_2.md) — 实现、兼容性、测试与 host limitation
- V3.1.2 Thesis Engineering Materials：[MD](../development/Thesis_Materials_V3_1_2_Language_UX_Output_Quality.md) · [UTF-8 TXT](../development/Thesis_Materials_V3_1_2_Language_UX_Output_Quality.txt)
- [V3.1.2 Release Notes](Release_Notes_V3_1_2.md) — 发布功能、边界与限制
- [Permanent Version Documentation Contract](Version_Documentation_Contract.md) — 每个 major/minor/patch 版本的双格式论文素材、文档、tag、双远端发布与验证硬门禁

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
- V3.1.1：RELEASED
- V3.1.1 release commit：`683479da2fd3b72c17cba3f03101bc23e275f40b`
- V3.1.1 final release-record HEAD：`0238cc0bd5254ac782aa3981cdc755d5a59c498e`
- V3.1.1 tag：`v3.1.1`
- V3.1.1 push / remote verification：Completed（GitHub / Gitee branch and tag）
- V3.1.0 / V3.1.1 documentation closure：Completed
- V3.1.2 Language / UX / Output Quality：RELEASED
- V3.1.2 tests：targeted + LLM contracts 35；production 198；experiments 240；full 951
- V3.1.2 branch / branch point：`v3.1.2-dev` / `2036cb6c82860b9bf8229ecac0f4d4add420855d`
- V3.1.2 tag：`v3.1.2`
- V3.1.2 push / remote verification：Pending（本轮仅本地 finalize）
- V3.2 Multi-Agent Collaboration：Not Started
