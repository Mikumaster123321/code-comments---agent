# V3.1.0 Phase 6.3 前置工程：冻结 Benchmark Execution Wiring

## 状态与范围

- 初始分支 `v3.1.0-dev`，初始 HEAD `ae10c40ba89d81692a9fcecf6e0088d2a3bff827`；既有用户未跟踪目录 `docs/thesis/` 未读取、列举、修改或暂存。
- Phase 6.2 保持 `CLOSED`；Phase 6.3 保持 `ALLOWED BUT NOT STARTED`；Formal RQ1–RQ4 保持 `NOT STARTED`。
- English Dev 正式 Dry Run 仍为 `0/12`，正式执行的 matrix configuration 仍为 `0/17`；English Test 执行 `0`；`DryRunReceipt` 未创建。
- 本轮仅新增执行接线和合成测试；不调整冻结 Query、split、GT、Grade、指标、参数或 authority chain。

## 根因与执行结构

原 `BenchmarkRunner` 只消费调用方注入的 `BenchmarkStrategy`。Phase 6.1 测试通过 `TinyStrategy` 验证 Runner、TruthMapper 和指标，但无冻结源码、生产索引、17 项配置与 Runner 的正式连接，因而不能把 `0/12`、`0/17` 推进为真实 Dry Run 结果。

新增 `experiments/execution.py`：`executable_config` 从现有冻结配置绑定核对 matrix ID；`bind_frozen_dataset` 只读取 manifest 列出的 fixture 文件和 self-repository 冻结提交 blob，逐个校验 SHA-256，再用生产 `ProjectScanner`、`SnapshotBuilder`、`CorpusBuilder` 重建 Snapshot / Symbol 文档。适配器按现有 File/Chunk 文本合同构建候选，并与 `DatasetEvidenceRegistry` 的 File/Symbol/Chunk identity、span、文件 hash 集合核对。`ProductionBenchmarkStrategy` 调用生产 `RetrievalIndex`、`BM25Index`、`LocalE5EmbeddingProvider`、`HybridRetriever`、`expand_graph` 和 `ContextBuilder`，只把生产命中转成 Runner 的 `StrategyHit`。Runner 仍负责 reference/GT 映射和原有 Recall@5、MRR 等指标。

File/Chunk 的旧 `ExperimentalBM25Index` 已改为薄身份适配器，调用生产 `BM25TextScorer`；BM25 计分和稳定同分排序保留在生产模块。Graph pair ablation 在生产 `expand_graph` 的邻接构造阶段过滤冻结 `(relation, direction)`，先过滤后施加原预算，避免先用错误方向消耗预算。Weighted/RRF 的分数公式仍由生产 `HybridRetriever` 负责。

正式输入由既有 `ValidatedExecutionInputs` 携带原始 `DatasetManifest`、`QueryRecord` 和 `ReferenceRecord`；`prepare_frozen_execution` 要求它由 validator 签发，且配置身份相等。正式策略构造也要求同一 authority。`FrozenBenchmarkExecution.run()` 只转交原有 Runner，Runner 会重新验证 repository authority。English Test 仅允许正式执行路径；既有 FORMAL gate 仍要求有效 DryRunReceipt，因此本轮没有 English Test 路径可运行。

## 冻结 17 项配置映射

全部 `top_k=10`；BM25 `k1=1.5, b=0.75, code-lexical-v1`；语义项使用冻结 E5 768 维、L2、`query: ` / `passage: `、512 token 显式截断；Weighted 权重按表；RRF `rrf_k=60`。Graph ON 共用一跳、每 seed 五项、总三十节点及冻结方向/关系因子。

| 稳定 ID | Unit | Backend / fusion | Graph | L/S/G |
| --- | --- | --- | --- | --- |
| RQ1-FILE | File | BM25 | OFF | 1/0/0 |
| RQ1-SYMBOL | Symbol | BM25 | OFF | 1/0/0 |
| RQ1-CHUNK | Chunk 1200/200 | BM25 | OFF | 1/0/0 |
| RQ2-BM25 | Symbol | BM25 | OFF | 1/0/0 |
| RQ2-E5 | Symbol | real E5 | OFF | 0/1/0 |
| RQ3-GRAPH-OFF | Symbol | Weighted | OFF | 1/1/0 |
| RQ3-GRAPH-ON | Symbol | Weighted | ON, all four pairs | 1/1/0.25 |
| RQ3-CONTAINS-FORWARD | Symbol | Weighted | ON, CONTAINS/FORWARD | 1/1/0.25 |
| RQ3-CONTAINS-REVERSE | Symbol | Weighted | ON, CONTAINS/REVERSE | 1/1/0.25 |
| RQ3-IMPORTS-FORWARD | Symbol | Weighted | ON, IMPORTS/FORWARD | 1/1/0.25 |
| RQ3-IMPORTS-REVERSE | Symbol | Weighted | ON, IMPORTS/REVERSE | 1/1/0.25 |
| RQ4-LEXICAL | Symbol | BM25 | OFF | 1/0/0 |
| RQ4-EMBEDDING | Symbol | real E5 | OFF | 0/1/0 |
| RQ4-HYBRID-NO-GRAPH | Symbol | Weighted + ContextBuilder | OFF | 1/1/0 |
| RQ4-HYBRID-GRAPH | Symbol | Weighted + ContextBuilder | ON, all four pairs | 1/1/0.25 |
| RRF-HYBRID-NO-GRAPH | Symbol | RRF | OFF | 1/1/0 |
| RRF-HYBRID-GRAPH | Symbol | RRF | ON, all four pairs | 1/1/0.25 |

协议表将四个 RQ3 pair 简写为 `-F` / `-R`；既有 `BenchmarkConfig` 冻结的是上表展开的 `-FORWARD` / `-REVERSE` 执行 ID，本轮沿用该绑定，不另增配置。

## 验证边界

测试覆盖 17 行解析、未知 ID 拒绝、三种 unit、生产 BM25 复用、E5 类与冻结 fingerprint、Graph ON/OFF 与单 pair、Weighted/RRF、稳定顺序、错误 split、English Test 防误执行、合成样例的 `StrategyResult → BenchmarkRunner → metrics`，以及生产模块无 `experiments` 反向导入。合成 embedding 测试明确使用测试专用假向量；另有独立测试用离线 stub 只核对**真实 E5 adapter 类**接线，不把该 stub 当成语义结果。

初始全量基线 `813 passed`；相关定向回归 `362 passed`；最终工作树全量回归 `825 passed`（`python -m pytest -p no:debugging`）。直接 `python -m pytest` 因本机 pytest debugging 插件加载时 segfault，禁用该插件后无测试失败。未增加 skip/xfail、删除测试或放宽断言。

## 冻结 E5 资产恢复与真实烟测

只读检查 `/private/tmp`、用户 Hugging Face 缓存及常规缓存目录，仅发现两份已知损坏的同 revision snapshot：其 symlink 指向已删除的 blob，不作为可用资产。恢复方式为 `EXACT_REVISION_DOWNLOAD`：通过 `huggingface_hub.snapshot_download` 明确指定 `intfloat/multilingual-e5-base` 的 `d128750597153bb5987e10b1c3493a34e5a4502a`，下载到新隔离目录 `/private/tmp/v31-e5-recovered-cache/`。官方调用返回的 resolved snapshot 路径以该精确 commit 命名；没有使用 `main`、`latest` 或其他模型，也没有覆盖历史损坏缓存。

恢复后的 snapshot 为 `/private/tmp/v31-e5-recovered-cache/models--intfloat--multilingual-e5-base/snapshots/d128750597153bb5987e10b1c3493a34e5a4502a`。机械检查覆盖全部 **23** 个 snapshot 文件、全部 symlink target、`config.json`、`tokenizer.json`、`tokenizer_config.json`、`special_tokens_map.json`、`sentencepiece.bpe.model`、`model.safetensors`、`modules.json`、`sentence_bert_config.json` 与 `1_Pooling/config.json`；必需文件均非零，`model.safetensors` 为 **1,112,201,288 bytes**，`config.hidden_size=768`，悬空 symlink **0**。模型资产仅保存在仓库外，没有提交缓存或向量。

运行时为 `/private/tmp/phase62-eligibility-runtime/bin/python3.12`，Python **3.12.14**、torch **2.8.0**、transformers **4.56.2**、CPU、float32。该既有环境原先缺少可加载的 libffi/OpenSSL 路径；通过为进程指定本机现有的 libffi 3.4.8 与 OpenSSL 3.5.8 库路径恢复运行，没有新建环境或修改 requirements。以 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`、`model_path` 指向上述 snapshot、`local_files_only=True` 调用真实 `LocalE5EmbeddingProvider`。模型成功加载；真实 query 与 passage 向量均为 **768** 维、全部 finite、L2 范数分别为 **1.00000000549** 与 **0.99999996499**。Provider 冻结 fingerprint 使用 `query: ` 与 `passage: ` 前缀，真实推理经过其 `_embed_batch` 准备文本及模型前向路径；无 stub、fake、mock。

生产链路最小烟测使用一个**合成** Python fixture 查询和两份 Symbol 文档：`ProductionBenchmarkStrategy` 持有上述真实 Provider，构建生产 `RetrievalIndex` 的两个语义向量，返回两个有序命中，并交给原 `BenchmarkRunner` 与既有 metrics；Runner 状态 `success`、`Recall@5=1.0`，token diagnostics **3**。这只证明真实 E5 到生产 benchmark adapter 的最小集成链路，不作为正式检索质量或 English Dev 结果。没有执行完整 corpus、Chinese benchmark、English Test 或 Formal RQ。

恢复后复核冻结配置 **17/17**；接线、embedding、runner/experiment 定向测试 **177 passed**，全量回归 **825 passed**（`python -m pytest -p no:debugging`）。普通 `python -m pytest` 仍在主机 Python 3.13 的 debugging 插件加载时 segfault，禁用插件后无测试失败。本前置接线条件现已满足，可单独提交；Phase 6.3、正式执行计数和 DryRunReceipt 状态保持本报告开头所列值。下一动作是另行启动 English Dev Dry Run。
