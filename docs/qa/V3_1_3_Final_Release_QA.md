# V3.1.3 Independent Final Release QA

本文件是 V3.1.3「Repository / Directory / Documentation Architecture」的独立 Final
Release QA 证据。它由独立 QA 角色在真实执行后生成，不得预先写成 PASS，也不得由实现
阶段（Codex）代写。该证据必须在 release commit C1 之前进入 Git history。

## 1. QA identity and role

- QA model / role：**DeepSeek V4.1 Flash — Independent Final Release QA + Final Release Publisher**
- QA 职责：作为 V3.1.3 发布的最后一个独立 Gate，独立复核 scope、release identity、
  architecture compatibility、tests、CPython 3.10 UI smoke、Formal immutability、
  documentation QA，并在全部 blocking gate 通过后执行 finalize、annotated tag、main
  sync、双远端发布与远端校验。
- QA 原则：不采信 Codex 自述，一切结论基于真实 Git object、真实 diff、真实测试输出、
  release schema、文档与远端状态；只读复核，不修改业务代码、测试、provider。
- QA 日期：2026-10-09
- 复核仓库（QA worktree）：`/Users/guo_wang/.codex/worktrees/8917/code-comments---agent`
- 受保护路径：`docs/thesis/`（全程只通过 `git status` 观察，未读取、未列出、未搜索、
  未修改、未移动、未暂存、未删除）。

## 2. Reviewed revision

- Reviewed branch：`v3.1.3-dev`
- Reviewed HEAD：`d8e752577d3c07e6c1b130b7a77f09d0180f87e8`
- Reviewed diff range：`93e4c0ab326e5eaf2fb6051c241fc5c76072afe9..d8e752577d3c07e6c1b130b7a77f09d0180f87e8`
- 分支点 / V3.1.2 main 基线：`93e4c0ab326e5eaf2fb6051c241fc5c76072afe9`（ancestor of HEAD = **YES**）
- 该范围内的提交（恰好 3 个）：
  - `2a6233d` — `docs(v3.1.3): freeze repository architecture scope`
  - `f078206` — `refactor(v3.1.3): strengthen repository and release architecture`
  - `d8e7525` — `docs(v3.1.3): prepare repository architecture release materials`
- V3.1.2 基线身份：main `93e4c0a...`、C1 `247bbfc1f849b929a00b32b09ada5e060ceef9d9`、
  tag `v3.1.2`（annotated，peeled `247bbfc1...`）。
- 复核时不存在 `v3.1.3` tag。本 QA 证据文件在复核的 Git revision 中尚不存在（untracked），
  将在 release commit **C1** 首次进入 Git history —— 符合「证据必须在 C1 之前/当时进入历史」
  的要求，且由独立 QA 真实生成，而非由实现阶段预写。

## 3. Scope verification

真实 diff `93e4c0a..d8e7525` 共 **25 个文件变更**（`+4238 / -2738`），与冻结的六项范围
一一对应，无 scope creep：

| 冻结项 | 对应变更 | 结论 |
| --- | --- | --- |
| V313-REL-01 release schema v2 | `docs/release/release_state.json`、`scripts/dev.py`、`docs/release/Version_Documentation_Contract.md`、`docs/release/README.md`、`tests/test_release_workflow.py` | 符合 |
| V313-DOC-02 documentation / docs indices | `docs/README.md`、`docs/development/README.md`、`docs/qa/README.md`、`docs/release/Release_Notes_V3_1_3.md`、`docs/architecture/Repository_Architecture_Map_V3_1_3.md` | 符合 |
| V313-CONTEXT-03 PROJECT_CONTEXT 重构 | `PROJECT_CONTEXT.md`、`docs/development/PROJECT_CONTEXT_History_Through_V3_1_2.md` | 符合 |
| V313-APP-04 应用模块抽取 | `code_comments_agent/{__init__,ui_styles,workspace}.py`、`processor.py`、`ui.py` | 符合 |
| V313-NAV-05 导航 / 索引 | `README.md`、`docs/README.md`、`docs/release/README.md` | 符合 |
| V313-TEST-06 tests | `tests/test_repository_architecture.py`、`tests/test_release_workflow.py`、`tests/test_developer_workflow.py` | 符合 |

范围边界复核（全部通过）：

- 禁止模块目录：`rag`=absent、`agents`=absent、`router`=absent、`api`=absent、`vscode`=absent。
- 未引入 tree-sitter / ANTLR / JavaParser 等新依赖（`requirements` 相关文件未在范围内变更）。
- `docs/experiments` 在范围内变更文件数 = **0**（实验文档保持冻结）。
- `docs/thesis` 在范围内变更文件数 = **0**；受保护路径未被触碰。
- `code_comments_agent` 仅含 3 个 tracked 文件：`__init__.py`、`ui_styles.py`、`workspace.py`。

## 4. Release identity verification

- `docs/release/release_state.json` 为 **schema v2**，字段集精确为：
  `schema_version`、`version`、`state`、`expected_development_branch`、`expected_main_branch`、
  `release_commit`、`tag`、`baseline`、`required_documents`、`final_qa_evidence`。
- **不存在自引用字段** `final_head`（v2 不记录 final HEAD），也未出现 `github_main` /
  `gitee_main` 之类自引用字段。符合 §4 / §22。
- 复核基线（candidate）态：`state = RELEASE_CANDIDATE`、`version = 3.1.3`、
  `expected_development_branch = v3.1.3-dev`、`expected_main_branch = main`、
  `release_commit = null`、`tag = null`。
- baseline 与代码常量一致：`{"version": "3.1.2", "commit": "247bbfc1f849b929a00b32b09ada5e060ceef9d9", "tag": "v3.1.2"}`；
  `BASELINE_RELEASE_COMMIT` / `BASELINE_TAG` 与之一致。
- `required_documents` 共 14 项，包含 `docs/qa/V3_1_3_Final_Release_QA.md`；
  `final_qa_evidence = docs/qa/V3_1_3_Final_Release_QA.md`，以 `docs/qa/` 开头且属于
  `required_documents`。
- fail-closed 行为已实测：`release-check --version 3.1.3` 在缺 Final QA evidence 时
  以明确原因失败（“What failed: Final QA evidence / Expected: reviewed evidence at
  docs/qa/V3_1_3_Final_Release_QA.md / Actual: missing / Safe recovery: run independent
  Final Release QA and commit its real evidence before release”）。该失败是**预期且正确**的
  门禁行为，不是缺陷。
- 代码版本：`code_maintenance.__version__ = "3.1.3"`，与 `release_state.version` 一致；
  README 含 `### V3.1.3` 版本小节。
- 身份规则（§26）复核：C1 = `release_commit` 意图；annotated tag → C1；C1 必须是运行时
  HEAD 的 ancestor；`final_head` 允许不等于 `release_commit`，**从不要求二者相等**；
  旧 tag / 旧 commit / 旧记录不得改写。

## 5. Legacy v1 compatibility

- release schema v1（V3.1.2 及更早）仍可被读取：`_load_release_state` 对 v1/v2 字段集
  分别校验。`tests/test_release_workflow.py` 含 **legacy v1 readable** 用例并通过。
- 旧记录未被修改：范围内 `docs/release/release_state.json` 仅承载 V3.1.3 候选态；
  V3.1.2 的 C1 `247bbfc1...` 与其 annotated tag `v3.1.2`（peeled `247bbfc1...`）保持
  不变；V3.1.1 C1 `683479da...`、tag `v3.1.1`（peeled `683479da...`）保持不变；
  V3.1.0 C1 `8813e4c2...`、tag `v3.1.0`（peeled `8813e4c2...`）保持不变。
- 未对任何旧 tag 做移动、重打或 force 操作。

## 6. Architecture compatibility

- `ui.py` 由内联样式表重构为引用 `code_comments_agent.ui_styles`（`CUSTOM_CSS` 等），
  并对根命名空间保持兼容再导出。
- `workspace` 持久化逻辑抽取到 `code_comments_agent.workspace`，`processor.py` 兼容再导出。
- 兼容性再导出 identity 实测（APP-04）：

  ```
  processor.save_workspace is code_comments_agent.workspace.save_workspace  -> True
  （共 7 个 processor 符号 identity-equal = True）
  root CUSTOM_CSS is code_comments_agent.ui_styles.CUSTOM_CSS                  -> True
  APP-04 IDENTITY EQUAL: True
  ```

- `tests/test_repository_architecture.py`（新增，8 例）通过，覆盖包内文件集约束与
  identity-equal 再导出。
- 结论：抽取为边界清晰的内嵌包，且对原有根级 import 保持 100% 向后兼容，未改变运行时
  behavior 契约。

## 7. Tests

独立复跑全部必需 profile（离线，`python scripts/dev.py test <profile>`，非真实 provider
请求）：

| Profile | 命令 | 结果 |
| --- | --- | --- |
| Targeted | `pytest tests/test_repository_architecture.py tests/test_release_workflow.py` | **24 passed** |
| LLM contracts | `pytest tests/test_llm_contracts.py` | **6 passed** |
| Production | `dev.py test production` | **198 passed** |
| Experiments | `dev.py test experiments` | **240 passed** |
| Release | `dev.py test release` | **24 passed**（candidate 态下 release gate 报告 `NOT_EXECUTED_AWAITING_FINAL_QA`，符合预期） |
| Full | `dev.py test full` | **968 passed** (359.99s) |

- 与冻结基线一致：Targeted 24 / LLM 6 / Production 198 / Experiments 240 / Release 24 /
  Full 968。实现前基线为 **951 passed**。
- `dev.py test release` 的 `release_profile=PASS`，artifact identity
  `acd8f46479...`，artifact SHA-256 `2ac32989ad...`，formal scope = 17 configs / 48 queries /
  816 pairs。
- 所有测试均为离线，无真实 LLM API 调用、无真实 API key。

## 8. CPython 3.10 UI smoke

- 环境：**CPython 3.10.20 + gradio 6.27.0**（本机唯一可用且受支持的 CPython 3.10 环境）。
- 环境说明：实现阶段文档与任务 §15 记录的 implementation QA 环境为 CPython 3.10.22 /
  Gradio 6.27.0；本机不存在 3.10.22 小版本，故本 QA 以真实可用的 CPython 3.10.20 独立复现
  该 smoke，并**不声称**复现过 3.10.22。实现文档中的 3.10.22 措辞属于实现阶段记录，本 QA
  不据以作出结论。
- `create_ui()` 构建成功，返回类型 `Blocks`，`blocks_count = 106`。
- 兼容再导出实测：`CUSTOM_CSS is code_comments_agent.ui_styles.CUSTOM_CSS` → `True`；
  `processor.save_workspace is code_comments_agent.workspace.save_workspace` → `True`。
- 结果：**UI SMOKE: PASS**。
- 说明：Anaconda Python 3.13.5 主机在 IPython/rlcompleter → gradio import 期间终止，
  记录为 HOST LIMITATION，非业务代码回归；CPython 3.10 下构建正常。

## 9. Formal immutability

- Formal execution revision：`2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- Formal archive commit：`c3ee6ec1b7aa28c2539d2fe849d1f25268807677`
- Formal artifact canonical identity：`acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- Formal artifact SHA-256：`2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`
- `experiment-validate archive-v3.1.0`：**archive_v3.1.0 = PASS**（archive commit
  `c3ee6ec...`，identity `acd8f464...`）——即受保护的正式实验产物在 V3.1.3 变更后仍字节
  级不可变。
- `experiment-validate --purpose formal`：`experiment_preflight = formal:PASS`、
  `current_gate = CLOSED`、`phase_status = COMPLETED`。
- 结论：V3.1.3 的仓库/文档架构重构**未影响**正式实验 revision、archive、artifact identity
  与 SHA-256。

## 10. Documentation QA

- 关键文档行数（复核 revision `d8e7525`；release 定稿后 README/PROJECT_CONTEXT 会有小幅度
  行数变化）：`PROJECT_CONTEXT.md`=154、`README.md`=725、`docs/README.md`=24、
  `docs/release/README.md`=124、`docs/development/README.md`=22、`docs/qa/README.md`=16、
  architecture map=100、Thesis MD=114、Thesis TXT=130、Development Report=116、
  Release Notes=67、`PROJECT_CONTEXT_History_Through_V3_1_2.md`=1822、Scope=202。
- 当前 Source of Truth 分层正确：Machine = Git objects + `release_state.json`；Human =
  README / PROJECT_CONTEXT（current section）/ `docs/release/README.md`；历史快照
  （`docs/development/PROJECT_CONTEXT_History_Through_V3_1_2.md`、既往 QA 报告、
  Scope Freeze、V3.1.0–V3.1.2 版本化文档）不得被当作当前权威。
- 双格式 Thesis Materials 合规：TXT 为独立文本（无 Markdown 标题/围栏代码块/链接/HTML
  注释/管道表格），并以「素材来源与身份 / MATERIAL SOURCES AND IDENTITY」结尾，含 repo-relative
  路径与基线 commit。MD 版本结构完整。
- 候选态在 QA 开始时被正确标记：README / PROJECT_CONTEXT / `docs/release/README.md`
  均标注 `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`、Final QA evidence = NOT YET
  EXECUTED、tag/push = NO/NO。此为**正确的候选态基线**，本 QA 通过后随 release 定稿一并
  更新为 V3.1.3 RELEASED。
- 文档一致性：README Version History、PROJECT_CONTEXT、docs 索引、Release Notes 与
  `release_state.json` 相互一致；历史快照（含 V3.1.0–V3.1.2、Scope Freeze）未被改写。

## 11. Blocking findings

**无（0）。** 所有 blocking gate 均通过：

- scope 与冻结六项一致，无 scope creep，无禁止模块/依赖。
- release schema v2 正确、无自引用 `final_head`、fail-closed 行为正确。
- legacy v1 仍可读，旧 tag/commit/记录未被改写。
- architecture 抽取向后兼容，identity-equal 再导出成立。
- 全部 required tests 以预期基线通过（Targeted 24 / LLM 6 / Production 198 /
  Experiments 240 / Release 24 / Full 968）。
- CPython 3.10 UI smoke PASS。
- Formal revision / archive / identity / SHA-256 字节级不变。
- 文档 Source of Truth 分层与候选态标记正确。

## 12. Non-blocking findings

1. V3.1.2 在上一轮仅完成本地 finalize，远端 publication 记录为 Pending（历史遗留），
   不影响 V3.1.3 本次发布判断。
2. Anaconda Python 3.13.5 主机的 gradio import 终止为 HOST LIMITATION，非业务回归；
   已在 CPython 3.10 环境证伪。
3. 候选态措辞（README / PROJECT_CONTEXT / `docs/release/README.md` / Release Notes /
   Development Report / Thesis Materials 中的 `IMPLEMENTATION COMPLETE / AWAITING FINAL QA`
   等）需在本 QA 通过后随 release 定稿更新为 **V3.1.3 RELEASED**；历史快照不改写。

以上均为非阻塞，不阻碍发布。

## 13. Release verdict

所有 blocking gate 已真实通过，未发现阻塞性缺陷，非阻塞项不构成阻碍。

**FINAL RELEASE QA: PASS**

本 verdict 授权在独立 QA 完成后执行：release 措辞定稿为 V3.1.3 RELEASED → C1
`release(v3.1.3): finalize v3.1.3`（含本证据）→ annotated tag `v3.1.3` → C1 → C2
`release(v3.1.3): record final release identity` → main sync → 双远端 push → 远端校验。
