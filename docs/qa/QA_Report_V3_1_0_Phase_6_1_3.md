# V3.1.0 Phase 6.1.3 — Annotation Lifecycle Independent Directed Retest QA Closure

## 结论与证据边界

**Directed Retest: PASS WITH LOW NOTES。** Phase 6.1.3 的 M-1 为
**CLOSED / RESOLVED**；最终 Critical / Medium 为 **0 / 0**，Phase 6.1.4
**NOT REQUIRED**。独立复测针对提交
`675bf0d5c78bba10577d639dc5e39fcd2df0a877`，仓库外独立探针结果为
**69 passed / 0 failed**。该探针数与仓库内 pytest 结果分开记录。

本报告将已完成的 DeepSeek 独立复测结论落盘；本次文档收口未重新执行或扩大独立
QA。仓库内全量回归在收口时复跑，结果为 **628 passed**。

## 缺陷与实现

Phase 6.1.2 原 blocker 是 `GroundTruthRecord` 强制 `reviewed_at` 为非空
timestamp，无法表达冻结规范要求的 `drafted + reviewed_at=null`。该 blocker
已 **CLOSED / RESOLVED**。

Phase 6.1.3 的唯一 Medium（M-1）是 `annotation_status=reviewed` 仍可携带
非空 `adjudicator_id`，与 Addendum A 中“review completed without adjudication”
的语义冲突。提交 `675bf0d5c78bba10577d639dc5e39fcd2df0a877` 在
`GroundTruthRecord` 生命周期校验中拒绝此组合；未将 `wang` 身份硬编码进通用
schema，也未改变 48 小时、序列化或 hash 契约。

## 独立复测覆盖

| 状态与边界 | 预期及复测结果 |
| --- | --- |
| `drafted + reviewed_at=null` | ACCEPT |
| `drafted + adjudicator_id` 非空 | REJECT |
| `reviewed + reviewed_at≥48h + adjudicator_id=null` | ACCEPT |
| `reviewed + adjudicator_id` 任意非空值 | REJECT |
| `adjudicated + reviewed_at≥48h + adjudicator_id` 非空 | ACCEPT |
| `adjudicated + adjudicator_id=null` | REJECT |
| `frozen + reviewed_at≥48h + adjudicator_id=null` | ACCEPT |
| `frozen + reviewed_at≥48h + adjudicator_id` 非空 | ACCEPT |
| review 延迟 `47h59m59s` | REJECT |
| review 延迟恰好 `48h` | ACCEPT |
| review 延迟 `48h+1s` | ACCEPT |

序列化与 hash 复测 **PASS / NO REGRESSION**。通用 schema 不硬编码 `wang`。
独立探针共 **69 passed / 0 failed**；未发现新 Critical 或 Medium。

## 回归与残余 Low

| 范围 | 结果 |
| --- | ---: |
| Phase 6.1 / lifecycle | 52 passed |
| Phase 5 | 48 passed |
| Phase 4 | 37 passed |
| Phase 3.2 | 10 passed |
| Phase 3.1 | 12 passed |
| Phase 2 | 14 passed |
| Phase 1 | 41 passed |
| 离线 LLM smoke | 6 passed |
| 全量回归 | 628 passed |

全量回归使用 `python -m pytest -p no:debugging`（已批准的宿主机 workaround）；
无网络调用。

残余 **3 项非阻塞 Low**：L1，通用 schema 不强制 reviewer/adjudicator 为
`wang`，此身份约束属于 Phase 6.2 dataset contract；L2，`_timestamp` 的
异常 `__cause__` 可能保留格式错误的 timestamp 原文，不影响 authoritative
annotation path；以及既有 Phase 6.1 UUID v7 shape / `RunMetadata.run_id`
仅作非空校验的防御性说明。这些 Low 不阻塞 Phase 6.2A。

## 门禁后果

Phase 6.1.2 与 Phase 6.1.3 均 **COMPLETED**；M-1 **CLOSED / RESOLVED**，
Phase 6.2A blocker **LIFTED**。Phase 6.2A **ALLOWED BUT NOT STARTED**。
Dataset、Query Set、Ground Truth 均 **NOT CREATED**，Phase 6.2 Gate **OPEN**，
Phase 6.3、Formal RQ1–RQ4 与 V3.2 均 **NOT STARTED**。
