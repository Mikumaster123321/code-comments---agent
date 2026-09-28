# V3.1.0 Phase 6.2 Java Evidence 响应映射修复

## 根因与合同裁决

**ROOT CAUSE VERDICT: EXTERNAL/INTERNAL MAPPING BUG。** 起点为 `v3.1.0-dev` / `554490c75e9146478abf8088ca79d1dc6264fa4d`，tracked 工作区与暂存区无改动；用户已有 `docs/thesis/` 未读取、列举、修改或暂存。普通 `python -m pytest` 在主机 Python 3.13 的 pytest debugging 插件初始化时段错误；按任务指定的 `-p no:debugging` 基线为 **775 passed**。

Source of Truth 包括 Protocol、Addenda A–D、Dataset/Query/GT Specification、Reference Lifecycle Engineering Specification v1 与 Raw Reply Boundary Amendment 1，以及冻结 prepared generator、12 份 input/blank record。Addendum D §5 和工程规格 §3 冻结的是有限审查的语义、三值 verdict、完整证据身份、原始回复与逐项转录边界；prepared prompt 明确要求顶层 `query_id`、`overall_status`、`evidence_reviews`、`scope_statement`、`end_marker`，以及逐项 E 编号、原始文件/SymbolId/span、源码行为或原因、span/Grade 怀疑。**它没有要求 DeepSeek 输出 `EvidenceReview.to_record()` 的六个内部字段，也未冻结逐项 JSON 的唯一字段名。** 因而 loader 原有 `raw evidence_reviews == [EvidenceReview.to_record()]` 属错误接口假设，不能据此判定模型全面违约。

外部 capture manifest 中 10 份 `CAPTURE_READY` 原始 Final Answer 各自通过 manifest SHA-256 校验；`et-dq-ja-01`、`et-cf-ja-02`、`et-mt-ja-01`、`et-bl-ja-02` 从原始 bytes 均复现 `audit_reply_reviews_mismatch`。10 份回复顶层五字段一致，但逐项出现十种完整字段形状，例如 `status`/`verdict`、`preserved_identity`/`source_identity`/`identity_preserved`、`source_behavior_check`/`observed_behavior` 与多种 Grade 疑点字段。部分身份以扁平字段呈现，部分 SymbolId 只重复了足以与同一 prepared 项交叉核验的路径、qualified name、签名及 span；缺省的内部身份字段只从冻结 prepared evidence 派生，绝不采信模型自由文本补全。

四个核心问题的答案：Q1 **否**，prepared prompt 没要求内部六字段；Q2 旧 loader 把外部 DTO 错当内部 record；Q3 10 份 READY 回复满足提示要求的顶层及逐项语义，逐项字段名未被提示限定，其中不完整复写的 SymbolId 分量通过 path/name/signature/span 与 prepared 唯一身份交叉核验；Q4 **可以**，严格解析与确定性映射不改变 raw bytes、模型 verdict、Grade、GT 或研究方法。不能证明完整 UI 导出范围的另外两份 capture 继续 BLOCKED。

| 外部响应 | 内部 `EvidenceReview` | 处理 |
| --- | --- | --- |
| 顶层 `query_id` | `EvidenceAuditRecord.query_id` | 与 prepared / audit query 严格相等 |
| 逐项 `evidence_id` | `evidence_id` | 与 prepared E 集合恰好一致，无重复或遗漏 |
| `status` 或 `verdict` | `verdict` | 仅三值枚举；逐项状态推导并核对顶层 `overall_status` |
| 文件与 SymbolId 表示（嵌套或扁平） | `evidence_identity` | 对所有呈现字段逐项核对 prepared `original_identity`；完整 canonical hash 从 `(query_id, original_identity)` 生成 |
| `span` 与可选原 Grade | `source_locations` / `grade_observation` | span 四字段严格相等；显式 Grade 若存在必须等于 prepared；位置由经核对的 prepared 身份确定 |
| 源码行为、理由、Grade 判定、疑点及附注 | `reason` / `grade_observation` | 已识别的完整逐项形状才接收；相关模型内容以确定性 JSON 保留，不以模型判断改写 Grade/GT |
| 顶层 `scope_statement`、`end_marker` | 外部 parsed response | scope 非空；end marker 与 query 严格匹配；原始回复持续由 `raw_reply` bytes/hash 留存 |

## 实现和边界

`experiments/reference.py` 增加严格外部解析与确定性 normalization：UTF-8 JSON、重复键/非有限值、顶层 exact 字段、十种观察到的逐项 exact 字段形状、基本类型、可选嵌套结构、E 集合、身份/SymbolId/span/Grade、verdict/overall/end marker 均受检验。未知字段、非法类型或无法映射的未来布局 fail closed，不把模型文本直接反序列化成内部记录。输出同时包含已解析外部响应与按 E 编号排序的内部 `EvidenceReview`；原始 bytes 从不修改。

`experiments/eligibility.py` 先验证 raw capture hash、完整 Final 与 raw reply 同 hash，再从原始 raw bytes 重算外部解析及 normalized reviews；只有它们与独立存档的 canonical `EvidenceAuditRecord.evidence_reviews` 完全相等才通过，转录 hash/内容仍单独核验。原有 Reference Approval、Phase 6.2 Closure、Dry Run Receipt、current_gate 及 Formal fail-closed 权限链不变。合成测试的外部回复改为实际语义 DTO，保留原授权链路验证。

此次是工程接口映射修复，不修改 Protocol、Addenda、Dataset Specification、prepared inputs、Dataset/Query/GT、检索实现、模型 verdict 或冻结 Grade。十种逐项字段布局是对现有 raw capture 的保守适配，**不是声称这些字段名原先被方法文档逐字冻结**；新布局必须另行显式审核和实现，不自动忽略未知字段。

## 验证与状态

- 真实 10 份 READY capture 的只读验证：manifest SHA-256、raw parse、exact 外部布局、身份/SymbolId/span/Grade 交叉核对、overall/end marker、normalization 与 `EvidenceReview` 构造均 **10/10 PASS**；没有正式 materialize EvidenceAudit。
- prepared verifier：**PASS，12 inputs / 23 evidence / 12 blank records**。
- 新增针对缺字段、未知字段、错 query/E/SymbolId/span、非法 verdict、overall 矛盾、重复/遗漏 E、raw 不变、排序、恶意字段、bool/type 与重复 JSON 键的离线测试；既有合成 Formal 授权/拒绝测试继续覆盖 Draft GT、legacy gate、current_gate、Approval、Closure 和 Dry Run Receipt。
- 专项回归（Reference lifecycle、Phase 6.2 dataset contract、离线 LLM contract）**171 passed**；全量 `python -m pytest -p no:debugging` **794 passed**，基线为 775；无真实模型、Provider、网络或正式 RQ 调用。

Formal Java Evidence Audit **0/12**；Reference Approval、Phase 6.2 Closure、Dry Run Receipt 均未创建；Phase 6.2 **OPEN**，Phase 6.3 **BLOCKED / NOT STARTED**。下一动作是对现有 10 条 READY capture 重新执行 batch materialization；另外两条 BLOCKED capture 不计入本次成功数。本轮不新增子 Phase 或独立 QA。
