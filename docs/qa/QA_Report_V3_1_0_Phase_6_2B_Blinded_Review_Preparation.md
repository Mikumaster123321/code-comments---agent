# V3.1.0 Phase 6.2B — Blinded Review Preparation Independent QA Documentation Closure

## 结论与边界

**Phase 6.2B blinded review preparation independent QA：PASS WITH LOW NOTES。**
生成器和实际隔离包分别为 **PASS WITH LOW NOTES**；综合结论按用户提供的
DeepSeek V4.1 Flash 独立 QA 回复记录为
**PASS FOR BLIND-REVIEW PREPARATION WITH LOW NOTES**。本次仓库及现存包的
直接核验与此结论没有冲突。回复报告 Critical / Medium 为 **0 / 0**；本次核验
未发现身份漂移、实际包答案泄漏或关键合同冲突。DeepSeek 的原始探针脚本、
命令输出与另行生成的包未提供或归档，因此其独立探针结果不能写成本次亲自复算。

**本次关闭的仅是准备材料独立 QA 的 Documentation Closure：CLOSED。**
人类 delayed blinded self-review **NOT COMPLETED**；本报告不关闭最终 Data QA、
不冻结 Dataset，也不证明材料已正确交付给 `wang`。

## 审计对象与权威依据

入场分支 `v3.1.0-dev`，HEAD
`adf95ba1f285b60297a59a065699ae975c659037`；工作树仅显示受保护的
`?? docs/thesis/`，该目录内部没有在本次读取、列举或处理。准备提交自身仅改动
`PROJECT_CONTEXT.md` 及 `docs/experiments/blind_review/` 下的说明、空白页和
`prepare_bundle.py`。本次核验的实际隔离包位于仓库外
`/private/tmp/phase62b-blind-bundle-9161ff4/`。

依据为当前 Git 跟踪的 `PROJECT_CONTEXT.md`、
`docs/experiments/Experiment_Protocol_V3_1_0.md`、Addenda A/B/C、
`docs/experiments/Dataset_Query_GroundTruth_Specification_V3_1_0.md`、
`docs/qa/QA_Report_V3_1_0_Phase_6_2A_Independent_Draft_Data.md`、
准备提交的材料和生成器，以及冻结 Query、GT、annotation audit、
`datasets/v1/identity.json` 和相关数据合同。Addendum A 要求唯一人类标注者
`wang` 至少间隔 48 小时，在遮蔽初稿下固定独立第二次判断，随后比较并对
需要裁决的分歧留证；模型 QA 不是第二位人类 reviewer，不能产生 human IAA。

## 证据归属

### 本次从仓库或现存隔离包直接核验

| 项目 | 本次结果 |
| --- | --- |
| 准备提交与工作树 | 上述 HEAD 的提交文件与准备范围一致；入场无其他已跟踪改动。 |
| 实际包验证 | 现存目录的只读 `--verify-bundle` 成功：72 条唯一 Query、93 个冻结源码文件、无多余文件。 |
| 包结构 | 顶层仅 `README.md`、`queries_for_second_judgment.jsonl`、`source_catalog.json`、`sources/`；共 96 个文件，其中 93 个源码文件；未发现 symlink。 |
| 冻结 Query 身份 | `identity.json` 的 `query_set_hash` 为 `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`，与冻结 Query 的 canonical hash 一致；包内 72 个唯一 ID 的文本、语言、任务、项目、split 与冻结 Query 逐字段一致。 |
| 空白与遮蔽 | 72 个 `review` 中待填写值均为 `null` 或空数组；包内没有 GT、audit、初始 Symbol/span/grade/rationale、预选候选、Query 定向源码映射、可打开的初始判断指针，亦无检索排名、检索得分或结果字段。冻结 Query 原文中普通的 “score”/“ranking” 用词不属于检索结果泄漏。 |
| 正式数据状态 | GT 72 条、annotation audit 72 条均为 `drafted`；GT `reviewed_at` 均为空，audit 的 delayed judgment、comparison、masking confirmation 等仍为空。 |
| 正式数据身份 | manifest、identity、checksum、Query、GT、annotation audit 的原始字节与入场 HEAD 逐一相同；本次未改写它们。 |
| 合同与回归 | 本次执行离线 Phase 6.2 数据合同 94 passed，全套回归 722 passed；均退出码 0。 |

本次主要核验命令及可取得证据：

```text
git branch --show-current
git rev-parse HEAD
git status --short
git diff
git diff --cached
git show --format= --name-only HEAD
python docs/experiments/blind_review/prepare_bundle.py --verify-bundle /private/tmp/phase62b-blind-bundle-9161ff4
python -m pytest -p no:debugging tests/test_phase62_dataset_contract.py -q
python -m pytest -p no:debugging
```

另以只读本地检查逐字段比对 Query 与包内空白页、统计目录和 symlink，
并将上述六份正式数据文件的原始字节与 `git show HEAD:<path>` 对照。
`-p no:debugging` 是当前宿主机的 pytest 插件 workaround；测试包含已有
离线 stub/合成路径，本次未运行 E5、正式检索、Dry Run 或 RQ1–RQ4。

### DeepSeek 独立 QA 回复所述，原始产物未归档

回复称生成器及实际包各为 **PASS WITH LOW NOTES**，综合为
**PASS FOR BLIND-REVIEW PREPARATION WITH LOW NOTES**；独立脚本 37 项断言
通过，Phase 6.2 数据合同 94 passed，实际包的 `--verify-bundle` 通过，
另行生成的包与实际包逐字节一致，Critical / Medium 为 **0 / 0**。
其中 37 项独立断言、逐字节复现及其原始脚本、命令日志和生成包未随回复归档；
这些细节只归属于 DeepSeek 回复，不能由本次同名测试或现存包核验替代。

### 未来交付或人类行为，当前不可证明

包的结构通过不证明它已在仅含 GT-free 材料的环境中正确交付 `wang`，也不
证明 `wang` 复核期间没有查看完整仓库。当前同一系统账户仍可访问含 GT 的
仓库；这是实际交付与隔离流程的**待控限制**。GT/audit 目前为 `drafted` 仅
说明正式记录未升级，不能证明没有人开始过未记录的复核。复核前应在独立于
含 GT 仓库视图的环境中交付并复验包，由 `wang` 记录真实遮蔽观察与时间。

## 发现项与过程偏差

| 性质 | 记录 |
| --- | --- |
| 非阻塞溯源建议 | 包内没有整体生成版本、生成时间或包级 hash 标记；`source_catalog.json` 的逐源身份不能充当包整体身份。交付时宜单独记录实际包 hash/时间及所审计准备提交。当前不改包或生成器。 |
| 命名观察 | 现存包目录名含较早基线的短哈希 `9161ff4`，并非本次审计的准备提交 `adf95ba…`；交接时应明确实际路径与完整准备提交，避免把目录名当成包身份。 |
| Low hardening note | 生成器第 166 行用 `destination.exists()` 检查目标是否存在；悬空 symlink 的 `exists()` 可为 false，故该检查不能可靠拒绝这种目标。现存实际包未发现 symlink 且通过验证。本任务不修改生成器。 |
| 待控隔离限制 | 同一系统账户仍可打开完整仓库中的 GT；需在真实人类复核前落实仅含独立包的访问环境，不能用准备验证替代。 |
| 合同允许的设计事实 | 冻结 self-repository 语料含 28 个测试源码文件（另有 44 个生产源码文件）；Protocol 允许这种自仓库语料组成，不记为数据缺陷。 |
| DeepSeek QA 过程偏差 | 用户转述称 DeepSeek 曾以递归目录清点显示受保护目录内一个文件名，并声明未读文件内容。原始命令日志未归档，本报告不复制、推断该名称，也不将“未读内容”冒充本次对其过程的独立证明；本次只读取工作树顶层状态。 |

上述观察不增加 Critical 或 Medium；不为凑 Low 数量将合同允许的设计或
探针说明写成产品缺陷。本次直接核验与独立 QA 回复摘要没有出现相冲突的
blocker；现存包验证的结论只及于本次所见的路径和内容。

## 门禁与下一入口

| 项目 | 当前状态 |
| --- | --- |
| Phase 6.2B blinded review preparation independent QA | **PASS WITH LOW NOTES** |
| 准备材料 QA Documentation Closure | **CLOSED** |
| 人类 delayed blinded self-review | **NOT COMPLETED** |
| Dataset / Query / GT | **DRAFTED / DRAFTED / DRAFTED** |
| Phase 6.2 Gate | **OPEN** |
| Phase 6.3 | **BLOCKED / NOT STARTED** |
| Formal RQ1–RQ4 | **NOT STARTED** |

最早真实人类复核开始时间为 `2026-09-25T04:00:42.357095+00:00`
（北京时间 `2026-09-25 12:00:42.357095`）。到达门禁后，下一步须由
`wang` 在隔离环境中完成并固定真实第二次独立判断，然后才可比较初始 GT、
处理分歧及必要裁决。当前任务不自动开始这些工作；随后仍需最终独立 Data QA
及 Dataset Freeze 判定。
