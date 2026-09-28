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


## Phase 6.2 Java Evidence Batch Materialization — RETRY（2026-09-28）

起点 `v3.1.0-dev` / `a6cc001aad5f5c9588d46fa756b669bf06e6f075`，原有未跟踪 `docs/thesis/` 未读取、修改或暂存；执行前正式 Java Audit 为 **0/12**。使用仓库外既有 capture workspace 的 `capture_manifest.json`、`recapture/stage1_review.json` 和 `recapture/partial_progress.json`；未重新调用 DeepSeek，未对 verdict、Grade 或 Query 作判断。

逐条从原始 Final Answer bytes 重算 SHA-256，核对 manifest 的长度/hash、prepared input hash、实际 recapture sent bytes（适用时）、Query/GT/E 集合、source/SymbolId/span/Grade、顶层五字段、scope/end marker、隐私扫描与来源标记。调用 `a6cc001` 的 strict parser 与确定性 normalization；10/10 通过。原始 reply bytes 未改写。其真实首份合格回复均为 `SUPPORTS`，逐项 verdict 原样转录。

经用户明确裁决，正式 `attempt_number` 使用真实 capture attempt 编号（1/2/3）；第 2/3 次成功者设 `supersedes_attempt=attempt_number-1`。此前失败 attempt 的分类、原因、来源文件名与 raw SHA-256 单独存于各成功目录的 `failed-attempts.json`；失败原文留在仓库外 capture workspace，其中隐私扫描失败的 Copy All 不进入 Git，也不充当 completed audit。`et-cf-ja-01` 后续 attempt 3 同样仅记为未选中的失败 capture，首份合格的 attempt 2 保持选中。

正式 `EvidenceAuditRecord` 由 canonical serialization 和 append-only artifact writer 发布；目录中的 `record.json`、raw sent input、raw reply、外部 parsed response、内部 normalized reviews、transcription、provenance 和 checksums 分别保存。`visible_final` 指向原始 Final Answer；无法完整导出的独立 Thinking 明确记 `unavailable`。界面 task locator、观测模型名、alias 来源及时间精度取自既有 capture 记录；`ended_at` 为文件捕获时间，**不是精确模型完成时刻**，限制已在 record 中说明。平台 session ID、精确 revision、token usage、finish reason 未获证实，均记 `unavailable`。没有把这些限制解释成平台内部版本证据。

由原有 72 条 drafted GT 机械派生的候选 Reference content 写入 `docs/experiments/reference/v3.1-phase6-spec-anchor-reference-v1.jsonl`，collection identity 为 `d3d5f54f8256b2dadd151f26cd0f1f7674c1c62fa464846fb13bc5c295dc8f04`；它仅为 audit lineage，不是 Reference Approval，也未使 Draft GT 变成 frozen。

| Query | 正式 attempt | 原 verdict | EvidenceAudit identity | raw reply SHA-256 |
| --- | ---: | --- | --- | --- |
| `et-bl-ja-02` | 2 | `SUPPORTS` | `789c919d08d254dd7ae66d6eace97c9d0907882a8c055d9cd9a23a6a2a0ec5df` | `62164b63f829b7a3195bb274eb2c070b02327851bedfe1d66a71948be4e2da8e` |
| `et-cf-ja-01` | 2 | `SUPPORTS` | `ed622fabb000173b2620cf0ff47b3b3bf81c87b57c62fdd5211628a86133d1a6` | `241ae35d06a9af3170413e5516b2abf5d8db64e4def338df1f9bc5d96ece436e` |
| `et-cf-ja-02` | 1 | `SUPPORTS` | `cbc90b9feaf2e20fde1441d7268f24251762dc856712fb1974522ef251060d04` | `b78935b156639bbf7be62d32197457439a7306293b07392178a557abceea78d8` |
| `et-dq-ja-01` | 1 | `SUPPORTS` | `f39ce549a52d65c9f1c526e30bbd0a4b65e067c96ca818de0ecbf62d2f5d836d` | `7e3da8851343628f7833f5da1c7cd48c4c1531a1cc116212f7bb8486293aaeac` |
| `et-dq-ja-02` | 3 | `SUPPORTS` | `36e64819624fbbf9ec7bff4f8e0e94ab927139fe081e2ed835c2b10c0eaed2e7` | `a3e294fce157175592ddae98ddc1d10cb51985c3ba5d893edf5f3786ebeadb73` |
| `et-fl-ja-01` | 1 | `SUPPORTS` | `2f83516ca22e438725713cffe335e14305176a53466e7e76888fd0b24c2b6cfc` | `103945074233ea77dad4d1154a4a9c988413911d6f534be6d482b8aa85821fe7` |
| `et-mt-ja-01` | 1 | `SUPPORTS` | `53404b2822bfcb715de4e79e4eaf3c4df59c3dd41b89cdef32eb52619c76d21f` | `8976426de59961aca599aff06343eaa147a2c9990f0abdedc9e82442182fad78` |
| `et-mt-ja-02` | 1 | `SUPPORTS` | `98ebbcd282e13d67d3db4cb472914429f9ef14d1c5c3546677361fb76d832932` | `9430c7bb360b668fdec0eef8ab551bd60ba570ce31a972ffe4e5159a4b4813d9` |
| `et-sl-ja-01` | 2 | `SUPPORTS` | `2d6026dfe88f43443c18656a1f1370ac9c8f27292c516aae97dc663fc63009ba` | `cf657cea5cac15dad5817daf780a8896e45d71a24d600916ed800853491332dc` |
| `et-sl-ja-02` | 2 | `SUPPORTS` | `8b4a5b8657912ffbffe6a210f46e59c54102b9ce02bf6b41fb42d7dc1d32451c` | `daada6af0d437b21703046251c3a6a68add91a990eecfedbcc72a2a710dd96fd` |

写盘重载对 10 条逐一检查 schema、identity、各 blob hash、raw bytes、external→internal normalization、Query/E cross-reference、transcription 与 append-only 目录，**10/10 PASS**；候选提交态下的 `RepositoryAuthority.load_audit()` 与仓库外原始 raw bytes 对照也是 **10/10 PASS**。prepared verifier **PASS：12 inputs / 23 evidence / 12 blank records**。相关专项 **172 passed**；候选提交态全量 `python -m pytest -p no:debugging` **795 passed**（初始基线 794）。Query **72**、Draft GT **72/72**、Evidence **134**；原 Query/GT/Grade/rationale/span/prepared input 均未修改。

Formal Java Evidence Audit **10/12**；`et-bl-ja-01`、`et-fl-ja-02` 保持 **BLOCKED / NO FORMAL AUDIT**。Reference Approval、Phase 6.2 Closure **NOT CREATED**；Phase 6.2 **OPEN**；Phase 6.3 **BLOCKED / NOT STARTED**。
