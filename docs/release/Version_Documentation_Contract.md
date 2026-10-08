# Permanent Version Documentation Contract

## 1. Purpose and scope

本合同适用于本仓库的 **every formal release**，不区分 major、minor 或 patch。它将版本
文档、Release QA、annotated tag 与双远端发布组成一个不可分割的发布门禁。任何后续版本
都必须在 tag 和 push 之前满足本合同；聊天记录不能替代 Git-tracked release evidence。

V3.1.0 与 V3.1.1 已经发布，本文件是 post-release documentation closure，不移动、删除、
覆盖或重建其 tag，也不追溯改写其 Formal 结果或发布身份。

## 2. Required release package

每个正式版本在 tag / push 前必须具备并完成审查：

1. README update，准确记录当前版本、状态、能力边界和后续版本状态。
2. README Version History entry，包含版本、状态、主要变化与测试基线。
3. `Thesis_Materials_<VERSION>_*.md`。
4. `Thesis_Materials_<VERSION>_*.txt`，UTF-8 plain text。
5. Development Report。
6. Release Notes。
7. `PROJECT_CONTEXT.md` update。
8. Documentation / Release index update。
9. 与变更风险相称的 Tests、documentation consistency QA 和 Final Release QA。
10. Reviewed release commit。
11. 指向 release commit 的 annotated tag。
12. GitHub branch push。
13. GitHub tag push。
14. Gitee branch push。
15. Gitee tag push。
16. GitHub 与 Gitee 的 branch / annotated-tag target remote verification。

文档入口应简洁，不要求 README 复制整个文档目录；release index 负责更完整的导航。

## 3. Hard release gates

以下任一情况均为 **RELEASE BLOCKER**：

- README 未更新或 Version History 缺少当前正式版本。
- Thesis Materials 缺少 Markdown 或 UTF-8 plain-text 任一格式。
- Development Report 缺失或仍记录与当前发布事实冲突的候选状态。
- Release Notes 缺失。
- `PROJECT_CONTEXT.md` 或文档索引未更新。
- 文档事实、测试数字、版本身份、Formal identity 或链接不一致。
- Final Release QA 未通过。
- release commit 或 annotated tag 尚未形成。

要求的任一正式 remote 未完成 branch / tag push 或未完成 target verification 时，状态必须
标记为 **REMOTE PUBLICATION INCOMPLETE**，不得标记为 `RELEASED` 或
`FULLY RELEASED`。

不得在 README、双格式 Thesis Materials、Development Report 或 Release Notes 缺失时
提前创建 tag。发布后才发现缺失文档只能作为显式 post-release closure 记录，不能被当作
正常发布顺序，也不能借此移动既有 tag。

## 4. Thesis Materials dual-format rule

每个版本必须同时提供：

- Markdown：repository-friendly structured reference，可包含链接、Markdown 表格和代码块。
- TXT：面向论文写作、Word、学校系统和 external model 的 UTF-8 plain-text material。

两种格式的事实、版本身份、测试数字、实验数字与 claim boundary 必须一致。TXT 不得只是
机械删除 Markdown 标记的 lossless-looking export；它必须可独立阅读、有清晰章节层次，
且不得包含 Markdown 标题、fenced code block、Markdown link、HTML comment 或 pipe table。

TXT 末尾必须包含“素材来源与身份”，使用 repo-relative path 列出 README、Development
Report、对应 Markdown Thesis Materials、Release Notes 及版本所需的权威实验或 scope
来源，并记录 release commit / tag。不得写入本机绝对路径、Credential 或 secret。

## 5. Mandatory release sequence

正式流程按以下顺序执行：

Implementation complete

→ Tests

→ README

→ Thesis Materials MD

→ Thesis Materials TXT

→ Development Report

→ Release Notes

→ PROJECT_CONTEXT / documentation indexes

→ Documentation consistency QA

→ Final Release QA

→ Release commit

→ Annotated tag

→ GitHub branch push

→ GitHub tag push

→ Gitee branch push

→ Gitee tag push

→ Remote branch / tag target verification

→ RELEASED

任何失败步骤都必须停止状态推进，保留可审计的失败原因与安全恢复动作。未经单独授权，
只读 release tooling 不得执行 stage、commit、tag、push、fetch、force update 或历史重写。

## 6. Release identity contract

`release_commit` 可以不同于 `final_head`。允许在 release commit 与 annotated tag 形成后，
以正常后继 commit 记录最终发布身份或进行明确的 post-release documentation closure，前提是：

- `release_commit` 是 `final_head` 的 Git ancestor；
- annotated tag 始终指向已审查的 `release_commit`；
- 后继 commit 不追溯改写 release commit 或冻结实验历史；
- 文档准确区分 release commit、tag target 与后续 final/documentation HEAD。

禁止要求 `final_head == release_commit` 作为通用发布合同。禁止 force-push、rebase、amend、
删除、覆盖、移动或重新创建已经发布的 tag。

## 7. Documentation consistency QA

tag 前至少检查：

1. 所有 required paths 已跟踪且链接目标存在。
2. TXT 可按 UTF-8 解码，且没有 Markdown-only 语法污染。
3. MD / TXT 的事实、版本身份、测试结果和限制一致。
4. Formal 数字来自冻结 artifact / deterministic export，而不是手工猜测或 Prompt。
5. Release commit、tag target、baseline 和 final HEAD 的关系符合身份合同。
6. README、Version History、Development Report、Release Notes、PROJECT_CONTEXT 和索引状态一致。
7. 文档不包含本机绝对路径、Credential、secret 或不应发布的数据。
8. protected user paths 与冻结 Formal paths 未被意外读取、修改或暂存。
9. executable code 变更触发相应完整测试；纯文档变更执行 link、release 与 archive checks。

## 8. V3.1 post-release closure record

- V3.1.0：`RELEASED`；release commit
  `8813e4c2fb0dc07f38c2013d520441bf399dcbc4`；annotated tag `v3.1.0`。
- V3.1.1：`FULLY RELEASED`；release commit C1
  `683479da2fd3b72c17cba3f03101bc23e275f40b`；annotated tag `v3.1.1` 指向 C1；
  final release-record HEAD C2 为 `0238cc0bd5254ac782aa3981cdc755d5a59c498e`。
- V3.1.0 与 V3.1.1 的 Markdown / TXT Thesis Materials、Development Report、Release Notes、
  README 入口和 release index 在本次 closure 中补齐或校正。
- V3.1.0 Formal artifact identity 与 file SHA-256 保持不变；本次 closure 不重新执行 Formal
  benchmark，也不改变 retrieval、ranking、Query、Ground Truth 或 Grade。
- V3.1.2：`RELEASE_CANDIDATE`；implementation complete，awaiting independent Final QA；
  tag / push 均未执行。
- V3.2：`NOT STARTED`。
