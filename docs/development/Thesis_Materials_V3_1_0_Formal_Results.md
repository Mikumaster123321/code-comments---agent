# V3.1.0 Formal Results 论文实验章节素材索引

本文件是论文写作的事实素材，非最终论文。数值来自冻结 [Formal 结果报告](Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)及其 [artifact set](../experiments/audits/phase64_formal_english_test/artifact_set.json)；解读边界见 [正式解读档案](../experiments/Formal_Results_Interpretation_V3_1_0.md)。正式 artifact-set identity 为 `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`，归档提交为 `c3ee6ec1b7aa28c2539d2fe849d1f25268807677`，execution revision 为 `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`。独立 QA：PASS WITH NON-BLOCKING NOTES；解读判定：ACCEPT — CLAIM-BOUNDED。该判定和 Claude Sonnet 5 / Medium / Off 元数据由本轮用户说明提供；Claude 原文未随材料提供，本文件的文字由正式报告整理。

## 素材与图表索引

| 用途 | 数据源 | 写作提示 |
| --- | --- | --- |
| RQ1–RQ4 主表 | [Formal_Result_Table_RQ1_RQ4_V3_1_0.csv](../experiments/Formal_Result_Table_RQ1_RQ4_V3_1_0.csv) | 17 项配置，Recall@5、MRR；RRF 行 `secondary=true` |
| 扩展结果与分群 | [Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv](../experiments/Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv) | 全体、Python、Java、六种 task type；七项已有指标 |
| Figure A–D | [Formal_Figure_Data_A_D_V3_1_0.csv](../experiments/Formal_Figure_Data_A_D_V3_1_0.csv) | A=RQ1，B=RQ2，C=RQ3，D=RQ4；D 内 RRF 为 secondary |
| Figure E / ContextBuilder 表 | [Formal_ContextBuilder_Diagnostics_V3_1_0.csv](../experiments/Formal_ContextBuilder_Diagnostics_V3_1_0.csv) | 仅两个 Weighted Hybrid 配置；预算、GT evidence、截断 |
| 导出与复核 | [export_formal_thesis_tables.py](../../scripts/export_formal_thesis_tables.py) | 从正式 artifact 自动提取；`--check` 比较 CSV 原字节 |

CSV 保留正式 artifact 的原始浮点表示；以下段落使用正式报告已发布的四位小数及描述性差值。

## A. Experiment setup summary

**可直接进入论文正文。** 本实验在冻结的 English Test 上比较 RQ1–RQ4 的 17 项预定配置。测试集包含 48 条 Query，其中 Python 36 条、Java 12 条，六类维护任务各 8 条；816 个 query-config 组合均成功完成。主指标为 Recall@5 和 MRR；Recall@1、Recall@10、nDCG@5、Precision@5 与 Hit Rate@5 作为已记录的扩展指标。检索指标在 ContextBuilder 构建上下文之前计算。

**仅供讨论/备选解释。** 六种任务的均衡数量便于展示任务切片，但每类只有 8 条，不能用切片挑选有利结论。

## B. RQ1 facts + bounded interpretation

**可直接进入论文正文。** File、Symbol、Chunk 的 Recall@5 分别为 0.8906、0.5368、0.5836，MRR 分别为 0.7364、0.6130、0.6274。File 相对 Symbol 的 Recall@5/MRR 差值为 +0.3538/+0.1233；这些数值描述固定 Query 集及各单元的相关性映射。File 的 coarse-grained relevance set 限制了跨粒度优劣推断。

**仅供讨论/备选解释。** File 的较高覆盖可能与粗粒度相关性集合有关；Symbol 仍是系统细粒度的主要检索单元，维护任务中的实际定位价值需要另行评估。

## C. RQ2 facts + bounded interpretation

**可直接进入论文正文。** BM25 的 Recall@5/MRR 为 0.5368/0.6130，E5 为 0.5057/0.7311。E5 相对 BM25 的 Recall@5 差值为 -0.0311，MRR 差值为 +0.1181；两个主指标须分别报告。

**仅供讨论/备选解释。** 本数据可能反映语义匹配对首个相关结果位置和前五项覆盖的不同作用；尚不能将该现象归因于一般 embedding 模型特性。

## D. RQ3 facts + bounded interpretation

**可直接进入论文正文。** Graph ON 相对 Graph OFF 的 Recall@5/MRR 差值为 +0.0191/+0.0354。方向消融中，CONTAINS/FORWARD 为 0.5316/0.6600，CONTAINS/REVERSE 为 0.5542/0.7086；IMPORTS/FORWARD 与 IMPORTS/REVERSE 均为 0.5333/0.6617，在这两个总体指标上与 Graph OFF 数值相同。方向消融是次级归因证据。

**仅供讨论/备选解释。** 本集合中的图贡献可能集中于 CONTAINS 的反向扩展；需要逐 Query 审查才能解释机制，不能把 IMPORTS 的相同总体值解释为普遍无效。

## E. RQ4 facts + bounded interpretation

**可直接进入论文正文。** Weighted Lexical、Embedding、Hybrid no graph、Hybrid graph 的 Recall@5/MRR 依次为 0.5368/0.6130、0.5057/0.7311、0.5333/0.6617、0.5524/0.6971。Hybrid graph 相对 no graph 为 +0.0191/+0.0354。作为 secondary robustness，RRF no graph 为 0.5490/0.7365，RRF graph 为 0.5451/0.6978，后者相对前者为 -0.0038/-0.0387。RRF 不替代预注册 Weighted 比较。

**仅供讨论/备选解释。** 图信号的表现可能依赖融合方式；这一观察需要在独立数据上复核。

## F. ContextBuilder diagnostics

**可直接进入论文正文。** 在两个 Weighted Hybrid 配置下，总预算均为 384000 字符。No graph 与 graph 的已用预算分别为 272990 与 321821，GT evidence rendered 分别为 101/165 与 124/165，snippet count 分别为 425 与 533，发生 package truncation 的 Query 分别为 20 与 24。Graph-only rendered snippets 分别为 0 与 166；retained but unrendered graph provenance 分别为 0 与 386。诊断描述上下文渲染，不参与检索 ranking 或 Recall/MRR。

**仅供讨论/备选解释。** 更多 GT evidence 与更多预算消耗及截断并存，提示后续可研究证据选择和预算分配；当前没有下游 LLM 维护质量实验来判断净效益。

## G. Cross-RQ synthesis

**可直接进入论文正文。** 四个研究问题共同显示：在冻结集合中，检索粒度、词法与语义信号、图扩展及融合配置对 Recall@5 和 MRR 呈现不同的描述性结果。正式结果同时保留正向、负向和相同数值，不建立跨 RQ 单一排序。

**仅供讨论/备选解释。** 论文可讨论稳定 Symbol identity、项目关系和有界 ContextBuilder 的系统集成价值，但本实验不证明新检索算法或端到端维护能力提升。

## H. Limitations

**可直接进入论文正文。** Formal English Test 仅 48 条，采用 frozen single-repo + controlled fixtures 和 silver reference；没有 human IAA。Java limited audit 不等于全体 GT 验证；Chinese 不进入 English main result。File 使用 coarse-grained relevance set。Retrieval quality 不等于 downstream LLM maintenance quality。本轮没有 preregistered significance testing，也未完成重复计时性能协议，因此不作统计显著性或 latency/SLA 结论。

**透明度说明（QA-L-01）。** `phase62_closure_identity` 指 `Phase62ClosureRecord.identity_hash`，不是 raw file SHA-256。

## I. V3.2 transition

**可直接进入论文正文。** V3.1 实验结果与 ContextBuilder diagnostics 为后续多智能体维护任务设计提供检索与上下文输入基线。后续若评估任务效果，应另设端到端任务与人工判定，将检索指标和实际维护质量分开报告。

**状态。** V3.2 **NOT STARTED**。当前剩余工作为论文素材审校、V3.1 Release Gate 和 v3.1.0 发布；本文件不构成发布批准。

## V3.1 Release Gate 准备索引

Release Gate 可直接核对：冻结 Formal artifact-set 身份与文件 SHA-256、结果归档提交及 execution revision；[正式结果报告](Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)；独立 QA 的 PASS WITH NON-BLOCKING NOTES 与本轮用户提供的 ACCEPT — CLAIM-BOUNDED 判定；四份由 artifact 导出的 CSV 及导出脚本的 `--check`；本文件的 claim boundary 和 QA-L-01 说明。正式 Gate 仍须检查本轮提交后的工作区、测试和发布文档，并作独立批准。本轮不创建版本 tag、不 push、不进入 V3.2。
