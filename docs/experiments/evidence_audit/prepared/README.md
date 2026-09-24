# PREPARED / NOT EXECUTED — Phase 6.2 Java Evidence Audit 输入包

这里保存 [Addendum D](../../Experiment_Protocol_Addendum_D_V3_1_0.md) §4–6 预注册的 **12 条 English-test Java Query** 的逐条 TraeWork 输入及空白留证记录。它们恰好是 English test 的全部 12 条 Java Query；这是固定字典序产生的 Java 分层 evidence audit，**不是** 48 条 English test 的代表性样本、全量 LLM silver 标注或人类盲审。Python 与 Chinese coverage 均不在本包中。

本目录状态为 **PREPARED / NOT EXECUTED**。当前没有模型输出、审计意见、调用时间或 reference approval。用户提供的 Addendum D 独立合同 QA 回复报告为 **PASS WITH NOTES**；其原始探针和完整回复尚未在本仓库归档，Git 文档收口待另行确认。本目录的生成与机械核验不替代那项独立 QA，也不关闭 Phase 6.2 Gate。

## 文件与冻结身份

- `inputs/<query_id>.txt`：每条可单独复制的完整输入，共 12 份；每份首尾标明状态并有独立终止哨兵。
- `records/<query_id>.json`：每条一份 **NOT_EXECUTED** 空白执行记录；既有 evidence 身份只用于后续对应，所有模型结论与平台观察栏均未填。
- `manifest.json`：12 份输入和空白记录的 SHA-256、输入 UTF-8 字节数、Unicode code-point 数、evidence 数、被引源码文件清单与逐文件原始 hash。
- `generate_inputs.py`：只读冻结 Git blob 的确定性生成器；`verify_prepared.py`：从冻结 Git 身份独立读取并核对输入、Java adapter 身份/span、完整源码和空白记录。两者都不调用模型或检索器。

输入固定在入场 Git commit `1ed215e6a4c4505898207111bbdee720772ca461` 的 Query、v1 drafted GT、manifest、identity、Addendum D 和 Java fixture blob。Java fixture 的 `source_revision=fixture-v1`，源文件原始 SHA-256 与 manifest 逐项一致；生成器不从当前工作树读取 fixture 内容。冻结 Query Set hash 为 `5393d520d4935f55a4fd5e2f33d1ae051fc1a0914c2f58b3093fb574d56c54ba`，v1 drafted truth hash 为 `d31161954d6090b7ecfa6fd5e5c66ce1a21975c2b7e680c25c2fc0c66c6bcc87`。输入含既有 Grade/rationale，所以是**已知证据 audit**，不是遮蔽重判。

从仓库根目录机械核验（不会发送模型请求）：

```bash
python -B docs/experiments/evidence_audit/prepared/verify_prepared.py
```

如需在空目录重建并比对，指定一个新的隔离目录；生成器拒绝覆盖已有材料：

```bash
python -B docs/experiments/evidence_audit/prepared/generate_inputs.py --destination /private/tmp/phase62-java-audit-rebuild
python -B docs/experiments/evidence_audit/prepared/verify_prepared.py --directory /private/tmp/phase62-java-audit-rebuild
```

重建目录仅用于核验；**本 Git 跟踪目录才是准备材料的持久副本**。生成后比较两份 `manifest.json` 的字节及各文件 hash。不要把可能清理的 `/private/tmp` 当作唯一保存位置。

## TraeWork 逐条操作（未来执行，本轮未执行）

1. 先运行上述核验，核对 `manifest.json` 中目标文件 hash、字节数和终止哨兵。按 manifest 顺序逐条处理；每条打开**全新的独立会话**，选择界面显示为 `DeepSeek-V4.1-Flash` 的模型。不要复用曾看过 GT 的旧 QA 会话，也不要携带上一条 Query 的结论。
2. 仅复制对应 `inputs/<query_id>.txt` 的**全部**文字，从 `PREPARED / NOT EXECUTED` 首行至本条 `END_PHASE62_JAVA_EVIDENCE_AUDIT_INPUT_...` 末行。不要添加其他 Query、GT、检索排名/得分、仓库上下文或链接；不要开启可自行读取本仓库的工具。如界面自动注入无法核实的上下文，停止该条并记为 `CANNOT_ASSESS`。
3. 粘贴后确认首尾、所有 `E01...` 项和每个 `[[SOURCE_BEGIN...]]` 至 `[[SOURCE_END...]]` 的**完整文件**均可见。实际粘贴文本另存原文并计算 SHA-256；不等于 manifest hash 时先停下核查。不能为适应界面长度而删去证据或源码。字符数不证明 TraeWork 的 token 容量或无截断。
4. 发送时记录真实 UTC 开始/结束时间、界面显示模型名及可见版本、会话标识（若有）。分别保存**思考区可见原文**、**最终答案可见原文**及完整界面回复；各自计算 SHA-256。若思考区不可见、精确 revision、token usage、`finish_reason` 或完整原始响应不可导出，在执行记录的对应字段写 `unavailable`，保留可见范围说明，不用模型自述代替平台证据。不要保存凭据、cookie 或私人账号信息。
5. 核对回答的 `query_id`、每个 evidence ID 恰好一次、允许状态、逐项理由、总体状态、范围声明及本条 `RESPONSE_END_...`。逐证据结构化转录另算 SHA-256，与原始回复分开留存。若输入/回复截断、无法完整复制、JSON 损坏、遗漏项、混淆 Query 或缺结束标记，原样保存失败证据并标 `CANNOT_ASSESS`；不得默认为 `SUPPORTS`。模型意见不能直接写回 GT。

执行时应把本目录的空白 `records/<query_id>.json` **复制**到后续独立、版本化的执行记录位置再填写；保留本准备包、manifest 和 hash 不变。对 `QUESTIONS` / `CANNOT_ASSESS` 按 Addendum D 做独立冻结源码核查；不能用未来检索结果决定修正。TraeWork 精确模型 revision、token 限额与截断状态尚未验证，实际界面一旦不能完整承载输入或输出，停止对应审计。

v1 GT 仍 **DRAFTED**；新 reference approval 未完成；Phase 6.2 Gate **OPEN**；Phase 6.3 **BLOCKED**；Formal RQ1–RQ4 **NOT STARTED**。
