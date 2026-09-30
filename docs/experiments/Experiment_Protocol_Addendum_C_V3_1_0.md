# V3.1.0 Phase 6 — Query Leakage Control and Frozen Query Wording Addendum C

## 1. 状态、修正范围与依据

- Addendum ID: `v3.1-phase6-protocol-addendum-c`
- Addendum version: `v1`
- Status: **FROZEN**
- Documentation date: `2026-09-23`
- Nature: **normative correction / erratum**
- Methodology Review / Multi-token Clarification: **COMPLETED**；依据用户提供的
  已完成方法论裁决与修订说明；全表核对发现第四条后，用户进一步明确授权
  `et-cf-py-01` 的替换并完成门禁。本次 tokenizer 核对属于工程验证。
- Applies to: `Experiment_Protocol_V3_1_0.md` §5.5，以及
  `Dataset_Query_GroundTruth_Specification_V3_1_0.md` §4.1、§6 的对应内容。

冻结 Specification 同时要求逐字 materialize Query wording，并禁止非
`symbol_lookup` Query 包含 Grade-2 目标的简单名 identifier token。下述四条
旧句分别直接包含 `update`、`charge`、`grant`、`document`，因此需要更正措辞并精确定义
匹配算法。旧句继续作为历史证据保留；本附录列出的 replacement wording
是后续材料化应使用的文本。

本附录仅修正指定 Query wording 和 Grade-2 full-identifier-token leakage
algorithm。Query ID、task type、split、language、project allocation、
Grade-2 anchor、Grade-1 evidence、任务难度设计和 72-query count 均保持不变。

## 2. 四条 Query 的旧句、替换句与锚点

四条均属于 `self-code-comments-agent`、`english_test`、`python`。前三条来自
原定修正范围；第四条依据本次全表核对后的用户明确补充授权。

### 2.1 `et-bl-py-01` — `bug_localization`

Grade-2 anchor: `RetrievalIndex.update`。
Grade-1 evidence: `RetrievalIndexIdentity.for_snapshot`。

OLD — historical / superseded:

> Incremental index update rejects the operation because the previous index identity is stale. Where is that rejection?

REPLACEMENT:

> An incremental index operation is refused because the recorded index identity no longer matches. Where is that refusal?

完整 identifier token 为 `update`；旧句命中，替换句不命中。

### 2.2 `et-bl-py-03` — `bug_localization`

Grade-2 anchor: `InMemoryCreditLedger.charge`。
Grade-1 evidence: `InsufficientCreditsError`。

OLD — historical / superseded:

> A charge is refused because the account balance cannot cover it. Where is that refusal decided for the in-memory ledger?

REPLACEMENT:

> A deduction is refused because the account balance cannot cover it. Where is that refusal decided for the in-memory ledger?

完整 identifier token 为 `charge`；旧句命中，替换句不命中。

### 2.3 `et-mt-py-03` — `maintenance_tasks`

Grade-2 anchor: `AdminCreditService.grant`。
Grade-1 evidence: `AdminCreditService._record_from_row`、
`SQLiteCreditLedger._append_transaction`。

OLD — historical / superseded:

> An administrator grant must keep the operator reason with both the stored admin operation and the ledger note. Which grant entry point and persistence paths must stay consistent?

REPLACEMENT:

> An administrator credit award must keep the operator reason with both the stored admin operation and the ledger note. Which entry point and persistence paths must stay consistent?

完整 identifier token 为 `grant`；旧句命中，替换句不命中。

### 2.4 `et-cf-py-01` — `cross_file_understanding`

Grade-2 anchor: `CorpusBuilder._document`。
Grade-1 evidence: `CorpusBuilder.build`、`RetrievalDocument.__post_init__`。

OLD — historical / superseded:

> How does a snapshot symbol become a retrieval document whose text hash matches the extracted source range?

REPLACEMENT:

> How does a snapshot symbol become a retrieval unit whose text hash matches the extracted source range?

简单名 `_document` 的完整 normalized identifier token 为 `document`；旧句
命中，替换句不命中。该事实已用冻结 self-repository commit
`12391233daa2149ead4f451e920b2e0d8a1a6beb` 的真实 adapter 输出复核。用户明确
授权以 `retrieval unit` 替换 `retrieval document`，并保持锚点及其他字段不变。

## 3. 确定性的 Grade-2 full-identifier-token 算法

使用现有 `project_intelligence.lexical.tokenize`，其冻结版本为
`code-lexical-v1`。对每条 Query 的每个真实 Grade-2 Symbol 执行以下规则；
不得用显示名称、Java signature 或自行重建的分词器代替 authoritative
`qualified_name` 和现有 tokenizer。

```python
simple_name = qualified_name.rsplit(".", 1)[-1]
simple_tokens = tokenize(simple_name)
if not simple_tokens:
    # FAIL CLOSED: report the query and authoritative Symbol identity.
    raise ValueError("empty simple-name token sequence")

banned_identifier_token = simple_tokens[0]
if task_type != "symbol_lookup":
    query_tokens = tokenize(query_text)
    if banned_identifier_token in query_tokens:
        raise ValueError("Grade-2 full identifier token leakage")
```

必须先提取最后一个 `.` 之后的 simple name，再 tokenize。
`tokenize(qualified_name)[0]` 会读到前面的类名等组件，不能替代上述算法。
空 token 序列在所有 task 中 fail closed；`symbol_lookup` 只豁免后续的
identifier-token 命中判定，因为该 task 本身就是 identifier lookup。

比较对象是完整 token 的精确相等关系，不做 substring matching：`builder`
不等于 `build`，`saved` 不等于 `save`，`grants` 不等于 `grant`。规范化完全
交给冻结 tokenizer；不得额外引入 stemming、lemmatization、POS tagging、
semantic exception 或 ordinary-English exception，也不设 manual allowlist。
无论相同 token 在 Query 中看起来是代码名、普通英语还是领域术语，非
`symbol_lookup` 命中都必须失败。

## 4. Compound identifier 与 tokenizer 契约

**不得要求 `len(tokenize(simple_name)) == 1`。** 该要求是先前未落 Git
提案中的错误限制，并非现有生产契约。`code-lexical-v1` 先输出完整 normalized
identifier token，再追加 identifier components；多 token 本身不会造成失败。

| simple name | 实际有序 `tokenize` 输出 | banned identifier token |
| --- | --- | --- |
| `update` | `("update",)` | `update` |
| `charge` | `("charge",)` | `charge` |
| `grant` | `("grant",)` | `grant` |
| `normalize_payload` | `("normalize_payload", "normalize", "payload")` | `normalize_payload` |
| `count_open_stops` | `("count_open_stops", "count", "open", "stops")` | `count_open_stops` |
| `markClosed` | `("markclosed", "mark", "closed")` | `markclosed` |
| `_read_source` | `("read_source", "read", "source")` | `read_source` |
| `__post_init__` | `("post_init", "post", "init")` | `post_init` |

以上八例已直接调用冻结 tokenizer 验证。实现先追加正则匹配词的 Unicode
`casefold` 值，再追加 snake_case / camelCase 等 components；前后下划线不属于
匹配词，内部下划线保留。既有
`tests/test_project_intelligence_lexical.py::test_tokenizer_contract_covers_code_identifiers_and_unicode`
验证完整 token 先于 components 的顺序，
`test_tokenizer_version_is_frozen_to_code_lexical_v1` 验证版本固定。

因此 Grade-2 为 `normalize_payload` 时，Query 中的 `payload` 不因本条规则
失败；Grade-2 为 `count_open_stops` 时，Query 中的 `open stops` 也不因本条
规则失败。Components 属于正常维护语言，将它们全部禁止会系统性破坏自然语言
Query。该许可仅界定本条 full-identifier-token gate，其他泄漏控制继续生效。

## 5. 现有控制、公平性与 Source of Truth

继续保留 Specification 中的 qualified-name、relative-path、
semantic-disambiguator、manifest-path、Java-package-prefix、near-duplicate /
Jaccard 以及 fixture/query leakage controls。`symbol_lookup` 仍受路径、Java
package prefix 和其他既有禁令约束。本附录不把 component-token 许可扩展为对
其他控制的豁免。

该修正旨在消除目标 Grade-2 完整 identifier token 对 BM25 的直接词面提示，
主要保护 RQ2（BM25 vs E5）与 RQ4（Hybrid comparison）的公平性。BM25 消费
lexical tokens，不能判断相同 token 的语用角色。这是 leakage-control correction，
不构成 BM25、E5 或 Hybrid 的效果证据。

RQ1–RQ4 definitions、metrics、K、Hybrid weights、Graph config、E5 identity、
Ground Truth anchors、72-query allocation 和 Addendum B semantics 均保持不变。
Addendum B 的 direct edit set `3/2/2`、authoritative SnapshotDiff `5/2/2/0`、
新 embedding 文档 `7` 仍有效；本次未执行增量检索或真实 E5。

执行依据为 **Protocol + Addendum A + Addendum B + Addendum C**。A 管理
annotation lifecycle；B 管理 incremental fixture SnapshotDiff；C 管理指定
Query wording correction 与 Grade-2 identifier leakage algorithm。Dataset
Specification 在各附录覆盖范围内服从相应附录，其余内容继续适用。
历史 authority list、旧 wording 和旧规则段落通过醒目引用连接到本附录，不删除。
未来执行者必须直接读取这些 Git 文档，不能依赖聊天记录选择有效文本。

## 6. 文档哈希沿革与无效草稿

下表均为文件原始 bytes 的 SHA-256。Protocol 与 Dataset Specification 本轮
只增加 Addendum C references / superseded markers，原有正文和 Query table
cells 保留。引用改变 bytes，因此旧哈希不可代表新文件。

| Document state | Commit / provenance | SHA-256 |
| --- | --- | --- |
| Protocol original freeze | `7a224c456f7615e4f4dbc79b1065755df3c8033f` | `ea08482fec6b0dfef4fe71089b14df1fca84a4276460cf92084c8a0e57070dbe` |
| Protocol with Addendum A reference | `e124c77037d8396601ce57d915babf1b7a416026` | `868309ca2127e8d1cbf7eeaa4ad2cb4b645b3b44831558f92bde40c82fb8b173` |
| Protocol previous current, with Addendum B references | `3dac455b5648c2b2acddbf8bf176f6621ac936d0` | `132f74590b7973bc4b6b38586929ca19c819ad1e758630012e17b01e41f27df9` |
| Protocol new reference-updated bytes | Addendum C references in this correction | `214360ac17633db7d77caec2ea2a135bf4372a773f9343b2fcb91bff8ee4e341` |
| Dataset Specification original freeze | `a532444c185d5984fe19b47017ea85ac228e0a62` | `3fb9a039a4fde7ef983218db09671424b0d412f054d6d5c39740b31a737b7d84` |
| Dataset Specification previous current, with Addendum B references | `3dac455b5648c2b2acddbf8bf176f6621ac936d0` | `fddcf5993223ee86e3bc0a3d5cfcafec186325cf4a904534aeca1203a802a18d` |
| Dataset Specification new reference-updated bytes | Addendum C references / superseded markers in this correction | `4e72ceb84f06df361e10a24a6ab273ed3f6eba4d3649b96177a810c6a0c30a92` |

Addendum C 自身的 raw-byte SHA-256 记录于 `PROJECT_CONTEXT.md`，
避免在本文件内嵌自身 hash。Addendum A/B 和原有历史 hash 记录均未修改。

此前 Phase 6.2A 在 Query wording / leakage policy conflict 上停止，生成的
34 个未跟踪失败草稿已经清理。其状态为 **INVALID / NOT AUTHORITATIVE /
NOT COMMITTED / NOT REUSABLE**，不存在正式 Dataset、Query Set 或 Ground
Truth。本次不恢复这些文件。未来 Phase 6.2A 必须从有效 Git Source of Truth
重新完整 materialize，不得 byte-for-byte reuse 已作废草稿：有效 Query wording
已变化，query-set hash 及相关 identity chain 必须重新建立，`created_at` 必须
属于成功的 draft materialization，延迟复核时钟目前 **NOT STARTED**。

## 7. 验证与门禁状态

基线全量回归为 **628 passed**。八个 tokenizer 例子及四条 old/new membership
核对通过。只读检查覆盖冻结表的 72 条 Query、60 个非 `symbol_lookup`
Grade-2 目标；其中 39 个简单名有多个 token，本规则允许其形态。

旧表有四条 full-identifier-token 命中；精确应用 §2 的四条 replacement 后，
本条 Grade-2 token gate 对全部 60 个非 `symbol_lookup` 目标的失败数为 **0**。
本次只读词面检查不是正式 Dataset / Ground Truth 验证，也不代替后续 adapter、
span、rationale、其他 leakage controls 或延迟复核。

- Addendum C: **FROZEN**
- Query Leakage Conflict: **CLOSED / RESOLVED**
- Corrected Queries: **4**（原定 3 条 + 用户补充授权 1 条）
- Leakage Rule: **FULL IDENTIFIER TOKEN ONLY**, `code-lexical-v1`
- Compound Component Tokens: **ALLOWED BY THIS GATE**
- Manual Allowlist: **NONE**
- Invalid Draft: **DISCARDED / NOT REUSABLE**
- Dataset / Query Set / Ground Truth: **NOT CREATED / NOT CREATED / NOT CREATED**
- Delayed Review Clock: **NOT STARTED**
- Phase 6.2A blocker: **LIFTED AFTER ADDENDUM C**
- Phase 6.2A: **ALLOWED BUT NOT STARTED**
- Phase 6.2 Gate: **OPEN**
- Phase 6.3 / Formal RQ1–RQ4 / V3.2: **NOT STARTED / NOT STARTED / NOT STARTED**

后续 Phase 6.2A 必须重新材料化，并完成全部现有机械与研究门禁；本次文档门禁
不开始该阶段。本次无 Dataset/Query/GT materialization、Retriever/E5 调用或
正式 RQ 结果。
