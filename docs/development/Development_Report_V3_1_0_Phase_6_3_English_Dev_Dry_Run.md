# V3.1.0 Phase 6.3 English Dev Dry Run 执行报告

## 范围与判定

**DRY RUN QA ONLY — NOT FORMAL RESULT。** 在 `v3.1.0-dev` 初始 HEAD `f0f4d2da169a071c71a6099c1d106fc3fec23299` 上，以冻结 English Dev 的 12 条 Query 和 17 项配置完整执行 **204/204** 个 query-config 组合。17 个 run 均为 `success`，无 `failed`、`invalid` 或 `degraded`。English Test 执行 **0**、Chinese 执行 **0**；Formal RQ1–RQ4 **NOT STARTED**。本报告不解释研究问题，也不将这些数值作为正式结果。

执行前全量基线为 `877 passed`。正式执行使用 CPython 3.12.14、torch 2.8.0、transformers 4.56.2、CPU float32，以及本机已存在的 `intfloat/multilingual-e5-base` 冻结 snapshot `d128750597153bb5987e10b1c3493a34e5a4502a`。模型通过 `local_files_only` 离线加载；运行进程设置 HF/Transformers 离线标志并通过 socket audit hook 阻断网络操作。固定 runtime 的动态库由本机现有路径解析；未修改模型、Provider、检索器、Runner、指标或冻结输入。

## 冻结身份与覆盖

| 项目 | 身份或数量 |
| --- | --- |
| corpus revision | `12391233daa2149ead4f451e920b2e0d8a1a6beb` |
| execution revision | `f0f4d2da169a071c71a6099c1d106fc3fec23299` |
| 17-config matrix identity | `ce5a58783a68f7e20c0635d264fc19d119212604cee1ed80b4a6b25d49863a25` |
| artifact-set identity | `08f753fe7e9cb24e29a38baa5057005203f09524d0d94a48c4fbd98c19c8715b` |
| DryRunReceiptV2 identity | `8383eb1c0e45ca68927cecc5170a18a0ae56cc62dcbf2e5b3ff53448073fff3e` |
| coverage | English Dev 12/12、configs 17/17、pairs 204/204、无重复或缺项 |
| leakage | English Test 0、Chinese 0 |

12 个准确 Query ID：`ed-bl-py-01`、`ed-bl-py-02`、`ed-cf-py-01`、`ed-cf-py-02`、`ed-dq-ja-02`、`ed-dq-py-01`、`ed-fl-py-01`、`ed-fl-py-02`、`ed-mt-py-01`、`ed-mt-py-02`、`ed-sl-ja-02`、`ed-sl-py-01`。每项配置各执行这 12 条，manifest、aggregate 和 raw 共同绑定 mode/split、Query、config、dataset、Reference、Approval、两种 revision 和指标身份。17 个 `run_manifest.json`、`aggregate_results.json`、`raw_results.jsonl` 及 run checksum 均从磁盘重载；artifact set、确定性/泄漏证据与 receipt 的 SHA-256 sidecar、canonical identity 和相互绑定均复核通过。

完成 204 个组合后，**全部 17 项配置、204 条结果**再次运行并比较 identity、ranked hits、scores、metric inputs、metrics、status、degraded 状态和 token diagnostics，观察到 **0** 项不一致。实际测量的 `latency_ns` 不属于确定性比较字段。每条原始结果的指标已按冻结 metric config 重算；aggregate 又按原始记录重算。`determinism_evidence.json` 和 `leakage_evidence.json` 绑定同一 artifact set、matrix 与全部 17 个 raw SHA-256。

Receipt 由 append-only lifecycle writer 创建并重载验证。它绑定的是上述 execution revision；包含它的 Commit A 是之后从 Git 历史派生的归档提交，不能代替 execution revision。此报告只记录机器复核与本次执行证据，不声称另有外部模型或人工独立 QA 已完成。

## Dry Run QA 指标

**DRY RUN QA ONLY — NOT FORMAL RESULT。** 以下为 12 条 English Dev 的每配置 aggregate 均值，不作 RQ 排名或结论解释。

| 冻结配置 | Recall@5 | MRR |
| --- | ---: | ---: |
| RQ1-FILE | 0.8750 | 0.5972 |
| RQ1-SYMBOL | 0.5625 | 0.4571 |
| RQ1-CHUNK | 0.7083 | 0.5486 |
| RQ2-BM25 | 0.5625 | 0.4571 |
| RQ2-E5 | 0.6875 | 0.7083 |
| RQ3-GRAPH-OFF | 0.6667 | 0.5361 |
| RQ3-GRAPH-ON | 0.7708 | 0.5425 |
| RQ3-CONTAINS-FORWARD | 0.6250 | 0.5347 |
| RQ3-CONTAINS-REVERSE | 0.7083 | 0.6319 |
| RQ3-IMPORTS-FORWARD | 0.6667 | 0.5361 |
| RQ3-IMPORTS-REVERSE | 0.6667 | 0.5361 |
| RQ4-LEXICAL | 0.5625 | 0.4571 |
| RQ4-EMBEDDING | 0.6875 | 0.7083 |
| RQ4-HYBRID-NO-GRAPH | 0.6667 | 0.5361 |
| RQ4-HYBRID-GRAPH | 0.7708 | 0.5425 |
| RRF-HYBRID-NO-GRAPH | 0.6875 | 0.6000 |
| RRF-HYBRID-GRAPH | 0.6875 | 0.5933 |

## 测试迁移与 Commit A 门槛

两个旧测试在 Phase 6.2 时要求 `docs/experiments/runs/` 不存在；完整 Dry Run 合法创建该 namespace 后，该阶段性断言失效。保留测试并迁移为共用的 fail-closed 校验：无 artifact set 时，runs/receipt 不得提前出现；有 artifact set 时，run 目录必须恰好匹配冻结 17 项，原始结果必须覆盖准确的 12×17 English Dev 组合且无额外、重复或跨 split 记录，config/revision/schema/hash 必须匹配。冻结 Query、GT、Grade、Reference 和历史 Phase 6.2 审查事实未修改。

- 两个直接相关测试文件：`147 passed`。
- production execution、reference lifecycle/eligibility/receipt、serialization/security 专项：`154 passed`。
- `python -m pytest -p no:debugging`：**877 passed**。

Commit A 仅归档正式 Dry Run artifacts、artifact set、receipt、证据、本报告、必要 `PROJECT_CONTEXT.md` 状态及这两处测试迁移；`current_gate.json` 不在 Commit A 中更新。Commit A SHA 以 Git 历史为准。下一步必须从 Commit A 新 HEAD 创建 `RepositoryAuthority` 并运行 `validate_formal_eligibility(purpose=FORMAL)`；只有 PASS 才能另行更新导航并提交 Commit B。Formal RQ1–RQ4 仍 **NOT STARTED**，未 push、未 tag。
