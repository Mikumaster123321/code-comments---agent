# V3.1.4 Independent Final Release QA

本文件是 V3.1.4「Reliability / Maintainability / Pre-V3.2 Stabilization」的独立 Final
Release QA 证据。它由独立 QA 角色在真实执行后生成，不得预先写成 PASS，也不得由实现
阶段（Codex）代写。该证据必须在 release commit C1 之前进入 Git history。

## 1. QA identity and role

- QA model / role：**DeepSeek V4.1 Flash — Independent Final Release QA + Final Release Publisher**
- QA 职责：作为 V3.2 Multi-Agent Collaboration 之前最后一个 maintenance release gate，
  独立复核 scope、release identity、provider credential isolation、network retry ownership、
  batch/resource correctness、cancellation、temp/workspace lifecycle、diagnostics/redaction、
  runtime/startup/CI、pre-V3.2 compatibility、full regression、Formal immutability 与
  documentation QA，并在全部 blocking gate 通过后执行 finalize、annotated tag、main sync、
  双远端发布与远端校验。
- QA 原则：不采信 Codex 报告本身；一切结论基于真实 Git history、真实 diff、真实测试输出、
  真实 runtime behavior、credential behavior、network behavior、resource lifecycle、
  release identity、documentation 与 remote state。只读复核，不修改业务代码、测试、provider。
- QA 日期：2026-10-09
- 复核仓库（QA worktree）：`/Users/guo_wang/Desktop/code-comments---agent`
- 受保护路径：`docs/thesis/`（全程只通过 `git status` 观察，未读取、未列出、未搜索、
  未修改、未移动、未暂存、未删除）。

## 2. Reviewed revision

- Reviewed branch：`v3.1.4-dev`
- Reviewed HEAD：`134afdfea9b20cc7339141b007b8b0799f97b8fb`
- Reviewed diff range：`7f6ac6ffe20991d47f094d271213f1d57d3c5efd..134afdfea9b20cc7339141b007b8b0799f97b8fb`
- 分支点 / V3.1.3 main 基线：`7f6ac6ffe20991d47f094d271213f1d57d3c5efd`（ancestor of HEAD = **YES**）
- 该范围内的提交（恰好 4 个）：
  - `47ee7d7` — `docs(v3.1.4): freeze reliability stabilization scope`
  - `37905ac` — `fix(v3.1.4): isolate provider credentials by provider`
  - `593109d` — `fix(v3.1.4): stabilize runtime failure and resource contracts`
  - `134afdf` — `docs(v3.1.4): prepare reliability release materials`
- V3.1.3 基线身份：main `7f6ac6f...`、C1 `7710abd2adf46f89c28b67898cce7eff2d92dc96`、
  tag `v3.1.3`（annotated，peeled `7710abd2...`），release schema v2。
- 复核时不存在 `v3.1.4` tag。本 QA 证据文件在复核的 Git revision 中尚不存在（untracked），
  将在 release commit **C1** 首次进入 Git history —— 符合「证据必须在 C1 之前/当时进入历史」
  的要求，且由独立 QA 真实生成，而非由实现阶段预写。
- worktree 干净：`git status --short` 仅显示受保护路径 `?? docs/thesis/`（非本次范围，未触碰）。

## 3. Scope verification

真实 diff `7f6ac6f..134afdf` 共 **30 个文件变更**（`+2284 / -318`），与冻结的七项范围
一一对应，无 scope creep：

| 冻结项 | 对应变更 | 结论 |
| --- | --- | --- |
| V314-CRED-01 provider credential isolation | `config.py`、`llm_provider.py`、`.env.example`、`tests/test_provider_foundation.py` | 符合 |
| V314-RUNTIME-02 runtime / startup contract | `code_comments_agent/reliability.py`（新增）、`llm_service.py`、`main.py`、`.github/workflows/pytest.yml` | 符合 |
| V314-NET-03 network timeout / retry ownership | `llm_provider.py`、`llm_service.py`、`code_comments_agent/reliability.py` | 符合 |
| V314-CANCEL-04 cooperative cancellation | `processor.py`、`code_comments_agent/reliability.py` | 符合 |
| V314-RESOURCE-05 resource / ZIP / batch correctness | `processor.py`、`code_comments_agent/workspace.py`、`code_comments_agent/reliability.py` | 符合 |
| V314-DIAG-06 diagnostics / redaction | `processor.py`、`i18n.py`、`ui.py` | 符合 |
| V314-API-07 pre-V3.2 compatibility contract | `docs/architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md`、`docs/architecture/V3_1_4_Runtime_Reliability_Contract.md`、`tests/test_repository_architecture.py` | 符合 |
| 测试与文档 | `tests/test_v3_1_4_reliability.py`（新增）、`docs/development/*`、`docs/release/*`、`docs/README.md`、`docs/qa/README.md`、`README.md`、`PROJECT_CONTEXT.md`、`scripts/dev.py`、`code_maintenance/__init__.py` | 符合 |

范围边界复核（全部通过）：

- 禁止模块目录：`rag`=absent、`agents`=absent、`router`=absent、`api`=absent、`vscode`=absent。
- 未引入 tree-sitter / ANTLR / JavaParser 等新依赖。
- `docs/experiments` 在范围内变更文件数 = **0**（实验文档保持冻结）。
- `docs/thesis` 在范围内变更文件数 = **0**；受保护路径未被触碰。
- `code_comments_agent` 仅含 4 个 tracked 文件：`__init__.py`、`reliability.py`、
  `ui_styles.py`、`workspace.py`（新增 `reliability.py` 为可靠性契约单一真源，未引入
  agent/planner/router/critic/orchestrator API，未改动 retrieval / ranking / BM25 / E5 /
  Graph / RRF / ContextBuilder）。

## 4. Release identity verification

- `docs/release/release_state.json` 为 **schema v2**，字段集精确为：
  `schema_version`、`version`、`state`、`expected_development_branch`、`expected_main_branch`、
  `release_commit`、`tag`、`baseline`、`required_documents`、`final_qa_evidence`。
- **不存在自引用字段** `final_head`（v2 不记录 final HEAD）。符合 §4 / §26。
- 复核基线（candidate）态：`state = RELEASE_CANDIDATE`、`version = 3.1.4`、
  `expected_development_branch = v3.1.4-dev`、`expected_main_branch = main`、
  `release_commit = null`、`tag = null`。
- baseline 与预期一致：`{"version": "3.1.3", "commit": "7710abd2adf46f89c28b67898cce7eff2d92dc96", "tag": "v3.1.3"}`。
- `required_documents` 共 **15 项**，包含 `docs/qa/V3_1_4_Final_Release_QA.md`；
  `final_qa_evidence = docs/qa/V3_1_4_Final_Release_QA.md`，以 `docs/qa/` 开头且属于
  `required_documents`。
- fail-closed 行为已实测：`release-check --version 3.1.4` 在缺 Final QA evidence 时以明确
  原因失败（“What failed: Final QA evidence / Expected: reviewed evidence at
  docs/qa/V3_1_4_Final_Release_QA.md / Actual: missing / Safe recovery: run independent
  Final Release QA and commit its real evidence before release”）。该失败是**预期且正确**的
  门禁行为，不是缺陷。
- 代码版本：`code_maintenance.__version__ = "3.1.4"`，与 `release_state.version` 一致；
  README 含版本小节。
- 身份规则（§26）复核：C1 = `release_commit` 意图；annotated tag → C1；C1 必须是运行时
  HEAD 的 ancestor；`final_head` 允许不等于 `release_commit`，**从不要求二者相等**；
  旧 tag / 旧 commit / 旧记录不得改写。

## 5. Legacy v1 compatibility

- release schema v1（V3.1.2 及更早）仍可被读取：`_load_release_state` 对 v1/v2 字段集分别
  校验；`tests/test_release_workflow.py` 的 legacy v1 readable 用例通过。
- 旧记录未被修改：范围内 `docs/release/release_state.json` 仅承载 V3.1.4 候选态；
  V3.1.3 C1 `7710abd2...` 及其 annotated tag `v3.1.3`（peeled `7710abd2...`）保持不变；
  V3.1.2 C1 `247bbfc1...`、tag `v3.1.2`（peeled `247bbfc1...`）不变；
  V3.1.1 C1 `683479da...`、tag `v3.1.1`（peeled `683479da...`）不变；
  V3.1.0 C1 `8813e4c2...`、tag `v3.1.0`（peeled `8813e4c2...`）不变。
- 未对任何旧 tag 做移动、重打或 force 操作。

## 6. Pre-V3.2 compatibility / architecture compatibility

- 冻结契约文档：`docs/architecture/V3_1_4_Runtime_Reliability_Contract.md` 与
  `docs/architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md` 明确划分
  Stable / Legacy-Compat / Frozen-Formal 三类表面。
- 兼容性再导出 identity 实测（与 V3.1.3 抽取一致）：`processor.save_workspace is
  code_comments_agent.workspace.save_workspace` → `True`；`CUSTOM_CSS is
  code_comments_agent.ui_styles.CUSTOM_CSS` → `True`。
- `tests/test_repository_architecture.py`（含 V3.1.4 兼容性用例）通过，覆盖包内文件集约束、
  identity-equal 再导出与 pre-V3.2 兼容表面。
- `tests/test_v3_1_4_reliability.py` 的兼容性用例断言 retrieval / ranking / ContextBuilder 等
  既有公开契约未被改变。
- 结论：V3.1.4 为**加法式**稳定化，未改变 V3.2 前置依赖的既有运行时行为契约。

## 7. Provider credential isolation (V314-CRED-01, P0)

独立行为复核（源码 + 负向矩阵 + 实测 probe）：

- provider 作用域环境键：仅 OpenAI 与 Custom（OpenAI-compatible）可接受通用
  `OPENAI_API_KEY`；各 vendor（如 DeepSeek）**不读取** `OPENAI_API_KEY`，只读取各自的
  provider-specific 键。
- 跨 provider 切换（含 UI key 为空）**永不继承**上一个 provider 的凭据：切换后目标 provider
  在无凭据时得到占位 `EMPTY_API_KEY`，且 `config._active_api_key is None`，旧密钥不被复用。
- 显式当前 provider 凭据优先于环境键（`test_explicit_current_provider_credential_overrides_environment`）。
- 通用 `OPENAI_API_KEY` 不与其它 vendor 共享（`test_generic_openai_environment_key_is_not_shared_with_other_vendors`）。
- 密钥不持久化到 workspace（`test_v3_1_4_reliability.py` workspace 用例 + 独立 probe）。
- 结论：P0 凭据隔离契约成立。

## 8. Network timeout / retry ownership (V314-NET-03)

- 单一重试归属：`SDK_MAX_RETRIES == 0`（SDK 层重试关闭）、`APPLICATION_GENERATION_ATTEMPTS == 1`、
  `TRANSPORT_ATTEMPTS_PER_APPLICATION_ATTEMPT == 1`、`config.MAX_RETRIES == 1`。
- 默认 client factory 实测：`max_retries == 0`、`timeout == RUNTIME_LIMITS.generation_timeout_seconds`
  （实测 90.0s）。
- 非瞬态异常矩阵（`APIConnectionError` / `APITimeoutError` 等）**不自动重试**：probe 断言
  `provider.calls == 1`，且错误文本中不含任何密钥片段（不泄漏凭据）。
- 歧义连接失败不自动重试以避免静默重复生成（成本安全）；
  `test_ambiguous_connection_failure_is_not_automatically_retried` 通过。
- 结论：重试/超时归属唯一且明确，成本安全契约成立。

## 9. Cancellation / resource / workspace (V314-CANCEL-04, RESOURCE-05)

- 协作式取消：取消后状态为 `Cancelled`（非 `Idle`）；shutdown 使用
  `{"wait": True, "cancel_futures": True}` 取消待执行 future 同时允许在跑工作收尾。
- 集中式资源限制（`RuntimeLimits`）：单一真源；ZIP 解压具备 **5 项守卫**（路径穿越 / 符号
  链接 / 条目数 / 大小 / 压缩比），均抛 `ResourceLimitError`（独立 probe 逐项验证）。
- 批处理结果分类：全部失败时**不产生 ZIP**，文案为“成功 0 / 失败 1 / ALL_SYMBOLS_FAILED”；
  部分成功 / 取消结果正确清理；部分 ZIP 被移除。
- workspace 往返 / 版本校验 / fail-closed（版本 999 明确失败）均通过。
- 结论：批处理与资源生命周期正确，无脏临时文件残留。

## 10. Diagnostics / runtime / CI (V314-DIAG-06, RUNTIME-02)

- 结构化诊断 allow-list 脱敏：未授权字段（secret / prompt / 绝对路径）被脱敏，`operation_id`
  与 `error_category` 保留；`javac` 路径被脱敏（独立 probe 断言 `TOPSECRET`、
  `SOURCE-CODE`、`/Users/private` 均被移除）。
- 惰性导入：import 应用不拉入 gradio / transformers（`test` 断言）。
- CI 契约：`.github/workflows/pytest.yml` 含 python-3.10 / import / UI / full smokes 断言。
- 结论：诊断脱敏与运行时/启动契约成立。

## 11. Tests

独立复跑全部必需 profile（离线，`python scripts/dev.py test <profile>` 或直接 `pytest`，
非真实 provider 请求，无真实 API key）：

| Profile | 命令 | 结果 |
| --- | --- | --- |
| Targeted（组合） | `pytest tests/test_provider_foundation.py tests/test_v3_1_4_reliability.py tests/test_llm_contracts.py tests/test_processor_regressions.py tests/test_developer_workflow.py` | **98 passed** |
| Reliability | `pytest tests/test_v3_1_4_reliability.py` | **28 passed** |
| P0 credential | `pytest tests/test_provider_foundation.py` | **33 passed** |
| LLM contracts | `dev.py test llm` | **6 passed** |
| Production | `dev.py test production` | **198 passed** |
| Experiments | `dev.py test experiments` | **240 passed** (311.80s) |
| Release / architecture | `dev.py test release` | **24 passed** |
| Full | `dev.py test full` | **1010 passed** (360.82s) |

- 与冻结基线一致：Targeted 98 / Reliability 28 / P0 33 / LLM 6 / Production 198 /
  Experiments 240 / Release 24 / Full 1010。
- `dev.py test release` 的 release profile = PASS，artifact identity `acd8f46479...`，
  artifact SHA-256 `2ac32989ad...`，formal scope = 17 configs / 48 queries / 816 pairs。
- 独立 probe（`v314_independent_probe.py`，QA 自建、不进入仓库）**25/25 PASS**，覆盖
  registry fallback、跨 provider 不复用、通用 openai 不共享、sdk-retries=0、timeout=90、
  no-retry 矩阵、诊断脱敏、5 项 ZIP 守卫、batch all-failed、workspace、no-scope-creep。
- 所有测试均为离线，无真实 LLM API 调用。

## 12. CPython 3.10 UI smoke

- 环境：**CPython 3.10.20 + gradio 6.27.0**（本机唯一可用且受支持的 CPython 3.10 环境）。
- 环境说明：本机不存在 3.10.22 小版本；本 QA 以真实可用的 CPython 3.10.20 独立复现该
  smoke。实现阶段文档曾记录“本机无 3.10 解释器”，本 QA 以真实运行结果**证伪**该说法。
- `create_ui()` 构建成功，返回类型 `Blocks`，`blocks_count = 106`。
- 兼容再导出实测：`CUSTOM_CSS is code_comments_agent.ui_styles.CUSTOM_CSS` → `True`；
  `processor.save_workspace is code_comments_agent.workspace.save_workspace` → `True`。
- 结果：**UI SMOKE: PASS**（RELEASE BLOCKER 解除）。

## 13. Formal immutability

- Formal execution revision：`2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- Formal artifact canonical identity：`acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Formal artifact SHA-256：`2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`
- `experiment-validate archive-v3.1.0`：**PASS**（archive commit / identity 与既有记录一致）
  ——即受保护的正式实验产物在 V3.1.4 变更后仍字节级不可变。
- `export_formal_thesis_tables.py --check`：**4 / 4 CSV verified**（确定性导出）。
- 结论：V3.1.4 的可靠性稳定化**未影响**正式实验 revision、archive、artifact identity 与
  SHA-256。

## 14. Documentation QA

- 关键文档行数（复核 revision `134afdf`；release 定稿后 README/PROJECT_CONTEXT 会有小幅
  行数变化）：`PROJECT_CONTEXT.md`=152、`README.md`=771、`docs/README.md`=29、
  `docs/release/README.md`=137、`docs/development/README.md`=22、`docs/qa/README.md`=17、
  Runtime Reliability Contract=105、Pre-V3.2 Compatibility Contract=105、
  Development Report=169、Scope=283、Thesis MD=125、Thesis TXT=119、Release Notes=79。
- Source of Truth 分层正确：Machine = Git objects + `release_state.json`；Human = README /
  PROJECT_CONTEXT（current section）/ `docs/release/README.md`；历史快照（既往 QA 报告、
  Scope Freeze、V3.1.0–V3.1.3 版本化文档）不得被当作当前权威。
- 双格式 Thesis Materials 合规：TXT 为独立文本（6082 字节、UTF-8、无 BOM、无 CRLF、无非
  ASCII 污染，无 Markdown 标题/围栏代码块/链接/HTML 注释/管道表格），并以「素材来源与身份」
  结尾，含 repo-relative 路径与基线 commit。MD 版本结构完整。
- 候选态在 QA 开始时被正确标记：README / PROJECT_CONTEXT / `docs/release/README.md` /
  Release Notes 均标注 `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`、tag/push = NO/NO。
  此为**正确的候选态基线**，本 QA 通过后随 release 定稿一并更新为 V3.1.4 RELEASED。
- 文档一致性：README、PROJECT_CONTEXT、docs 索引、Release Notes、Development Report 与
  `release_state.json` 相互一致；历史快照未被改写。

## 15. Blocking findings

**无（0）。** 所有 blocking gate 均通过：

- scope 与冻结七项一致，无 scope creep，无禁止模块/依赖。
- P0 凭据隔离成立（provider 作用域、跨 provider 不复用、通用键不共享、不持久化）。
- network 重试/超时归属唯一，非瞬态与歧义失败不自动重试（成本安全）。
- cancellation → `Cancelled`；资源限制单源、ZIP 5 项守卫、batch 结果分类正确。
- diagnostics allow-list 脱敏、runtime 惰性导入、CI 契约成立。
- pre-V3.2 兼容表面（Stable / Legacy-Compat / Frozen-Formal）未被破坏。
- release schema v2 正确、无自引用 `final_head`、fail-closed 行为正确。
- legacy v1 仍可读，旧 tag/commit/记录未被改写。
- 全部 required tests 以预期基线通过（98 / 28 / 33 / 6 / 198 / 240 / 24 / 1010）。
- CPython 3.10 UI smoke PASS。
- Formal revision / archive / identity / SHA-256 字节级不变，4/4 确定性 CSV 校验通过。

## 16. Non-blocking findings

1. V3.1.2 在历史上仅完成本地 finalize，远端 publication 记录为 Pending（历史遗留），
   不影响 V3.1.4 本次发布判断。
2. 实现阶段文档与 Release Notes 曾记录“本机无 CPython 3.10 解释器”，本 QA 以真实可用的
   CPython 3.10.20 复现 UI smoke 并证伪；该措辞需随 release 定稿更新。
3. 候选态措辞（README / PROJECT_CONTEXT / `docs/release/README.md` / Release Notes /
   Development Report / Thesis Materials 中的 `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`
   等）需在本 QA 通过后随 release 定稿更新为 **V3.1.4 RELEASED**；历史快照不改写。

以上均为非阻塞，不阻碍发布。

## 17. Release verdict

所有 blocking gate 已真实通过，未发现阻塞性缺陷，非阻塞项不构成阻碍。

**FINAL RELEASE QA: PASS**

本 verdict 授权在独立 QA 完成后执行：release 措辞定稿为 V3.1.4 RELEASED → C1
`release(v3.1.4): finalize v3.1.4`（含本证据）→ annotated tag `v3.1.4`
（`V3.1.4 - Reliability and Pre-V3.2 Stabilization`）→ C1 → C2
`release(v3.1.4): record final release identity` → main sync → 双远端（github / gitee）push
→ 远端校验。
