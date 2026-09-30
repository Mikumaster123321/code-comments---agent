# V3.1.0 Formal Execution Git Ancestry 合同澄清

- 版本：`v1`
- 范围：仅澄清 Phase 6.3 Dry Run receipt 与后续 FORMAL 执行的 Git revision 身份及祖先关系；不改变冻结 Query、Ground Truth、Grade、Reference、配置、指标、检索实现或 Dry Run artifacts。
- 本文件不记录 Formal RQ1–RQ4 结果。

## 三个独立身份

1. **Dry Run execution revision**：实际产生 204 个 English Dev Dry Run 结果的代码 HEAD。当前 receipt、artifact set、17 个 run manifest 和 aggregate 均绑定 `f0f4d2da169a071c71a6099c1d106fc3fec23299`。
2. **DryRunReceipt archive commit**：将 Dry Run artifacts、artifact set 和 `DryRunReceiptV2` 首次纳入当前 Git authority 的提交。当前为 `ae063161a98cc0d88aafd7fffea8e81cbc57f335`，由 `RepositoryAuthority` 从当前 HEAD 可达的提交历史及已提交原始字节派生，不写入 receipt。
3. **Formal execution revision**：实际执行 Formal benchmark 的 pre-run 代码 HEAD。每次 FORMAL 资格请求传入该提交；它可晚于 receipt 归档提交。原计划候选 `bd1f9d71658132718caaa1d79715b8289b5f1f19` 只代表当时的 HEAD，后续修复提交产生新的候选值。

## 祖先与交叉身份规则

FORMAL validator 必须在当前 HEAD 的已提交 authority 下验证以下 Git 关系（含相等）：

```text
Dry Run execution revision <= DryRunReceipt archive commit <= Formal execution revision <= current HEAD
```

`<=` 表示左侧是右侧的 Git 祖先或同一提交。允许在 receipt 归档 Commit A 的 HEAD 验证 FORMAL 资格，符合 Amendment 3 的提交顺序。不同分支、未来才归档的 receipt、当前 execution history 中不可达的 receipt 均须拒绝；时间戳不能代替 Git 祖先关系。`current_gate.formal_execution_eligible` 仅是导航状态，不能绕过这些检查。

Receipt、artifact set、17 个 Dry Run manifest 与 aggregate 的 `execution_revision` / `code_commit` 必须一致地指向 **Dry Run execution revision**。FORMAL 请求的 `code_commit` 与签发的 `ValidatedExecutionInputs.code_commit` 指向 **Formal execution revision**。两者不要求相等。FORMAL 请求仍须通过现有 `verify_execution_code`，且所有 receipt identity、原始字节 hash、12 个 English Dev ID、17 项配置、204 覆盖、determinism、零 English Test/Chinese 泄漏、corpus revision、Reference Approval 与 Phase 6.2/6.3 closure 校验保持不变。

本修订仅覆盖 Amendment 4 中将 FORMAL 请求的 `execution_revision` 要求为 receipt archive commit 的祖先，以及将 Dry Run run 的 execution revision 要求等于 FORMAL 请求提交的两处表述；其余 Amendment 3/4 合同继续有效。
