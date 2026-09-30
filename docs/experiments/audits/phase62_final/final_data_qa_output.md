# FINAL INDEPENDENT DATA QA VERDICT: PASS WITH NON-BLOCKING NOTES

**Critical:** 0
**Validity-blocking Medium:** 0
**Non-blocking Medium:** 0
**Low:** 4

冻结状态核对：HEAD = `61cbc0db166e1577068101ffbe92b3b58e38e152`（与指定一致），branch `v3.1.0-dev`，worktree 仅 `docs/thesis/` 未跟踪；未创建或修改任何仓库文件。以下结论全部由正式 artifact 独立重算，未直接采信报告数字。

> 重要前置观察：题面称外部 methodology review 已完成、中文语义审查 12/12 PASS，但**仓库冻结 artifact 与之不符**——`current_gate.json` 仍写 `External independent methodology review: REQUIRED / NOT YET ARCHIVED`、`Chinese ... semantic review: PENDING`；`Methodology_Review_Package_..._v1.md` 状态为"未收到审查结论"；`PROJECT_CONTEXT.md` 记 "EXTERNAL METHODOLOGY REVIEW REQUIRED BEFORE APPROVAL ... 尚未发生"。据此，题面所载 Grok 4.7 verdict 目前**仅存在于对话文本**，未落为 Git 跟踪身份。此点在第 7、8 节作为 L-ZH-01 的绑定前置处理，**不构成效度阻塞**（见严重度说明）。

## 1. Dataset counts（独立重算，全部一致）

| 项 | 期望 | 实测 |
|---|---|---|
| Queries | 72 | 72 |
| English test / dev / Chinese | 48 / 12 / 12 | 48 / 12 / 12 |
| GT | 72 | 72 |
| Evidence 行 | 134 | 134 |
| GT drafted | 72/72 | 72/72（`reviewed_at` 全为 null） |
| Grade 2 / Grade 1 | 72 / 62 | 72 / 62 |
| Java limited execution | 12/12 | 12/12 |
| Structured-valid Java reviews | 10/12 | 10/12 |
| Model SUPPORTS / QUESTIONS | 10 / 0 | 10 / 0 |
| Execution-level CANNOT_ASSESS | 2 | 2 |

语言 `python 58 / java 14`；六类 task 各 12；`queries.jsonl`/`ground_truth.jsonl` 实测 SHA-256 与 `checksums.sha256` 一致。

## 2. Identity integrity
- `query_id` 唯一（72）、`ground_truth_id` 唯一（72）、命名恒为 `gt-<query_id>`。
- GT ↔ query 一一对应，无 orphan / duplicate；reference 72 条与 query 集合相等，且 `ref.ground_truth_id` 与 GT 一致。
- split / language / task_type / project(fixture) identity 正确；`symbol_lookup` 12 条均落在正确 split。
- 冻结 hash 链**用冻结代码重算**并与声明一致：`dataset_hash 164994a8…`、`path_manifest_hash 9adddbc3…`、`query_set_hash 5393d520…`、`ground_truth_hash d3116195…`、reference identity `d3d5f54f…`；`methodology_identity 733eb5fe…`；`engineering_identity 6b3bb320…`；`verify_frozen_checksums()` PASS；`verify_commit(12391233…)` PASS。

## 3. GT / evidence integrity
- 134 条 evidence 全部具备 `rationale`，无缺失；每条 GT 至少含 1 条 Grade 2。
- fixture evidence 75 条：文件存在、span 在界内、symbol 命中，0 问题。
- self-repo evidence 59 条：在冻结 revision `12391233…` 下 span 在界内、symbol 命中，0 问题。
- 无 orphan、无重复引用。

## 4. Leakage（按冻结 Addendum C 原样重跑）
- 工具：`project_intelligence.lexical.tokenize`，版本 `code-lexical-v1`；算法 `simple_name = qualified_name.rsplit(".",1)[-1]` → `tokens[0]` 为 banned。
- 60 个 non-`symbol_lookup` query、60 个 Grade-2 目标；空 token 0；**完整 identifier token 命中 0**。
- 四条修正 query（`et-bl-py-01`/`et-bl-py-03`/`et-mt-py-03`/`et-cf-py-01`）确为 replacement 措辞（旧句 `update`/`charge`/`grant`/`document` 已消失）。未发明新规则。

## 5. Java audit integrity
- 12/12 通过冻结 `RepositoryAuthority.load_audit`（sent_input / raw_reply / session / context / model_metadata / transcription 全链 raw hash 重算；目录名 == `identity_hash`）。
- **10 条 v1**：存在合法 `EvidenceReview`；重解析 raw reply 得到的 normalized reviews 与记录逐字段（identity/verdict/reason/grade_observation）一致，verdict = `SUPPORTS`。
- **2 条 v2**（`et-bl-ja-01`→`76334e61…`、`et-fl-ja-02`→`d8c74c81…`）：`evidence_reviews=[]`、`model_verdict=unavailable`、`execution_outcome=CANNOT_ASSESS`、`failure_reason=response_contract_failure`，transcription 精确匹配三字段。`et-bl-ja-01/raw-reply.txt` 自由文本**确实含** `"overall_status":"SUPPORTS"` 与 `status:"SUPPORTS"`，但整段被 markdown 代码围栏与散文包裹，冻结严格 parser 的 `json.loads` 失败——**该 SUPPORTS 未被采纳为正式 verdict**，无伪造 `EvidenceReview`，`reply_complete=true` 仅表示 Final Answer 捕获完整，不代表结构化审查合格。

## 6. Resolution integrity
- 两条 `ResolutionRecord` 存在（digest `1680c646…`、`ac39e307…`），`target_identity` 分别 = 对应 audit `identity_hash`（`76334e61…` / `d8c74c81…`）。
- 冻结 `_validate_source_resolution` **PASS**：基于冻结源码 / prepared evidence；`source_sha256` 与冻结 fixture 一致；span 切片与 `source_excerpt` 一致；`overall_resolution=SUPPORTED_BY_FROZEN_SOURCE`；`gt_or_grade_changed=false`；`evidence_identity` = `source_resolution/*.json` 的 raw checksum。
- 原始执行级 `CANNOT_ASSESS` 保持不变（`execution_outcome_retained=CANNOT_ASSESS`）。

## 7. Chinese audit readiness
12 条中文 query（Python、六类各 2、split=`chinese_coverage`）身份/配额/证据/机械泄漏检查通过。但仓库中**不存在**任何 `chinese_coverage_audit` 归档记录或身份；`current_gate.json` 仍记 PENDING。12/12 PASS 目前仅为对话文本，不能成为 authority（见 L-ZH-01）。

## 8. Methodology review binding
仓库中**不存在** Git 跟踪的外部方法论审查归档/身份（`Methodology_Review_Package` 自身声明"未收到审查结论"）。因此 `chinese_coverage_audit` 与 `methodology_review` 两个 REQUIRED 先决身份目前均未 materialize，L-RES-01 的"显式绑定"与 L-ZH-01 的"绑定 methodology review identity"在当前 commit 下**尚无法执行**。此为可追踪性前置，非数据缺陷。

## 9. Formal RQ boundary
仓库无任何 Formal RQ1–RQ4 运行结果，无 Recall@5 / MRR 结论文件；`tests/fixtures/experiments/*_oracle.json` 为测试夹具，非实验结果。无 `reference_approval/` 目录、无 Phase 6.2 Closure。`current_gate.json` 记 `Formal RQ1–RQ4: NOT ELIGIBLE / NOT STARTED`、`dry_run_eligible=false`、`formal_execution_eligible=false`。Phase 6.2 artifact 仅表示 benchmark/reference readiness。

---

## Issues

**L-GT-01** ｜ Severity: LOW（NON-BLOCKING）
- Evidence: 72/72 GT `annotation_status=drafted`、`reviewed_at=null`；`identity.json.annotation_status=drafted`；`earliest_allowed_review_at` 存在但延迟复核时钟 NOT STARTED。
- Required action: approval 叙述须以 `drafted` / `reviewed_at=null` 为准，不得描述为已复核或已批准标签。

**L-AUDIT-01** ｜ Severity: LOW（NON-BLOCKING）
- Evidence: 2 条 v2 记录 `evidence_reviews=[]`、`model_verdict=unavailable`、`execution_outcome=CANNOT_ASSESS`；冻结 loader 强制 `audit_failure_response_is_valid`（可解析则报错）。
- Required action: approval 叙述须以 empty reviews + unavailable + CANNOT_ASSESS 为准；**不得**把 `reply_complete=true` 描述为合格 structured review。

**L-RES-01** ｜ Severity: LOW（NON-BLOCKING）
- Evidence: 两条 `ResolutionRecord` digest `1680c646…`、`ac39e307…`，`target_identity` 与两条 audit identity 精确对应；`_validate_source_resolution` PASS。
- Required action: Approval 阶段必须显式绑定这两个 `ResolutionRecord` identity（`resolution_identities`）。

**L-ZH-01** ｜ Severity: LOW（NON-BLOCKING）
- Evidence: 无 `chinese_coverage_audit` 归档身份；无 `methodology_review` 归档身份；`current_gate.json` 两项均 PENDING/NOT YET ARCHIVED。
- Required action: 将 12 条中文语义审查确定性归档为正式 `chinese_coverage_audit` 记录并产生身份，且该身份必须绑定 `methodology_review` 身份；同时把外部方法论审查 verdict materialize 为 Git 跟踪身份。聊天文本不得作为最终 authority。**不得重写 12 条 query。**

> 严重度说明：L-ZH-01/L-RES-01 的归档与绑定属于可追踪性前置，中文集合按规格仅用于单独覆盖分析、不得并入 English test 主结果或调参，故不构成对主实验效度的影响；未发现任何数据级 Critical 或 validity-blocking Medium。按判定规则，不得仅因 Low 阻塞。

---

**REFERENCE APPROVAL DATA-QA STATUS: ELIGIBLE**

（数据质量层面通过；在创建 Reference Approval 前，须完成 L-ZH-01 的归档/绑定与 L-RES-01 的身份绑定，并确保正式 eligibility validator 通过。）

PROMPT COMPLETENESS: CONFIRMED
END MARKER: SEEN
=== END OF V3.1 PHASE 6.2 FINAL INDEPENDENT DATA QA ===