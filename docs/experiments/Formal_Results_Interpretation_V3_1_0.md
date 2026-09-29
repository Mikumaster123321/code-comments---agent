# V3.1.0 Formal Results Interpretation 归档

**FORMAL RESULTS INTERPRETATION VERDICT: ACCEPT — CLAIM-BOUNDED**

## 来源与身份

本文件依据已冻结的 [Formal RQ1–RQ4 结果报告](../development/Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)和本轮用户提供的审查结论元数据整理。用户标识的 reviewer 为 **Claude Sonnet 5**，reasoning 为 **Medium**，thinking 为 **Off**；独立 Formal Results QA 判定为 **PASS WITH NON-BLOCKING NOTES**，Critical 0，validity-blocking Medium 0，论文结果解释资格为 **ELIGIBLE**。本轮未收到 Claude 解读原文；下文是基于正式报告起草的可审计解读，不声称为 reviewer 的逐字意见。

| 绑定项 | 冻结值 |
| --- | --- |
| Formal artifact-set canonical identity | `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` |
| artifact-set file SHA-256 | `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` |
| Formal result archive commit | `c3ee6ec1b7aa28c2539d2fe849d1f25268807677` |
| Formal execution revision | `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` |

数据源是 [主表](Formal_Result_Table_RQ1_RQ4_V3_1_0.csv)、[扩展表](Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv)、[ContextBuilder 表](Formal_ContextBuilder_Diagnostics_V3_1_0.csv)和 [Figure A–D 数据](Formal_Figure_Data_A_D_V3_1_0.csv)。这些 CSV 由 `scripts/export_formal_thesis_tables.py` 从正式 artifact 自动导出，并可用 `--check` 逐项核对。Figure E 直接使用 ContextBuilder 表。CSV 保留 artifact 的原始数值精度；本文显示正式报告的四位小数。

## 1. Scope / Claim Boundary

**FORMAL OBSERVATION。** 冻结 English Test 共 48 条 Query（Python 36、Java 12，六种任务各 8 条），17 项配置共 816 个 query-config 组合全部 success。Recall@5 和 MRR 是主指标；检索指标在 ContextBuilder 前计算。中文 Query 不属于 English 主结果。

**INTERPRETATION。** 本归档只讨论这一组冻结输入、配置和指标的描述性关系。不同指标呈相反方向时分别报告，不合成单一总分。RRF 是 secondary robustness 对照，不能替代预注册 Weighted Hybrid 主比较。

**LIMITATION。** 无预注册显著性检验，不能作统计显著、总体排序、跨项目泛化或生产延迟/SLA 结论。

## 2. Overall Interpretation

**FORMAL OBSERVATION。** File 的 Recall@5/MRR 为 0.8906/0.7364；Symbol 为 0.5368/0.6130；Chunk 为 0.5836/0.6274。E5 与 BM25 的两个主指标呈不同方向；Graph ON 相对 OFF 的两个主指标均有小幅正差值；Weighted Hybrid graph 相对 no graph 同样如此。RRF graph 相对 RRF no graph 的两个主指标则为负差值。

**INTERPRETATION。** 冻结数据支持“检索单元、语义信号、图方向和融合方式均影响观察到的检索结果”的有限陈述。各 RQ 的配置、相关性集合和比较目的不同，不应跨 RQ 选出统一优胜配置。

**LIMITATION。** File 使用 coarse-grained relevance set；File 与 Symbol 的分数不能直接解释为下游代码定位粒度或维护质量的优劣。

## 3. RQ1 — File / Symbol / Chunk

**FORMAL OBSERVATION。** Recall@5 分别为 0.8906、0.5368、0.5836；MRR 分别为 0.7364、0.6130、0.6274。File 相对 Symbol 的两个差值为 +0.3538/+0.1233；Chunk 相对 Symbol 为 +0.0468/+0.0144。

**INTERPRETATION。** 在冻结的相关性映射和 Query 集上，File 更容易覆盖粗粒度目标；Symbol 作为系统的细粒度主要单元，不能仅据这一指标否定其设计价值。Chunk 的结果显示该回退单元在本集合上有独立表现。

**LIMITATION。** File coarse-grained relevance set 改变了比较的语义，不能据此宣称任一单元对所有维护任务普遍更好。

## 4. RQ2 — BM25 / E5

**FORMAL OBSERVATION。** BM25 Recall@5/MRR 为 0.5368/0.6130；E5 为 0.5057/0.7311。E5 − BM25 为 -0.0311/+0.1181。

**INTERPRETATION。** 语义检索在本次主指标上呈现覆盖与首个相关结果位置的不同方向，说明两项指标需要并列解释。

**LIMITATION。** 仅一个冻结 E5 模型、单一语料和固定 Query 集；不能推广为所有 embedding 模型对词法检索的结论。

## 5. RQ3 — Graph OFF / ON 与方向消融

**FORMAL OBSERVATION。** Graph ON − OFF 的 Recall@5/MRR 为 +0.0191/+0.0354。CONTAINS/FORWARD 为 0.5316/0.6600，CONTAINS/REVERSE 为 0.5542/0.7086；IMPORTS/FORWARD 与 IMPORTS/REVERSE 均为 0.5333/0.6617，与 Graph OFF 的这两个总体指标相同。

**INTERPRETATION。** 观察到的图贡献与方向有关；CONTAINS/REVERSE 在本集合中提供了可见的次级归因线索。IMPORTS 两个方向的总体指标相同，不能据此推断该关系在其他 Query 或语料中无用。

**LIMITATION。** 方向消融是次级描述证据；小样本分群不能支持机制因果判定。

## 6. RQ4 — Weighted 信号消融与 secondary RRF

**FORMAL OBSERVATION。** Weighted Lexical、Embedding、Hybrid no graph、Hybrid graph 的 Recall@5/MRR 分别为 0.5368/0.6130、0.5057/0.7311、0.5333/0.6617、0.5524/0.6971。Hybrid graph − no graph 为 +0.0191/+0.0354。Secondary RRF no graph 为 0.5490/0.7365，RRF graph 为 0.5451/0.6978；graph − no graph 为 -0.0038/-0.0387。

**INTERPRETATION。** Weighted 配置内的 graph 差值方向为正，而 RRF 配置内方向为负；融合方法会影响本次图信号的观察结果。RRF 仅用于稳健性讨论，不能被表述为预注册主比较的替代结论。

**LIMITATION。** 不从这些配置挑选单一“最优系统”，也不将 RRF 数值外推为一般融合规律。

## 7. ContextBuilder Diagnostics

**FORMAL OBSERVATION。** 两个 Weighted Hybrid 配置各有 48 条 Query，总预算均为 384000 字符。No graph 与 graph 的 budget used 分别为 272990、321821；GT evidence rendered 分别为 101/165、124/165；snippet count 为 425、533；truncated packages 为 20、24；graph-only snippets 为 0、166；retained but unrendered graph provenance 为 0、386。

**INTERPRETATION。** Graph 配置渲染了更多 GT evidence，同时使用更多预算、出现更多 package truncation。图来源被保留但未渲染的计数提醒后续设计关注预算和可见证据之间的关系。

**LIMITATION。** ContextBuilder diagnostics 只描述实际上下文渲染；不参与 Recall/MRR，也不测量下游 LLM 维护任务质量。

## 8. Cross-RQ Synthesis

**FORMAL OBSERVATION。** RQ2 的 Recall@5 与 MRR 方向不同；RQ3 和 RQ4 Weighted graph 比较均为小幅正差值；secondary RRF graph 比较为负差值。正式报告保留了正、负和相同结果。

**INTERPRETATION。** 论文可以将本系统表述为稳定 Symbol identity、项目结构检索和有界上下文构建的系统性集成与评估，而非新检索算法的发现。各信号对固定任务集合的作用具有配置依赖性。

**LIMITATION。** 跨 RQ 汇总不是新的聚合指标或事后统计检验。

## 9. Limitations

1. Formal English Test 只有 48 条，且是 frozen single-repo + controlled fixtures；外部项目泛化尚未验证。
2. Reference 是 silver reference；没有 human inter-annotator agreement（IAA）。Java limited audit 不等于全体 GT 已验证。
3. Chinese 不进入 English main result；不据 English 数值推断中文效果。
4. File 使用 coarse-grained relevance set；跨检索单元的相关性解释须保留这一边界。
5. Retrieval quality 不等于 downstream LLM maintenance quality；ContextBuilder 诊断也不是端到端维护成功率。
6. 没有 preregistered significance testing，也没有完成性能协议的重复计时，因此没有 latency/SLA conclusion。
7. Grade-2-only 预注册次级敏感性分析未被正式 artifact 独立物化，不能补算成此次结果。
8. `phase62_closure_identity` 是 `Phase62ClosureRecord.identity_hash`，不是 raw file SHA-256（QA-L-01 透明度说明）。

## 10. Thesis-ready Conclusions

**可进入论文正文的有界表述。** 在冻结的 48 条 English Test Query 和 17 项配置上，检索单元、检索信号及图扩展方向对 Recall@5 与 MRR 呈现不同的描述性结果。File 在本次粗粒度相关性集合中的 Recall@5 为 0.8906；BM25 与 E5 在 Recall@5 和 MRR 上方向不一致；Weighted Hybrid 加入 graph 后的两个主指标较 no-graph 分别增加 0.0191 和 0.0354。ContextBuilder 的 graph 配置渲染更多 GT evidence，同时使用更多预算并出现更多截断。这些观察仅适用于冻结语料、Reference 和 Query 集，不代表统计显著性或下游维护收益。

## 11. V3.2 Implications

**INTERPRETATION。** V3.2 如消费 `RetrievalService` 和 `ContextPackage`，应把检索排序指标与渲染证据指标分开记录，并继续保留 graph provenance、预算和截断信息。若将来评估维护任务效果，需另设端到端任务、人工判定和相应门槛；当前 Formal 结果不构成 V3.2 已开始或已验证的证据。

**状态。** V3.1 实验已完成；后续是论文素材校核、Release Gate 与 v3.1.0 发布。V3.2：**NOT STARTED**。
