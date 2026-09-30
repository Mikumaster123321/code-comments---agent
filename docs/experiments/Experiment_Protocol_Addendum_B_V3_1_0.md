# V3.1.0 Phase 6 — Incremental Fixture SnapshotDiff Semantics Addendum B

## 1. 状态、权限与修正范围

- Addendum ID: `v3.1-phase6-protocol-addendum-b`
- Addendum version: `v1`
- Status: **FROZEN**
- Effective date: `2026-09-23`
- Nature: **normative correction / erratum**，不是新的研究问题或生产语义变更
- Review provenance: Grok 4.7 Incremental Fixture Semantics methodology review
- Applies to: `Experiment_Protocol_V3_1_0.md` §10.3，以及
  `Dataset_Query_GroundTruth_Specification_V3_1_0.md` §3.4、§13 中的对应增量计数

本附录只取代旧文档把 `direct edit set = 3/2/2` 当作 authoritative
`SnapshotDiff`，并推导 `changed + added = 5` 个新 embedding 文档或五次
embedding 调用的计数。原始数字和段落保留为历史冻结记录；其他 Protocol、
Dataset Specification 与 Addendum A 条款继续有效。

此前 Phase 6.1.3 的 annotation-lifecycle blocker 已解除，故旧的
`Phase 6.2A blocker=LIFTED` 是正确历史状态。后来 Phase 6.2A materialization
尝试发现独立的 incremental fixture specification conflict，并停止执行。
本附录解决该新冲突后，Phase 6.2A 可重新进入，但本轮不开始 materialization。

## 2. 三个正式术语与预期结果

**direct edit set** 指作者直接设计的叶子级源码编辑，不是 SnapshotDiff：

| Direct operation | Symbols | Count |
| --- | --- | ---: |
| changed | `Bin.put`, `Shelf.add`, `checksum` | 3 |
| added | `Bin.count`, `Shelf.label` | 2 |
| removed | `Bin.remove`, `Shelf.drop` | 2 |

**enclosing symbol effect** 指 `Bin` 与 `Shelf` 的类 Symbol 源码范围覆盖其
成员源码。成员修改、新增或删除改变了类源码片段及其 content hash，因此这两个
容器 Symbol 也成为 derived/container changes。它们不是额外人工编辑；
这里也不存在独立的 graph closure algorithm。

**authoritative SnapshotDiff** 只能由生产 `compare_snapshots(old, new)` 产生，
并由 `IncrementalIndexPlan` 与 `RetrievalIndex.update` 消费。对本 fixture，
冻结预期如下：

| SnapshotDiff category | Exact Symbols | Count |
| --- | --- | ---: |
| changed | `Bin`, `Bin.put`, `Shelf`, `Shelf.add`, `checksum` | 5 |
| added | `Bin.count`, `Shelf.label` | 2 |
| removed | `Bin.remove`, `Shelf.drop` | 2 |
| unchanged | 无 | 0 |

Phase 6.2A 的机械验证必须分别检查 direct edit set 的 `3/2/2` 和
authoritative SnapshotDiff 的 `5/2/2/0`，不能以直接编辑数代替真实 diff。
若实际生产输出不符合本 fixture 预期，应停止并核查 fixture 与证据，
不得修改生产算法来迎合旧计数。

## 3. Embedding 调用与等价性

`RetrievalIndex.update` 对 authoritative `changed ∪ added` 生成新 document
embeddings：changed 为 5 个、added 为 2 个，共 **7 个文档**。removed 与
unchanged 各产生 0 个 embedding 文档或调用。`embed_documents` 调用 **1 次**，
其单个 batch 含 **7 段文本**，对应：

```text
Bin
Bin.count
Bin.put
Shelf
Shelf.add
Shelf.label
checksum
```

上述批次是按 `SymbolId` 确定性排序的文档集合；验证时应检查文档身份、
文本数与批次数。旧文档的“五个新 embeddings / 五次调用”不再是本 fixture
的有效预期。增量更新与最终 Snapshot 的全量重建仍须按 Protocol §10.3
验证 index identity、文档与 content hash、BM25、Semantic 与最终检索结果等价。
本附录不构成 E5 性能或检索质量结果，也不授权提前运行 E5。

## 4. 生产语义与研究影响

本修正依从现有分层源码范围哈希语义。`Py/parser.py` 的类源码范围包含
成员源码；`code_maintenance/adapters.py` 为该范围生成 Symbol content hash；
`code_maintenance/snapshot.py` 的 `compare_snapshots` 按 Symbol 身份和状态
比较；`project_intelligence/index.py` 使用其 changed/added 集合进行更新。
parser、`SymbolId`、Snapshot、SnapshotDiff、`RetrievalIndex` 和生产 hashing
均 **UNCHANGED**。实验必须测量真实生产语义。

RQ1、RQ2、RQ3、RQ4 的方法均 **UNAFFECTED**。72-query allocation、Ground
Truth、metrics、Hybrid/Graph 配置、E5 identity、File/Symbol/Chunk baseline，
以及 route、intake、Java 三个主 fixture 均 **UNAFFECTED**。修正只影响增量
engineering fixture、其 mechanical validation、SnapshotDiff 预期计数、
新 embedding 文档计数及相关 performance/reuse evidence。不得创建 RQ5，
也不得据此声称任何 RQ 已获回答。

## 5. Source of Truth 与文档身份沿革

正式依据为 Experiment Protocol + Addendum A + Addendum B。Addendum A 只解释
annotation lifecycle/review；Addendum B 只修正 incremental fixture
SnapshotDiff semantics。在上述修正范围内，本附录优先于 Dataset Specification；
其余 Dataset Specification 内容仍按冻结版本执行。聊天记录不是执行依据。

以下均为文件原始 bytes 的 SHA-256。历史冻结文件仅增加指向本附录的醒目
引用，原有错误计数未删除或改写。引用改变了文件 bytes，因此旧哈希不能代表
当前文件：

| Document state | Commit / provenance | SHA-256 |
| --- | --- | --- |
| Protocol original freeze | `7a224c456f7615e4f4dbc79b1065755df3c8033f` | `ea08482fec6b0dfef4fe71089b14df1fca84a4276460cf92084c8a0e57070dbe` |
| Protocol before Addendum B (Addendum A reference present) | `e124c77037d8396601ce57d915babf1b7a416026` | `868309ca2127e8d1cbf7eeaa4ad2cb4b645b3b44831558f92bde40c82fb8b173` |
| Protocol with Addendum B references | this documentation correction | `132f74590b7973bc4b6b38586929ca19c819ad1e758630012e17b01e41f27df9` |
| Dataset Specification original freeze | `a532444c185d5984fe19b47017ea85ac228e0a62` | `3fb9a039a4fde7ef983218db09671424b0d412f054d6d5c39740b31a737b7d84` |
| Dataset Specification with Addendum B references | this documentation correction | `fddcf5993223ee86e3bc0a3d5cfcafec186325cf4a904534aeca1203a802a18d` |

本附录自身的 SHA-256 记录于 `PROJECT_CONTEXT.md`，避免在本文件内嵌入
自身哈希造成循环身份。未来 Phase 6.2A 应以当前 Git 文档及上述 precedence
执行，核对文件实际 bytes 后再建立其版本化文档身份；不得将历史哈希冒充
当前 reference-updated bytes。

## 6. 门禁状态

- Incremental Fixture Specification Conflict: **CLOSED / RESOLVED BY ADDENDUM B**
- Phase 6.2A blocker: **LIFTED AGAIN AFTER ADDENDUM B**
- Phase 6.2A: **ALLOWED BUT NOT STARTED**
- Dataset / Query / Ground Truth: **NOT CREATED / NOT CREATED / NOT CREATED**
- Phase 6.2 Gate: **OPEN**
- Phase 6.3: **NOT STARTED**
- Formal RQ1–RQ4: **NOT STARTED**
- V3.2: **NOT STARTED**
