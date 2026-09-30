# Phase 6.2B 独立重判工作页

**PREPARATION ONLY / NOT REVIEWED**

本页与 `queries_for_second_judgment.jsonl`、`source_catalog.json`、`sources/`
组成独立的遮蔽材料包。它仅列出 72 条冻结 Query 与四个项目的全部 93 个冻结
源码文件。源码目录按项目及原始相对路径排列；目录顺序、文件列表和 Query
顺序均不表示候选优先级。不要从包含原始标注或检索结果的仓库视图执行重判。

## 开始门禁

初稿时间为 `2026-09-23T04:00:42.357095+00:00`。实际开始时间必须不早于
`2026-09-25T04:00:42.357095+00:00`（北京时间
`2026-09-25 12:00:42.357095`）。材料准备、复制或阅读本说明均不表示复核
已经开始；到时也不自动开始。由 `wang` 自行决定并记录真实开始与完成时间。

## 独立判断操作

1. 在仅含本材料包的独立目录工作。开始前查看目录是否只有本说明、空白 Query
   工作页、完整源码目录及完整源码目录清单；如可访问原始标注或检索排名，
   停止并重新隔离。真实观察写入 `masking_observation`，不要预填成功结论。
2. 复制空白工作页为新的可写文件，保留原始空白页。逐条读取 `query_id`、
   `query_text`、`language`、`task_type`、`project_id`、`split`。
3. 只按 `project_id` 打开 `source_catalog.json` 对应项目的**完整**文件列表，
   再在 `sources/<project_id>/` 中自行查找冻结源码。清单不按 Query 筛选，
   不提供初始候选、符号、span 或高亮。
4. 在 `review` 中填写实际 `reviewer_id=wang`、`started_at`；对每条 Query
   独立写下自己的 `evidence`。每项 evidence 记录源码相对路径、能识别的
   Symbol 身份、源码 span、相关性等级 `0/1/2` 与理由；允许多项。如判断
   没有相关源码，也要明确填写 `no_relevant_source_found` 与理由，不能用
   尚未填写的空数组暗示结论。
5. 难以判断、多个可能候选与需要稍后裁决的问题，分别记录在
   `uncertainty_notes`、`candidate_ambiguities`、`questions_for_adjudication`。
   中文 Query 的非机械直译判断写入 `chinese_non_translation_notes`。
6. 全部独立判断完成时，填写真实 `completed_at`。先保存并固定这份第二次
   判断及其文件哈希，再交给比较步骤；在固定前不要打开原始标注、先前
   比较结果或检索结果。比较与裁决说明不属于本遮蔽材料包。

`review.evidence` 起初是空数组，填写时每个候选可使用以下**全空白**结构，
不得把它误作已有判断：

```json
{
  "relative_path": null,
  "symbol_id": {
    "language": null,
    "relative_path": null,
    "qualified_name": null,
    "kind": null,
    "semantic_disambiguator": null,
    "fallback_line": null
  },
  "start_offset": null,
  "end_offset": null,
  "start_line": null,
  "end_line": null,
  "relevance": null,
  "rationale": null
}
```

Symbol 身份字段可先按冻结源码独立记录，再由后续受信任步骤按现有 adapter
核对完整身份。span 的 offset 使用 LF 规范化源码上的零起点、end-exclusive
位置；行号从 1 开始。不得根据 Query 字面或文件排序预设答案。

本包的结构检查只能说明准备时未放入初始判断。它不能证明 `wang` 未来
实际没有通过别的途径看到原始标注，也不能代替真实的延迟盲自审记录。
