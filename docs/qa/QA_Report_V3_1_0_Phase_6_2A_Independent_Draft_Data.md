# V3.1.0 Phase 6.2A — Independent Draft Data QA Documentation Closure

## 结论与范围

**Phase 6.2A Independent Draft Data QA：PASS WITH LOW NOTES。**
**本次 QA Documentation Closure：CLOSED。** 这里关闭的是独立草稿数据 QA
结论入库事项。Dataset、Query Set 和 Ground Truth 仍为 **DRAFTED**；
Phase 6.2 Gate **OPEN**，Phase 6.2B **PENDING**。

本报告将用户提供的 DeepSeek V4.1 Flash 独立草稿数据 QA 回复摘要与本次仓库复核
分开记录。该回复报告 Critical / Medium 为 **0 / 0**，结论为
**PASS WITH LOW NOTES**。原始 DeepSeek 对话全文、仓库外 `probe1`–`probe9`
脚本、原始输出及运行日志均未作为本次输入提供，也未见于当前 Git 跟踪文件；
探针的详细结果因此仅是**依据独立 QA 回复报告，未归档原始探针产物**，不作为
本次仓库执行者亲自复算的结果。本次可复算的身份、状态及离线测试与回复摘要一致。

## 审计对象与依据

入场核验：分支 `v3.1.0-dev`，材料化提交
`5341240b5bf7d567ac95d46550785a5e2bdd8607`；`git status --short --branch`
仅显示受保护的 `?? docs/thesis/`。该目录的内部内容没有读取、列举或处理。
本次审计基于这个提交中的正式数据，而非后续工作树源码。

| 身份字段 | 当前 `identity.json` 与本次独立重算一致的值 |
| --- | --- |
| `dataset_hash` | `164994a826fe51936d5fcb012a8d102967c33110787405fd3b0f7972efe8ade7` |
| `query_set_hash` | `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba` |
| `ground_truth_hash` | `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87` |

依据包括 `PROJECT_CONTEXT.md`、
`docs/experiments/Experiment_Protocol_V3_1_0.md`、Addenda A/B/C、
`docs/experiments/Dataset_Query_GroundTruth_Specification_V3_1_0.md`、
`docs/qa/QA_Report_V3_1_0_Phase_6_1_3.md`、材料化提交中的 manifest、
`identity.json`、Query/GT/annotation audit、checksum，以及
`tests/test_phase62_dataset_contract.py`。仓库没有单独的 Phase 6.2A
材料化报告文件；该提交、`PROJECT_CONTEXT.md` 和上述正式数据提供可核查的
材料化记录。本报告不将较早 Phase 6.1.3 报告的历史状态误作当前状态。

## 检查结果与证据归属

| 检查事项 | DeepSeek 回复摘要所述 | 本次仓库核验所得 |
| --- | --- | --- |
| 分支、HEAD、工作树 | 与交接基线一致；仅 `?? docs/thesis/` | 一致；未触碰该目录 |
| 三项 draft hash | 与 `identity.json` 一致 | 从已加载的 schema 记录重新计算并逐项比对，一致 |
| 数据文件 checksum | 34 项通过 | 逐项对原始文件 bytes 计算 SHA-256，34/34 一致 |
| 自仓库与 fixture | 72 文件 / 1233 Symbol；三项主 fixture 通过 | 本轮合同测试通过；自仓库与 fixture 的逐源文件校验属于该测试范围 |
| Query / GT / evidence | 72 / 72 / 134 | 重新加载为 72 / 72 / 134；Grade 2/1 为 72/62 |
| Addendum B/C 与数据合同 | 机械合同通过 | 本轮 94 项合同测试通过，覆盖增量差异、四条更正、泄漏、Java、RQ1 映射等现有断言 |
| 标注生命周期 | 仍为 drafted | 72 条 GT 与 72 条 audit 均为 `drafted`；GT `reviewed_at`、`adjudicator_id` 为空，audit 无 delayed judgment |
| 运行产物 | 未见正式运行 | 当前 `docs/experiments/runs/` 不存在；HEAD 下未见相关跟踪运行文件 |
| 独立探针 | 仓库外 `probe1`–`probe9` | **依据独立 QA 回复报告，未归档原始探针产物**；本次未执行这些探针 |

本次执行的命令及结果（退出码均为 `0`）：

```text
python -m pytest -p no:debugging tests/test_phase62_dataset_contract.py -q
94 passed

python -m pytest -p no:debugging -q
722 passed
```

全量回归沿用仓库批准的 `-p no:debugging` 宿主机 workaround。测试含原有
离线合成/stub 路径；本次文档收口没有发起 E5、正式检索、Dry Run 或 RQ1–RQ4
运行。`identity.json` 中 `retrieval_runs_before_freeze=0`，加上当前未见
`runs/`，仅说明当前数据身份及可见仓库状态；它们不能证明历史上从未存在
临时或未跟踪的检索运行。

## Findings、观察事项与未完成的人类工作

独立 QA 回复摘要报告 **Critical 0 / Medium 0**；本次仓库校验及离线回归
没有出现与其冲突的失败。以下 L1–L5 保留为 Low notes 或观察，不把符合规范
的现象冒称数据缺陷：

| 编号 | 记录与后续归属 |
| --- | --- |
| L1 | 盲自审时遮蔽初始 grade、rationale、judgment 须由 Phase 6.2B 实际执行并留证；当前 audit 不能证明未来遮蔽。 |
| L2 | 中文查询的非机械直译与相关性语义判断留待 Phase 6.2B 人类复核；当前 `not_mechanical_translation` 为待审状态。 |
| L3 | 符合规格的跨记录证据复用是允许且已审计的重叠，属观察，不是数据缺陷。 |
| L4 | DeepSeek 回复称其探针自身的错误已更正；缺少原始探针资料，本报告不复述未能核对的细节，也不将其记为数据缺陷。 |
| L5 | 单人标注、无第二位人类标注者及无 human IAA 是 Addendum A 已确认的方法限制；独立模型 QA 不替代人类复核。 |

用户提供的摘要未附 DeepSeek 原始消息记录。其尾标在转述中显示为
`\=== END ... ===`；仅凭展示文本无法判断反斜杠是否属于原文，本次既不声称
逐字核验成功，也不将其认定为失败。

本次没有检查远端引用，**未核验材料化提交是否已 push**。HEAD 的本地
branch/tag 状态不能代替远端事实。本报告也不推断仓库外探针脚本、临时数据
或未跟踪运行产物的历史存在与否。

## 门禁与下一入口

| 项目 | 本次状态 |
| --- | --- |
| Phase 6.2A Independent Draft Data QA | **PASS WITH LOW NOTES**（DeepSeek 回复摘要；仓库核心证据复核一致） |
| QA Documentation Closure | **CLOSED**，仅报告入库 |
| Dataset / Query / Ground Truth | **DRAFTED / DRAFTED / DRAFTED** |
| Phase 6.2 Gate | **OPEN** |
| Phase 6.2B | **PENDING** |
| Phase 6.3 | **BLOCKED / NOT STARTED** |
| Formal RQ1–RQ4 | **NOT STARTED** |

初稿 `created_at=2026-09-23T04:00:42.357095+00:00`；最早允许复核时间为
`2026-09-25T04:00:42.357095+00:00`。Phase 6.2B 须在真实达到至少 48 小时
后，由 `wang` 完成遮蔽初稿的独立时序判断、中文非直译核查、比较与必要的
歧义裁决；随后还需最终独立 Data QA、最终 hash/checksum 校验与正式 freeze
判定。本次草稿 QA 文档收口不承担这些步骤，也不关闭 Phase 6.2 Gate。
