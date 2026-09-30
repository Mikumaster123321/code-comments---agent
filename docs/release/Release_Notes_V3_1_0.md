# V3.1.0 Release Notes

**Status:** Released

**Version:** `3.1.0`

**Theme:** Project Intelligence / RAG

V3.1.0 在现有项目维护核心、BYOK 与可选 Managed AI Access 之上增加项目级代码
检索与上下文证据层，并完成冻结 Protocol 下的 Formal RQ1–RQ4 evaluation。正式
release commit 为 `8813e4c2fb0dc07f38c2013d520441bf399dcbc4`，tag 为 `v3.1.0`；
branch 与 tag 已 push 并完成 remote verification。

## Highlights

- 以稳定 `SymbolId` 贯穿 Snapshot、Corpus、Graph、RetrievalHit 与 Context evidence
- File / Symbol / Character Chunk 三种可比较 retrieval unit
- 离线 deterministic BM25 与可选本地 real multilingual E5
- 有界、可解释的 `CONTAINS` / `IMPORTS` Graph expansion
- SnapshotDiff 驱动的 incremental indexing 与严格 index identity
- Weighted Hybrid 主融合策略与 secondary RRF robustness comparison
- 确定性 ContextBuilder、显式字符预算、截断和 provenance metadata
- Protocol、Dataset、Reference、Dry Run 与 Formal artifact 的可审计 lifecycle
- 当前完整离线回归基线：**892 passed**

## New Architecture

```text
Project Source
    -> Scanner / Graph / Snapshot
    -> CorpusBuilder / stable SymbolId
    -> BM25 / E5 / Graph Expansion
    -> Weighted Hybrid or RRF
    -> ContextBuilder -> immutable ContextPackage
```

依赖方向保持 `experiments -> project_intelligence -> code_maintenance`。
`project_intelligence/` 复用 V3 project core；`experiments/` 只在外层调用生产能力，
生产模块不依赖实验实现。`RetrievalService.retrieve()` 是未来 LLM / Agent 消费
`ContextPackage` 的边界，但 V3.1 不包含 Agent runtime。

## Retrieval Capabilities

- **Corpus / identity:** `CorpusBuilder` 从 authoritative Snapshot 与语言 Adapter 构建
  immutable `RetrievalDocument`；source hash 不一致时 fail closed。
- **Lexical:** 标准库 BM25，冻结 `code-lexical-v1`、`k1=1.5`、`b=0.75` 与确定性排序。
- **Semantic:** `intfloat/multilingual-e5-base` 固定 revision、768 维、query/passage
  prefix、CPU float32 与 L2 normalization；模型和 cache 不随仓库分发。
- **Units:** Symbol 是生产主要单元；File 保留粗粒度上下文；Chunk 是实验对照和回退。
- **Index:** index identity 绑定 project、Snapshot、config 与 embedding fingerprint；
  added/removed/changed/unchanged 对应 add/delete/replace/reuse。

## Context and Graph

Graph retrieval 仅使用冻结 `CONTAINS` / `IMPORTS`，并显式保留 relation、direction、
hop、seed 和 node provenance。Traversal direction 是 retrieval provenance，不是新的
Graph relation；扩展受 hop、关系、per-seed 和全局预算限制。

Weighted Hybrid 保留 lexical、semantic、graph score component。RRF 保留为次级对照，
不替代正式 Weighted 主比较。ContextBuilder 在 ranking 之后执行去重、排序、source
snippet 组装、预算与截断，并返回可观察 metadata。

## Experiment Validation

冻结数据共 72 条 Query：48 English Test、12 English Dev、12 Chinese coverage。
Phase 6.3 在 English Dev 上完成 12/12 × 17/17 = 204/204 Dry Run；Formal 阶段仅执行
48 条 English Test，完成 48/48 × 17/17 = **816/816** query-config，全部 success，
failed / invalid / degraded 为 0。Chinese coverage 不进入 English 主结果。

| 绑定项 | 值 |
| --- | --- |
| Formal result archive commit | `c3ee6ec1b7aa28c2539d2fe849d1f25268807677` |
| Formal execution revision | `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` |
| Artifact-set identity | `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` |
| Artifact-set file SHA-256 | `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` |
| Independent Formal Results QA | `PASS WITH NON-BLOCKING NOTES` |
| Formal interpretation | `ACCEPT — CLAIM-BOUNDED` |

## Formal RQ Summary

| RQ | Comparison | Recall@5 | MRR |
| --- | --- | ---: | ---: |
| RQ1 | File | 0.8906 | 0.7364 |
| RQ1 | Symbol | 0.5368 | 0.6130 |
| RQ1 | Chunk | 0.5836 | 0.6274 |
| RQ2 | BM25 | 0.5368 | 0.6130 |
| RQ2 | E5 | 0.5057 | 0.7311 |
| RQ3 | Graph OFF | 0.5333 | 0.6617 |
| RQ3 | Graph ON | 0.5524 | 0.6971 |
| RQ4 | Lexical | 0.5368 | 0.6130 |
| RQ4 | Embedding | 0.5057 | 0.7311 |
| RQ4 | Hybrid no graph | 0.5333 | 0.6617 |
| RQ4 | Hybrid graph | 0.5524 | 0.6971 |
| RQ4 secondary | RRF no graph | 0.5490 | 0.7365 |
| RQ4 secondary | RRF graph | 0.5451 | 0.6978 |

RQ3 方向消融的 Recall@5/MRR：CONTAINS/FORWARD 0.5316/0.6600、
CONTAINS/REVERSE 0.5542/0.7086、IMPORTS/FORWARD 0.5333/0.6617、
IMPORTS/REVERSE 0.5333/0.6617。

结果是冻结 benchmark 上的 descriptive comparison。RQ2 的 Recall@5 和 MRR 方向
不同；Weighted graph 比较为正差值，而 secondary RRF graph 比较为负差值。V3.1 不
据此宣称 significant、best、winner、全面领先或全面提升。

## Known Limitations

- 单一冻结仓库与 controlled fixtures；Formal English Test 仅 48 条。
- Specification-anchored single-judge silver reference；没有 human IAA。
- Python 36 条、Java 12 条；Java limited audit 不代表所有 GT 已被独立验证。
- Chinese coverage 不进入 English 主结果。
- File 使用 coarse-grained relevance mapping；跨 unit 数值不能直接解释为精确定位优劣。
- 不完整未判定池、单一 E5 模型和单一 CPU float32 环境限制外推。
- 未执行 preregistered significance testing、Grade-2-only 次级敏感性分析和 30 次 timing protocol。
- Retrieval quality 与 ContextBuilder diagnostics 不等于 downstream LLM maintenance quality。
- 不作 production latency、scalability 或 SLA 声明。

## Compatibility Notes

- `code_maintenance.__version__` 的正式发布值为 `3.1.0`。
- V3.0.1 Gradio、BYOK、Managed Access、Credits、Admin Operations 和 SQLite 数据合同保持兼容。
- `requirements.txt` 与普通安装路径不变；real E5 使用 `requirements-embedding.txt` 隔离可选环境。
- 生产核心不需要 Vector DB、ANN service、模型 cache 或远程 embedding service。

## Upgrade / Migration Notes

**No breaking migration is required.** 现有 V3.0.1 用户无需迁移 Credits、Managed
Access 或 Workspace 数据。若使用 V3.1 real E5，需显式创建可选 embedding 环境并按
冻结说明准备本地模型；默认路径不会自动下载模型，也不会把源代码发送到远程 embedding
服务。

## Documentation

- [V3.1 documentation index](README.md)
- [Final Development Report](../development/Development_Report_V3_1_0.md)
- [Experiment Evidence Index](../experiments/README.md)
- [Formal Results Report](../development/Development_Report_V3_1_0_Phase_6_4_Formal_RQ1_RQ4_Results.md)
- [Thesis Materials Package](../development/Thesis_Materials_V3_1_0_Formal_Results.md)

## Next

V3.1.x maintenance continues。V3.1.1 首先处理 Workflow & Developer Experience
Optimization；V3.2 **Controlled Multi-Agent Collaboration** 仍为 **NOT STARTED**。
