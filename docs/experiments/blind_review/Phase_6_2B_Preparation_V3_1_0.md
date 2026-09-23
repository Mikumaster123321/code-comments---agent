# V3.1.0 Phase 6.2B — 延迟盲自审材料准备与隔离流程

**PREPARATION ONLY / NOT REVIEWED。** 本文供准备者及完成独立重判后的
比较执行者使用，**不得在第二次判断固定前交给 `wang`**。交给 `wang` 的只有
由 `prepare_bundle.py` 生成并验证的独立目录。本文没有进行人类判断、比较
或裁决，也不证明未来实际遮蔽成功。

## 1. 依据和当前门禁

依据为当前 Git 跟踪的 Experiment Protocol、Addenda A/B/C、Dataset
Specification、`PROJECT_CONTEXT.md`、Phase 6.2A Independent Draft Data QA
报告及 `datasets/v1/identity.json`。独立草稿 QA 为 **PASS WITH LOW NOTES**，
其 Documentation Closure 为 **CLOSED**；Dataset、Query、GT 仍是 **DRAFTED**。
Addendum A 规定唯一人类标注者及复核者为 `wang`，至少延迟 48 小时，
独立判断固定前遮蔽初始 grade、rationale 与 judgment，之后才比较，
分歧须保留原始判断并必要时裁决。

初稿 `created_at=2026-09-23T04:00:42.357095+00:00`；最早真实复核开始时间
为 `2026-09-25T04:00:42.357095+00:00`，即北京时间
`2026-09-25 12:00:42.357095`。本次生成包和验证包不开始复核；到时也不
自动授权 Codex 代替 `wang` 判断。

## 2. 材料构成、字段审计和交付隔离

仓库中 `blank_second_judgment.jsonl` 有 72 条，按冻结 `query_id` 字典序
排列。每条**只**投影冻结 Query 的 `query_id`、`query_text`、`language`、
`task_type`、`project_id`、`split`，外加全空白 `review`：

| 字段或来源 | 交付处理 | 防泄漏理由 |
| --- | --- | --- |
| Query 的六个显示字段 | 原文照录，不改写 | Protocol 允许 Query 原文；按 Query ID 排序，不按 GT 或候选排序 |
| `ground_truth_id`、`authoring_source`、`notes`、版本/内部标识 | 不投影 | 避免可打开的 GT 指针或不必要的内部线索 |
| `reviewer_id`、开始/完成时间、遮蔽观察 | `null` | 不冒称人类复核已开始或完成 |
| evidence、候选歧义、待裁决问题 | 空数组 | 无预选 Symbol、span、grade、rationale 或高亮 |
| 无相关源码、难点、中文非直译判断 | `null` | 不预填第二次判断 |
| 源码路径与 hash | `source_catalog.json` 按项目列**全部** 93 个文件 | 从 dataset manifest 而非 GT 产生；无 Query 到文件的定向映射 |
| 冻结源码 | `sources/<project_id>/<relative_path>` | 自仓库取冻结 Git commit 原始 blob，三个主 fixture 取已冻结源文件；逐文件核对 SHA-256 |

`prepare_bundle.py` 只读取 Query、dataset manifest、identity、冻结源码与
本目录空白材料；**不读取 GT 或 annotation audit**，不调用检索。它对 Query
做全字段身份 hash 核对，再生成严格六字段投影；`--verify-bundle` 对包中
每个文件、目录、内容和 symlink 作完整白名单检查。工作页的原始 Query
字面可能自然出现“score”等术语；这不是检索得分，投影中没有排名、得分、
候选或结果字段。

在受信任的准备环境中，从仓库根运行：

```text
python docs/experiments/blind_review/prepare_bundle.py --bundle <新的独立目录>
python docs/experiments/blind_review/prepare_bundle.py --verify-bundle <同一目录>
```

目标父目录须已存在，目标目录须不存在；脚本不覆盖旧包。本轮已在仓库外的
`/private/tmp/phase62b-blind-bundle-9161ff4` 实际生成并验证一个包，结果为
**72 个唯一 Query、93 个冻结源码文件、无多余文件**。包内仅有：

```text
README.md
queries_for_second_judgment.jsonl
source_catalog.json
sources/<project_id>/<relative_path>  # 93 files
```

**仅交付这个独立目录，不交付仓库根、本文、生成脚本、原始 manifest、
identity、QA、GT、annotation audit 或任何检索输出。** 最好在没有完整仓库
挂载或访问权限的独立账户/工作环境中给 `wang` 使用，并在开始前复验包。
当前同一 macOS 用户仍可能自行打开完整仓库中的
`docs/experiments/ground_truth/v1/ground_truth.jsonl`；本仓库和本脚本不能
强制阻断这种访问。因此结构检查只能证明**交付包**不泄漏，不能证明
未来人类未通过别的途径看到初始判断。如无法隔离仓库视图，或 `wang`
实际看到了初始判断，停止并如实记录，不能声称盲审完成。

## 3. 第二次判断固定之后的比较流程（不得提前交付）

1. `wang` 在合法时间、隔离包中自行记录实际开始/完成时间和遮蔽观察，
   对 72 条 Query 逐条完成独立 judgment；不可从初始 GT 或检索输出补答案。
   中文 Query 的非机械直译判断也由 `wang` 记录。
2. 在接触初始 GT **之前**，保存完整第二次判断文件，核对 72 个唯一 ID、
   必填判断和时间，记录其 raw-byte SHA-256、固定时间及只读副本。此后
   第二次原始判断不得被比较过程覆盖。
3. 受信任比较步骤才读取
   `docs/experiments/ground_truth/v1/ground_truth.jsonl` 与
   `docs/experiments/ground_truth/v1/annotation_audit.jsonl`，按 `query_id`
   一对一匹配。逐项比较相关性等级、全部 Symbol 身份、evidence span
   （路径、offset、行号）及理由；分别列出两侧独有的 evidence 与任何语义差异。
   先记录比较，再由 `wang` 查看两次原始判断及差异。
4. 对等级、身份或 span 的任何分歧，设置 `ambiguity_flag=true`，保留
   初稿、第二次判断、比较记录及 `adjudication_note` 中的解决过程。
   理由差异也要记录并判断是否需要裁决；不得静默覆盖。需要裁决时
   仅由 `wang` 在比较之后作出，`annotation_status=adjudicated`、
   `adjudicator_id=wang`。无须裁决时，完成实际延迟复核后可用
   `annotation_status=reviewed`、`adjudicator_id=null`；`reviewer_id=wang`
   始终表示自审，不表示第二个人。`reviewed_at` 必须是真实复核时间。
5. 只有根据真实隔离与人的记录才能填写 `masking_confirmed`；本准备阶段
   不能预设为 `true`。物质性的 relevance、身份或 span 更正须依合同提升
   GT version，重新计算 canonical hash，保留先前记录。随后仍需最终独立
   Data QA、机械验证、hash/checksum 校验及正式 freeze；不能直接升级为
   `frozen`。模型 QA 不是第二位人类 reviewer，不能报告 human IAA。

比较记录的**空白**结构至少保留以下栏位；本轮不填写任何实际结果：

```text
query_id | second_judgment_sha256 | comparison_at |
initial_evidence_preserved | second_evidence_preserved |
relevance_comparison | symbol_identity_comparison |
span_comparison | rationale_comparison |
ambiguity_flag | adjudication_note | adjudicator_id | resolution
```

## 4. 本轮机械验证边界

- 冻结 Query 的 canonical hash：
  `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`。
  投影后 72 个 ID 唯一，split 为 English test/dev/Chinese `48/12/12`；
  逐字段的文本、语言、任务、项目、split 与冻结 Query 一致。
- 空白页 raw-byte SHA-256：
  `eb031f55870a35e74824454cdae9fd6d2ab5654e1906a1205761b4658678f095`。
  每条 `review` 的时间、复核者及文字判断为 `null`，数组为空。
- 文件白名单检查证明包中无 GT、audit、初始判断指针、排名文件、
  Query 定向源码候选或可打开仓库的链接；源码内容本身是 Protocol 允许的
  冻结材料。结构检查不能证明未来实际人类行为。
- 原始 Query、GT、annotation audit、manifest、identity 与 checksum
  均未修改；本次不运行 BM25、E5、Semantic、Hybrid、Graph、RRF 或正式 RQ。

## 5. 阶段状态

- Phase 6.2B：**PREPARATION ONLY / NOT REVIEWED**。
- Dataset / Query / GT：**DRAFTED**。
- Phase 6.2 Gate：**OPEN**。
- Phase 6.3：**BLOCKED / NOT STARTED**。
- Formal RQ1–RQ4：**NOT STARTED**。
