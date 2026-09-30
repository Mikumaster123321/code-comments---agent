# V3.1.1 Development Report

<!-- release-state: V3.1.1 RELEASE_CANDIDATE -->

## 1. Summary

- **Version:** 3.1.1
- **Theme:** Workflow & Developer Experience Optimization
- **Status:** IMPLEMENTED / RELEASE CANDIDATE
- **Branch:** `v3.1.0-dev`
- **Released baseline:** V3.1.0 commit
  `8813e4c2fb0dc07f38c2013d520441bf399dcbc4`, tag `v3.1.0`
- **Scope freeze:** `eaf74c1` (`docs(v3.1.1): freeze workflow and dx scope`)
- **Implementation:** `e1de983` (`feat(v3.1.1): add developer workflow tooling`)
- **V3.2:** NOT STARTED

V3.1.1 实现六项已冻结 DX 工作，不修改 retrieval、ranking、benchmark protocol 或
V3.1.0 Formal 结果。

## 2. Audit findings

实现前审计确认：developer 命令分散；当前 host 的普通 pytest 在 plugin initialization
阶段异常，而 `-p no:debugging` 可完成 892 项基线；E5 full validator 顶层依赖 POSIX
`resource`；关键 CSV/model 验证脚本使用会被 `python -O` 移除的 `assert`；V3.1.0 已
发布但部分 tracked 文档仍记录为 release candidate；测试 profile 缺少单一稳定入口。

## 3. Frozen scope and implementation

| Item | Implementation | Status |
| --- | --- | --- |
| V311-DX-01 | `scripts/dev.py` command hub、cwd-independent root、轻量 project smoke | COMPLETE |
| V311-DX-02 | core/optional/historical environment doctor、pytest subprocess probe、secret redaction | COMPLETE |
| V311-DX-03 | offline E5 snapshot preflight、显式 1+1 smoke、portable resource metrics | COMPLETE |
| V311-DX-04 | llm/production/experiments/full/release profiles 与 passthrough | COMPLETE |
| V311-DX-05 | V3.1.0 archive validator、authority preflight、CSV/assert hardening | COMPLETE |
| V311-DX-06 | machine-readable lifecycle metadata 与 read-only release consistency gate | COMPLETE |

## 4. Design decisions

1. 使用 stdlib `argparse` 与参数数组，不引入 task-runner dependency，也不使用
   `shell=True`。
2. 测试 profile 映射只在 `scripts/dev.py` 定义；CI 调用 `test full`，不复制列表。
3. doctor 只报告 credential-like 环境变量是否存在，绝不输出值。
4. E5 检查 fail closed，限定冻结 repository/revision/dimension/dependencies，且无任何
   download path。
5. archive validation 复用现有 authority、typed record、canonical serialization 与 CSV
   checker；command hub 不复制 BenchmarkRunner failure schema。
6. `release_state.json` 仅保存版本、lifecycle、baseline、tag/commit、文档 sentinel 与
   必需文档路径；避免依赖易漂移的整段 prose regex。
7. 受保护目录只允许通过 `git status --porcelain` 识别状态；工具不读取、列举、搜索或
   修改其内容。

## 5. Changed files

Implementation commit：

- `scripts/dev.py`
- `scripts/export_formal_thesis_tables.py`
- `scripts/validate_phase32_real_model.py`
- `tests/test_developer_workflow.py`
- `tests/test_release_workflow.py`
- `docs/release/release_state.json`
- `code_maintenance/__init__.py`
- `.github/workflows/pytest.yml`

Documentation commit 更新 README、PROJECT_CONTEXT、release index、V3.1.0 historical
release status，并新增本报告、V3.1.1 thesis materials 与 release notes。

## 6. Backward compatibility

- `python main.py`、`python -m pytest`、targeted pytest 与原独立 scripts 保持有效。
- 未改变 `processor`、UI、provider、retrieval production APIs、artifact schemas 或
  BenchmarkRunner semantics。
- Core requirements 不新增 dependency；E5 仍是隔离的 optional environment。
- CI 只把完整测试的调用入口替换为统一 profile，没有扩大 Python matrix。

## 7. Tests

| Validation | Result |
| --- | ---: |
| Initial legacy baseline with host workaround | 892 passed |
| New workflow/release tests | 30 passed |
| Production profile | 198 passed |
| Experiments profile | 240 passed |
| Full profile | 922 passed |
| Legacy full pytest with host workaround | 922 passed |
| Formal CSV check under normal Python | PASS |
| Formal/archive validation under `python -O` | PASS |
| Corrupt checksum/identity/CSV/model metadata under `python -O` | Rejected |

普通 pytest 在当前 Anaconda Python 3.13.5 host 仍于 plugin initialization 返回 signal
11；这是被 doctor 动态观察到的 host condition。新旧全量结果均使用明确的
`-p no:debugging` 环境 workaround，测试语义与收集范围未改变。

## 8. Formal-result immutability

Post-check 继续得到：

- execution revision：`2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- archive commit：`c3ee6ec1b7aa28c2539d2fe849d1f25268807677`
- artifact identity：`acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- file SHA-256：`2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`
- scope：17 configs、48 English Test queries、816 query-config pairs

没有重跑 Formal，没有修改 protected Formal paths，也没有重新计算 ranking。

## 9. Known limitations

- 当前 host 的 pytest plugin crash 仍是环境问题，本版本提供检测与安全恢复提示，不修改
  第三方环境。
- 当前 core 环境未安装冻结 optional E5 dependencies/cache，因此真实 `--smoke` 未执行；
  fake runtimes 覆盖了 preflight failure boundaries，历史 real-model evidence 保持不变。
- 默认 release gate 不验证 remote；`--remote` 需要网络可用。
- DeepSeek Final Release QA、V3.1.1 tag 与 push 不属于本轮。

## 10. Release readiness

实现与文档已进入 RELEASE_CANDIDATE。Critical 0；validity/release-blocking Medium 0。
下一步是独立 DeepSeek Final Release QA。V3.1.x maintenance continues；V3.2 未开始。
