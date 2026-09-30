# V3.1.1 Workflow & Developer Experience 论文工程素材

<!-- release-state: V3.1.1 RELEASED -->

## 1. 定位与边界

V3.1.1 是 V3.1.0 之后的工程维护版本，主题为 **Workflow & Developer Experience
Optimization**。其贡献是提高开发、验证与发布流程的可复现性、可诊断性和一致性，
不是新的 retrieval research result。V3.1.0 的 Query、Ground Truth、Grade、17 项配置、
ranking semantics、Formal runs、metrics、artifact 与 interpretation 均保持冻结。

## 2. Motivation

V3.1.0 已完成 Project Intelligence / RAG 与 Formal RQ1–RQ4，但工程入口分散、核心与
可选 E5 环境边界不够直观、pytest host failure 需要人工辨别、Formal archive 与发布文档
状态缺少统一只读门禁。这些问题不改变算法，却会增加结果复核、环境迁移和维护发布时的
操作歧义。因此 V3.1.1 将 workflow 本身视为可测试的工程对象。

## 3. Workflow reproducibility

`scripts/dev.py` 提供纯 Python、repository-root aware 的统一入口。它从仓库内外 cwd
均可定位项目，使用参数数组启动子进程，不使用 `shell=True`，并保留底层 pytest exit
code。入口默认不联网、不下载模型、不运行 Formal benchmark，也不执行 stage、commit、
tag、push 或其他 Git 写操作。原有 `python -m pytest`、独立验证脚本和应用入口继续有效。

## 4. Developer diagnostics

`doctor` 将环境分为 Core runtime、Optional E5 runtime 和 Historical Formal runtime。
它报告 Python executable/version/implementation/platform、依赖可用性、Git branch/HEAD，
并只将敏感环境变量显示为 set/unset。普通 pytest 通过独立子进程探测；只有观察到插件
初始化异常时才建议 `-p no:debugging`，且明确标注为 host workaround，而非测试语义变化。

## 5. Test profile standardization

`llm`、`production`、`experiments`、`full` 与 `release` profile 在一个 source of truth
中定义，避免 README、CI 和临时 shell snippet 分别维护测试文件列表。V3.1.0 的
198/240/892 仅作为历史基线；新增 30 项 workflow/release 测试后，V3.1.1 full baseline
为 922，不通过排除新测试来维持旧数字。

## 6. E5 environment reproducibility

`model-check` 固定检查 `intfloat/multilingual-e5-base` revision
`d128750597153bb5987e10b1c3493a34e5a4502a`、768 维和冻结依赖版本。它仅检查显式路径或
标准本地 cache，不扫描整机、不创建 repo 内 cache、不下载模型。检查覆盖 snapshot、必要
文件、dangling symlink、repository identity、resolved revision 与 cache location。显式
`--smoke` 只执行 1 query + 1 document，并验证 finite、dimension 与 L2 behavior。

## 7. Experiment traceability

`experiment-validate archive-v3.1.0` 组合已有 `RepositoryAuthority`、canonical identity、
typed receipt 与 deterministic CSV checker，验证 execution/archive ancestry、artifact
SHA-256、canonical identity、17 configs、48 English Test queries、816 query-config pairs
及 Formal 路径未变。`--purpose` preflight 继续以既有 authority validator 为 Source of
Truth；CLI 只补充 Expected/Actual/Safe recovery，不修改 frozen failure schema。

## 8. Release consistency gate

最小机器可读 `docs/release/release_state.json` 区分 PREPARING、RELEASE_CANDIDATE 与
RELEASED。`release-check` 只读核对 branch/HEAD、working tree、protected-path staging、
代码版本、稳定文档 sentinel、V3.1.0 baseline tag、V3.1.1 tag state 与 Formal archive。
默认不访问网络；仅显式 `--remote` 使用 `git ls-remote` 读取远端 tag 状态。

## 9. Assert hardening

Formal CSV checker 与 Phase 3.2 real-model validator 的 correctness gate 从 `assert`
改为显式条件和异常。因而 `python -O` 不会跳过错误 artifact checksum、identity、CSV 或
model metadata 校验，也不会在失败后错误打印 verified。POSIX `resource` 不可用时只将
RSS metrics 标记为 unavailable，验证的其他部分仍可运行。

## 10. Engineering contribution

本版本的论文工程贡献可表述为：为带有冻结实验历史的代码智能维护系统构建一套
offline-first、read-only-by-default、failure-explicit 的可复现维护工作流，并用自动测试将
环境诊断、实验追溯和发布一致性纳入软件质量边界。它增强的是研究软件工程可信度与交付
可审计性，而不是检索效果。

## 11. Verification facts

- Workflow/release tests：30 passed
- Production profile：198 passed
- Experiments profile：240 passed
- Full profile：922 passed
- Legacy `python -m pytest -p no:debugging`：922 passed
- Formal artifact identity：`acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Formal artifact file SHA-256：`2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

## 12. Limitations

- E5 preflight 不能替代完整 Phase 3.2 performance/corpus validation。
- `--smoke` 依赖用户已准备且版本精确匹配的本地 cache；本版本不负责下载或修复 cache。
- release remote validation 是显式 opt-in，离线默认门禁不证明远端状态。
- 稳定 profile 反映当前仓库结构；未来测试重组仍需审查单一映射。
- V3.1.1 不提供新的数据集、统计检验、外部有效性或 downstream LLM quality 证据。
