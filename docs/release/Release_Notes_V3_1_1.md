# V3.1.1 Release Notes

<!-- release-state: V3.1.1 RELEASE_CANDIDATE -->

**Status:** Release Candidate / Ready for DeepSeek Final Release QA

**Version:** `3.1.1`

**Theme:** Workflow & Developer Experience Optimization

V3.1.1 是已发布 V3.1.0 之上的维护候选版本，集中改善开发命令、环境诊断、测试入口、
冻结实验追溯和发布一致性。它不改变 Project Intelligence retrieval semantics 或 ranking。

## Highlights

- 新增纯 Python `scripts/dev.py` developer command hub
- 从任意 cwd 稳定定位 repository root
- Core / Optional E5 / Historical Formal 环境分层诊断
- offline-first、no-download 的冻结 E5 snapshot preflight
- 五个稳定测试 profile 与 pytest 参数透传
- 只读 V3.1.0 Formal archive 与 experiment authority validation
- PREPARING / RELEASE_CANDIDATE / RELEASED 发布状态模型
- Formal CSV 与 real-model validator 的 `python -O` correctness hardening
- 不支持 POSIX `resource` 时继续验证并标记 RSS metrics unavailable

## Developer commands

```bash
python scripts/dev.py --help
python scripts/dev.py doctor
python scripts/dev.py project-smoke
python scripts/dev.py test llm
python scripts/dev.py test production
python scripts/dev.py test experiments
python scripts/dev.py test full
python scripts/dev.py test release
python scripts/dev.py model-check [--cache-dir PATH | --model-path PATH] [--smoke]
python scripts/dev.py experiment-validate archive-v3.1.0
python scripts/dev.py experiment-validate --purpose dry-run
python scripts/dev.py experiment-validate --purpose formal
python scripts/dev.py release-check --version 3.1.1 [--remote]
```

## Diagnostics

失败输出统一给出 What failed、Expected、Actual 和 Safe recovery。doctor 不输出 secret
值，只显示环境变量 set/unset。pytest workaround 由子进程 probe 的实际结果决定，不固化
host、Python distribution 或 debugger 原因。

## Test profiles

- `llm`：offline LLM contract smoke
- `production`：V3.1.0 production profile，198 passed
- `experiments`：V3.1.0 experiment profile，240 passed
- `full`：全部测试，V3.1.1 baseline 922 passed
- `release`：full profile 后继续执行 archive 与 release consistency gate

直接 `python -m pytest` 继续受支持。892 是 V3.1.0 发布基线，不是 V3.1.1 硬编码阈值。

## Experiment/archive validation

V3.1.0 archive check 验证 Formal execution/archive ancestry、artifact file SHA-256、
canonical identity、17 configs、48 English Test queries、816 query-config pairs、run/evidence
checksums、typed DryRun receipt、protected Formal paths 与 deterministic CSV。它不写
artifact/receipt，不运行 benchmark，也不重新计算 retrieval ranking。

## Release preflight

`release_state.json` 是最小 lifecycle metadata。默认 release check 完全离线；只有
`--remote` 才对已配置 remotes 执行只读 `git ls-remote`。该命令从不 stage、commit、tag、
push、fetch 或修改版本/文档。

## Validator hardening

scope 内关键 correctness checks 已从 `assert` 改为显式异常和 non-zero exit。优化模式测试
确认错误 artifact checksum、identity、CSV 与 model metadata 仍被拒绝。

## Compatibility

- 无 breaking migration。
- 无新增 core dependency。
- 原应用、pytest 与独立验证入口继续有效。
- 未修改 UI、processor、provider、retrieval APIs、frozen schema 或 experiment protocol。

## Formal-result boundary

V3.1.0 Formal results 完全不变：

- execution revision `2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- archive commit `c3ee6ec1b7aa28c2539d2fe849d1f25268807677`
- artifact identity `acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- file SHA-256 `2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`

本版本不是新的 retrieval research result，不新增或修改任何 Formal claim。

## Known limitations

- E5 smoke 需要用户已存在的精确冻结 cache 和 optional dependency environment。
- `model-check` 不替代完整 Phase 3.2 validator 或性能评估。
- remote release state 默认不检查，需显式 `--remote` 和可用网络。
- 当前 host 的 pytest plugin initialization 异常仍需环境 workaround。

## Next maintenance version

V3.1.x maintenance continues。V3.2 **NOT STARTED**；本候选版不启动 Multi-Agent 工作。
