# V3.1.0 Phase 6.2B.2 Raw Reply Boundary 澄清报告

## 范围与版本

- 起点：`v3.1.0-dev`，HEAD `b9df2870ebb73dcd646755c2abd7ac6b7ac2947c`；tracked 工作区与暂存区为空，用户已有 `?? docs/thesis/` 未读取、修改或暂存。
- 机制：冻结 [Engineering Specification v1](../experiments/Reference_Lifecycle_Engineering_Specification_V3_1_0.md) §1 允许 `v2` 或 versioned amendment；本轮采用最小的独立 [Amendment 1](../experiments/Reference_Lifecycle_Engineering_Specification_Amendment_1_V3_1_0.md)，ID `v3.1-phase62b-raw-reply-boundary-a1`、版本 `v1`、原始字节 SHA-256 `5cf10c271268ac7cbcd45f718a3f519bb2783e115db51f4834ec010088d3dffa`。原 Engineering Specification v1 hash `6b3bb3200ee6cec43efc1620e7da2e467cfe57055e4e79b7953c8962bc5fa045` 与 Addendum D v1 原文件均不变。
- 性质：版本化合同边界澄清，不是 EvidenceAudit execution、GT/Query 修改、Reference Approval、Phase 6.2 Closure、Dry Run 或 Formal RQ。此文件与 amendment 的提交以 Git 历史为准，不嵌入自身 commit SHA。

## 决定与实现边界

`raw_reply` 精确定义为平台向用户提供、用户可以完整导出的 Final Answer 原始字节。`reply_complete=true` 仅声称此 exportable final response 从首字符到末字符完整留存，并要求原始字节/hash、结束标记、JSON/response contract 与导出范围证据；它不声称不可导出的 Thinking 或隐藏推理已捕获。单独可见且可完整导出的 Thinking 作为独立 `visible_thinking` raw capture/hash 留存；单独可见但不可完整导出时，`visible_thinking=unavailable(reason)`、`capture=null`，reason 与 provenance 明确说明 UI 可见和导出限制；UI 无单独 Thinking 区时采用不同 reason，不混淆两种状态。Thinking 不直接决定逐证据 verdict，不能通过截图/OCR/推测重建。

现有 `Availability`、`VisiblePart`、`RawCapture` 与 `EvidenceAuditRecord` 已能表达该组合；`experiments/` 实现和 tests 均未修改。原合同的 exact sent input、独立会话、真实时间、model provenance、原始回复与 privacy 校验、derived verdict、append-only attempt 和后续批准门禁未放宽。现有 `current_gate.json` 仅能以 schema 合法值保留 `6.2B.2 / ALLOWED BUT NOT STARTED`；本报告的“proof not yet completed”是事实陈述，不创建新 gate 枚举或授权。

## 验证与状态

- 修改前离线基线：`python -m pytest -p no:debugging`，**775 passed**。当前主机普通 `python -m pytest` 的 Anaconda Python 3.13 debugging-plugin 段错误为既有环境问题。
- 纯合成 schema 验证：构造 `visible_thinking=unavailable` 且 reason 明示 UI 可见/无法完整导出、`capture=null`；`visible_final=available`、`raw_reply` 指向完整 Final capture、`reply_complete=true`，`EvidenceAuditRecord` 构造及严格往返通过；试图在 `unavailable` Thinking 上附加部分 capture 被拒绝。未创建正式 artifact 或调用外部模型。
- 文档修改后的全量回归：`python -m pytest -p no:debugging`，**775 passed**，与修改前基线一致。
- `et-dq-ja-01`：用户报告首次真实 capture 使用 fresh session、Final Answer 可导出、Thinking 在 UI 可见但完整导出 unavailable；原始 capture 与其他 provenance 尚待按新合同核验。本轮未 materialize，正式 Java Evidence Audit **0/12**。
- Phase 6.2B.2 **ALLOWED BUT PROOF NOT YET COMPLETED**；Reference Approval **NOT CREATED**；Phase 6.2 **OPEN**；Phase 6.3 **BLOCKED / NOT STARTED**；Formal RQ1–RQ4 **NOT ELIGIBLE / NOT STARTED**。下一步是重新验证同一次 `et-dq-ja-01` capture，不重新调用 DeepSeek。
