# V3.1.0 Phase 6.4 Formal RQ1–RQ4 实验结果报告

## 判定与范围

**FORMAL RESULT。** 本轮从 `v3.1.0-dev` 初始 HEAD
`2749969cd3a2d4d6e1e8d81160eebd5fb360879b` 完整重新执行冻结 English Test：
48/48 Query × 17/17 配置 = 816/816 个唯一 query-config 组合。全部记录为
`success`，`failed=0`、`invalid=0`、`degraded=0`。未执行 English Dev 或 Chinese
benchmark，未复用此前失败 Formal attempt 的 ranking、metrics 或 artifact。

本报告严格记录冻结 Protocol 下的事实结果和描述性差值。未修改 Query、GT、
Grade、BM25、E5、Graph、Hybrid、RRF、ContextBuilder、权重或指标；未新增复合
分数或事后显著性检验。检索指标在 ContextBuilder 前计算，ContextBuilder
diagnostics 单独报告。

## 冻结身份、运行时与覆盖

| 项目 | FORMAL RESULT / 身份 |
| --- | --- |
| execution revision | `2749969cd3a2d4d6e1e8d81160eebd5fb360879b` |
| corpus revision | `12391233daa2149ead4f451e920b2e0d8a1a6beb` |
| matrix identity | `ce5a58783a68f7e20c0635d264fc19d119212604cee1ed80b4a6b25d49863a25` |
| Formal artifact-set canonical identity | `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3` |
| artifact-set file SHA-256 | `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41` |
| DryRunReceiptV2 identity | `8383eb1c0e45ca68927cecc5170a18a0ae56cc62dcbf2e5b3ff53448073fff3e` |
| E5 | `intfloat/multilingual-e5-base` @ `d128750597153bb5987e10b1c3493a34e5a4502a` |
| E5 fingerprint | `00528591f55523ebe4f440835075bf36979de9f52e70749d46e7bf95aaf9b422` |
| runtime | CPython 3.12.14；torch 2.8.0；transformers 4.56.2；CPU float32 |
| English Test | 48/48；Python 36、Java 12；六种 task type 各 8 |
| Formal configs / pairs | 17/17；816/816；无缺项、重复或额外项 |
| leakage | English Dev 0；Chinese 0；Dry Run Query ID 引用 0 |

17 个 run 的 raw、aggregate、manifest、run checksum 与 authority binding 均写入后
从磁盘重载，并验证 schema、mode/split、Query/config identity、corpus/execution
revision、Reference Approval、Phase 6.2 Closure、DryRunReceiptV2、artifact hash 和
canonical identity。两个冻结 RQ4 Weighted Hybrid run 还完成了
`context-diagnostic-v1` 的同级绑定；其余 15 个配置保持合法 `null`/absent。

## 配置级总体指标

**FORMAL RESULT。** 每项均为固定 48 条 English Test Query 的 macro arithmetic mean。
Recall@5 与 MRR 为主指标；Recall@1、Recall@10 与 nDCG@5 为 Protocol 主体要求的
辅助指标；Precision@5 与 Hit Rate@5 为附录指标。

| 冻结配置 | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@5 | Precision@5 | Hit Rate@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RQ1-FILE | 0.3976 | 0.8906 | 0.9688 | 0.7364 | 0.7294 | 0.2875 | 0.9375 |
| RQ1-SYMBOL | 0.1472 | 0.5368 | 0.6672 | 0.6130 | 0.4817 | 0.3417 | 0.8333 |
| RQ1-CHUNK | 0.2094 | 0.5836 | 0.6536 | 0.6274 | 0.5246 | 0.3208 | 0.8542 |
| RQ2-BM25 | 0.1472 | 0.5368 | 0.6672 | 0.6130 | 0.4817 | 0.3417 | 0.8333 |
| RQ2-E5 | 0.2245 | 0.5057 | 0.6512 | 0.7311 | 0.4926 | 0.3292 | 0.8542 |
| RQ3-GRAPH-OFF | 0.1602 | 0.5333 | 0.6686 | 0.6617 | 0.4818 | 0.3417 | 0.9167 |
| RQ3-GRAPH-ON | 0.1637 | 0.5524 | 0.6859 | 0.6971 | 0.4975 | 0.3542 | 0.9167 |
| RQ3-CONTAINS-FORWARD | 0.1401 | 0.5316 | 0.6634 | 0.6600 | 0.4644 | 0.3417 | 0.8958 |
| RQ3-CONTAINS-REVERSE | 0.1880 | 0.5542 | 0.6979 | 0.7086 | 0.5159 | 0.3542 | 0.9167 |
| RQ3-IMPORTS-FORWARD | 0.1602 | 0.5333 | 0.6686 | 0.6617 | 0.4818 | 0.3417 | 0.9167 |
| RQ3-IMPORTS-REVERSE | 0.1602 | 0.5333 | 0.6686 | 0.6617 | 0.4818 | 0.3417 | 0.9167 |
| RQ4-LEXICAL | 0.1472 | 0.5368 | 0.6672 | 0.6130 | 0.4817 | 0.3417 | 0.8333 |
| RQ4-EMBEDDING | 0.2245 | 0.5057 | 0.6512 | 0.7311 | 0.4926 | 0.3292 | 0.8542 |
| RQ4-HYBRID-NO-GRAPH | 0.1602 | 0.5333 | 0.6686 | 0.6617 | 0.4818 | 0.3417 | 0.9167 |
| RQ4-HYBRID-GRAPH | 0.1637 | 0.5524 | 0.6859 | 0.6971 | 0.4975 | 0.3542 | 0.9167 |
| RRF-HYBRID-NO-GRAPH | 0.1991 | 0.5490 | 0.7003 | 0.7365 | 0.5212 | 0.3542 | 0.9167 |
| RRF-HYBRID-GRAPH | 0.1627 | 0.5451 | 0.7142 | 0.6978 | 0.4905 | 0.3500 | 0.8958 |

## RQ 层描述性结果

### RQ1 — File / Symbol / Chunk

**FORMAL RESULT。** File、Symbol、Chunk 的 Recall@5 分别为 0.8906、0.5368、
0.5836，MRR 分别为 0.7364、0.6130、0.6274。在本冻结数据集上，File 相对
Symbol 的 Recall@5 / MRR 差值为 +0.3538 / +0.1233，相对 Chunk 为
+0.3071 / +0.1090；Chunk 相对 Symbol 为 +0.0468 / +0.0144。这些差值只描述
本次固定映射和查询集，不外推为普遍的检索单元优越性。

### RQ2 — BM25 / E5

**FORMAL RESULT。** BM25 的 Recall@5 / MRR 为 0.5368 / 0.6130，E5 为
0.5057 / 0.7311。E5 − BM25 的 Recall@5 差值为 -0.0311，MRR 差值为
+0.1181；同时 Recall@1 为 +0.0773、Recall@10 为 -0.0160、nDCG@5 为
+0.0108。结果呈现不同指标之间的方向差异，不据此构造单一 winner score。

### RQ3 — Graph OFF / ON 与方向消融

**FORMAL RESULT。** 主比较中 Graph ON 相对 Graph OFF 的 Recall@5 / MRR
差值为 +0.0191 / +0.0354；Recall@1、Recall@10、nDCG@5、Precision@5 的
差值分别为 +0.0035、+0.0174、+0.0157、+0.0125，Hit Rate@5 相同。

四个冻结方向消融的 Recall@5 / MRR 为：CONTAINS/FORWARD
0.5316 / 0.6600，CONTAINS/REVERSE 0.5542 / 0.7086，IMPORTS/FORWARD
0.5333 / 0.6617，IMPORTS/REVERSE 0.5333 / 0.6617。相对 Graph OFF，
CONTAINS/REVERSE 的差值为 +0.0208 / +0.0469；两个 IMPORTS 方向在这两个
总体指标上与 Graph OFF 数值相同。方向消融是预注册的次级归因证据。

### RQ4 — Signal ablation 与 RRF robustness

**FORMAL RESULT。** Weighted 四行的 Recall@5 / MRR 为：Lexical
0.5368 / 0.6130，Embedding 0.5057 / 0.7311，Hybrid no graph
0.5333 / 0.6617，Hybrid graph 0.5524 / 0.6971。Hybrid graph 相对 Hybrid
no graph 的差值为 +0.0191 / +0.0354；Hybrid graph 相对 Lexical 为
+0.0156 / +0.0841。Embedding 相对 Lexical 仍呈 Recall@5 -0.0311、MRR
+0.1181 的不同方向。

**FORMAL RESULT（secondary robustness）。** RRF no graph 的 Recall@5 / MRR
为 0.5490 / 0.7365，RRF graph 为 0.5451 / 0.6978；RRF graph − no graph
为 -0.0038 / -0.0387。RRF 是独立的次级稳健性表，不改变预注册 Weighted
比较的地位。

## ContextBuilder diagnostics

**FORMAL RESULT。** 两个诊断均为 `context-diagnostic-v1`，每条 Query 的固定
预算为 8000 字符；下表总预算 384000 = 48 × 8000。诊断描述 ContextBuilder
实际渲染，不参与检索 ranking 或 retrieval metrics。

| 诊断项 | RQ4-HYBRID-NO-GRAPH | RQ4-HYBRID-GRAPH |
| --- | ---: | ---: |
| Query | 48 | 48 |
| budget used / total | 272990 / 384000 | 321821 / 384000 |
| budget utilization | 0.7109 | 0.8381 |
| context characters | 272990 | 321821 |
| snippet count | 425 | 533 |
| relevant GT evidence rendered / total | 101 / 165 | 124 / 165 |
| relevant ranked hits rendered / total | 101 / 105 | 100 / 107 |
| package truncation count / rate | 20 / 0.4167 | 24 / 0.5000 |
| snippet truncation count / rate | 20 / 0.0471 | 24 / 0.0450 |
| ranked hits not rendered | 55 | 113 |
| Graph-only rendered snippets | 0 | 166 |
| retained but unrendered Graph provenance | 0 | 386 |

诊断引用与身份：

- `RQ4-HYBRID-NO-GRAPH/context_diagnostics.json`：canonical identity
  `b075ab55f6714d7326eb549e5a1fa5c578f84ced1950d8c0e91b94c78c1d68e8`，
  file SHA-256 `d968fd689159d7f03b0df81107362b8eac5fb98abfca9b29af2941ec8366fc57`。
- `RQ4-HYBRID-GRAPH/context_diagnostics.json`：canonical identity
  `581fb03d5d21e6793139f6afe9f9d67686739d496f47a35d189907985619ee9a`，
  file SHA-256 `4f946a5ea18d20a417c44b5fcdcac0bf92a548b7616fb401ac0c8aba9ba4ec0e`。

Graph 配置比 no-graph 配置多渲染 23 个 GT evidence，使用字符多 48831，
Graph-only snippet 为 166；同时 ranked hits not rendered 多 58，package
truncation 多 4 个 Query。以上为描述性上下文诊断，不能替代 Recall/MRR。

## Language 分群

**FORMAL RESULT。** 单元格为 `Recall@5 / MRR`；Python n=36，Java n=12。

| 配置 | Python | Java |
| --- | ---: | ---: |
| RQ1-FILE | 0.8542 / 0.6670 | 1.0000 / 0.9444 |
| RQ1-SYMBOL | 0.4889 / 0.5257 | 0.6806 / 0.8750 |
| RQ1-CHUNK | 0.4633 / 0.5356 | 0.9444 / 0.9028 |
| RQ2-BM25 | 0.4889 / 0.5257 | 0.6806 / 0.8750 |
| RQ2-E5 | 0.4822 / 0.6971 | 0.5764 / 0.8333 |
| RQ3-GRAPH-OFF | 0.4912 / 0.5906 | 0.6597 / 0.8750 |
| RQ3-GRAPH-ON | 0.5097 / 0.6100 | 0.6806 / 0.9583 |
| RQ3-CONTAINS-FORWARD | 0.4819 / 0.5975 | 0.6806 / 0.8472 |
| RQ3-CONTAINS-REVERSE | 0.5190 / 0.6253 | 0.6597 / 0.9583 |
| RQ3-IMPORTS-FORWARD | 0.4912 / 0.5906 | 0.6597 / 0.8750 |
| RQ3-IMPORTS-REVERSE | 0.4912 / 0.5906 | 0.6597 / 0.8750 |
| RQ4-LEXICAL | 0.4889 / 0.5257 | 0.6806 / 0.8750 |
| RQ4-EMBEDDING | 0.4822 / 0.6971 | 0.5764 / 0.8333 |
| RQ4-HYBRID-NO-GRAPH | 0.4912 / 0.5906 | 0.6597 / 0.8750 |
| RQ4-HYBRID-GRAPH | 0.5097 / 0.6100 | 0.6806 / 0.9583 |
| RRF-HYBRID-NO-GRAPH | 0.5236 / 0.6833 | 0.6250 / 0.8958 |
| RRF-HYBRID-GRAPH | 0.5324 / 0.6665 | 0.5833 / 0.7917 |

## Task type 分群

**FORMAL RESULT。** 单元格为 `Recall@5/MRR`，每类 n=8。BL =
bug localization，CF = cross-file understanding，DQ = dependency questions，
FL = feature localization，MT = maintenance tasks，SL = symbol lookup。

| 配置 | BL | CF | DQ | FL | MT | SL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RQ1-FILE | 0.8750/0.8264 | 0.8438/0.5845 | 0.8750/0.7292 | 0.9375/0.6979 | 0.8125/0.8929 | 1.0000/0.6875 |
| RQ1-SYMBOL | 0.4125/0.5000 | 0.3563/0.5833 | 0.5312/0.5354 | 0.5417/0.7470 | 0.5042/0.6667 | 0.8750/0.6458 |
| RQ1-CHUNK | 0.5312/0.5417 | 0.5243/0.6146 | 0.5958/0.6667 | 0.6417/0.6979 | 0.5417/0.5875 | 0.6667/0.6562 |
| RQ2-BM25 | 0.4125/0.5000 | 0.3563/0.5833 | 0.5312/0.5354 | 0.5417/0.7470 | 0.5042/0.6667 | 0.8750/0.6458 |
| RQ2-E5 | 0.2938/0.4708 | 0.3302/0.7292 | 0.5417/0.8333 | 0.4375/0.7312 | 0.6604/0.8167 | 0.7708/0.8056 |
| RQ3-GRAPH-OFF | 0.4188/0.4938 | 0.3604/0.6458 | 0.5312/0.6083 | 0.4896/0.6875 | 0.5667/0.7708 | 0.8333/0.7639 |
| RQ3-GRAPH-ON | 0.4500/0.5500 | 0.4021/0.7292 | 0.5312/0.6292 | 0.5312/0.8333 | 0.5667/0.8229 | 0.8333/0.6181 |
| RQ3-CONTAINS-FORWARD | 0.4188/0.4000 | 0.3604/0.7812 | 0.4896/0.6500 | 0.4896/0.6667 | 0.5979/0.8229 | 0.8333/0.6389 |
| RQ3-CONTAINS-REVERSE | 0.3875/0.5563 | 0.4021/0.6458 | 0.5729/0.6292 | 0.5312/0.8229 | 0.5979/0.8542 | 0.8333/0.7431 |
| RQ3-IMPORTS-FORWARD | 0.4188/0.4938 | 0.3604/0.6458 | 0.5312/0.6083 | 0.4896/0.6875 | 0.5667/0.7708 | 0.8333/0.7639 |
| RQ3-IMPORTS-REVERSE | 0.4188/0.4938 | 0.3604/0.6458 | 0.5312/0.6083 | 0.4896/0.6875 | 0.5667/0.7708 | 0.8333/0.7639 |
| RQ4-LEXICAL | 0.4125/0.5000 | 0.3563/0.5833 | 0.5312/0.5354 | 0.5417/0.7470 | 0.5042/0.6667 | 0.8750/0.6458 |
| RQ4-EMBEDDING | 0.2938/0.4708 | 0.3302/0.7292 | 0.5417/0.8333 | 0.4375/0.7312 | 0.6604/0.8167 | 0.7708/0.8056 |
| RQ4-HYBRID-NO-GRAPH | 0.4188/0.4938 | 0.3604/0.6458 | 0.5312/0.6083 | 0.4896/0.6875 | 0.5667/0.7708 | 0.8333/0.7639 |
| RQ4-HYBRID-GRAPH | 0.4500/0.5500 | 0.4021/0.7292 | 0.5312/0.6292 | 0.5312/0.8333 | 0.5667/0.8229 | 0.8333/0.6181 |
| RRF-HYBRID-NO-GRAPH | 0.3875/0.4562 | 0.4021/0.7917 | 0.5312/0.7750 | 0.5521/0.8542 | 0.5875/0.7917 | 0.8333/0.7500 |
| RRF-HYBRID-GRAPH | 0.3812/0.3970 | 0.4062/0.8750 | 0.5312/0.7750 | 0.5938/0.9167 | 0.5667/0.7396 | 0.7917/0.4833 |

分群样本量较小，尤其 Java n=12、每类任务 n=8；这些切片用于完整披露，不用于
挑选 favourable subset 或作额外总体结论。

## 确定性、泄漏与边界

**FORMAL RESULT。** 在 816 个主执行组合完成后，独立重复
`RQ1-FILE`、`RQ1-SYMBOL`、`RQ1-CHUNK`、`RQ2-BM25`、`RQ2-E5`、
`RQ3-GRAPH-ON`、`RQ4-HYBRID-GRAPH`、`RRF-HYBRID-GRAPH`，共比较
384 条 Query。ranking、scores、metrics 与 identity 的 mismatch 为 0；适用的
RQ4 diagnostic serialization mismatch 为 0。测量噪声字段 `latency_ns` 按冻结
规则不进入确定性身份。

泄漏证据确认 Formal Query set 精确等于 English Test 48：English Dev execution
0、Chinese execution 0、Dry Run Query ID reference 0。所有 17 个 raw SHA-256
同时绑定 determinism 与 leakage evidence。

测试验证：ContextBuilder、benchmark infrastructure、production execution、
serialization/security、reference lifecycle/eligibility 专项为 **240 passed**；
`python -m pytest -p no:debugging` 完整回归为 **892 passed**。无 skip、xfail、
删除测试或放宽断言。

Addendum D 预注册的 Grade-2-only 次级敏感性分析未由本轮冻结 runner 和 Formal
artifact schema 独立物化，因此标记为**未执行的预注册次级分析**；不在本报告中
临时重算，也不替代主指标。未执行性能协议的 30 次 timing repetition，因此本报告
不作生产延迟、方差、扩展性或 SLA 声明。

## 研究解释限制与状态

**FORMAL RESULT。** 本结果仅支持对冻结单仓库、固定 48 条 English Test Query、
固定 Reference 与 17 个配置的直接比较。单标注者、不完整未判定池、Python 比重、
有限 Java、构造 fixture、单一 E5 模型与 CPU 环境均限制外推；确定性复跑不等于
统计重复样本。负向、相同和反直觉结果均已保留。

Formal artifact set、两个 RQ4 diagnostic、determinism evidence 与 leakage evidence
均为 PASS。归档提交后必须从新 HEAD 再次重载全部 Formal artifacts，并确认其中
`execution_revision` 仍为 `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`；归档
commit 只表示这些结果进入 Git 历史，不改写执行身份。该重载通过后，Formal
execution 与 RQ1、RQ2、RQ3、RQ4 状态为 `COMPLETED`；V3.2 保持 `NOT STARTED`。
