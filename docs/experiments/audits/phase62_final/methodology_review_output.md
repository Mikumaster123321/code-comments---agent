INDEPENDENT METHODOLOGY REVIEW VERDICT:
PASS WITH NON-BLOCKING NOTES

Critical: 0\
Validity-blocking Medium: 0\
Non-blocking Medium: 0\
Low: 4

审查者身份：本会话实际模型是 Grok 4.7，按本次指派承担 Independent Methodology Reviewer。审查输入为 `docs/experiments/Methodology_Review_Package_V3_1_0_Phase_6_2_v1.md`，版本 v1，提交 `61cbc0db166e1577068101ffbe92b3b58e38e152`，原始 SHA-256 `ac86ceeeb9f4cac880689e7f3bd373be9d7a231c46e732c063f8116c25b05d58`。日期 2026-09-28。本审查未修改 Query、GT、Grade 或源码。

REFERENCE APPROVAL RECOMMENDATION:
ELIGIBLE TO PROCEED

这里的 eligible 只表示：当前实验设计与 reference/evidence 基础没有必须阻止审批的方法学缺陷。它不批准任何 RQ 结果。English Dev Dry Run 仍须等本审查被归档、中文语义记录与最终独立 Data QA 按既有合同绑定，并且 Phase 6.2 Gate 关闭之后。

## Chinese coverage semantic review

判定规则：中文 query 是否能独立作为检索问题；query intent 与已冻结 GT/evidence 是否对得上；只有会实质扭曲检索任务的直译痕迹才记为 MATERIAL。

| query\_id     | natural\_independent\_query | semantic\_alignment | translation\_artifact\_risk | note                                                                                                                                    |
| ------------- | --------------------------- | ------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `zh-sl-py-01` | PASS                        | PASS                | LOW                         | 「请定位 canonicalize\_graph」可独立作为符号查找。冻结 `canonicalize_graph` 按节点键与边键排序后重建 `ProjectGraph`。无对应英文同题。                                         |
| `zh-sl-py-02` | PASS                        | PASS                | LOW                         | 「请定位 validate\_entry」可独立成立。`validate_entry` 拒绝空 `route_id` 并返回合法条目。无对应英文同题。                                                             |
| `zh-fl-py-01` | PASS                        | PASS                | LOW                         | 退款记为正向流水，与 `InMemoryCreditLedger.refund` 使用正 `amount` 入账一致。`validate_integer_amount` 经 `_validate_positive_amount` 提供金额约束，作 Grade 1 合理。 |
| `zh-fl-py-02` | PASS                        | PASS                | LOW                         | 问拒绝记录里编号与原因的保存位置。`IntakeAudit.record` 追加 `(envelope_id, reason)`。与英文 maintenance 题共享符号，问法独立。                                            |
| `zh-dq-py-01` | PASS                        | PASS                | LOW                         | 关闭后的通知出口与文字拼接，分别对应 `notify_closed` 与 `format_message`。                                                                                  |
| `zh-dq-py-02` | PASS                        | PASS                | LOW                         | 入队操作与准入规则对应 `Dispatcher.enqueue` 与 `IntakeRules.accepts`。「解析结果」在该 fixture 中就是待入队 envelope，不改变目标。                                        |
| `zh-bl-py-01` | PASS                        | PASS                | LOW                         | 重新打开工作区失败时的读取逻辑对应 `load_workspace` 的缺失、格式、编码与解析失败返回。`save_workspace` 是写入侧支持证据。                                                          |
| `zh-bl-py-02` | PASS                        | PASS                | LOW                         | `RouteService.reopen` 只把 `status` 改为 `open` 并保存，不恢复 `pending`。与「重开后剩余停靠数未复原」及已写明的 rationale 一致。                                         |
| `zh-mt-py-01` | PASS                        | PASS                | LOW                         | `CancelToken` 是取消状态；`process_batch_with_progress` 在解压与逐文件阶段检查 `is_canceled()`。                                                          |
| `zh-mt-py-02` | PASS                        | PASS                | LOW                         | 拒绝说明由 `IntakeParser.reject_reason` 拼出。与英文 bug 题共享符号，任务意图不同。                                                                             |
| `zh-cf-py-01` | PASS                        | PASS                | LOW                         | `add_stop` 增加 `pending` 后调用 `MemoryRouteStore.save`；`save` 按 `route_id` 覆盖内存记录。                                                         |
| `zh-cf-py-02` | PASS                        | PASS                | LOW                         | 声明校验值来自 `Envelope.declared_checksum`，重算值来自 `compute_checksum`。句中的 envelope 是领域对象，不是 Grade-2 标识符泄漏。                                      |

Chinese semantic coverage: PASS

## 1. Dataset composition

72 条与冻结协议一致。独立计数：English test 48、English dev 12、Chinese coverage 12。English test 为 Python 36 / Java 12，每类任务 8 条，其中 Python 6、Java 2。English dev 为 Python 10 / Java 2，六类任务各 2 条；两条 Java dev 分别是 `symbol_lookup` 的 `ed-sl-ja-02` 与 `dependency_questions` 的 `ed-dq-ja-02`。Chinese coverage 12 条全部 Python，六类各 2 条。项目分配为 self 32、route-ledger 13、intake-queue 13、desk-queue 14。Query 与 `gt-{query_id}` 一一对应。Addendum C 的四条替换句已写入 `queries.jsonl`。

未发现达到 LOW 及以上的配额或分群问题。

## 2. Ground Truth methodology

72/72 为 `annotation_status=drafted`，`reviewed_at=null`。Evidence 134，其中 Grade 2 为 72、Grade 1 为 62，每条至少有一条 Grade 2。这与 Addendum D 的 specification-anchored 材料化路径一致：锚点来自事先规格，记录仍是草稿，不构成逐条人类标注、延迟盲审或 human IAA。

Java limited audit 在审查包、Addendum D §4 与 prepared README 中都被限定为 12 条 English-test Java 的既有证据核查。它没有被写成 72 条 GT 的独立验证。

Issue ID: L-GT-01\
Severity: LOW\
Evidence: Addendum D §2 把 `review_method=delayed_blinded_self_review` 描述为旧记录中的预置字段。`ground_truth/v1/ground_truth.jsonl` 实际没有该字段；状态是 `drafted`，`reviewed_at` 为 null，`primary_annotator_id` 与 `reviewer_id` 为 `wang`。\
Why it matters: 字段叙述比字节更强，但字节本身没有把未完成的人类复核写成已完成。\
Required action: 后续 provenance 以 `drafted` 与 `reviewed_at=null` 为准。不必改 GT。

## 3. Java limited audit

选择规则与数据一致：English test 内按六种 `task_type` 对 `query_id` 字典序取前两条，得到的 12 个 ID 恰好是全部 English-test Java query。12 个执行记录存在。10 条 v1 的逐项 verdict 全部为 `SUPPORTS`，`QUESTIONS` 为 0。两条 v2 没有 `EvidenceReview`。

该审计的有效范围是这 12 条 English-test Java query 上、已引用 span 是否支持既有等级。它不估计 48 条 English test、Python、Chinese coverage 或全部 silver reference 的通过率。审查包与 Addendum D §4 已写明这一边界。

未发现把该便利样本外推成总体质量估计的问题。

## 4. Response-contract failures

`et-bl-ja-01` 与 `et-fl-ja-02` 的正式记录是 schema v2：`evidence_reviews=[]`，`model_verdict=unavailable`，`execution_outcome=CANNOT_ASSESS`，`failure_reason=response_contract_failure`。原始回复仍含无法通过严格解析的正文。`et-bl-ja-01` 在 JSON 前有散文；`et-fl-ja-02` 的 JSON 在结束标记处不完整，且内部引号未按严格 JSON 闭合。自由文本里出现的 SUPPORTS 字样没有被采纳为模型 verdict。

保留失败原文、不修 JSON、不把失败重跑成 SUPPORTS，符合 Addendum D §6 与 Amendment 2。工程规范允许追加 attempt，并要求保留失败尝试。两次失败的先前采集停在格式失败或采集阻塞；被接受的第 4 次采集仍然是合同失败，不是有利 verdict。仓库内的冻结协议没有另立「两次后禁止任何采集」的研究规则；操作笔记中的 recapture cap 不是 Addendum D 条款。

Issue ID: L-AUDIT-01\
Severity: LOW\
Evidence: Amendment 1 写明 response contract 失败时 `reply_complete` 不能为 true。两条 v2 记录却是 `reply_complete=true`，同时 `execution_outcome=CANNOT_ASSESS`。`eligibility.py` 对 v2 的检查是：原始回复必须无法被严格解析，转录只能是这三个执行字段。\
Why it matters: `reply_complete=true` 可能被读成一份合格模型审查。控制结论的字段仍是空 reviews、unavailable verdict 与执行级 `CANNOT_ASSESS`。\
Required action: 审批叙述以这三个执行字段为准。不必重跑，不必把原文改成合法 JSON。

## 5. Source-grounded resolution

两条决议均为 `source_verification/closed`，`gt_or_grade_changed=false`，执行结果仍保持 `CANNOT_ASSESS`。独立核对冻结 fixture 后，span 与行为一致：

- `et-bl-ja-01`：`Ticket.isOpen` 仅在 `status.equals("open")` 时为真，Grade 1；`DeskQueue.listOpen` 返回 `folder.entries.length`，不按状态过滤，Grade 2。
- `et-fl-ja-02`：`Ticket.markClosed` 执行 `status = "closed"`，Grade 2。

这可以作为 Reference Approval 的补充依据：它只确认已引用证据与冻结源码、prepared evidence 和未改动 GT 一致。它不把模型 verdict 改为 `SUPPORTS`，也不证明项目中没有其他相关 Symbol。`DeskQueue.closeTicket` 会调用 `markClosed`，但该 query 的已引用直接写入点仍然成立；决议自己写了只检查已引用证据。

Issue ID: L-RES-01\
Severity: LOW\
Evidence: 两条 `record.json` 的 `resolution_identities` 仍为 `[]`。关闭关系写在独立 `ResolutionRecord` 中，`target_identity` 分别指向 `76334e61…` 与 `d8c74c81…`。\
Why it matters: 只读执行记录会以为两条仍未决议。旁路决议文件已经闭合，且方向符合「原始证据不回写」的生命周期。\
Required action: 创建 approval 时显式绑定这两个 resolution identity。不必因此修改 GT。

## 6. Chinese semantic review

机械配额与上一节的逐条语义核查一致：12 条、全部 Python、六类各 2、GT 12/12、相关证据 19（Grade 2 为 12，Grade 1 为 7）。语义覆盖结论为 PASS。Java audit 对这 12 条没有证明力，项目文本也没有把 Java audit 写成中文审查。

Issue ID: L-ZH-01\
Severity: LOW\
Evidence: Reference Lifecycle Engineering Specification §4 要求中文核查的规则、输入、verdict schema 与身份在执行前冻结，并写明不能从对话推断 PASS。本次判定规则来自本次审查任务；仓库中还没有 `chinese_coverage_audit` 身份。Final Closure 报告也写明最终独立 Data QA 尚未签发。\
Why it matters: 语义内容已经在本审查中成立，但聊天记录不是仓库 Source of Truth，不能单独充当审批前置身份。\
Required action: 将本审查的 12 条判定归档为中文核查记录，再由最终独立 Data QA 绑定该身份与本方法论审查身份。不必因措辞风格改写这 12 条 query。

## 7. Leakage control

按 Addendum C 的 `code-lexical-v1` 规则，对每条非 `symbol_lookup` query 检查 Grade-2 simple name 的首个 identifier token。72 条均未命中。空 token 序列为 0。Query 文本中没有 `src/com/desk` 或路径形式的答案位置。两条中文 `symbol_lookup` 含简单名，这是该任务的既定许可。

未发现把 Grade-2 答案标识泄漏进非 `symbol_lookup` query 的问题。

## 8. Independence / circularity

角色分离与合同一致，未形成会使比较失效的循环验证：

- 主参考来自事先规格锚点的机械材料化，状态保持 `drafted`。
- DeepSeek 看到的是既有等级与理由，任务是检查所引 span 是否支持它们。Addendum D 已说明这不是盲注重判。
- 两条合同失败没有被模型原文改写成 `SUPPORTS`。源码决议使用冻结源码与 prepared evidence，没有改 Grade。
- 本外部审查单独核对了配额、泄漏、两条 span 和 12 条中文语义，没有反过来修改标签。

同一开发链路既材料化锚点、又做这两条源码复核，因此源码决议不是第二标注者。Addendum D §9 已要求论文披露这一点。在「相对固定 specification-anchored reference 比较系统」的范围内，这不构成严重 circular validation。

## 9. Formal RQ boundary

审查过的协议、审查包、Final Closure 报告与 `identity.json` 均把 Formal RQ1–RQ4 标为未开始；`retrieval_runs_before_freeze` 为 0。仓库 `docs/experiments/` 下没有正式结果表。Dataset QA、Java audit 与本方法论审查只能作为 benchmark/reference readiness evidence。它们不能写成 RQ1–RQ4 的实验结果。

未发现越界写成正式结果的问题。

## 10. Known limitations

这些限制已写在 Addendum D §3 与 §9，本审查确认它们仍然有效：

- 主结果只能解释为相对这 72 条 query、冻结源码和固定 specification-anchored reference 的系统比较。
- 未被列入 Grade 1/2 的候选在指标中按 0 分计，其含义是「未被该参考列入」。遗漏真实相关证据是构念效度限制。
- 12 条 Java audit 是确定性便利样本，只核查已引用证据。
- 没有逐条人类标注、延迟盲审或 human IAA，也不能外推到外部项目。
- English dev 只用于后续 Dry Run；Chinese coverage 单独报告。
- Addendum D §10 末段仍写着 audit NOT STARTED。该句是合同写入时的状态。当前执行计数以 12 份执行记录和审查包为准。这是历史状态句，不改变方法条款，因此不单列阻断项。

PROMPT COMPLETENESS:
CONFIRMED

END MARKER:
SEEN

\=== END OF INDEPENDENT PHASE 6.2 METHODOLOGY REVIEW ===