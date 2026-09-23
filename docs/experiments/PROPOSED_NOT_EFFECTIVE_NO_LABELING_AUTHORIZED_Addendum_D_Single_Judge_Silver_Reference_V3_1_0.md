# PROPOSED / NOT EFFECTIVE / NO LABELING AUTHORIZED — V3.1.0 Phase 6.2 Addendum D 候选提案：Single-Judge LLM Silver Reference

> **PROPOSED / NOT EFFECTIVE / NO LABELING AUTHORIZED**
> 本文是方案提案待用户裁决，不是生效的 Addendum D，不授权任何标签生成、
> schema/loader 变更、数据冻结、Dry Run 或正式实验。下文的“应／必须”均为
> 候选合同要求。未正式批准并版本化之前，原 Protocol + Addenda A/B/C 继续有效。

- Proposal ID：`v3.1-phase6-addendum-d-proposal-01`；草案日期：`2026-09-23`。
- 生效日期、批准记录、精确 judge 版本：**未确定**；不是默认批准。
- 入场 branch：`v3.1.0-dev`；HEAD：`0d8ca949658673da40246593772ff53c62e3f45d`。
- 入场工作树与暂存区无已跟踪改动，仅 `?? docs/thesis/`；未读取、列举该目录内部。
- Dataset / Query / GT：**DRAFTED / DRAFTED / DRAFTED**；Phase 6.2 Gate：**OPEN**；
  Phase 6.3：**BLOCKED / NOT STARTED**；Formal RQ1–RQ4：**NOT STARTED**。
- Grok 方法论建议及本次任务中的候选方法仅是设计输入，不是已生效规范；没有
  据此宣称完成独立方法论评审，也没有自动替代 Claude 的 Primary Reviewer 角色。

## 1. 权威依据、已有事实和待改写范围

已核对当前 Git 跟踪的 [Protocol](Experiment_Protocol_V3_1_0.md)、
[Addendum A](Experiment_Protocol_Addendum_A_V3_1_0.md)、
[B](Experiment_Protocol_Addendum_B_V3_1_0.md)、
[C](Experiment_Protocol_Addendum_C_V3_1_0.md)、
[Dataset Specification](Dataset_Query_GroundTruth_Specification_V3_1_0.md)、
[6.2A QA closure](../qa/QA_Report_V3_1_0_Phase_6_2A_Independent_Draft_Data.md)、
[6.2B 准备 QA closure](../qa/QA_Report_V3_1_0_Phase_6_2B_Blinded_Review_Preparation.md)、
`datasets/v1/identity.json`、Query/GT/audit 结构、`experiments/schemas.py`、
`baselines.py` 的 registry/TruthMapper、`metrics.py`、runner 入口、数据合同测试，
以及 [现有遮蔽包生成器](blind_review/prepare_bundle.py) 和准备说明。

现行方法要求 `wang` 在至少 48 小时后作真实 delayed blinded self-review。
当前机械草稿记录 `reviewed_at=null`，并不证明人类已逐条标注或复核。
用户本次表示不进行逐条人类盲审，因此现行人类路线不能冒充已完成，须等待方法变更裁决。
6.2A/B 的 CLOSED 只指各自准备／QA 文档事项，不关闭 Phase 6.2。

### 1.1 可沿用的合同

Protocol §3–4 的冻结源码、manifest、72 条 Query 及 48/12/12 分组；§5.1 的
单一 canonical evidence 和禁止被评估 retriever 自标；§5.2 的 2/1/0 数值含义、
未列项映射为零及非空相关集要求；§6 的 File/Symbol/Chunk 映射；§7 的全部指标
和分母；§8–10 的检索配置、E5 身份、RQ 矩阵和性能边界；§11–16 的可复算、
失败、版本化、结果纪律和门禁顺序均继续沿用。原条款中的“human”来源含义不能沿用到银标签。
Addendum B 的增量 5/2/2/0 与七个新 embedding 文档完全不受本方案影响。

### 1.2 必须由正式版本逐项改写的条款（本轮一项也未生效）

| 现行位置与含义 | 候选改写及限制 |
| --- | --- |
| Phase 0 Architecture Decision 的 human-primary GT、Phase 0 QA 研究基线及 PROJECT_CONTEXT Frozen Decisions | 正式 D 必须明确限定本 72-query 实验的 silver 例外与研究结论降级，并经独立方法论评审；不能只改 Phase 6 字段而留下上层 human-primary 假象。旧架构/QA 作为历史记录保留。 |
| Protocol §5.1、§5.3–5.4；A §2–4、§6–7；Spec §10、§14–15 | 用单一指定模型的独立逐查询判断作为新 reference，建立独立 method/lifecycle/provenance；不再以 human 48 小时延迟作为新模型路线完成证据。原人类记录、时钟和语义原样保留。 |
| A §5 的“模型只作 QA”范围 | 仅对新 silver namespace 显式扩展为模型标签来源；独立 Data QA 仍是 QA，绝不变成人类第二标注者或 human IAA。 |
| Spec §4 表格固定 Grade-2/1 锚点；C §1–2、§5 对锚点不变的声明 | 仅把旧锚点保留为 v1 草稿历史／后验审计参照；新发现不受锚点交集或否决约束。C 的四条 Query 更正及冻结 Query 字节继续有效。 |
| Spec §5 的 Grade 0 仅用于已裁决 negative；Protocol §5.2 的 unjudged | 新 silver Grade 0 可记录该 judge 明确的负判断；未列出项仅在完整覆盖成功后按 silver-negative 进入零分映射，不称人类确认不相关。不批量制造所有候选 Grade 0 记录。 |
| Spec §7、§8、§13 的相关项配额与指定 truth probes | 提议将“银标签必须符合旧锚点／相关性配额”改为透明差异诊断；原 v1 准备检查历史仍保留。源码长度、固定分块、真实映射算法测试继续强制有效。不为凑配额增加、降级或删除标签。 |
| C §3 的 Grade-2 token gate；Spec §6 的身份泄漏、dev/test Grade-2 不重叠与中文非直译审查 | 提议保留原算法，对全部新 silver 证据重新审计；新发现触发泄漏／重叠冲突时保存原始输出并停止冻结，不删除发现、不降级绕过、不改 Query。解除须另行版本化裁决。中文语义审核拟改为有独立模型来源标记的审计，不伪填人类 delayed-review 字段；未完成或有冲突仍阻断。 |
| Spec §5、§11–12、§14；Protocol §11 | 引入独立 silver method、schema/version、provenance、truth hash 和结果 namespace；不得复用 v1 reviewed/human 标记。Query 原字节与旧 ground_truth_id 的绑定需要显式版本选择合同，见 §8。 |
| Protocol §13–14、Spec §10 的单人已标注／已延迟自审表述 | 新结果披露无人逐条标注／human IAA、模型遗漏及共享偏差；不继承“已完成人类自审”的缓解措辞。 |
| Protocol §15–16、Spec §15 的 48 小时＋human self-review freeze 条件 | 改为经批准的新方法、完整覆盖、72/72 合法非空判断、无未解决歧义、来源审计、独立最终 Data QA 和身份校验；批准文档本身不等于这些条件已完成。 |

正式批准前，上表所有原条款继续有效；本文不覆盖任何冲突。若最终 D 不接受
某项候选改写，其对应冲突继续阻断，不能靠实现作出隐含选择。Protocol 页首要求
实质方法变更具有新版本、理由、独立评审及新结果 namespace；本提案提交不满足该生效门槛。

## 2. 独立源码规模复算与可行性结论

本轮从 manifest 指定路径读取 self commit 原始 Git blobs，fixture 从已跟踪 v1
原始 bytes 读取；逐文件验证 SHA-256，并以当前真实 PythonAdapter/JavaAdapter
解析 `SourceFile`，没有实例化或调用 retriever。另从冻结 Git tree 独立列举 regular
`.py/.java` 源文件，72 个路径与 self manifest 完全一致；三个 fixture 的 Git
跟踪源文件数亦独立核对。未遍历未跟踪目录。增量 fixture 不属于主候选全集。

| 项目 | Query 数 | 文件 | Symbols | 原始字节 | LF 字符（Unicode code points） | 行数 | 固定 Chunk 数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| self-code-comments-agent | 32 | 72 | 1233 | 853120 | 821157 | 23229 | 857 |
| fixture-py-route-ledger | 13 | 8 | 28 | 3096 | 3096 | 114 | 8 |
| fixture-py-intake-queue | 13 | 7 | 15 | 3678 | 3678 | 98 | 8 |
| fixture-java-desk-queue | 14 | 6 | 23 | 3281 | 3281 | 119 | 7 |
| 合计 | 72 | 93 | 1299 | 863175 | 831212 | 23560 | 880 |

行数按 LF 规范化文本 `splitlines()` 计数；Chunk 数按现有 1200/200/1000 公式
计算，不是建议 judge 使用的分片大小。self 的 class/method/function 为
190/377/666，有 8 个零 Symbol 文件；route/intake 各 1 个，Java 为 0。
零 Symbol 文件仍必须阅读，仍属于 File/Chunk 候选全集。

self 最大文件 `processor.py`：112510 bytes、98626 字符、2717 行、48 Symbols。
各 fixture 最大文件分别为 route `route_ledger/service.py` 851 bytes；intake
`intake_queue/parser.py` 1917 bytes；Java `src/com/desk/service/DeskQueue.java`
1318 bytes。对 self 的 32 条 Query 分别完整提供源码，未计包装和重读即累计
27299840 bytes；72 条总计 27433836 bytes。不能把“全项目读一次”记为每条 Query 已覆盖。

**可行性结论：小 fixture 规模允许设计整项目输入，但尚未验证任何具体模型；self
完整单次输入及完整输出的容量目前未证明。全数据集执行前 BLOCKED。** 文件目录、
上传成功、工具能读文件或既有 93 文件包均不能证明 judge 看到了全部源码。

本轮没有选定精确模型、下载 tokenizer、访问模型服务或测试调用。不能以字符数除以
固定系数冒充模型 token 数，也不臆测 DeepSeek V4.1 Flash 的当前上下文／输出上限。
正式执行前应记录提供方官方限额证据的日期与 hash、精确 tokenizer/revision、
端点实际可调用性及返回版本的固定能力。模型商品名或会随时间漂移的 alias 不够。
这些数值未知不是“容量足够”，而是 blocker。

对每条实际序列化请求（含 system/prompt、Query、源码、工具结构、历史、汇总材料），
要求模型 tokenizer 实测 `T_input + T_reserved_output + T_margin <= C_context`，
并分别满足提供方 input/output 限额；推理 token 是否占用输出预算也必须查明。
margin、最大输出及分片规则应预注册。以可能的全项目 1233 项正证据及覆盖记录
估算最坏输出容量，不得按旧草稿仅一两项相关证据预算；输出分页数与完成条件须固定。
遇到上下文压缩、工具返回截断、finish_reason=length、缺页、拒答或缺结束标记均失败。

## 3. 候选方法与完整覆盖合同

若批准，预先指定一个提供方的一个精确不可漂移模型版本，使用全新隔离上下文；
它对每条 Query 的完整判断构成唯一主 silver reference。同一模型的固定多次
分片调用仍属 single-judge workflow，并非多个独立 judge，也不宣称调用绝对确定。
32 条 self Query 不能由一个带本任务历史的会话接着作答。本任务的 Codex 已见 GT，
本会话不能担当 silver judge。

候选输入仅有冻结 Query 投影、对应项目完整冻结源码，以及从全部源码无 Query
偏向确定性导出的路径/hash/身份/坐标辅助表。六字段全量 Symbol 表如启用，必须
覆盖全部 Symbols、按固定路径/位置排序、不含等级或锚点；不是旧 GT 表。只用源码
生成身份辅助信息须在正式输入合同明定。本轮未生成或交付新模型包。

不提供初始 GT、Spec 锚点表、rationale、annotation/authoring audit、QA 对话、
旧比较记录或任一 BM25/E5/Hybrid/Graph/RRF 排名。模型不得调用这些检索器、联网
搜索答案或访问整个仓库。源码作为数据处理，其中的注释、字符串和指令不是执行权限。

### 3.1 两种待选择的覆盖方案

1. **整项目输入**：每 Query 的隔离调用携带所有文件的完整原文及边界；模型完成
   文件遍历记录、正证据和未解决项。容量／输出不足时不能悄悄改为相关片段输入。
2. **固定穷尽分片＋同一 judge 汇总**：准备者先按项目、POSIX 路径、源码位置制定
   与 Query、GT、检索分数无关的分片表。每 Query 遍历全部分片；每片包含该 Query
   原文和分片原文，不能仅提供目录。边界规则与重叠在执行前固定，超长文件分段仍
   要覆盖每个字节；跨片 Symbol 需完整重组后判断。每片输出暂定证据和待关联问题，
   尚不能单独宣告某 Query 完成或给未看源码标负。

分片路线还必须完成跨文件整合：把所有分片输出（含“无正项”及未解决项）保留并
确定性合并，全量身份目录和全部候选发现交给同一版本 judge；从源码明确的调用／
引用和未解决问题定位补读原文，保存所有补读内容及原因。不得只挑前若干正项，
不得使用被评估 Graph 的 seed、hop budget、score 或排名导航。汇总阶段每一保留、
删除、改级的理由必须来自本次源码判断并留痕，不以初稿或第二模型作裁决。

摘要和身份表不能替代第一次穷尽原文遍历，也不能证明跨文件语义已穷尽。若汇总
上下文不能容纳完整判断账本，需预先固定分层汇总树及逐项传递/原文复读规则，
确保不存在丢失的未解决项；规则尚未批准或无法核验时 STOP。不能无限追加自由
探索或以不断重问充当“固定分片”。分片方案的接受表示接受可审计的操作覆盖及
其模型遗漏风险，不等于证明模型理解了每一字节或找全所有语义相关项。

### 3.2 每 Query 覆盖证据与失败条件

候选 `coverage_receipt` 至少记录：query/project ID、attempt、session/request ID、
输入包 hash、分片编号/总数、源文件 raw hash、原始 byte 半开区间、规范化文本
code-point 半开区间及转换映射、实际传入内容 hash、token 数、工具返回是否截断、
judge 对各片处理状态、跨片/跨文件 unresolved 项、响应 hash 和终止原因。
UTF-8 多字节和换行转换不可用相同数字假定；每个文件以原始 bytes 与解码文本双重核对。

受信任验证器按每条 Query 重算各文件区间并集，要求等于该项目全文件范围，
无缺口、无未授权替换，Symbols 全部可定位，零长度文件有明确访问回执。逐项列出
实际传入哪些源码区间、哪些未传入；未传入集合必须为空且处理记录完整才可完成。
模型自报“全部读完”不能替代输入传输日志；传输日志也只能证明内容可见，不能
证明内部注意力或理解。独立 Data QA 须区分这两种证据。

当前 `prepare_bundle.py` 可抽取并核验 93 文件及 72 Query 空白页，但没有模型
端点/version pin、token 预检、实际逐查询阅读日志、输出分页／汇总完整性和 silver
validator。旧 README 和空白页又属于 `wang` 的人类路线，不能直接当新方法执行包。
**当前工具准备不足以证明完整候选覆盖**；须未来经授权实现并离线验证上述能力，
另行批准执行。没有覆盖证明时任何未看文件／Symbol 都是未完成判断，不是 silver-negative。

## 4. 标签证据与权威映射

每 Query 的每项 Grade 2/1 均应提交以下结构性内容，不接受只写文件名或自然语言位置：

```text
query_id, dataset_id, project_id, source_revision_or_fixture_hash
relative_path, raw_source_sha256
symbol_id: language, relative_path, qualified_name, kind,
           semantic_disambiguator, fallback_line
start_offset, end_offset, start_line, end_line
relevance: 2 | 1
rationale: 具体源码行为及其如何直接回答／支持该 Query
coverage_receipt_id, raw_response_sha256
```

其中 `raw_response_sha256` 与覆盖回执关联由受信任归档器在保存原始响应后附加，
不要求模型在自身输出内计算自身 hash；源码身份元数据来自冻结输入清单并独立复核。
这些封装字段不改变模型原始标签、理由或原始响应字节。

SymbolId 六字段必须完整出现，合法 null 值来自真实 adapter，不能把 Java 重载
signature 或 fallback_line 凭显示名补猜。项目独立验证，跨项目同名不可合并。
offset 为 LF 文本 Unicode code point 零起点、end-exclusive；行号一基。
候选延续 v1 数据合同：证据 span 使用该 adapter Symbol 的完整冻结范围，理由中
可另指出更小的行为行段；不得缩短/扩展 canonical span 来优化 Chunk 指标。
固定 commit/fixture hash、路径、qualified name、行段/offset 和可核实行为均须
在证据及理由中定位；空理由、仅“有关”、仅 IMPORTS/CONTAINS 都不合格。

受信任 adapter/validator 检查：项目/路径属于 manifest、raw hash 一致、六字段
精确唯一匹配、span 与 adapter/行号/文本一致、等级类型合法、理由非空且有具体
源码支撑、无重复证据/矛盾等级。结构校验不能独自证明理由在语义上正确，需在独立
Data QA 中明示这一局限。不存在身份、同名歧义、越界/错 span、空相关集、格式
错误或截断导致整个 Query attempt 无效；不得静默丢坏项后接受余下子集。
只有文件名／自然语言位置的响应保留为失败证据，不能由操作者挑一个 Symbol 补齐。
无 Symbol 源码如被认为必要，记录 unmappable 问题并停止；不得发明 Symbol 或扩大映射。

沿用 `DatasetEvidenceRegistry` 与 `TruthMapper` 的既有语义：

- File：同文件 canonical evidence 的最大 grade。
- Symbol：显式相同 SymbolId **或** evidence span 完全位于该 Symbol 范围内的
  最大 grade；容器类可能因范围包含而映射为相关，不能私改成仅精确 ID 匹配。
- Chunk：1200 字符、200 overlap、1000 stride，末尾非空短块保留；按
  `max(chunk_start, evidence_start) < min(chunk_end, evidence_end)` 取最大 grade，
  端点接触不算重叠。现有 Symbol-only fallback 仍按冻结 Symbol span。

映射后相关集可能大于 judge 显式列出的 Symbol 集。因此“未列出即 silver-negative”
精确定义为**没有被 canonical 正证据经既有映射赋正等级的候选**；不能把仍被
容器/重叠规则映射为正的候选强制归零。每种 unit 都须拥有非空 mapped relevant set。
不修改生产 adapter、SymbolId、truth mapping、固定 Chunk 或现有指标以迁就模型输出。

## 5. 隔离、模型来源与原始产物固定

正式执行前拟冻结一份 `judge_run_spec`：provider、精确 model ID/revision、端点、
版本核验依据、tokenizer、参数（temperature/top_p/seed 若支持、reasoning 配置、
最大输入输出、工具模式）、调用时区/UTC 时间、输入包逐文件清单/raw hashes、
包 manifest hash、完整 system/user/tool Prompt 原始字节 hash 和 workflow 版本。
不支持某参数应记 unsupported，不伪造固定值。服务无法 pin 或验证版本即停止。

隔离证据应含新 session ID、创建时间、完整可导出的请求消息清单；禁用先前消息、
项目记忆、跨会话记忆、检索连接器和完整仓库挂载，仅允许包内源文件。请求不得
含 previous conversation/response ID。若采用 UI，新建窗口本身不是证据，须能核对
历史为空、记忆设置、附件及工具权限；无法导出/核实则该调用方式不合格。分片内
只能延续同一 Query 的当前 attempt 证据，不能带入先前 Query 的标签；重试重新隔离。

已知接触史应单独记录：本仓库文档涉及 GPT/Codex 材料化、Grok 设计建议、DeepSeek
QA；这不证明任何新模型权重或新会话未见相关材料。用户明确提供的
**DeepSeek V4.1 Flash 旧 QA 会话已接触 GT，禁止复用**。新 DeepSeek 会话的
实际可调用性、准确版本、隔离和覆盖全部为执行前待验证，本文不预先认证。
模型族接触项目规格/GT 的已知会话与未知训练/跨会话记忆分别登记，未知就写未知。
“本次输入无答案”不得推导为“模型权重无相关信息”或“与初稿形成完全独立”。

在任何草稿比较、第二模型比较、检索或指标计算之前，保存全部 72 条原始响应、
分片/工具日志、失败响应、重试及请求/响应 ID、实际参数、时间与终止原因，按原始
bytes 固定 SHA-256、只读归档和包级清单。每条响应一产生即保存，全部完成后
整体封存；后续解析派生件单独 hash，不覆盖 raw output。审计者见过旧 GT 必须
披露，不能把其纠错意见回灌 judge。固定 hash 证明归档后未变，不证明事前盲法或
服务绝对可复现。不得归档明文凭据；source/prompt/output 的审计身份仍须完整可核对。

## 6. 等级、歧义、重试和冻结失败

| 状态 | 含义与指标入口 |
| --- | --- |
| silver Grade 2 | judge 认为直接必要／最佳证据，经身份与来源验证后进入正相关集。 |
| silver Grade 1 | judge 认为具有实质作用的支持证据，同样进入正相关集。 |
| silver Grade 0 | judge 明确判断的不相关证据，仍是模型判断；不得批量填零模拟全量负标注。 |
| silver-negative | 完整覆盖与有效 Query 完成后，未由 canonical 正证据映射为相关的候选，按现行算法取零；不是人类确认的无关项。 |
| incomplete / invalid / unresolved-disputed | 缺源码、漏片、拒答、格式/身份错误、空正集或 judge 未解决矛盾；不是零，不进入主指标，阻断整个数据冻结。 |

draft-vs-silver 的已记录差异不是投票，也不自动成为新标签的 unresolved dispute。
若只是来源不同的相关性意见，保留两侧及差异、主 truth 仍按预注册 judge；若揭示
身份、覆盖、泄漏或内部逻辑冲突，停止冻结。不能将真正未完成的判断在文档写为
“未知”却在 loader/mapper 的 default=0 中静默计算。

候选重试规则：每 Query 完整固定 workflow 初次 attempt 后**最多一次同包重试**，
上限、可重试失败类别及所有固定分页/分片步骤必须在正式执行前注册。仅当初次
因格式、身份、空集、截断、调用失败或未解决问题无效时重试；有效但与初稿不同
或预期指标不佳不能重试。重试使用相同 Query/源码包/Prompt/workflow/模型/参数，
不携带初次答案、草稿答案、QA 建议或检索结果。无反馈的同包重新执行，保留两次
原始输出；初次有效即选初次，否则仅接受第二次完整有效判断，不投票、不拼接两次
正项。模型换版、换包、扩大预算或再重问是新的方法执行，不能算本次第三次重试。

任一 Query 在这一次重试后仍没有合法且非空的相关证据，应保留该 Query 和全部
失败原因，停止整个 freeze。可报告完成度，不能仅对通过子集汇总主指标，不能
删除失败 Query、造 Grade 0 或从草稿补答案。重新设计方法只能另行裁决、版本化
并保留失败历史，不能在见到正式结果后挑新 truth。

## 7. 指标、差异审计和论文边界

冻结公式不变：`R_q` 为当前 unit 映射后的所有 Grade 1/2 身份，`H_q@K` 为前 K
个唯一 ranked hits；`Recall@K = |R_q ∩ H_q@K| / |R_q|`，K 为 1/5/10；
MRR 为 top 10 内首个相关项 rank 的倒数，无则零；`nDCG@5 = DCG@5 / IDCG@5`，
gain=`2^grade-1`、discount=`log2(rank+1)`，ideal 排序由完整 active-unit truth 决定。
`Precision@5` 分母固定 5，`Hit Rate@5` 及 primary/secondary 层级亦不变。
宏平均、任务/语言分层、ContextBuilder 前计分都保留。

**标注失败与检索运行失败不同**：前者依据 Protocol §5.2 阻断 dataset gate，
此时主指标不存在；后者在合法冻结 truth 之上按 §7.4/§12 保留分母并记零，
仍可能使整个 run 无效。不能借后者把无标签 Query 当合法零分。

预注册审计拟包含所有 72 Query 的旧稿/银标签 evidence 差异：两侧独有项、
等级改变、六字段身份、span、理由、按 unit 映射后的正集大小、任务/项目/split
分布、原配额和泄漏检查变化。先固定银输出再比较；差异不会给旧稿否决权。
旧机械草稿只作辅助敏感性 reference，必须标注 unreviewed mechanical draft。
待合法实验阶段，对同一冻结系统 ranked outputs 用两种 reference 分别计算
配对差异、方向翻转与相关集大小影响，不合并 truth、不选指标更高的一版。

可选第二模型敏感性分析须在正式结果可见前决定是否做，并固定模型精确版本、
相同覆盖与隔离规则、失败处理及独立 namespace；其原始输出须先封存再比较。
它不参与 majority vote、intersection、union、裁决或“验证”主银标签，模型间
一致程度只称 cross-model agreement，不称 human IAA。事后才提出的分析只能
另列 exploratory，永不能升级为主 truth。若不做，记录未做而非暗示已验证。

论文主结果只能表述为：**“在这 72 条 Query 与冻结源码、单模型 silver reference
上的系统间比较”**。这里 72 是研究总体；primary English test 为 48 条，English
dev 12 条与中文 coverage 12 条继续分别报告，不做 72 条混合主均值。
须披露：无人逐条人类标注/盲审、无 human IAA；judge 可能遗漏相关证据；未选中
映射零的 silver-negative 局限；shared model/design bias 与初稿形成不完全独立；
fixture 和 self-project 偏差、模型版本/上下文与提示依赖、Java parser 和
File/Symbol/Chunk 构念限制。不能声称 human-reviewed GT、绝对相关性真值、
外部项目泛化、通用系统优越性或维护补丁正确性。中文非直译审计也不得冒称人类确认。

## 8. 版本、历史与未来最小工程变更（仅设计）

保留 `datasets/v1`、`queries/v1`、`ground_truth/v1`、原 annotation audit、原
identity/checksums、A 的人类 self-review 历史与 6.2A/B 已关闭准备/QA 文档原样。
不把 `reviewer_id=wang`、`reviewed`、`adjudicated` 或旧时间重新解释为模型活动。
以下当前身份经本轮只读重算一致；canonical hash 与原始文件 hash 不混用：

| 身份 | SHA-256 |
| --- | --- |
| dataset canonical | `164994a826fe51936d5fcb012a8d102967c33110787405fd3b0f7972efe8ade7` |
| Query canonical | `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba` |
| v1 GT canonical | `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87` |
| v1 GT raw bytes | `b4bbcbd36b68939932fd78963e921fb8657383728162e8b4659eff85083e0478` |
| v1 annotation audit raw bytes | `d81e847aa2cf008d953b37ce37a9bad6b267202c0305f99a1087244553d928b2` |
| v1 identity raw bytes | `6aebeaf8ce7f5b662a097bc08f1360d071fd4a2a7d330865417b57f892fcd430` |
| v1 checksums raw bytes | `fc9cda240e817c813e1811c5d363f12be5273fca00ff9bdd21aa2bac97aa34b1` |

候选新 method：`single_judge_llm_silver`；候选 truth version：
`v3.1-phase6-silver-truth-v1`；候选隔离路径 `ground_truth/silver-v1/`；均未创建。
新协议 ID 必须与现行 `v3.1-phase6-protocol-v1` 区分。新 canonical truth hash
覆盖方法、证据和 provenance 引用；raw response、coverage、Prompt、模型 run spec
分别有 raw hash，并由独立 provenance manifest 联结，避免自包含 hash 循环。
所有失败与重试挂在同一预注册执行身份下。源数据和 Query 可沿用原 hash；若改动
任何字节必须新版本，不能声称旧 Query 不变。

| 未来最小范围 | 需要的变更／兼容性风险 |
| --- | --- |
| `experiments/schemas.py` | 保留 v1 human schema 和 ≥48h 校验；新增有显式 schema/method discriminator 的 silver envelope/lifecycle，例如 generated→validated→frozen（候选命名）。模型 actor、生成时间、验证时间和 provenance 不填进 human reviewer 字段；失败 attempt 独立可表示空证据，不能伪造合法 GT。现 `_exact` 会拒绝新字段，不能靠多加 JSON 键启用。 |
| `load_ground_truth`、序列化与 canonical hash | 显式按 schema/version 分派；拒绝未知／混合方法和缺 provenance，不自动将 silver 转为 reviewed。当前 Query 用 `ground_truth_id` 链接真值：候选保留 `gt-{query_id}` 逻辑 ID，在明确 truth version namespace 下解析，查询字节/hash 不改；禁止混合版本和仅靠 ID 查找旧稿。需要调整现仅接收 `GroundTruthRecord` 的类型边界。 |
| validator／`DatasetEvidenceRegistry` 接入 | 延用已有集合、路径、hash、identity 验证，补足 silver 全六字段、完整 adapter span/行号、一对一 72 Query、coverage、输出终止和来源一致性校验。现 registry 仅核对 Symbol 成员及文件 span 上界，不能冒称已具备全部新校验。独立验证器在映射前拒绝 incomplete/unknown，不靠 mapper 默认零吞掉。 |
| `experiments/baselines.py` 接口与 `runner.py` 输入守卫 | 如需接纳 silver，限 evidence 只读接口／方法 dispatch；File/Symbol/Chunk 算法不动。runner 必须绑定批准的方法、版本和 provenance 完整性，不能只把 `FormalGateEvidence` 的布尔值置 true。指标公式与检索策略不改。 |
| identity/config/run metadata/artifact layout | 新 identity/provenance/checksum/result namespace 指向正式 D hash、旧源码/Query、silver truth、模型与覆盖清单；旧 identity 不就地改写。核对 `config.py`/`artifacts.py` 等 version/hash 消费边界，显式保留所有旧结果历史。 |
| 遮蔽包与执行记录工具 | 新 method 的投影/说明、token 预算、覆盖记录、固定分页/汇总、原始响应封存与离线 validator；旧 human bundle 保留，不复用填过的空白页。没有通用 agents/router 或生产 Provider 重构授权。 |
| Gate/研究文档和测试 | 正式 D 列明 §1.2 的取代范围、评审/批准记录；另行记录 silver-ready、最终 Data QA/freeze，不改写旧 QA closure 历史。未来获授权时增加独立离线 contract tests；现有 v1 lifecycle/数据测试继续验证 v1，不删除断言来放行新方法。 |

上述改动必须另轮授权后实施和离线验收。本轮未修改任何 schema、loader、validator、
Query、GT、annotation audit、identity、checksum、fixture、生产代码或测试。
批准提案也不自动代表工程已兼容，更不能直接关闭 Gate。

## 9. 本轮检查与执行边界

只读检查已完成：基线 branch/HEAD/status/diff；适用 AGENTS；冻结源码 93 文件
raw hash、adapter Symbols、独立路径/文件数及文本规模复算；dataset/path/Query/GT
canonical identity；identity 引用的五份研究文档 raw hashes；34/34 原始 checksum；
72 GT 仍 drafted，audit 的 method/human 空白生命周期与准备文档一致。
这些是机械统计和身份检查，不是模型覆盖测试、标签质量结果或新的独立 Data QA。

本任务明确“只做必要只读统计和文档检查，禁止检索”，因此优先于 AGENTS 通用
pytest baseline 要求，本轮未运行 pytest（其全套含合成检索路径），也未运行
LLM-contract smoke、应用、BM25/E5/Hybrid/Graph、Dry Run 或 RQ。历史 722 passed
仍只归属于原 QA 报告，不写成本轮测试结果。提交前另检查 diff、链接和允许文件范围。
本轮只允许本文及 PROJECT_CONTEXT 的提案状态说明入库，不 push/tag/merge。

## 10. 用户裁决清单与停止条件

正式批准前最少必须确定以下五项；当前均 **未确定／未批准**：

1. **是否接受 single-judge silver reference 为论文主参考**：接受时一并明确
   §1.2 对 human-primary、旧锚点、配额／truth probes、中文审核和 Gate 的具体
   取代范围；完成 Protocol 要求的独立方法论评审并将批准材料化。仅认可思路不生效。
2. **具体提供方、精确模型版本及全新隔离调用方式**：完成版本固定、实际可调用性、
   上下文／输出／tokenizer 限额及空历史/记忆/权限证据核验；旧 DeepSeek QA 会话禁用。
3. **完整候选覆盖方案和验收标准**：选择整项目或批准固定分片/汇总；冻结 token
   预算、遍历/分页/跨文件规则与每 Query 100% 源码可见且无 unresolved 的记录标准。
   当前生成器缺少这些证据，self 单次容量未证，是实际执行 blocker。
4. **一次同包重试后仍无合法非空标签的处理**：候选为保留全部 Query 并停止整体
   冻结；不能仅对成功子集汇总。任何替代方法都要在执行前另行版本化批准，不能
   默许删题、补旧稿答案或无限重试。固定敏感性分析是否包含第二模型及其身份规则。
5. **是否接受论文结论降级和全部披露**：单模型 silver、无人逐条标注、无 human
   IAA、遗漏/负类约定/模型项目依赖、无外部泛化；48/12/12 始终分别报告。

任一未确定，本文不得转为生效 Addendum，不得开始标签生成。批准之后仍须依次
完成另轮工程兼容性与离线验证、真实隔离/容量/覆盖条件、标签执行与封存、全量
机械及语义来源审计、独立最终 Data QA、最终身份校验和正式 freeze 裁决。
期间如缺源码字节、错 hash、无法 pin 版本、污染历史、输出截断、身份/span 错误、
空相关集、未解决歧义/泄漏冲突、重试超限或任一 Query 未完成，立即停止并保存失败。
现有映射和负分约定不是绕过这些停止条件的授权。

**Addendum D 尚未生效；尚未执行 LLM 标注；Dataset / Query / GT 仍 DRAFTED；
Phase 6.2 Gate OPEN；Phase 6.3 BLOCKED / NOT STARTED；Formal RQ1–RQ4 NOT STARTED。**
