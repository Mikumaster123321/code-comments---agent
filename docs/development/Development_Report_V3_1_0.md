# V3.1.0 Final Development Report

## 1. Executive Summary

V3.1.0 的主题是 **Project Intelligence / RAG**。本版本在 V3.0.1 的项目维护核心、
BYOK 与可选 Managed AI Access 基础上，完成项目级语料、词法/语义/图检索、混合融合、
上下文构建、增量索引，以及可审计 benchmark/evidence lifecycle。Formal RQ1–RQ4 已
在冻结 English Test 上完成，独立结果 QA 为 **PASS WITH NON-BLOCKING NOTES**，
解释判定为 **ACCEPT — CLAIM-BOUNDED**。

当前状态是 **RELEASE CANDIDATE / READY FOR DEEPSEEK FINAL RELEASE QA**。版本元数据
已准备为 `3.1.0`，但本报告不构成 Final Release Gate；release commit、tag 和 push 均
未创建。V3.2 Multi-Agent Collaboration **NOT STARTED**。

## 2. Version Goal and Scope

V3.1 的目标是在已有 Project Scanner、Graph、Snapshot 和 Analysis Engine 之上建立
可复用的 Project Intelligence 层，使维护任务能够：

- 以稳定 `SymbolId` 连接项目状态、检索结果和上下文证据；
- 在 File、Symbol、Chunk 三种单元上进行可比较检索；
- 组合 deterministic BM25、real multilingual E5 和有界 Graph expansion；
- 使用 Weighted Hybrid 主策略与 secondary RRF 对照；
- 在显式字符预算内构建可解释的 `ContextPackage`；
- 以冻结 Protocol、Reference、Dry Run 和 Formal artifact 支持可重现评估。

不在 V3.1 范围内：Multi-Agent runtime、planner、memory、handoff、Router、VS Code
integration、Vector DB、ANN service、远程 embedding service，以及端到端 autonomous
maintenance quality claim。

## 3. Baseline from V3.0.1

V3.0.1 提供稳定的项目维护基础与 AI access infrastructure：Scanner、Graph、Snapshot、
Analysis Engine、Provider/BYOK、Managed Access、Credits、Usage Metering 和 Admin
Operations。V3.1 Phase 0 进入时完整回归为 **414 passed**，offline LLM-contract smoke
为 **6 passed**。V3.1 保持 Gradio、BYOK、Managed Access 与 Credits 兼容，没有改变
现有 SQLite 数据合同或普通安装依赖。

## 4. Final Architecture

```text
Project Source
    -> code_maintenance
       ProjectScanner -> ProjectGraph -> ProjectSnapshot / SnapshotDiff
    -> project_intelligence
       CorpusBuilder -> BM25 / E5 -> Graph Expansion
       -> Weighted Hybrid or RRF -> ContextBuilder -> RetrievalService
       -> immutable ContextPackage
    -> experiments
       frozen configs -> runner -> metrics -> append-only evidence artifacts
```

生产依赖方向冻结为：

```text
experiments -> project_intelligence -> code_maintenance
```

`code_maintenance` 拥有项目状态与稳定身份；`project_intelligence` 拥有生产检索、融合、
索引和上下文合同；`experiments` 只负责 File/Chunk baseline、配置矩阵、指标、runner、
schema、eligibility 和 evidence artifact。生产模块不反向依赖实验实现。

面向未来消费者的公开边界是不可变 `RetrievalQuery`、`ContextPackage` 与
`RetrievalService.retrieve()`。它可以被后续 LLM 或 Agent 使用，但 V3.1 没有实现
Agent runtime。

## 5. Phase 0 — Architecture and Research Freeze

Phase 0 冻结了 Project Intelligence 范围、依赖方向、RQ1–RQ4、检索单元政策、
Embedding 独立 Provider、Graph relation/direction 语义、Context 与 Retrieval 分离、
真实语义模型准入条件、benchmark 原则和 V3.2 exclusion。研究设计要求完整报告正向、
负向、相同和反直觉结果，不允许事后将多个指标压缩为营销式 winner。

状态：Architecture **FROZEN**；Research Methodology **FROZEN**；Documentation Gate
**CLOSED**；blocking issue 0。

## 6. Phase 1 — Corpus and Symbol Content Model

Phase 1 建立 immutable `RetrievalDocument` 与 deterministic offline `CorpusBuilder`。
Corpus 从 authoritative Snapshot、项目根目录和现有语言 Adapter 构建 source-backed
symbol document；构建时重算文件 hash，和 Snapshot 不一致则 fail closed。稳定
`SymbolId` 沿用 V3 合同，不建立新的 retrieval-only identity。

实现覆盖 Python/Java symbol range、qualified name、signature、source text、content
hash、imports 与 metadata。Phase 1.1 完成 freshness、非法输入和一致性 hardening。
Final QA：**PASS WITH LOW NOTES**；完整回归增长到 **455 passed**。

## 7. Phase 2 — Deterministic BM25

Phase 2 实现标准库、内存式 BM25，冻结 `code-lexical-v1` tokenizer、`k1=1.5`、
`b=0.75`，以及“一份 `qualified_name` + 一份 `source_text`”的公平输入合同。实现处理
空 Query、未知 term、document frequency、IDF、长度归一化、输入顺序独立、确定性
排序与 tie-breaking。Phase 2.1 修复 public config mutability 后 Final QA 为
**PASS FOR PHASE 2 WITH LOW NOTES**；完整回归 **469 passed**。

## 8. Phase 3 — Embedding Foundation and Real E5

Phase 3.1 建立独立 `EmbeddingProvider`、credential-free fingerprint、向量验证、L2
normalization 和 exact in-memory cosine `SemanticIndex`。Deterministic fake provider
仅用于离线测试，不提供语义质量证据。

Phase 3.2 选择并冻结 `intfloat/multilingual-e5-base` revision
`d128750597153bb5987e10b1c3493a34e5a4502a`：768 维、query/passage prefix、
attention-mask-aware mean pooling、CPU float32 baseline。`transformers==4.56.2` 与
`torch==2.8.0` 保持在 Python 3.12.14 隔离可选环境，模型权重/cache 不进入仓库。
初始 QA 发现 truncation diagnostics 与 revision consistency 问题；Phase 3.2.1 关闭
Critical 1、Medium 1，并保留审计前后 truncation 证据。Final QA：
**PASS FOR PHASE 3 WITH LOW NOTES**；完整回归 **491 passed**。

## 9. Phase 4 — Graph Retrieval and Incremental Indexing

Graph expansion 只读取冻结 `CONTAINS` / `IMPORTS`，显式记录 `FORWARD` / `REVERSE`、
hop、seed 和 provenance，并限制 relation、cycle、duplicate、per-seed 与全局预算。
方向是 retrieval provenance，不修改 `ProjectGraph` relation 类型。

`RetrievalIndexIdentity` 绑定 project、Snapshot content hash、retrieval config 和可选
embedding fingerprint。`SnapshotDiff` 的 added/removed/changed/unchanged 分别映射为
add/delete/replace/reuse；未变化 semantic vector 无需 Provider call。Phase 4.1 关闭
traversal direction 与 unchanged lookup complexity 两项 finding，并验证 incremental 与
full rebuild 在文档、BM25、exact semantic ranking、metadata 和 identity 上等价。
Final QA：**PASS FOR PHASE 4 WITH LOW NOTES**；完整回归 **528 passed**。

## 10. Phase 5 — Hybrid Retrieval and ContextBuilder

Phase 5 以稳定身份合并 lexical、semantic 和 graph candidates。Weighted Hybrid 保留
各 score component 和 graph provenance，是后续 Formal 主融合策略；RRF 使用 branch
rank 与固定参数，作为可选对照。

`ContextBuilder` 负责 deterministic dedup、Hybrid rank / Graph adjacency ordering、
source-only snippet、字符预算与 oversized snippet truncation，并返回可观测 metadata。
Semantic failure 仅在存在 lexical branch 时允许显式 lexical-only degraded result；
Formal semantic evidence 不能以 degraded 状态通过。`RetrievalService` 最终返回不可变
`ContextPackage`。Final QA：**PASS FOR PHASE 5 WITH LOW NOTES**；完整回归
**576 passed**。

## 11. Phase 6 — Experiment Infrastructure

Phase 6.0 在实现 benchmark 之前冻结 Protocol 与 Addenda。Phase 6.1 建立隔离实验层：
File/Chunk baselines、17 项 frozen config、七项 retrieval metrics、runner、严格 schema、
canonical serialization、append-only artifacts、eligibility 和 credential/source marker
scan。后续 hardening 关闭 matrix/config binding、status derivation、authoritative rank、
privacy sanitization、semantic schema 和 reproducibility 等问题。

Phase 6.1 Final QA：**PASS FOR PHASE 6.1 WITH LOW NOTES**；完整回归
**607 passed**。

## 12. Dataset Freeze and Reference Lifecycle

冻结 corpus revision 为 `12391233daa2149ead4f451e920b2e0d8a1a6beb`。Dataset 将
该提交的 tracked Python/Java source 与版本化 controlled fixtures 组合，并冻结路径、
内容 hash、Query、GT、evidence、grade、rationale 和 source span。

最终数据组成：

| 项目 | 数量 |
| --- | ---: |
| Query | 72（English Test 48 / English Dev 12 / Chinese 12） |
| Drafted GT | 72/72 |
| Evidence | 134 |
| Grade 2 / Grade 1 | 72 / 62 |
| English Test language | Python 36 / Java 12 |
| English Test task types | 6 类，各 8 |

Reference 是 specification-anchored single-judge silver reference，没有第二位人类
标注者或 human IAA。Phase 6.2 的 readiness、Approval、Approval Decision、Closure、
Documentation Decision 和 closed Gate 按顺序物化；authority loader 只接受提交态字节，
身份或 provenance 不一致时 fail closed。

## 13. Java Audit

Formal Java Evidence Audit 执行 12/12：10 条结构化结果为 `SUPPORTS`；2 条由于外部
response contract failure 记录为 execution-level `CANNOT_ASSESS`，没有伪造成模型
verdict。两条随后由冻结源码 Resolution 关闭，且 `gt_or_grade_changed=false`。Java
limited audit 仅覆盖这 12 条，不能外推为全部 English、Python 或 Chinese GT 的独立
复核。

## 14. Phase 6.2 Closure

Reference Approval identity：
`e89ce78f4c7b27754b52cab1b9217b349f5e7a382423bd75eb44a2a1deafb5d8`。
方法论审查与 Final Data QA 均为 **PASS WITH NON-BLOCKING NOTES / ELIGIBLE**。
Phase 6.2 完整验证 hash、source resolution、provenance、Git authority、中文 coverage
绑定和 Java resolution，最终状态 **CLOSED**。该阶段全量回归为 **813 passed**。

透明度边界：`phase62_closure_identity` 指 `Phase62ClosureRecord.identity_hash`，不是
raw file SHA-256。

## 15. Phase 6.3 English Dev Dry Run

Dry Run 基于 execution revision
`f0f4d2da169a071c71a6099c1d106fc3fec23299`：12/12 English Dev × 17/17 configs =
204/204 query-config，全部 success；English Test 和 Chinese execution 都为 0。

| 证据 | Identity |
| --- | --- |
| English Dev artifact set | `08f753fe7e9cb24e29a38baa5057005203f09524d0d94a48c4fbd98c19c8715b` |
| DryRunReceiptV2 | `8383eb1c0e45ca68927cecc5170a18a0ae56cc62dcbf2e5b3ff53448073fff3e` |

17 项完整确定性复跑零不一致；schema、hash、leakage 与 archive ancestry 均通过。
Phase 6.3 **CLOSED**；该阶段完整回归为 **877 passed**。

## 16. Formal RQ1–RQ4 Execution

| 绑定项 | 值 |
| --- | --- |
| Formal execution revision | `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` |
| Result archive commit | `c3ee6ec1b7aa28c2539d2fe849d1f25268807677` |
| Artifact-set identity | `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` |
| Artifact-set file SHA-256 | `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` |
| Coverage | 48/48 English Test × 17/17 configs = 816/816 success |
| Failed / invalid / degraded | 0 / 0 / 0 |

RQ1 比较 File/Symbol/Chunk；RQ2 比较 BM25/E5；RQ3 比较 Graph OFF/ON 与四项
relation-direction ablation；RQ4 比较 Lexical、Embedding、Weighted Hybrid，并将 RRF
保留为 secondary robustness。检索指标在 ContextBuilder 前计算；两个 Weighted Hybrid
run 另外生成 `context-diagnostic-v1`，不参与 ranking 或 retrieval metrics。

## 17. Final Metrics and Quality Evidence

| RQ | Configuration | Recall@5 | MRR |
| --- | --- | ---: | ---: |
| RQ1 | File | 0.8906 | 0.7364 |
| RQ1 | Symbol | 0.5368 | 0.6130 |
| RQ1 | Chunk | 0.5836 | 0.6274 |
| RQ2 | BM25 | 0.5368 | 0.6130 |
| RQ2 | E5 | 0.5057 | 0.7311 |
| RQ3 | Graph OFF | 0.5333 | 0.6617 |
| RQ3 | Graph ON | 0.5524 | 0.6971 |
| RQ3 | CONTAINS/FORWARD | 0.5316 | 0.6600 |
| RQ3 | CONTAINS/REVERSE | 0.5542 | 0.7086 |
| RQ3 | IMPORTS/FORWARD | 0.5333 | 0.6617 |
| RQ3 | IMPORTS/REVERSE | 0.5333 | 0.6617 |
| RQ4 | Lexical | 0.5368 | 0.6130 |
| RQ4 | Embedding | 0.5057 | 0.7311 |
| RQ4 | Hybrid no graph | 0.5333 | 0.6617 |
| RQ4 | Hybrid graph | 0.5524 | 0.6971 |
| RQ4 | RRF no graph | 0.5490 | 0.7365 |
| RQ4 | RRF graph | 0.5451 | 0.6978 |

RQ2 的 Recall@5 与 MRR 方向不同；Weighted graph 相对 no graph 为
+0.0191/+0.0354，而 RRF graph 相对 no graph 为 -0.0038/-0.0387。正式材料完整保留
这些 trade-off，不宣称 statistically significant、best、winner 或全面提升。

ContextBuilder 诊断中，no-graph / graph 的 budget used 为 272990 / 321821，GT
evidence rendered 为 101/165 / 124/165，truncated packages 为 20 / 24。更多渲染
evidence 与更高预算/截断并存，不能解释为下游维护质量变化。

## 18. Independent QA and Results Interpretation

Independent Formal Results QA：**PASS WITH NON-BLOCKING NOTES**；Critical 0、
validity-blocking Medium 0；Thesis Result Interpretation **ELIGIBLE**。Formal
interpretation：**ACCEPT — CLAIM-BOUNDED**。

仓库收到 reviewer 结论元数据，但没有收到逐字解读原文。因此
`Formal_Results_Interpretation_V3_1_0.md` 和 Thesis Materials 明确区分 formal
observation、interpretation 与 limitation，并说明文字由冻结报告整理。四份 CSV 从
Formal artifact 确定性导出，可用 `scripts/export_formal_thesis_tables.py --check`
逐字节复核。

## 19. Test Evolution

以下数字均来自对应阶段报告，不把局部专项数量与全量回归混用：

| Milestone | Full regression |
| --- | ---: |
| V3.0.1 / V3.1 Phase 0 baseline | 414 passed |
| Phase 1 Corpus | 455 passed |
| Phase 2 BM25 hardening | 469 passed |
| Phase 3 real E5 hardening | 491 passed |
| Phase 4 Graph / Incremental | 528 passed |
| Phase 5 Hybrid / ContextBuilder | 576 passed |
| Phase 6.1 Benchmark Infrastructure | 607 passed |
| Phase 6.2 Final Closure | 813 passed |
| Phase 6.3 English Dev Dry Run | 877 passed |
| Formal result stage / current release candidate | 892 passed |

最近一次技术 Gate 记录：Production targeted **198 passed**、Experiment lifecycle
**240 passed**、full regression **892 passed**，Critical / Medium / Low = **0 / 0 / 0**。
本轮只修改发布文档与版本元数据；最终状态以本轮验证报告为准。

普通 `python -m pytest` 在当前 Anaconda Python 3.13.5 主机于
`_pytest.debugging -> pdb -> rlcompleter` 加载时发生 segmentation fault；
`python -m pytest -p no:debugging` 是该主机的已验证完整回归命令。该宿主插件问题发生
在测试收集前，不作为 repository regression。

## 20. Known Issues and Limitations

- Formal English Test 仅 48 条，数据为 single frozen repository + controlled fixtures。
- Reference 是 single-judge silver reference，没有 human IAA。
- Python 36 条、Java 12 条；Java audit 为有限覆盖。
- Chinese coverage 不进入 English 主结果。
- File 使用 coarse-grained relevance mapping，不能据其数值推断精确定位更优。
- 不完整未判定池和构造 fixtures 限制绝对指标与外部泛化。
- 仅一个冻结 E5 模型与单一 CPU float32 环境。
- Deterministic rerun 不等于统计独立重复；未做 preregistered significance testing。
- Grade-2-only 次级敏感性分析和 30 次 timing protocol 未执行。
- Retrieval quality 与 ContextBuilder diagnostics 不等于 downstream LLM maintenance quality。
- 不作生产 latency、scalability 或 SLA 声明。

## 21. Release Readiness

V3.1 生产功能、实验执行、Formal artifact、独立 QA 和 claim-bounded interpretation 已
完成。README、Version History、Thesis Materials、Release Notes 与文档索引已进入最终
一致性校核。冻结 Formal run、artifact set、metrics、Query、GT、Grade、Evidence、
DryRunReceipt、Reference Approval 和 Phase 6.2 Closure 不在本轮修改范围内。

本轮目标状态：**RELEASE DOCUMENTATION READY FOR DEEPSEEK FINAL QA**。这不是
release approval；下一步由 DeepSeek V4.1 Flash 执行 Final Release QA，并在通过后
按用户授权处理 release commit/tag/push。

## 22. Next Version

V3.2 未来主题是 **Controlled Multi-Agent Collaboration**。可能的研究对象包括
Coordinator / Planner、Code Understanding Agent、Review Agent、Documentation Agent、
Refactor Agent 与 Test / Validation Agent，但这些都不是 V3.1 已实现能力。

当前状态：V3.1.0 **READY FOR DEEPSEEK FINAL RELEASE QA**；V3.2 **NOT STARTED**。
