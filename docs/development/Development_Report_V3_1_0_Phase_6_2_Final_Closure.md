# V3.1.0 Phase 6.2 Final Closure 准备报告

- 结论：**READY FOR EXTERNAL METHODOLOGY REVIEW**；Reference Approval 与 Phase 6.2 Closure **未创建**。
- 初始 HEAD：`95de94caa5f26793804248585c55ffee24d4dd06`；分支 `v3.1.0-dev`。原有未跟踪 `docs/thesis/` 未读取、列举、修改、暂存或提交。
- 方法边界：Addendum D §10.1 明确要求实质方法变更的独立方法论审查在 Reference Approval 前归档；§8 另要求中文非机械直译独立语义核查。缺少这两项时不得签发最终独立 Data QA PASS、批准或关闭 Phase 6.2。

## Java audit 与源码决议

12/12 执行；10/12 结构有效、模型 `SUPPORTS=10`、`QUESTIONS=0`；2 条执行级 `CANNOT_ASSESS`，模型 verdict 均 unavailable。Amendment 2 要求这两条在审批前作独立源码决议，不能直接当作 `SUPPORTS`，也不要求再次调用 LLM。既有工程规范 §4 的 `source_verification` 和 `ResolutionRecord` 是合法机制。

| Query | 冻结输入与源码核验 | 决议 |
| --- | --- | --- |
| `et-bl-ja-01` | `E01` 的 `Ticket.isOpen` 在 `src/com/desk/model/Ticket.java:16` 仅接受 `open`，支持 Grade 1 预期行为；`E02` 的 `DeskQueue.listOpen` 在 `src/com/desk/service/DeskQueue.java:38` 直接返回 `folder.entries.length`，支持 Grade 2 故障定位。两项文件、完整 SymbolId、span、prepared evidence、GT 理由和等级与 JavaAdapter/冻结源码一致。 | `SUPPORTED_BY_FROZEN_SOURCE`；[核验证据](../experiments/audits/source_resolution/et-bl-ja-01.json)；resolution identity `1680c6463324907a8f39e11f8a1e5b52ff79a79c71ea628078eeed9d89b8bc37`。 |
| `et-fl-ja-02` | `E01` 的 `Ticket.markClosed` 在 `src/com/desk/model/Ticket.java:17` 将 `status` 设为 `closed`；文件、完整 SymbolId、span、prepared evidence、GT 理由与 Grade 2 一致。 | `SUPPORTED_BY_FROZEN_SOURCE`；[核验证据](../experiments/audits/source_resolution/et-fl-ja-02.json)；resolution identity `ac39e3072674ef7740eb53a194c8b2cc00bca3edf73ce8529ed25344faa26b1d`。 |

核验没有从非法 DeepSeek 原文提取 verdict；原始执行历史保持 `CANNOT_ASSESS`，Query/GT/Grade 未改。核验范围只覆盖既有引用证据，未搜索所有潜在相关 Symbol。

审批入口原先无条件拒绝 v2 记录；本轮按既有 `source_verification` 机制补上受约束的处理：类型化关闭决议必须指向准确的 v2 audit，核验证据原始 hash、Query/准备输入/证据身份、SymbolId/span/Grade 和冻结源码必须匹配；缺失或篡改仍 fail closed。此工程修复不构成 Reference Approval。

## Chinese coverage 与 Final Dataset QA

中文机械覆盖检查 **PASS**：12 条互异 `zh-*` Query；六类任务各 2 条；全部 Python；三个 Python 项目各 4 条；GT 12/12，相关证据 19 项（Grade 2 为 12、Grade 1 为 7）；Query/GT/dataset 身份相符。既有 dataset contract 测试覆盖来源表逐字一致性、SymbolId/span、Grade、配额、近重复、Grade-2 标识符泄漏、允许的跨语言证据重叠和源文件身份，全部通过。**中文非机械直译独立语义核查仍 PENDING**；机械检查不能替代 Addendum D §8 的审查，也不能使中文审批前置条件 PASS。

最终数据机械预审 **PASS**：Query 72（English test 48、English dev 12、Chinese 12），GT 72/72 `drafted`，Evidence 134，ID 唯一、无缺失或孤立 GT、各 split/语言/任务配额正确，相关 Grade 为 1/2 且每条至少有 Grade 2；冻结 manifest、源码、SymbolId/span、泄漏与 checksum 测试通过。12 条已提交 Java 执行 artifact 逐项通过 `RepositoryAuthority.load_audit`，prepared verifier 验证 12 输入和 23 项证据。dataset hash `164994a826fe51936d5fcb012a8d102967c33110787405fd3b0f7972efe8ade7`；query hash `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`；旧 drafted GT hash `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87`；候选 Reference hash `d3d5f54f8256b2dadd151f26cd0f1f7674c1c62fa464846fb13bc5c295dc8f04`。冻结 checksum 链和方法/工程身份验证通过。当前未发现数据 Critical 或影响实验有效性的 Medium。**最终独立 Data QA 尚未签发**，其结论必须绑定中文语义审查与外部方法论审查真实身份。

## 验证与下一授权动作

- prepared verifier：PASS，12 输入、23 证据、完整冻结源码、12 空白模板。
- Phase 6.2 dataset/reference lifecycle/benchmark 专项：222 passed。
- 全量 `python -m pytest -p no:debugging`：798 passed。普通 `python -m pytest` 在本机 Python 3.13 的 pytest debugging 插件载入 `rlcompleter` 时发生 segmentation fault；测试本身未执行，关闭该插件后 798 项全部通过。
- [只读方法论审查包](../experiments/Methodology_Review_Package_V3_1_0_Phase_6_2_v1.md) 原始 SHA-256：`ac86ceeeb9f4cac880689e7f3bd373be9d7a231c46e732c063f8116c25b05d58`。
- Formal RQ1–RQ4：0 次、NOT STARTED；Phase 6.3 English Dev Dry Run：NOT STARTED。
- 下一动作：将 [只读方法论审查包](../experiments/Methodology_Review_Package_V3_1_0_Phase_6_2_v1.md)交外部 reviewer，归档真实结论；按 Addendum D §8 预先版本化并完成中文非机械直译独立语义核查，再完成最终独立 Data QA。只有所有先决证据齐全且正式 eligibility validator 通过后，才能创建 Reference Approval；之后才可创建 Phase 6.2 Closure 并将 Phase 6.3 标为 ALLOWED BUT NOT STARTED。不得提前执行 Dry Run 或正式 RQ。
