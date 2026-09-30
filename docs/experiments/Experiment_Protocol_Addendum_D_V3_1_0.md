# V3.1.0 Phase 6 — Specification-Anchored Reference 与有限 LLM Evidence Audit Addendum D

## 1. 身份、批准范围与优先级

- Addendum ID：`v3.1-phase6-protocol-addendum-d`；版本：`v1`。
- 状态：**用户批准的方法合同与审计预注册 / Phase 6.2 数据 Gate 未关闭**。
- 记录日期：`2026-09-24`；适用范围：本仓库 V3.1.0 的 72 条冻结 Query 与四个主项目。
- 用户明确裁决：**以 72 条 specification-anchored reference 为主参考；DeepSeek 在 TraeWork 中仅对预注册的 12 条 English test 做 evidence audit，不称为人类盲审或全量 silver。**
- 变更理由：用户不进行逐条人类延迟盲自审；旧草稿由事先规格的锚点和等级机械材料化，不能通过填写旧人类字段伪装为完成该流程。
- 本文是正式方法合同，授权后续按本文准备和执行有限 evidence audit；**不批准现有 drafted 数据进入实验，不批准本轮调用模型、修改标签、运行检索或关闭 Gate**。方法获批与数据最终获批是两个身份。
- Protocol 页首要求实质变更有独立方法论评审及新的结果 namespace。用户裁决与本文版本化不冒充已完成独立方法论评审；正式 reference approval / Phase 6.2 Gate 关闭前还须归档独立方法论审查。未来结果 namespace 预留为 `v3.1-phase6-spec-anchor-reference-v1`，不得与旧人类 GT 或未生效 silver 方案共用。

权威链为 [Phase 0 Architecture & Research Decision](../development/Architecture_Decision_V3_1_0.md) + [Experiment Protocol](Experiment_Protocol_V3_1_0.md) + [Addendum A](Experiment_Protocol_Addendum_A_V3_1_0.md) + [B](Experiment_Protocol_Addendum_B_V3_1_0.md) + [C](Experiment_Protocol_Addendum_C_V3_1_0.md) + 本 Addendum D + [Dataset Specification](Dataset_Query_GroundTruth_Specification_V3_1_0.md)。本 D **仅在下表明确范围内**优先于旧的人类复核路径；其余冻结条款继续有效。旧架构决策、A/B/C、Protocol、Specification 和已关闭的 6.2A/B 准备 QA 均保留原文件及其历史状态。

| 原合同位置 | 本 D 的精确取代范围 |
| --- | --- |
| Phase 0 Architecture & Research Decision §18 的 “Ground truth is primarily human annotated” | 仅对此 72-query Phase 6 主参考，明确设立 specification-anchored 例外；不能继续以该旧句描述本次实际来源。其“被评估 retriever 不得产生自己的 truth”、公平比较及其他架构约束保留。该实质方法变化仍需独立方法论审查，未完成前不能批准数据用于正式实验。 |
| Protocol §5.1 的 “human annotated” 来源断言及 §5.3–5.4 的人类标注、延迟复核生命周期；A §2–4、§6–7；Specification §10、§14–15 | 仅对此 72-query **新主参考方法**，用事先规格锚点的机械材料化、有限 evidence audit、独立最终 Data QA 和新 reference approval 身份取代“`wang` 必须完成 ≥48 小时延迟盲自审才能冻结”的路径。A 对旧 v1 drafted 人类流程的字段含义及历史仍有效，不倒填完成状态。 |
| Protocol §14、Specification §10 中“单一人类标注者已标注／延迟自审可缓解偏差”的结果叙述 | 此新方法的论文叙述按 §3 与 §9 降级；不得从旧字段推出逐条人类标注、盲审或 human IAA。 |
| Specification §4.5、§6、§13、§15 中中文非机械直译须由 delayed-review 字段确认的执行方式 | 中文语义条件**不豁免**，但不得填旧人类 delayed-review 字段。改由 §8 的独立、带来源的中文核查记录；未完成时最终 Phase 6.2 Gate 仍 OPEN。 |
| Protocol §11、§15–16、Specification §12、§15 的人类 GT freeze 身份和运行入口 | 按 §7、§10 建立独立 reference approval、方法/数据 hash 与 fail-closed runner Gate。现有 v1 `drafted` 记录不可直接视作 human-frozen GT。 |

Addendum B 的 authoritative SnapshotDiff `5/2/2/0` 及 7 个新 embedding 文档不变。Addendum C 的四条 Query 修订、Grade-2 full-identifier-token 泄漏算法及其余泄漏门禁不变。Protocol 的 RQ1–RQ4、48/12/12 分群、`top_k=10`、K 值、BM25/E5/Graph/Hybrid 配置、File/Symbol/Chunk truth mapping、指标公式、失败处理、来源/hash 及正式运行顺序不变。此前 [single-judge silver 提案](PROPOSED_NOT_EFFECTIVE_NO_LABELING_AUTHORIZED_Addendum_D_Single_Judge_Silver_Reference_V3_1_0.md)仍为 **PROPOSED / NOT EFFECTIVE / NO LABELING AUTHORIZED** 的历史候选，既不构成本 D 的附件，也不是并行执行路径；不得将其全候选覆盖或全量 LLM 标签要求移入本方法。

## 2. 主参考集的来源和身份

主参考称 **`specification-anchored reference`**，不称 human-reviewed ground truth、全量 silver 或 LLM-generated truth。72 条 Query、初始 Grade-2/1 锚点、2/1/0 定义源于事先版本化的 Specification 和 Addendum C。用户批准规格及材料化，不等于用户亲自逐条标注。Codex 将授权的锚点/等级机械材料化为 v1 草稿；[6.2A 独立草稿 QA](../qa/QA_Report_V3_1_0_Phase_6_2A_Independent_Draft_Data.md)已核对身份、hash、Symbol/span、泄漏与配额等机械合同。[6.2B 准备 QA](../qa/QA_Report_V3_1_0_Phase_6_2B_Blinded_Review_Preparation.md)关闭的是遮蔽准备材料的检查，未进行人类复核。两份 QA closure 不能充当 72 条语义判断的独立人类确认。

既有 `ground_truth/v1/ground_truth.jsonl` 和 `annotation_audit.jsonl` 的 72 条记录均保持 `drafted`，`reviewed_at=null`；`primary_annotator_id=wang`、`reviewer_id=wang` 及 `review_method=delayed_blinded_self_review` 是旧合同预置的**历史字段与未来角色**，不证明 `wang` 实际完成逐条人类初标或复核。旧原始 bytes、`identity.json`、旧 QA 与 hash 必须保留。新方法另建带 `review_method=specification_anchored_with_limited_llm_evidence_audit` 的来源/批准 artifact；不得复用旧 `reviewed`、`adjudicated`、`frozen` 或人类时间字段，也不得制造 human IAA。

初始 v1 `ground_truth_hash` 为 `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87`，它只标识**草稿**。任何后来经核实的证据更正须另立 truth version/hash，保留差异、理由、影响 Query 和独立 QA；不能改写 v1 原件或因检索分数决定更正。

## 3. 指标、分群与论文解释

主指标依现行 Protocol §7：Recall@1/5/10、MRR、nDCG@5 及既定 Precision/Hit Rate；Grade 1/2 对二值相关指标算相关，nDCG 使用 `2^grade - 1`。未被固定规格锚点参考集列为 Grade 1/2 的候选，在**现有指标实现**中按 grade 0 计算；其语义仅是“未被规格锚点列入”，不等于人类确认真实不相关。每条 Query 必须保留非空相关集；遗漏相关证据是构念效度风险。

主结果只可称“相对于这 72 条 Query、冻结源码和固定 specification-anchored reference 的系统间比较”。English test 48 条为主比较；English dev 12 条只作 Phase 6.3 Dry Run；Chinese coverage 12 条单独报告。该方法不证明人类真实相关性、逐条人类标注、human IAA、全量 LLM 复核或对外部项目泛化。English test 在 Phase 6.2 数据身份真正批准、Gate CLOSED 且 Phase 6.3 English-dev Dry Run PASS 之前禁止正式评估。

## 4. 12 条 English-test Evidence Audit 的预注册

冻结 Query Set 版本 `v3.1-phase6-queries-v1`，canonical `query_set_hash`：
`5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`（与当前 `datasets/v1/identity.json` 一致）。选择算法：仅过滤 `split=english_test`；按六种 `task_type` 分组，各组对原始 `query_id` 作 Unicode/字典序升序排序，取前两条。不得用 GT grade、审计难易、检索排名/结果或希望得到的指标调整样本。

| Task type | 预注册 Query ID 1 | 预注册 Query ID 2 |
| --- | --- | --- |
| `bug_localization` | `et-bl-ja-01` | `et-bl-ja-02` |
| `cross_file_understanding` | `et-cf-ja-01` | `et-cf-ja-02` |
| `dependency_questions` | `et-dq-ja-01` | `et-dq-ja-02` |
| `feature_localization` | `et-fl-ja-01` | `et-fl-ja-02` |
| `maintenance_tasks` | `et-mt-ja-01` | `et-mt-ja-02` |
| `symbol_lookup` | `et-sl-ja-01` | `et-sl-ja-02` |

机械核对结果为每类 2 条、共 12 个互异 ID、全部 English test。**因为 `ja` 在 `py` 前，12 条恰好是 English test 中全部 12 条 Java Query，没有 Python Query**；这是确定性便利样本，不是随机或总体代表性样本，不能据此估计 72 条总体审查通过率、Python 样本或中文样本的错误率。该局限不得通过事后换样修补；若日后需要 Python 审计，须在看正式结果之前另行版本化预注册，不可替换本表。

## 5. TraeWork 审查输入、输出与平台留证

候选执行界面是 TraeWork 中显示为 `DeepSeek-V4.1-Flash` 的模型选择项。这个显示名不证明精确 backend revision；先前曾看过 GT 的 DeepSeek QA 会话不得复用。正式审计须在新建的专用隔离会话进行，记录每条 Query 的会话边界、实际可见模型显示名、真实调用时间与界面模式。不可从本合同推定该模型已调用、token 限额已验证，或当前 GUI 能导出 provider 原始响应。

逐 Query 的输入只包含：冻结 Query 原文及身份、当前 v1 草稿引用的每个证据的项目/文件/SymbolId 六字段/span/Grade/rationale，以及该 Query 所引每个文件的**完整冻结源码**（同一文件只放一次，固定路径序）。使用完整被引文件是中立且确定性的上下文边界；不按 GT 优劣增删文件，也不使本审计成为全项目候选搜索。每个输入包记录 Query/GT/dataset hash、引用文件的原始 bytes hash、实际序列化输入 hash 与界面可见发送内容；若 TraeWork 注入其他上下文且不可核实，记录该限制并停下待核查。不得给模型任何被评估 BM25/E5/Hybrid/Graph/RRF 的排名、分数或正式结果，不允许其调用这些检索器。

任务是逐项检查“**所引源码 span 是否支持既有等级及理由**”。模型可以指出不支持、上下文不足或冲突，但不要求寻找全项目所有相关 Symbol；看到既有证据、等级与理由意味着它不是 blinded re-judgment。每条输出须逐一引用输入证据 ID、给出 `SUPPORTS`、`QUESTIONS` 或 `CANNOT_ASSESS`，并说明所据源码位置/原因；逐项状态全部保留，总体状态若有 `QUESTIONS` 则为 `QUESTIONS`，否则若有 `CANNOT_ASSESS` 则为 `CANNOT_ASSESS`，仅全部为 `SUPPORTS` 才是 `SUPPORTS`。格式错误、漏证据项或无法追踪来源按 `CANNOT_ASSESS` 处理，不自行补写支持。

每次审计在任何草稿修正或检索运行前保存：实际发送内容与 hash、界面显示的完整原始响应及 hash、显示模型名、实际 UTC 调用时间、会话/任务标识、思考区和最终答案的**分别**可见内容、逐证据结构化转录及转录 hash。若思考区不可见/不可导出、精确 revision、token usage、`finish_reason` 或完整原始响应不可得，对应字段填 `unavailable` 并保留可见画面/导出范围及限制；不得由模型自述补成平台证据。无法证明原始内容完整时该条为 `CANNOT_ASSESS`。原始记录须与审计结论分开归档；不得包含凭据或私人账户信息。

## 6. 审查结果与疑点处理

- `SUPPORTS`：在**已提供**源码范围内，所引 span 能支持既有 Grade 与理由；不表示发现了全部相关证据。
- `QUESTIONS`：span、身份、理由或等级的支撑存疑，保留逐项疑点与原文。
- `CANNOT_ASSESS`：输入/输出截断、上下文不足、格式/导出失败或其他无法判断，保留原因；不能转为 Grade 0 或 `SUPPORTS`。

LLM 输出不直接改写 GT。对 `QUESTIONS` / `CANNOT_ASSESS`，在任何正式检索前按冻结源码与权威 adapter 做独立核查。可机械证实的身份/span/源码行为错误，提出新 truth version/hash、逐项差异、影响范围、理由及独立 Data QA，再由新 reference approval 绑定；不能改写旧 v1 bytes。若争议属实质相关性而机械核查无法裁定，或无法按预注册规则解决，列为待版本化用户/方法裁决 blocker，Phase 6.2 Gate 维持 OPEN。Codex 或审计模型不得静默裁决；不按未来指标高低选择标签版本。12 条 `SUPPORTS` 也不使其余 60 条成为 LLM-reviewed，更不单独关闭 Gate。

## 7. 独立 reference approval 与未来迁移（本轮不实施）

旧 `GroundTruthRecord` schema 将 `reviewed`/`adjudicated`/`frozen` 与人类复核时间及 ≥48 小时绑定；因此旧 v1 `drafted` 文件不能被改称 frozen，也不能仅将 `FormalGateEvidence.phase_6_2_dataset_truth_frozen=true` 就进入正式运行。未来须在独立版本路径创建 reference records/provenance 和 approval artifact，例如 `ground_truth/spec_anchor_v1/`；此处路径是**待实现设计**，不是现有文件或本轮交付。保持 Query 的 `ground_truth_id=gt-{query_id}` 不变，以 `reference_method + truth_version + truth_hash` 显式选择该 ID 的版本，不让 loader 默认从旧 v1 读取。

新 approval 至少记录：`reference_method=specification_anchored_with_limited_llm_evidence_audit`、方法版本与本 D hash、独立方法论审查状态、dataset/query/truth 各版本和 hash、旧 v1 草稿 hash、12-ID 预注册表 hash、12 条逐项审计状态及原始证据 hash、中文非直译状态、最终独立 Data QA/hash/泄漏结论、`approval_status=pending|approved|blocked` 与批准时间。旧 v1 文件、`identity.json`、checksums 及 6.2A/B QA 证据原样保留；新 truth/reference 版本即使证据内容未变，也须以新方法和 provenance 有独立 hash，不能复用 v1 `drafted` hash 冒充已批准的人类 GT。

最小后续工程范围：增加独立 reference/provenance schema 与 loader；版本化 `ground_truth_id` 解析和 canonical hash/checksum；扩展 Data QA validator 以验证 72/72 身份、span、非空相关集、hash、泄漏、12 审计证据与中文状态；扩展 `FormalGateEvidence`、runner/RunMetadata 及结果 namespace 绑定新 approval；更新数据合同和 runner 的 fail-closed 测试与 Gate 文档。现有 `experiments/schemas.py` 的 `GroundTruthRecord`、`experiments/runner.py` 的 formal gate、`experiments/baselines.py` 的 truth mapping 及 `tests/test_phase62_dataset_contract.py` 都需要逐项兼容性审查。不得仅为通过 Gate 放松现有 File/Symbol/Chunk mapping 或把旧 `reviewer_id=wang` 重新解释为模型审查。新路径应让旧人类流程的历史文件与测试继续可读，拒绝旧 v1 drafted 被直接作为 formal truth。

## 8. 中文覆盖的未决门禁

Specification §4.5、§6 与 §13 将每条中文 Query 的“非机械直译”判断列为延迟复核的一部分；当前 `not_mechanical_translation` 仍待审。§4 的 12 条 English-test Java 审计对中文没有任何证明力。本 D 保留**12 条中文非机械直译的独立语义核查**作为最终 Data QA 条件，同时仅取代其必须填在旧人类 delayed-review 字段中的记录方式。具体核查者、输入/判定规则与来源 artifact 必须在执行前单独版本化；未确定或未完成时 `chinese_nontranslation_status=pending`、Phase 6.2 Gate OPEN，中文分析不能声称已通过非直译审查，也不得混入 English test 主结果。此条件不要求用户假装完成 72 条人类盲审。

## 9. 预先固定的次级敏感性分析与论文限制

预注册一项**次级** “Grade 2 only” 敏感性分析：对同一次已固定的 ranked hits，Grade 2 计相关、Grade 1/0 计不相关，重算 Recall@1/5/10 与 MRR；nDCG@5 的 gain 明确设为 Grade 2 → `2^2-1=3`，Grade 1/0 → `0`，再用相同定义的 ideal DCG 归一化。它不替代原 2/1/0 主指标，不改变任何排序、GT 或运行配置；须报告全部固定分群，不按结果好坏决定是否展示。若未来实现不能精确复算并独立验证，应标为**未执行的预注册次级分析**，不得把它做成 Phase 6.2 Gate 的替代条件或事后调整定义。

论文须披露：没有逐条人类标注及 delayed blinded self-review、没有 human IAA；规格锚点可能漏掉真正相关证据，未列出即按零分是操作性评价而非真实负例；12 条便利样本全为 Java、只审既有证据，不检查全项目候选或剩余 60 条；固定项目、轻量 Java parser、单一 E5 与模型界面限制；不能宣称对外部项目泛化。不能把 LLM 的 `SUPPORTS` 写成人类确认或全量 silver 通过。

## 10. Phase 6.2 最终 Gate 与顺序

以下是分别可审计的条件；**本文件落 Git 只完成第 1 项的方法记录，不关闭数据 Gate**：

1. 本 Addendum D 的身份、精确取代范围、新结果 namespace 与用户裁决落 Git；实质方法变更的独立方法论审查在正式 reference approval 前归档。
2. §4 的 12-ID 表、Query Set 版本/hash、§5 输入/输出规则在任何正式检索前固定。
3. 12 条 TraeWork evidence audit 实际完成；原始可见内容、思考区/最终答案及平台可得证据逐条归档，缺失字段明示 `unavailable`。
4. 审计的 `QUESTIONS` / `CANNOT_ASSESS` 经冻结源码独立核查并有可追溯结论；未决项使 Gate OPEN。
5. 72 条参考记录及中文 §8 条件经最终独立 Data QA：身份、span、hash、配额、泄漏与 File/Symbol/Chunk mapping 均通过；旧 QA closure 不替代此步。
6. §7 的新 reference approval、schema/loader/runner/Formal Gate 及独立测试真正实现并 fail closed；旧 v1 drafted 不能直通。
7. 最终 dataset/query/truth/method/审计 hash 相符，正式 RQ 运行数仍为 0，旧文件与修订链可复核。
8. **仅当以上全部通过且 Phase 6.2 Gate 明确 CLOSED 后**，Phase 6.3 才可用 English dev 执行 Dry Run；Formal RQ1–RQ4 仍须等待 Dry Run PASS。

当前状态：方法合同写入不等于第 3–7 项完成。12 条 LLM evidence audit **NOT STARTED**；旧 v1 为 `drafted`；Dataset / Query / GT **DRAFTED / NOT APPROVED**；Phase 6.2 Gate **OPEN**；Phase 6.3 **BLOCKED / NOT STARTED**；Formal RQ1–RQ4 **NOT STARTED**。
