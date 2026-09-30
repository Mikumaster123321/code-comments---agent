# V3.1.0 Phase 6.3 前置：Credential Scanner False-Positive Fix

## 范围与结论

本轮仅修复 benchmark artifact serialization 的凭据扫描误判，未继续正式 Dry Run、未创建 DryRunReceiptV2、未执行 Formal RQ1–RQ4。修复前 HEAD 为 `9568610cac2616ddd0599ba05bc3b88f366bd296`。

根因：`experiments/serialization.py` 原扫描器对所有 dict key 使用相同的 credential substring 规则。`RawQueryResult.metric_inputs` 的 key 实际是候选身份数据；当 symbol identity 内的 `qualified_name` 为 `RuntimeCredential` 时，被误判成 credential 字段。普通值已有独立 secret-pattern 扫描。

修复后，结构化字段名仍按 credential 语义拒绝；仅 `metric_inputs` 中带 `file:` / `chunk:` / `symbol:` 候选身份前缀且值为合法 relevance grade `0/1/2` 的 key 被视作候选身份数据，依旧扫描真实 secret pattern。`symbol:` 身份中的 JSON 被解析并递归扫描，阻止嵌入 credential 字段。普通数据值保留原有 provider key、Bearer、AWS key、PEM 与 marker 检测，并增加明显 secret assignment 检测。`RuntimeCredential`、`CredentialStore`、`TokenParser`、`ApiKeyValidator`、`SecretManagerFactory`、`access_token_parser`、`password_policy` 等合法源码标识符可序列化。

## 上次局部运行产物处置

未提交目录 `docs/experiments/runs/phase63-ed-rq1-file-9568610cac26/` 来自旧 execution revision `9568610cac2616ddd0599ba05bc3b88f366bd296`，corpus revision 为 `12391233daa2149ead4f451e920b2e0d8a1a6beb`。manifest 标为 `dry_run / english_dev`；该单项 RQ1-FILE 的 12 条 raw result 均为 success，但完整 17 项矩阵未完成，所以不能视作成功的 Phase 6.3 Dry Run，也不能续跑或签发 PASS receipt。生命周期合同未要求归档此类未提交的局部成功单项；记录以下身份与原始字节 SHA-256 后移除该目录，以便未来从修复后的新 HEAD 完整重跑 17/17：

| 文件 | SHA-256 |
| --- | --- |
| `aggregate_results.json` | `4890caf98820248edfcd602afbcdabb0871fb969e3819488e9083a95a9b25d78` |
| `checksums.sha256` | `70487ffc6cf349418d2bed33e52a2573fd6904164f7008ddf5e6a293f3e44f74` |
| `raw_results.jsonl` | `60948df66905a87929fcaa205b3d5f1f1b419c68f0d123f644fd5d65f1f4c2a7` |
| `run_manifest.json` | `6f50a9aa7b1eab191ca0f559201dd7f15f2714aea11feedb04a55dbdaccab70b` |

完整 English Dev Dry Run：`0/12`；矩阵：`0/17`；English Test：`0`；Chinese：`0`；DryRunReceiptV2：`NOT CREATED`；Formal RQ1–RQ4：`NOT STARTED`。上述 12 条历史 raw result 只记录为失败尝试的局部证据，不计入正式完成数。

## 验证

- 修复前：`metric_inputs` 中包含 `RuntimeCredential` 的 symbol identity 触发 `SerializationError: credential-bearing field is forbidden`；普通 `symbol_id` 值不触发。修复后，同一结构的最小序列化烟测通过。
- 原始全量基线在局部运行目录存在时为 `848 passed, 2 failed`；两项失败都断言 `docs/experiments/runs/` 不存在。清理该目录后，无需修改或删除这两项测试。
- 序列化安全、benchmark runner、生产执行及 reference lifecycle 定向测试：`206 passed`。
- 离线 LLM contract smoke：`6 passed`，未发送真实 Provider 请求。
- 最终全量回归：`python -m pytest -p no:debugging`，`877 passed`（原 850 项 + 新增 27 项）。默认 pytest 调试插件在本机 Python 3.13 环境触发段错误，故按任务指定禁用该插件。
