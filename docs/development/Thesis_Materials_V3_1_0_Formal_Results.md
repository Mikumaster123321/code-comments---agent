# V3.1.0 Project Intelligence / RAG 论文写作素材包

<!-- release-state: V3.1.0 RELEASED -->

## 0. 文档定位与冻结身份

本文件是可直接用于论文写作的 **V3.1 事实、表格、图表与论证边界素材包**，不是
最终毕业论文。它不包含学校封面、致谢、最终目录或参考文献格式，也不替代论文作者
对章节结构和表达的最终决定。

正式结果来自冻结的 [Formal RQ1–RQ4 结果报告](Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)
及其 [artifact set](../experiments/audits/phase64_formal_english_test/artifact_set.json)：

| 绑定项 | 冻结值 |
| --- | --- |
| Formal result archive commit | `c3ee6ec1b7aa28c2539d2fe849d1f25268807677` |
| Formal execution revision | `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` |
| Artifact-set canonical identity | `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` |
| Artifact-set file SHA-256 | `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` |
| Independent Formal Results QA | `PASS WITH NON-BLOCKING NOTES` |
| Critical / validity-blocking Medium | `0 / 0` |
| Formal interpretation | `ACCEPT — CLAIM-BOUNDED` |

正式解读边界见 [Formal Results Interpretation](../experiments/Formal_Results_Interpretation_V3_1_0.md)。
仓库只收到 reviewer 结论元数据，没有收到逐字解读原文；因此本素材包的解释文字依据
冻结报告整理，不冒充 reviewer 原话。

## 1. 建议论文章节结构

1. 研究背景与问题定义
2. V3.1 Project Intelligence 总体架构
3. Corpus、Symbol identity 与检索表示
4. BM25、E5、Graph 与融合检索设计
5. ContextBuilder 与增量索引
6. Benchmark、Reference 与实验协议
7. RQ1–RQ4 结果
8. ContextBuilder 诊断与综合讨论
9. Threats to Validity
10. V3.1 贡献与 V3.2 过渡

## 2. 研究背景与目标

**可直接用于正文。** 传统单文件代码生成或问答难以稳定利用项目范围内的符号身份、
跨文件依赖与历史快照。V3.1 的目标是在既有项目扫描、图和快照能力上构建
Project Intelligence / RAG 层：将项目源代码转换为带稳定身份的检索语料，组合词法、
语义和图结构信号，最后在显式预算内生成可追踪的上下文证据。该层服务于项目级代码
理解、代码检索和维护任务的上下文准备，而不是通用知识库问答，也不是多智能体运行时。

V3.1 的研究贡献边界是“面向软件维护的系统性集成与受控实证验证”，而不是发明新的
BM25、embedding 或图算法。核心研究问题覆盖检索单元、词法与语义策略、图信号和
融合策略；增量索引与 ContextBuilder 作为工程与诊断证据单独报告。

## 3. 系统架构

```text
Project Source
    -> ProjectScanner / ProjectGraph / ProjectSnapshot
    -> CorpusBuilder / stable SymbolId / RetrievalDocument
    -> BM25 + real E5 + bounded Graph expansion
    -> Weighted Hybrid (primary) or RRF (secondary)
    -> ContextBuilder
    -> immutable ContextPackage
    -> future LLM / maintenance-task consumer
```

### Table 1 — V3.1 architecture/components

| 层 | 主要组件 | 责任与边界 |
| --- | --- | --- |
| Project core | Scanner、Graph、Snapshot、`SymbolId` | 提供确定性项目状态、身份和 `CONTAINS` / `IMPORTS` 关系 |
| Corpus | `CorpusBuilder`、`RetrievalDocument` | 从 authoritative Snapshot 与语言 Adapter 生成 source-backed symbol corpus；hash 不一致时 fail closed |
| Lexical | BM25、`code-lexical-v1` tokenizer | 离线、确定性、可解释的词法基线 |
| Semantic | `EmbeddingProvider`、real multilingual E5、exact cosine index | 独立于聊天 Provider；固定模型 revision、维度、归一化和 fingerprint |
| Graph | bounded expansion、relation/direction provenance | 只读现有 `CONTAINS` / `IMPORTS`；限制 hop、per-seed 和全局预算 |
| Index | `RetrievalIndexIdentity`、incremental update | 绑定 snapshot/config/fingerprint；added/removed/changed/unchanged 映射为 add/delete/replace/reuse |
| Fusion | Weighted Hybrid、RRF | Weighted 为主策略；RRF 只作 secondary robustness comparison |
| Context | `ContextBuilder`、`ContextPackage` | 去重、排序、source snippet、字符预算、截断和 provenance；不拥有 prompt 或 Agent plan |
| Evaluation | `experiments/`、schema、runner、artifact lifecycle | 隔离 File/Chunk baseline、指标、Dry Run、Formal artifacts；生产层不依赖实验层 |

生产依赖方向为 `experiments -> project_intelligence -> code_maintenance`。V3.1 没有
实现 Coordinator、Planner、Agent memory、handoff 或多智能体协作运行时。

## 4. Project Intelligence 与检索表示

### 4.1 Stable Symbol identity

**可直接用于正文。** V3.1 复用 V3 已冻结的 `SymbolId`，没有建立第二套检索身份。
稳定身份贯穿 Snapshot、Corpus、Graph、RetrievalHit 和 Context evidence，使相同代码
实体能在结构关系、排名结果与上下文证据之间被确定性关联。`content_hash` 负责新鲜度，
但不是普通身份的一部分。

### 4.2 Symbol / File / Chunk

- **Symbol** 是生产检索的主要单元，提供语义边界、细粒度定位和图关联。
- **File** 保留文件级上下文，并作为 RQ1 的 coarse-grained 对照。
- **Character Chunk** 是实验对照与无符号/超大内容的回退单元，不是默认代码表示。

三种单元共享冻结数据、Query、BM25 参数、`top_k` 与证据映射，但 File 的相关性集合
天然更粗。因而 RQ1 数值不能被解释为 File 对下游精确定位或维护任务普遍更优。

## 5. BM25 设计

**可直接用于正文。** 词法基线使用标准库内存实现，冻结 tokenizer
`code-lexical-v1`、`k1=1.5`、`b=0.75`，检索文本为一份 `qualified_name` 加一份
`source_text`。实现覆盖 document frequency、IDF、长度归一化、空 Query、未知词、
输入顺序独立和确定性 tie-breaking。BM25 完全离线，不调用 LLM 或远程服务。

## 6. E5 Embedding 设计

**可直接用于正文。** 正式语义检索使用 `intfloat/multilingual-e5-base`，固定 revision
`d128750597153bb5987e10b1c3493a34e5a4502a`、768 维、query/passage prefix、
attention-mask-aware mean pooling、CPU float32 和 L2 normalization。模型运行位于隔离
可选环境；模型权重和 cache 不进入仓库。Embedding fingerprint 不含 Credential，且
模型、维度或归一化变化都会阻止旧向量被静默复用。测试用 fake provider 只证明合同和
确定性，不支持 RQ2/RQ4 的语义质量结论。

## 7. Graph retrieval 设计

Graph expansion 只读冻结 `ProjectGraph` 的 `CONTAINS` 与 `IMPORTS`。每个候选保留
seed、relation、direction、hop 与 node identity；`FORWARD` 始终表示
`edge.source -> edge.target`，`REVERSE` 表示相反方向。扩展受 hop、关系白名单、
per-seed 和全局节点预算限制，并处理 cycle 与 duplicate。方向是检索 provenance，
不是新的 Graph relation。

RQ3 主比较为 Graph OFF / ON；次级消融分别保留 `CONTAINS/FORWARD`、
`CONTAINS/REVERSE`、`IMPORTS/FORWARD` 和 `IMPORTS/REVERSE`，不能把依赖方和
被依赖方合并成一个无方向信号。

## 8. Hybrid / RRF 设计

Weighted Hybrid 以稳定文档身份合并 BM25、cosine 与 Graph 候选，并保留各分量、
权重和 provenance，是 RQ3/RQ4 的预注册主融合策略。RRF 基于分支排名和固定
`rrf_k` 进行融合，只是 **secondary robustness comparison**；其数值不得替代或与
Weighted 主比较混合成单一结论。

## 9. ContextBuilder 设计

`ContextBuilder` 与 retrieval ranking 分离。它按确定性顺序去重和组装 source-backed
snippet，保留 Hybrid rank 与 Graph adjacency，执行显式字符预算和 oversized snippet
截断，并返回 budget、truncation、rendered evidence 与 provenance metadata。
`ContextPackage` 是不可变输出，可供未来 LLM 或 V3.2 使用；本阶段不包含 prompt
模板、任务规划、Agent memory 或端到端维护质量评估。

## 10. Incremental indexing

`RetrievalIndexIdentity` 绑定 project ID、Snapshot content hash、retrieval config hash
和可选 embedding fingerprint。Snapshot diff 的 added、removed、changed、unchanged
分别映射为 add、delete、replace、reuse；未变化语义向量不重新调用 Provider。实现以
全量重建等价性测试验证文档身份、BM25、exact semantic ranking、metadata 与 index
identity。相关性能记录属于工程证据，不是正式 RQ1–RQ4 主结果，也不支持生产 SLA。

## 11. Benchmark construction

### Table 2 — Dataset composition

| 项目 | 数量 / 状态 | 用途 |
| --- | ---: | --- |
| Frozen Query | 72 | 48 English Test + 12 English Dev + 12 Chinese coverage |
| English Test | 48 | 正式 RQ1–RQ4 主结果；Python 36、Java 12 |
| English Dev | 12 | Phase 6.3 Dry Run；不进入 Formal 结果 |
| Chinese coverage | 12 | 自然独立性/语义对齐覆盖；不进入 English 主结果 |
| Task types | 6 | BL、CF、DQ、FL、MT、SL，各 8 条 English Test |
| Drafted GT | 72/72 | specification-anchored single-judge silver reference |
| Evidence | 134 | Grade 2 / Grade 1 = 72 / 62 |
| Java audit | 12 executed | 10 structured `SUPPORTS`；2 execution-level `CANNOT_ASSESS` 后由冻结源码 resolution 处理 |
| Formal configs | 17/17 | RQ1–RQ4 主配置与 secondary RRF |
| Formal pairs | 816/816 | 48 English Test × 17 configs，全部 success |

数据由冻结 self-repository commit 与版本化 Python/Java controlled fixtures 组成。
Self-repository 只纳入冻结提交中的 tracked `.py` / `.java` 文件；未跟踪文件、cache、
模型和生成结果被排除。该设计提供现实跨文件结构与受控边界案例，但不是多仓库外部
泛化样本。

## 12. Query / GT / evidence composition

Query 覆盖 bug localization、cross-file understanding、dependency questions、feature
localization、maintenance tasks 和 symbol lookup。Ground Truth 使用规范锚定的
single-judge silver reference，绑定 evidence span、grade、rationale、source hash 与
Reference lifecycle。Phase 6.2 的 Approval、Decision、Closure 和 Documentation
Decision 在执行前物化并校验；没有第二位人类标注者，也没有 human IAA。

**QA-L-01 透明度说明。** `phase62_closure_identity` 是
`Phase62ClosureRecord.identity_hash`，不是 `phase62_closure.json` 的 raw file
SHA-256。

## 13. Experimental protocol

实验遵循冻结 [Protocol](../experiments/Experiment_Protocol_V3_1_0.md)、Addenda
[A](../experiments/Experiment_Protocol_Addendum_A_V3_1_0.md)、
[B](../experiments/Experiment_Protocol_Addendum_B_V3_1_0.md)、
[C](../experiments/Experiment_Protocol_Addendum_C_V3_1_0.md)、
[D](../experiments/Experiment_Protocol_Addendum_D_V3_1_0.md) 以及 Reference Lifecycle
Specification 与五份 Amendments。主指标为 Recall@5 和 MRR；扩展披露 Recall@1、
Recall@10、nDCG@5、Precision@5、Hit Rate@5。检索指标在 ContextBuilder 前计算。

Phase 6.3 先在 12 条 English Dev 上执行 17 配置，完成 204/204 query-config Dry Run；
Formal 阶段再独立执行 48 条 English Test。Formal 结果的 deterministic rerun 比较
8 个代表配置、384 条 Query，ranking、score、metrics 与 identity mismatch 均为 0；
leakage evidence 确认 English Dev 与 Chinese execution 均为 0。

## 14. RQ1–RQ4 definitions

- **RQ1 — Retrieval Unit：** 在相同词法条件下比较 File、Symbol、Chunk。
- **RQ2 — Retrieval Strategy：** 在 Symbol 单元与 Graph OFF 下比较 BM25 与 real E5。
- **RQ3 — Graph Signal：** 比较 Weighted Hybrid 的 Graph OFF / ON，并进行 relation-direction 消融。
- **RQ4 — Hybrid Retrieval：** 比较 Lexical、Embedding、Weighted Hybrid no graph / graph；RRF 为次级稳健性证据。

## 15. Formal experimental results

### Table 3 — RQ1–RQ4 Formal main results

| RQ | Configuration | Recall@5 | MRR | 地位 |
| --- | --- | ---: | ---: | --- |
| RQ1 | File | 0.8906 | 0.7364 | primary |
| RQ1 | Symbol | 0.5368 | 0.6130 | primary |
| RQ1 | Chunk | 0.5836 | 0.6274 | primary |
| RQ2 | BM25 | 0.5368 | 0.6130 | primary |
| RQ2 | E5 | 0.5057 | 0.7311 | primary |
| RQ3 | Graph OFF | 0.5333 | 0.6617 | primary |
| RQ3 | Graph ON | 0.5524 | 0.6971 | primary |
| RQ3 | CONTAINS/FORWARD | 0.5316 | 0.6600 | direction ablation |
| RQ3 | CONTAINS/REVERSE | 0.5542 | 0.7086 | direction ablation |
| RQ3 | IMPORTS/FORWARD | 0.5333 | 0.6617 | direction ablation |
| RQ3 | IMPORTS/REVERSE | 0.5333 | 0.6617 | direction ablation |
| RQ4 | Lexical | 0.5368 | 0.6130 | primary |
| RQ4 | Embedding | 0.5057 | 0.7311 | primary |
| RQ4 | Hybrid no graph | 0.5333 | 0.6617 | primary |
| RQ4 | Hybrid graph | 0.5524 | 0.6971 | primary |
| RQ4 | RRF no graph | 0.5490 | 0.7365 | secondary robustness |
| RQ4 | RRF graph | 0.5451 | 0.6978 | secondary robustness |

原始精度与可机器复核数据见 [main CSV](../experiments/Formal_Result_Table_RQ1_RQ4_V3_1_0.csv)。

## 16. Formal result interpretation

### RQ1

File、Symbol、Chunk 的 Recall@5/MRR 分别为 0.8906/0.7364、0.5368/0.6130、
0.5836/0.6274。File 使用 coarse-grained relevance mapping，较高覆盖不能外推为更精确
的 symbol localization 或更好的下游维护质量。

### RQ2

E5 相对 BM25 的 Recall@5 差值为 -0.0311，MRR 差值为 +0.1181。两个主指标方向
不同，必须并列报告，不能构造单一 winner。

### RQ3

Graph ON 相对 OFF 的 Recall@5/MRR 差值为 +0.0191/+0.0354。消融中
CONTAINS/REVERSE 为 0.5542/0.7086；IMPORTS 两个方向在这两个总体指标上与 Graph
OFF 相同。该结果只提示配置与方向依赖性，不证明因果机制或 IMPORTS 普遍无效。

### RQ4

Weighted Hybrid graph 相对 no graph 为 +0.0191/+0.0354。Secondary RRF graph
相对 no graph 为 -0.0038/-0.0387。相反方向说明图信号的观察结果依赖融合方式；RRF
不替代预注册 Weighted 主比较。

### Cross-RQ synthesis

正式结果同时保留正向、负向与相同数值。可支持的结论是：在冻结 benchmark 中，
检索粒度、语义信号、图方向和融合方式与观察到的 Recall@5/MRR trade-off 相关；不可
据此宣称“全面提升”“显著优于”“最佳配置”或跨项目普遍规律。

## 17. ContextBuilder diagnostics

### Table 4 — Extended metrics

Recall@1、Recall@10、nDCG@5、Precision@5、Hit Rate@5，以及 Python/Java 和六种
task type 的分群值不在本文件重复抄写，统一引用
[Extended metrics CSV](../experiments/Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv)。
Java `n=12`、各任务类型 `n=8`，仅用于完整披露，不用于选择 favourable subset。

### Table 5 — ContextBuilder diagnostics

| 诊断项 | Hybrid no graph | Hybrid graph |
| --- | ---: | ---: |
| budget used / total | 272990 / 384000 | 321821 / 384000 |
| budget utilization | 0.7109 | 0.8381 |
| GT evidence rendered / total | 101 / 165 | 124 / 165 |
| snippet count | 425 | 533 |
| truncated packages | 20 | 24 |
| graph-only rendered snippets | 0 | 166 |
| retained but unrendered graph provenance | 0 | 386 |

Graph 配置多渲染 23 个 GT evidence，同时多使用 48831 个字符并多出现 4 个 package
truncation。该诊断只描述上下文渲染，不参与 ranking、Recall 或 MRR，也没有测量下游
LLM 维护质量。机器数据见 [ContextBuilder CSV](../experiments/Formal_ContextBuilder_Diagnostics_V3_1_0.csv)。

## 18. Threats to validity / limitations

1. Formal English Test 只有 48 条，数据为 single frozen repository + controlled fixtures；没有外部多仓库泛化验证。
2. Reference 是 specification-anchored single-judge silver reference；没有第二位人类标注者或 human IAA。
3. Python 36 条、Java 12 条；Java limited audit 不能外推为全部 GT 已被独立验证。
4. Chinese coverage 不进入 English 主结果；不得从 English 数值推断中文效果。
5. File 使用 coarse-grained relevance mapping，跨单元比较须保留相关性粒度差异。
6. 不完整未判定池可能压低或扭曲绝对指标；正式结论以冻结 Reference 为边界。
7. 只评估一个冻结 E5 模型与单一 CPU float32 环境，没有跨模型/跨硬件复现。
8. Retrieval quality 不等于 downstream LLM maintenance quality；ContextBuilder diagnostics 也不是任务成功率。
9. 没有 preregistered significance testing；deterministic rerun 不等于统计独立重复样本。
10. Grade-2-only 次级敏感性分析与 30 次 timing protocol 未执行，不作 latency、scalability 或 SLA 结论。

## 19. V3.1 contribution summary

**可直接用于正文。** V3.1 的工程贡献包括：基于 stable `SymbolId` 的项目级检索
语料；确定性 BM25 与冻结 real E5；有界、可追踪的 Graph expansion；带身份验证的
增量索引；可解释 Weighted Hybrid 与 secondary RRF；在字符预算内生成证据的
ContextBuilder；以及从 Protocol、Reference、Dry Run 到 Formal artifact 的可审计
生命周期。研究贡献是使用冻结的 72 条 Query 设计与 17 项正式配置，对检索单元、
策略、图信号和融合方式进行受控、claim-bounded 的比较。

## 20. Figure / table plan

| 编号 | 建议标题 | 数据源 |
| --- | --- | --- |
| Table 1 | V3.1 Project Intelligence 架构组件与责任 | 本文件 §3 |
| Table 2 | 冻结数据集、Query 与 Evidence 组成 | 本文件 §11；Dataset Specification |
| Table 3 | RQ1–RQ4 Formal 主结果 | [Main CSV](../experiments/Formal_Result_Table_RQ1_RQ4_V3_1_0.csv) |
| Table 4 | 扩展指标与语言/任务分群 | [Extended CSV](../experiments/Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv) |
| Table 5 | ContextBuilder 预算与 Evidence 诊断 | [Context CSV](../experiments/Formal_ContextBuilder_Diagnostics_V3_1_0.csv) |
| Figure 1 | V3.1 Project Intelligence / RAG architecture | 本文件 §3 的逻辑链 |
| Figure 2 | RQ1 File / Symbol / Chunk granularity comparison | [Figure data A](../experiments/Formal_Figure_Data_A_D_V3_1_0.csv) |
| Figure 3 | RQ2 BM25 与 E5 comparison | [Figure data B](../experiments/Formal_Figure_Data_A_D_V3_1_0.csv) |
| Figure 4 | RQ3 Graph OFF/ON 与方向消融 | [Figure data C](../experiments/Formal_Figure_Data_A_D_V3_1_0.csv) |
| Figure 5 | RQ4 Weighted 与 secondary RRF comparison | [Figure data D](../experiments/Formal_Figure_Data_A_D_V3_1_0.csv) |
| Figure 6 | ContextBuilder budget / evidence diagnostics | [Context CSV](../experiments/Formal_ContextBuilder_Diagnostics_V3_1_0.csv) |

图 2–5 应同时展示 Recall@5 与 MRR，避免把两项指标压成单一排序。Figure 5 必须在
图例或图题中标明 RRF 为 secondary robustness comparison。Figure 6 只能使用现有
CSV 字段，不补造下游质量、延迟或显著性数据。

## 21. 关键术语与 claim boundary

| 术语 | 本项目含义 |
| --- | --- |
| Project Intelligence | 从 Snapshot、Symbol、Graph 与检索信号构建项目级代码证据的能力层 |
| Stable `SymbolId` | 跨 Corpus、Graph、ranking 和 context 共用的确定性代码实体身份 |
| Silver reference | 有规范与 evidence 锚点、但没有双人独立标注和 IAA 的参考集合 |
| Weighted Hybrid | RQ3/RQ4 的主融合策略，保留 lexical、semantic、graph 分量 |
| RRF | 基于分支名次的次级稳健性对照，不替代主比较 |
| ContextPackage | 有顺序、来源、预算和截断 metadata 的不可变上下文输出 |
| Claim-bounded | 只陈述冻结数据、配置和指标直接支持的观察，不作统计或外部泛化扩张 |

允许使用 `observed`、`descriptive comparison`、`在冻结 benchmark 中表现出` 和
`trade-off`。禁止把本结果写成 `best`、`winner`、`significantly better`、`全面领先`
或“检索质量证明下游维护质量提升”。

## 22. V3.2 transition motivation

V3.1 已提供稳定的 `RetrievalQuery -> ContextPackage` 边界、Graph provenance 与预算
诊断，为未来受控多智能体维护提供一致证据输入。V3.2 可研究 Coordinator / Planner、
Code Understanding Agent、Review Agent、Documentation Agent、Refactor Agent 和
Test / Validation Agent，但这些均是未来候选方向，**不是 V3.1 已实现能力**。

若 V3.2 启动，应把 retrieval ranking、rendered evidence 与实际维护任务质量分别记录，
并为端到端输出建立新的任务集、人工判定和 Gate。当前状态：V3.1.0 **RELEASED**；
V3.1.1 **FULLY RELEASED**；V3.1.2 与 V3.2 均 **NOT STARTED**。

## 23. 复核入口

- 数据与实验总索引：[V3.1 Experiment Evidence Index](../experiments/README.md)
- 发布文档总索引：[V3.1 Documentation Index](../release/README.md)
- CSV 确定性导出脚本：[export_formal_thesis_tables.py](../../scripts/export_formal_thesis_tables.py)（`--check`）
- UTF-8 纯文本配套材料：[Thesis_Materials_V3_1_0_Formal_Results.txt](Thesis_Materials_V3_1_0_Formal_Results.txt)
- 当前 release 状态：`RELEASED`；release commit `8813e4c2fb0dc07f38c2013d520441bf399dcbc4`；annotated tag `v3.1.0`；branch / tag 已 push 并完成 remote verification
