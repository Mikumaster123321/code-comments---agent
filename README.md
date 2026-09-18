# Code Comments Agent

**当前版本：V3.0.0（`3.0.0`）— Stable Release**

Code Comments Agent 正在演进为面向项目级代码理解与智能维护的 **LLM-assisted Software Maintenance Platform**。V3.0.0 的定位是 **Project-level Maintenance Core Foundation**：在保留 V2 用户能力的同时，提供稳定的项目扫描、关系图、快照、确定性分析和 BYOK Provider 基础。

V3.0.0 已正式发布，但不是完整的 Autonomous Multi-Agent IDE。

## Available Now

### 用户能力

- Python / Java 注释生成与注释翻译
- Markdown API 文档生成
- 代码变更 Diff
- 多文件与 ZIP 批量处理
- 基础代码质量、类型注解与风格分析
- Gradio Web UI（中文、English、日本語）
- DeepSeek、OpenAI、Azure、DashScope、Moonshot 和自定义 OpenAI-compatible Provider

### V3 项目级维护核心

- **Stable `SymbolId`**：为 Python / Java 符号提供确定、可复用的内部身份
- **Project Scanner**：确定性发现项目文件、语言、忽略规则和内容哈希
- **Project Graph**：构建项目、文件、符号和外部模块的包含及导入关系
- **Project Snapshot**：以不可变状态表示文件、符号和项目图，并支持快照比较
- **Deterministic Analysis Engine**：基于现有 Snapshot / Graph 执行结构、复杂度和依赖分析；不调用 LLM
- **BYOK Provider Foundation**：无凭据的模型配置、仅运行时凭据、只读 Registry 和任务级 Provider 隔离

当前 V3 Core 是底层能力。既有 Gradio 用户流程继续通过 legacy-compatible Processor 工作。

## Architecture

```text
Gradio UI
   |
Legacy-compatible Processor
   |
   +---- LLM Provider / BYOK
   |
   +---- V3 Core
          |
          +-- Domain / SymbolId
          +-- Project Scanner
          +-- Project Graph
          +-- Project Snapshot
          +-- Analysis Engine
```

`AnalysisEngine` 是确定性、只读且不调用 LLM 的服务。`code_maintenance/` 不依赖 Provider 或 Credential；Provider 层位于 V3 Core 外部。

## BYOK

**BYOK = Bring Your Own Key。** V3.0.0 的正式产品原则是：项目不内置开发者自己的第三方 API Key。用户自行选择 Provider、Model 和 Credential。

当前 Registry 支持：

- DeepSeek
- OpenAI
- Azure OpenAI
- DashScope
- Moonshot
- Custom OpenAI-compatible

安全边界：

- `ModelConfig` 只保存 Provider、Model 和 Base URL，不含 Credential。
- `RuntimeCredential` 只用于运行时 Provider 构造，不支持普通序列化。
- Workspace 持久化白名单不保存 Credential。
- Task 开始时会固定其 Provider / Client；之后切换 legacy 全局 Provider 只影响未来 Task，不改变已经开始的 Task。
- `.env` 是本地配置文件，已被 Git 忽略；Gradio 中输入的 API Key 只覆盖当前运行时设置。

V3.0.0 未实现 OS Keychain、Vault 或 VS Code SecretStorage。

## Installation

- Minimum Python: **3.10**
- Recommended Python: **3.10**

```bash
git clone https://gitee.com/GuowangKako/code-comments---agent.git
cd code-comments---agent
python -m venv .venv
```

激活虚拟环境：

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

某些 Anaconda Python 3.13 主机可能遇到 Gradio / IPython 兼容问题；这不是已确认的 Python 3.13 产品不兼容。遇到此问题时，请改用标准 CPython 和独立 `venv`。干净的 CPython 3.13.7 环境已通过安装、启动和测试验证。

## Configuration

复制环境变量示例，并用占位值替换为自己的配置：

```bash
cp .env.example .env
```

最小示例：

```env
PROVIDER=deepseek
MODEL=deepseek-chat
DEEPSEEK_API_KEY=your-api-key-here
```

`.env.example` 列出了各 Provider 的变量名以及 Azure / Custom 的 Base URL 配置。也可以在 Gradio 的运行时 Provider 设置中选择 Provider、Model、API Key 和允许自定义的 Base URL。项目当前没有账户系统、数据库或 Secure Credential Store。

## Quick Start

1. Clone 仓库。
2. 创建并激活 `.venv`。
3. 运行 `python -m pip install -r requirements.txt`。
4. 通过 `.env` 或 Gradio 运行时设置配置 Provider / API Key。
5. 启动：

```bash
python main.py
```

默认访问地址为 `http://127.0.0.1:7860`。

## Testing

当前 V3.0.0 稳定版基线：**129 passed**。

```bash
python -m pytest
```

`python -m pytest -p no:debugging` 仅用于 RC1.1 已记录的特定 Anaconda Python 3.13.5 主机问题，不是标准测试命令。测试不会调用真实 LLM Provider，也不需要真实 API Key。

## Directory Structure

```text
code-comments---agent/
├── main.py
├── ui.py
├── processor.py
├── config.py
├── llm_service.py
├── llm_provider.py
├── Py/
├── Java/
├── code_maintenance/
│   ├── domain.py
│   ├── adapters.py
│   ├── scanner.py
│   ├── graph.py
│   ├── snapshot.py
│   └── analysis.py
├── tests/
├── docs/
│   ├── development/
│   ├── qa/
│   └── release/
└── .github/workflows/
```

`Py/` 和 `Java/` 仍是 legacy-compatible Processor 与 V3 Adapter 使用的生产模块，并未被 `code_maintenance/` 替代。

## Roadmap / Planned

以下能力均为 **Planned**，不属于 V3.0.0 的已实现功能。

### V3.0.1 — Managed AI Access & Credits

**Status: Planned**

V3.0.0 默认支持 BYOK。V3.0.1 计划在保留 BYOK 的同时，为不希望自行配置第三方 API 的用户增加可选的 Platform-managed AI access：

- Credit account
- Credit ledger
- Admin credit grants
- Usage metering
- Pricing policy abstraction
- Recharge / payment interface reservation

平台 Provider / API Credential 将只存在于服务端，不下发到客户端，不写入插件、前端或普通用户配置：

```text
Client -> Platform Backend -> Auth / Credit Check -> Server-side Provider -> LLM
```

以上均未在 V3.0.0 实现。

### Later Planned Versions

- **V3.1 — Project Intelligence / RAG** — Planned
- **V3.2 — Controlled Multi-Agent Collaboration** — Planned
- **V3.3 — Data-driven Multi-Model Router** — Planned
- **V3.4 — VS Code Integration + Secure Credential UI** — Planned

## Version History

从 V3 开始，README 保留简洁的永久版本记录。正式的 Major / Minor 版本条目可列出主要 Phase、Capability、Main changes 和 Tests；Patch 版本只记录主要修复、小功能和 Tests。完整过程继续保存在 Development Reports、QA Reports 和 Release Notes 中。

V2 及更早版本按当时的更新日志逐版本完整保留，并标注发布日期与版本类型。**V2 的测试数字均为当时记录，不代表当前 V3 基线**；V2 开发期自测脚本已在 `7a232c0`（2026-09-08）移除，当前测试统一位于 `tests/`。

V2 沿用当时定义的版本号规则：大版本 `vX.Y.0` 只记录新增底层架构能力的重要更新；小更新 `vX.Y.1`、`vX.Y.2`… 不单独占据大版本位，归入最近一次大版本的小更新子节。当时的大版本序列为 v1.0.0 → v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v2.4.0。

### 版本总览

| 版本 | 发布日期 | 类型 | 主题 |
| --- | --- | --- | --- |
| V3.0.0 | 2026-09-11 → 2026-09-18 | 大版本 | Project-level Maintenance Core Foundation |
| V2.4.1 | 2026-08-12 | v2.4.0 小更新 #1 | macOS + 手机端响应式自适应 |
| V2.4.0 | 2026-08-11 | 大版本 | 多 Provider / 多模型切换 + 运行时 API Key 管理 |
| V2.3.8 | 2026-08-10 | v2.3.0 小更新 #8 | 代码风格检查（PEP8 / Google Java Style） |
| V2.3.7 | 2026-08-10 | v2.3.0 小更新 #7 | 保存 / 加载用户工作区（会话持久化） |
| V2.3.6 | 2026-08-10 | v2.3.0 小更新 #6 | 代码编辑器搜索替换 + 大纲折叠 |
| V2.3.5 | 2026-08-07 | v2.3.0 小更新 #5 | 输出 ZIP 命名策略可配置 + 源目录结构保留 |
| V2.3.4 | 2026-08-07 | v2.3.0 小更新 #4 | Java 有效性严格化 + 注释后语法二次校验 |
| V2.3.3 | 2026-08-07 | v2.3.0 小更新 #3 | API Key 预检（1-token 心跳）+ Token 用量 / 成本估算 |
| V2.3.2 | 2026-08-07 | v2.3.0 小更新 #2 | 函数 / 类导航大纲 Sidebar + API 文档 TOC 锚点 |
| V2.3.1 | 2026-08-07 | v2.3.0 小更新 #1 | 实时进度条 + 可取消任务 |
| V2.3.0 | 2026-08-07 | 大版本 | 代码差异对比（Diff）底层能力 |
| V2.2.2 | 2026-08-07 | v2.2.0 小更新 #2 | 注释风格模板选择（Python 3 种 + Java 2 种） |
| V2.2.1 | 2026-08-07 | v2.2.0 小更新 #1 | 批量文件 / 文件夹处理 |
| V2.2.0 | 2026-08-07 | 大版本 | 多语言 i18n 底层能力 |
| V2.1.1 | 2026-08-06 | v2.1.0 小更新 #1 | 前端界面重构 + 代码有效性验证 |
| V2.1.0 | 2026-08-06 | 大版本 | Java 语言支持 + 目录结构分语言 |
| V2.0.0 | 2026-08-05 | 大版本 | 架构重构 + 并发生成 + 代码质量体系 |
| V1.0.0 | 2026-08-05 | 初始版本 | Python 注释与 Markdown API 文档生成 |

### V3.0.0 — 2026-09-11 → 2026-09-18（大版本）

**Project-level Maintenance Core Foundation — Released / Stable Release**

主要 Phase：

| Phase | 日期 | 提交 |
| --- | --- | --- |
| Phase 0 — Engineering Baseline | 2026-09-11 | `9881b58` |
| Phase 1 — Domain Core | 2026-09-11 | `f79841c` |
| Phase 1.1 — Stable Symbol Identity | 2026-09-11 | `b9a4a2a` |
| Phase 2 — Processor Symbol Migration | 2026-09-14 | `f531c9a` |
| Phase 3.1 — Project Scanner | 2026-09-14 | `f72b072` |
| Phase 3.2 — Project Graph | 2026-09-17 | `5531e60` |
| Phase 3.2.1 — Graph Identity & Containment Hardening | 2026-09-17 | `dd76fab` |
| Phase 3.3 — Project Snapshot | 2026-09-17 | `45bbd6d` |
| Phase 3.3.1 — Snapshot Post-QA Hardening | 2026-09-17 | `e59149c` |
| Phase 4 — Project Analysis Engine | 2026-09-17 | `2e42d77` |
| Phase 4.0.1 — Analysis Engine Post-QA Hardening | 2026-09-17 | `bbd081e` |
| Phase 4.1 — Provider / BYOK Foundation | 2026-09-17 | `9f2d151` |
| Phase 4.1.1 — Legacy Provider Atomicity Hardening | 2026-09-17 | `f28e3db` |

发布 Gate：

| Gate | 日期 | 结论 |
| --- | --- | --- |
| RC1.1 — Release Engineering Gate | 2026-09-17 | PASS WITH ISSUES |
| RC1.2 — Repository Hygiene Gate | 2026-09-17 | PASS WITH CLEANUP RECOMMENDED |
| RC1.3 — Product Documentation & README V3 | 2026-09-17 | Completed |
| RC1.4 — Full-System Release QA | 2026-09-17 | PASS |
| RC1.5 — Claude Final Release Review | 2026-09-17 | APPROVE WITH NON-BLOCKING NOTES |
| V3.0.0 — Release | 2026-09-17 | `c1f8b98` |
| V3.0.0 — README 定稿 | 2026-09-18 | `2b2b0cb` |

主要更新：Engineering baseline（自动化测试与 CI）、Stable `SymbolId`、Processor 从 name-key 迁移至 `SymbolId`、Project Scanner、Project Graph、Project Snapshot / SnapshotDiff、Deterministic Project Analysis Engine、Provider / BYOK Foundation、Task-scoped Provider isolation、Legacy Provider atomic update hardening，以及 Release engineering / QA / documentation gates。

Tests: **129 passed**（开发环境与仓库外干净 venv 一致）。Release Blockers: 0；Medium: 0。

### V2.4.1 — 2026-08-12（v2.4.0 小更新 #1）

**macOS + 手机端响应式自适应**

- 背景：旧版 CSS 仅针对桌面端 Windows 高分屏设计，在 macOS 与手机浏览器上字体回退不美观、滚动条偏粗、布局元素溢出。本次为纯 CSS 注入，零新增依赖、零组件结构变更。
- macOS 字体栈：全局字体 `-apple-system / BlinkMacSystemFont / SF Pro Display / PingFang SC / Hiragino Sans GB` 优先于 `Segoe UI / Microsoft YaHei`；代码等宽字体 `SF Mono / Monaco / Menlo` 优先于 `Fira Code / Consolas`；大纲折叠区 code 标签同步更新。
- macOS 滚动条：`(-webkit-min-device-pixel-ratio: 1) and (pointer: fine)` 下滚动条宽度由 10px 细化为 8px；`.cm-scroller::-webkit-scrollbar:vertical` 增加 `-webkit-appearance: none`，避免与 macOS overlay 滚动条冲突。
- 三档断点响应式布局：

| 断点 | 适用设备 | 主要调整 |
| --- | --- | --- |
| `max-width: 1024px` | iPad / 平板 | 容器全宽、header 内边距缩小、代码编辑器 500px、语言切换器 140px |
| `max-width: 768px` | 手机横屏 / 大手机竖屏 | header 垂直堆叠、等宽列垂直排列、编辑器 380px、按钮全宽垂直、Tab 水平滚动、下载按钮垂直、卡片圆角缩小 |
| `max-width: 480px` | iPhone SE / Android compact | header 17px、编辑器 300px 与 12px 字号、卡片 8px 圆角、Tab 12px 字号 |

- 触控优化：`(hover: none) and (pointer: coarse)` 下禁用 `.card-section:hover` 的 transform 与阴影增强、`.action-btn:hover` / `.dl-download-btn:hover` 的悬浮位移、`.outline-sidebar summary:hover` 的背景色变化，避免误触闪烁。
- 兼容性：纯 CSS 注入，零 Python 代码变更、零新增第三方依赖；Gradio 组件 id / class / 事件绑定零修改，已有测试零侵入；py_compile（`ui.py`）0 SyntaxError。
- Tests（当时记录）：**139 passed**（`test_provider_model 52 + test_style_lint 31 + test_workspace_persistence 25 + test_outline_collapsible 15 + test_batch_naming 16`）。

### V2.4.0 — 2026-08-11（大版本：多 Provider / 多模型切换 + 运行时 API Key 管理）

- 背景：用户持有多个 API Key，或希望在 DeepSeek / GPT / Qwen / Kimi 之间切换以对比注释质量；此前 `config.py` 硬编码只有 DeepSeek，扩展性受限。
- `config.py` 底层重构：以 `PROVIDERS` 统一字典集中定义 6 种 OpenAI 兼容协议 Provider（DeepSeek / OpenAI / Azure / 阿里百炼 DashScope / 月之暗面 Moonshot Kimi / Custom）。每项包含三语显示名 `label_zh / label_en / label_ja`、按优先级查找的环境变量列表 `api_key_env`、默认 `base_url`、`models` 映射、输入输出单价 `price_input_per_m / price_output_per_m`（元 / 1M tokens），以及 `customizable_base_url`（仅 Azure / Custom 允许自定义 Endpoint，其余强制官方 Endpoint）。
- 线程安全运行时状态：`threading.RLock()` 保护 `_active_provider / _active_model / _active_api_key / _active_base_url / _custom_model_name`，切换时调用 `_rebuild_client()` 重建 `openai.OpenAI` client 实例。
- 公开 API（UI 与 `llm_service` 只调用这些入口，禁止直接修改模块全局）：`get_providers(lang)`、`get_models_for_provider(pkey, lang)`、`switch_provider(...)`（原子切换，返回 `(ok, msg)`）、`set_api_key(key)`、`set_custom_base_url(url)`、`get_active_provider/model/client/base_url()`、`get_price_input_per_m()` / `get_price_output_per_m()`、`is_active_provider_customizable()`。
- 启动期 `.env` 初始化：读 `PROVIDER`（非法值回退 deepseek 且不报错）→ 读 `MODEL`（不在列表回退默认第一个）→ 读 `BASE_URL`（仅 customizable Provider 生效）→ 读 `CUSTOM_MODEL_NAME`（仅 custom）。
- 向后兼容 `__getattr__`：仍暴露 `client` / `MODEL` / `PRICE_INPUT_PER_M` / `PRICE_OUTPUT_PER_M` 等顶层名字，保证 `from config import client, MODEL` 的旧代码零修改运行。
- `llm_service` 去常量：不再 `from config import client, MODEL, PRICE_*`，全部改为动态 getter（`_cfg.get_active_client()` / `get_active_model()` / `get_price_input_per_m()` / `get_price_output_per_m()`），实现 UI 切换 Provider / Model / 单价后**下一次 LLM 请求立即生效，无需重启进程**；`ping_api_key` 错误提示从「请检查 DEEPSEEK_API_KEY」升级为通用的「请检查对应 Provider 的 API Key 环境变量」。
- UI 新增「Provider / 模型切换」独立区块（位于「注释风格选择」card 下方、「代码输入」card 上方），新增 `provider_dd`、`model_dd`、`api_key_tb`（password 类型，留空则使用 `.env`，非空则仅运行时内存覆盖且**不写文件**）、`base_url_tb`（仅 Azure / Custom 可编辑）、`custom_model_tb`、`apply_provider_btn`、`provider_status_md`、`provider_info_md` 等组件，含联动刷新与三语 i18n。
- `.env.example` 大更新：从单行 `DEEPSEEK_API_KEY=` 扩展为全局默认变量说明、各 Provider 可选模型名列表，以及按 Provider 分段的 API Key 环境变量（注明官网获取地址）。
- i18n 新增 16 个 key，中文 / English / 日本語 全覆盖。
- 兼容性：零破坏性改动，所有旧 API 签名不变；`analyze_code` 返回 5 元组、批量命名策略、会话持久化等 v2.3.x 功能零侵入；py_compile（`config` / `llm_service` / `i18n` / `ui` / `processor`）0 SyntaxError。
- Tests（当时记录）：新增 `test_provider_model.py` **52 passed**（覆盖 Provider 字典结构、三语 label、公开 getter、切换与原子性、base_url 限制、`__getattr__` 兼容层、LLM 动态单价、Custom 模型）；回归 **139 passed**，0 Failing。

### V2.3.8 — 2026-08-10（v2.3.0 小更新 #8）

**代码风格检查（PEP8 / Google Java Style）**

- 在「代码分析」Tab 新增「代码风格」区块，分析代码时自动检测风格问题并以 Markdown 表格展示。
- Python 侧（PEP8）：优先使用 `pycodestyle`（如已安装），覆盖 E1xx / E2xx / E3xx / E5xx / W1xx / W2xx 等规则；`pycodestyle` 不可用时降级到 `_lint_python_basic` 正则近似检查，覆盖 E501 行过长（>100 字符）、W291 尾随空格、W292 文件末尾无换行、W191 Tab 缩进、E221 多余空格、E303 空行过多。报告中标注实际使用的工具名（`pycodestyle (PEP8)` 或 `PEP8 basic (regex fallback)`）。
- Java 侧（Google Java Style 正则近似，无 JDK 依赖）：`_lint_java_regex` 检查 GJL001 行过长（>100 字符）、GJL002 尾随空格、GJL003 Tab 缩进（Google Style 要求 2 空格）、GJL004 逗号 / 分号后缺空格、GJL005 大括号前缺空格、GJL006 空行过多、GJL007 文件末尾无换行。
- 集成方式：`analyze_code` 返回值由 4 元组扩展为 5 元组 `(quality_report, annotation_report, summary, style_report, log_text)`；风格检查在质量分析与类型注解检查之后、LLM 摘要生成之前执行，非 LLM 调用，零延迟；`_analyze_java` 同步改造，Java 代码无效时返回「跳过风格检查」占位；UI 分析 Tab 新增 `style_title_md` 与 `style_output`，`analyze_btn.click` outputs 由 4 增至 5。
- 兼容性：`pycodestyle` 为可选依赖（`pip install pycodestyle`），不可用时自动降级且不报错；零新增必需第三方依赖；`analyze_code` 返回值由 4 元组变为 5 元组，所有调用方需适配（UI 已同步更新）。
- Tests（当时记录）：新增 `test_style_lint.py` **31 passed**；回归 **87 passed**（`test_style_lint 31 + test_workspace_persistence 25 + test_outline_collapsible 15 + test_batch_naming 16`），0 Failing。

### V2.3.7 — 2026-08-10（v2.3.0 小更新 #7）

**保存 / 加载用户工作区（会话持久化）**

- 目标：用户做到一半关闭浏览器无需重来，下次打开点「恢复上次会话」即可恢复代码、注释风格、语言选择、批量命名策略等完整工作区状态。
- 持久化方案：主存储为服务端 tempfile JSON，路径 `<tempdir>/<8 位用户名 MD5>_code_comments_agent_workspace.json`；多用户共享 temp 目录场景下以用户名前 8 位 hash 分离各 workspace，避免互相覆盖；采用 `write tmp + os.replace()` 原子写入，中途断电或崩溃不会写坏原文件。
- 白名单字段与安全保护：`WS_ALLOWED_FIELDS` 为不可变 `frozenset`，只允许 `source_code` / `language` / `ui_lang` / `python_style` / `java_style` / `naming_strategy` 6 个字段持久化；**API Key、api_base_url、password 等敏感字段绝不写入**（`save_workspace` 白名单过滤 + `load_workspace` 白名单二次过滤）；`None` 值字段跳过以保持 JSON 精简；即使磁盘文件被人工注入脏字段，`load_workspace` 仍按白名单过滤，不会回传任意内容。
- 容错设计：`load_workspace` 所有异常均不抛出，统一返回 `False` + 空 dict，覆盖文件不存在、空文件、非法 JSON、顶层为 list、缺少 `data` key、`data` 非 dict、非 UTF-8 编码等情况，分别给出对应提示。
- UI 与 i18n：批量区新增「会话持久化」小节（`workspace_title_md` 标题、`保存会话` / `恢复上次会话` / `清除已保存会话` 三按钮、`ws_tip_md` 安全提示「API Key 不会被保存」）；事件链路闭环，恢复操作按严格顺序输出 6 个组件 value 加日志消息；`ui_lang` 切换时同步更新 5 个组件文案；新增 5 个 i18n key 三语覆盖。
- 兼容性：零新增第三方依赖，仅使用 Python 标准库（`json` / `tempfile` / `getpass` / `hashlib` / `os.replace`）；旧版 processor 调用不受影响，三个 API 函数新增 `path` 可选参数使单元测试与生产解耦；UI 新增组件位于独立 card-section，不影响原有批量区与输出区布局。
- Tests（当时记录）：新增 `test_workspace_persistence.py` **25 passed**；回归 **56 passed**（`test_workspace_persistence 25 + test_outline_collapsible 15 + test_batch_naming 16`），0 Failing。

### V2.3.6 — 2026-08-10（v2.3.0 小更新 #6）

**代码编辑器搜索替换 + 大纲折叠**

- 背景：处理大文件（>500 行）时，用户需要直接在输出代码框内搜索函数名并折叠大纲，而不是在大文件中来回滚动。Gradio 6.x Code 组件底层为 CodeMirror 6，已内置 `@codemirror/search` 扩展（Ctrl+F / Cmd+F 触发），只需 CSS 注入确保面板可见并美化；函数大纲已有 `build_outline_markdown`，改造为 `<details>` 折叠结构即可。
- CodeMirror 搜索面板 CSS 注入（`ui.py` custom_css）：`.cm-panels` 容器改为 `display: flex` 与 `order: -1`，使搜索面板显示在编辑器顶部而非默认底部，并加灰底圆角；`.cm-textfield` 输入框圆角加 focus 高亮边框与光环；`.cm-button` 按钮圆角加 hover 背景；`.cm-searchMatch` 匹配项黄色半透明高亮，`.cm-searchMatch-selected` 当前选中项橙色高亮加白字；`.cm-panel label` 灰色小字。隐藏按钮选择器保持安全，`.cm-editor-header button` 与 `.cm-panels button` 为平级独立容器，不会误伤搜索面板按钮。
- 大纲折叠结构：`processor.build_outline_markdown` 新增 `collapsible` 参数。`collapsible=True`（新默认）输出 `<details>` + `<summary>` HTML 折叠结构，class 条目默认展开且方法作为嵌套 `<ul><li>`，顶级 function / method 默认折叠且各自独立；折叠箭头由 CSS `summary::before` 伪元素实现，展开时旋转 90 度并变色；层级按 `lineno` / `end_lineno` 范围包含关系推断方法归属哪个 class。`collapsible=False` 保持旧版平铺 Markdown 无序列表格式。
- 锚点一致性：slug 分配顺序始终按 items 原始顺序（lineno 排序），与 annotator 的 `build_markdown_docs` / `build_java_markdown_docs` 生成的 `<a id="...">` 完全一致，保证锚点跳转有效。
- i18n 新增 `search_hint` 三语文案，附加到 `output_code` 组件 label 后缀（提示 Ctrl+F 搜索 / 替换代码）。
- 兼容性：`build_outline_markdown` 签名新增 `collapsible: bool = True`，旧调用者不传参数即自动获得折叠版，显式传 `False` 可恢复旧格式；CSS 纯注入，无 JS、无新增第三方依赖；py_compile（`processor` / `ui` / `i18n`）0 SyntaxError。
- Tests（当时记录）：新增 `test_outline_collapsible.py` **15 passed**，其中 `T3_SlugConsistency` 以 Python / Java / collapsible 与 flat 三方对比保证锚点 slug 一致性。

### V2.3.5 — 2026-08-07（v2.3.0 小更新 #5）

**输出 ZIP 命名策略可配置 + 源目录结构保留**

- 背景：批量下载的 ZIP 内部原先按「上传时的文件名（无父目录）」平铺写入，解压后需要手动改名或覆盖到原工程目录；CI 场景希望可直接同名覆盖或统一放入子目录，而不是每次手工整理。
- 在批量区新增「ZIP 输出命名策略」下拉框（三语），提供 3 种策略（以 `src/pkg/utils.py` 为例）：

| 策略值 | UI 显示 | 效果 | 典型场景 |
| --- | --- | --- | --- |
| `same` | 同名覆盖（保留原文件名） | `src/pkg/utils.py` | CI 流水线：解压后直接覆盖源文件 |
| `suffix`（默认） | 添加 `_annotated` 后缀 | `src/pkg/utils_annotated.py` | 人工对比：不覆盖源文件，方便 diff |
| `subdir` | 放到 `annotated/` 子目录 | `annotated/src/pkg/utils.py` | 目录整洁：所有结果放一个顶层文件夹 |

- `processing.log` 与 `API_DOCS_ALL.md` 始终位于 ZIP 根目录，不受命名策略影响；非法值自动降级到 `suffix`，不会抛异常阻断下载。
- 关键实现：新增独立纯函数 `_apply_naming_strategy(rel_path, strategy)`（覆盖 3 策略 × 无子目录 / 有子目录 / Windows 反斜杠输入共 8 条分支）；`_build_batch_zip(..., naming_strategy)` 打包时仅对源码文件应用策略；`process_batch_files` 与 `process_batch_with_progress` 同时新增 `naming_strategy` 参数且签名向后兼容。批量路径内部重构：不再把 `basename` 当 rel_path 打平，而是收集全部原始源路径后按 `Path.parts` 求最长公共前缀、再向上退一层作为公共父级，对每个源文件求相对路径；跨盘符无公共前缀时退化为 `basename` 且不报错。
- 兼容性：旧签名调用者零侵入，默认 `suffix` 行为比旧版更安全（多一个 `_annotated` 后缀保护源文件）；`processor.py` 顶部补充 `from pathlib import Path`；无新增第三方依赖。
- Tests（当时记录）：新增 `test_batch_naming.py` **16 passed**，覆盖命名策略纯函数、ZIP 成员名校验、端到端批量处理与 i18n key。

### V2.3.4 — 2026-08-07（v2.3.0 小更新 #4）

**Java 有效性严格化 + 注释后语法二次校验**

- 背景：v2.3.3 完整端到端测试（49 用例全通过）后，测试报告列出 4 项潜在问题，本次修复其中可落地的 2 项；另 2 项为「mock LLM 难以验证翻译质量」与「无 Gradio UI 交互测试」，属测试基础设施限制而非产品缺陷，不在本次范围。
- 修复一（Java 有效性检测宽松）：旧版 `_is_valid_java` 只要源码出现 1 个 Java 关键字或 2 个大括号即判为有效，导致 `"hello class world"`、`"int x = 1; print(x);"` 等无意义文本被误判为有效 Java 代码并触发后续 LLM 调用，可能产生幻觉输出。现改为三重校验：必须有非空非注释行；必须包含作为独立词的 Java 类型声明关键字 `class` / `interface` / `enum` / `record`（正则词边界匹配，避免普通文本中的 `class` 误判）；必须有至少 1 对大括号且大括号匹配（复用 `Java.java_annotator._validate_braces`，屏蔽字符串与注释后校验）。
- 修复二（缺少 javac 语法验证与注释后二次校验）：Java 端此前仅在 `_analyze_java` 阶段做过一次大括号校验，注释插入后代码完整性无二次验证。新增 `processor._verify_java_annotated_code(annotated_code, log)`，在 `_process_java` 与 `_process_java_with_progress` 写临时文件前调用：先做大括号匹配二次校验，失败时日志追加警告；再通过 `shutil.which("javac")` 探测 PATH，若存在 javac 则写入临时文件调用 `javac -Xlint:none -encoding UTF-8`（`subprocess.run` + 15s 超时），返回码非 0 时取 stderr 首行作为警告，超时则提示超时，无 javac 时优雅跳过。
- 设计原则：校验失败仅记录日志警告，不抛异常、不阻断下载，符合「取消任务也要保留已完成结果」的产品约定；javac 可用性自动探测，无 javac 的开发机与有 javac 的 CI 环境均可正常运行。
- 兼容性：`_is_valid_java` 签名与返回类型不变，所有调用点零侵入；`processor.py` 顶部新增 `import re` 与 `import subprocess`，无新增第三方依赖；py_compile 全部 13 个 `.py` 文件（root 与 `Py/`、`Java/`）0 SyntaxError。
- Tests（当时记录）：Java 有效性边界 **13 条**通过（`"hello class world"` / `"just some text"` / `"{}"` / `"class Foo {"` / `"// only comment"` / `"int x = 1; print(x);"` 判为无效；`"class Foo {}"` / `"public class Foo { void bar() {} }"` / `"interface Bar { void run(); }"` / `"enum Color { RED, GREEN }"` 判为有效）；注释后校验 **3 条**通过。

### V2.3.3 — 2026-08-07（v2.3.0 小更新 #3）

**API Key 有效性预检（1-token 心跳）+ Token 用量 / 成本估算**

- `config` 新增 5 个常量（DeepSeek 官方参考价，2026 参考值）：`PRICE_INPUT_PER_M = 0.27`（元 / 1M 输入 tokens）、`PRICE_OUTPUT_PER_M = 1.10`（元 / 1M 输出 tokens）、`AVG_TOKENS_PER_ITEM = 350`（每个函数 / 方法实测经验值）、`INPUT_RATIO = 0.43` 与 `OUTPUT_RATIO = 0.57`（更精准的入出力拆分估算）。
- `llm_service.ping_api_key(timeout=6.0)`：独立 1-token 心跳请求，采用 `temperature=0.0`、`max_tokens=1`、`messages=[{role: user, content: "ping"}]`。覆盖 8 种错误映射（API Key 无效、无权限、频率超限或余额不足、模型或 base_url 错误、超时、兜底异常等），返回 `(ok, msg)` 二元组，失败时 msg 为人类可读提示。
- `llm_service.estimate_tokens_cost(num_items, avg_tokens_per_item=None)`：返回 `(total_tokens, input_est, output_est, cost_rmb)` 四元组；`num_items <= 0` 直接返回零向量；成本公式为 `(in/1e6)*0.27 + (out/1e6)*1.10`，精度 4 位小数。
- `processor.preflight_check(source_code, language, ui_lang, do_ping, avg_per_item)` 组合入口，返回 `(ok, preflight_md, estimate_md)` 三元组：按 `ui_lang` 从三语模板字典（3 语种 × 12 键）选择文案；`do_ping=True` 时调用 `ping_api_key`，`do_ping=False` 时跳过网络以支持实时估算；源码为空、语法异常、AST 解析 0 条定义分别给出对应提示；统计函数数、类数与总数后渲染 Markdown 报告（分析计数、总 tokens 与每条均值、入出力拆分、元成本与价格档位说明）。另提供 `estimate_markup_cost(num_items, lang, avg)` 无网络快速封装。
- UI 绑定：操作行新增预检按钮（点击 `do_ping=True`）；按钮下方新增预检区域与成本估算区域两个 Markdown；`ui_lang` 切换时同步翻译按钮与标签；生成器输出由 9 元组扩展为 11 元组，首帧前先执行 `preflight_check(do_ping=True)`，**失败则直接返回且绝不进入主生成循环**，避免因 Key 无效白花 token 与时间，中间帧返回 `None` 继承上一帧不闪烁，最终帧再以 `do_ping=False` 补算一次保证最新；`input_box` / `language` / `ui_lang` / `python_style` / `java_style` / `file_upload` 共 6 个组件的 `.change` 事件全部绑定无网络估算，实现粘贴代码或切换语言时实时刷新。
- i18n 新增 3 个 key 三语覆盖（预检按钮、用量 / 成本标签、预检区域标签）。
- Tests（当时记录）：新增 `test_cost_preflight.py` **12 passed**，覆盖成本向量与比例、`ping_api_key` 传参断言与 6 种异常映射、预检边界（空代码 / 0 函数 / Python / Java / 英日语言 / 未知语言回退中文）与 i18n key；全流程验证 **82 passed**（`test_styles 21 + test_smoke_comprehensive 24 + test_progress_cancel 16 + test_outline_navigation 9 + test_cost_preflight 12`），py_compile 全自有 `.py` 0 SyntaxError。

### V2.3.2 — 2026-08-07（v2.3.0 小更新 #2）

**函数 / 类导航大纲 Sidebar + API 文档 TOC 锚点**

- 「带注释的代码」Tab 顶部新增大纲栏，渲染内容来自新增的 `processor.build_outline_markdown(source, language, title)`：解析 Python / Java 解析器的定义结果，转成可点击的 Markdown 列表，每项包含图标、名称、类型（Class / Function / Method）与行号锚点链接。
- 「API 文档」Tab 顶部新增同内容目录栏，方便切到 Docs Tab 后立即有目录可点；UI 语言切换时大纲内容以 `gr.update()` 占位继承最新值。
- 生成器输出由 7 元组扩展为 9 元组（新增大纲与文档目录两项），所有分支（首帧 / 中间帧 / 最终帧 / 取消帧）严格 yield 9 项，中间帧返回 `None` 继承上一帧不闪烁；首帧立即渲染早期大纲，保证点击生成按钮瞬间即可看到函数 / 类列表而不必等待 LLM，最终帧再按最新 UI 语言渲染一次。
- API 文档内置 TOC 与锚点 Heading：`Py.annotator.build_markdown_docs` 升级，新增 `_slugify(name, prefix, used)`（字母、数字、连字符、下划线保留，其余转 `-`，重名自动加 `-2` / `-3` 去重），先遍历分配 `cls-` / `fn-` 前缀的 `slug_id` 写入每个 doc entry，顶部追加目录段，每条详情的 Heading 改为带 `<a id="slug_id"></a>` 锚点；`Java.java_annotator.build_java_markdown_docs` 同步升级，类前缀 `cls-`、方法前缀 `m-`（与 Python 的 `fn-` 区分避免命名空间冲突）。
- processor 层独立 API：`processor._slugify_name(name, prefix, used)` 与 `processor.build_outline_markdown(...)`（不依赖 `llm_service` 运行期调用，import 期只依赖 parser，测试无需 LLM mock 即可运行；空源码或语法错误时吞掉异常返回空字符串）。
- 锚点一致性保证（最关键）：processor 与 annotator 的 slug 规则完全一致，相同 name / type 与相同 used 插入顺序产生相同 `slug_id`；测试以真实「1 个 Class + 2 个 Method + helper/main 函数」验证 `doc_entries[*].slug_id` 同时出现在 `build_markdown_docs` 的 `<a id="..."></a>` 与 `build_outline_markdown` 的锚点链接中。
- 兼容性：两个 annotator 顶部新增 `from __future__ import annotations`，保证 Python 3.8 下联合类型注解不抛 `TypeError`；i18n 新增大纲标题 key 三语覆盖。
- Tests（当时记录）：新增 `test_outline_navigation.py` **9 passed**；独立进程 4 套件合计 **70 passed**（`test_styles 21 + test_smoke_comprehensive 24 + test_progress_cancel 16 + test_outline_navigation 9`）。注：同进程 `discover` 下 `test_styles` 与 `test_smoke_comprehensive` 因对 `openai` 模块注入顺序不兼容而互相干扰，属 v2.3.1 既有问题，与本改动无关，生产执行需分文件或分进程运行。

### V2.3.1 — 2026-08-07（v2.3.0 小更新 #1）

**实时进度条 + 可取消任务**

- 单文件生成：生成按钮改用生成器函数配合 `gr.Progress()`，每一步更新进度百分比（0.05 至 1.00）与阶段描述（解析代码结构、翻译已有注释、调用 LLM 生成注释、插入注释到源码、构建 API 文档、完成）。
- 批量处理：批量按钮改用生成器函数，每个文件处理完成后更新「x/N 处理 xxx.py」描述，0% 至 5% 展开 ZIP，5% 至 95% 按文件数线性推进，95% 后打包 ZIP。
- 取消按钮：单文件与批量生成按钮右侧新增红色停止样式按钮。单文件取消通过线程安全取消标志位立即置位，核心循环每步检测，检测到后立即取消排队中与运行中的 LLM future 并关闭执行器，节省 API token；批量取消在处理完当前文件后不再推进后续文件，已成功处理的文件照常打包返回。
- 取消不丢结果：取消流程不提前返回，继续执行到「构建 Markdown 与写临时文件」阶段，文档路径、源码路径、ZIP 路径均为有效路径，用户仍可下载取消前已完成的部分。
- processor 层新增：`processor.CancelToken`（线程安全取消标志位）、`_process_python_with_progress` / `_process_java_with_progress` 双语生成器版（每步 yield 5 元组中间态）、`process_code_with_progress(...)` 入口生成器（统一边界处理与路由）、`process_batch_with_progress(...)` 批量生成器。**原有同步函数 `process_code` / `process_batch_files` 签名与行为完全未变**，测试套件与旧调用方零侵入。
- Python 3.8 兼容：新增 `_shutdown_executor_safe(executor, futures_map)`，以 `try/except` 捕获 `TypeError`（`cancel_futures` 参数仅 Python 3.9+ 支持），降级为先手动取消每个 future 再关闭执行器，保证 Windows 自带 Python 3.8 下正常运行。
- i18n 新增 2 个 key 三语覆盖（取消任务、取消批量任务）。
- Tests（当时记录）：新增 `test_progress_cancel.py` **16 passed**（取消标志位多线程并发安全、边界单 yield、有效代码多帧 yield 与最终帧非空路径、进度回调最终比例、取消场景路径仍有效、批量空输入与非法路径、i18n key）；原 45 条用例一次通过，无破坏性改动。

### V2.3.0 — 2026-08-07（大版本：代码差异对比底层能力）

**代码对比 Diff 视图（GitHub 风格并排 Split）**

- 输出区新增第 5 个 Tab，位于「注释后的代码」之后，用户生成完成后可直接切换查看差异。
- 左右分栏并排显示 Before（注释前原始代码）与 After（注释后代码），各自独立行号并视觉对齐。
- 行级高亮：新增行绿底、删除行红底、未变行白底，行号列同步着色；顶部统计条展示「+N 插入 / -M 删除 / K 未变」，完全相同时自动提示未检测到代码差异。
- `processor.build_split_diff_html` 基于 `difflib.SequenceMatcher` 的 opcodes 逐行渲染，并自动 HTML 转义 `<>&"` 等特殊字符，避免 XSS 与样式错乱。
- 三语 i18n：Diff Tab 标签跟随 UI 语言切换。
- 事件绑定：生成注释后通过 `.then(...)` 自动异步计算 Diff，不阻塞原有 UI 跳转；Diff Tab 未破坏 `process_code` 签名，UI 层直接以原始输入与注释后输出为输入，processor 零侵入。
- Tests（当时记录）：新增 **7 passed**，覆盖同文无差异、纯插入、纯删除、替换行、空输入、语言标签传递与 HTML 特殊字符转义。

### V2.2.2 — 2026-08-07（v2.2.0 小更新 #2）

**注释风格模板选择（Python 3 种 + Java 2 种）**

- 新增 5 种注释风格，通过预定义 Prompt 模板灵活切换。Python：Google 风格（Args / Returns / Raises）、NumPy 风格（Parameters / Returns 与类型短横线分隔）、reStructuredText（`:param` / `:type` / `:return` / `:rtype`）；Java：标准 Javadoc（`/** ... */` 加 `@param` / `@return` / `@throws`）与极简行内注释（单行短注释）。
- `llm_service.py` 提供 Python 与 Java 风格常量，生成与翻译流程统一走风格规则注入：生成时按目标风格追加格式要求，翻译与重组时按目标风格重排输出结构；默认风格保持不变（Python 默认 Google，Java 默认标准 Javadoc），向下兼容 v2.x API。
- `processor.process_code` 与 `process_batch_files` 新增 `python_style` / `java_style` 可选参数，风格信息从 UI 一路透传到 LLM 层；Gradio UI 新增「注释风格选择」分区（两个并列下拉框），三语文案同步更新。
- 兼容性：修复 Python 3.8 类型注解问题，在 `llm_service.py` 与 `processor.py` 顶部添加 `from __future__ import annotations`，并将 `str | None` 改为 `Optional[str]`。
- Tests（当时记录）：新增 `test_styles.py` **14 passed**，覆盖 5 种风格的 prompt 关键词注入、翻译规则适配、默认风格行为与 processor 参数链路。

### V2.2.1 — 2026-08-07（v2.2.0 小更新 #1）

**批量文件 / 文件夹处理功能**

- 新增批量上传入口：支持一次选择多个 `.py` / `.java` 文件，或上传整个 `.zip` 压缩包（支持递归子目录），两种方式可混合使用。
- 新增 `process_batch_files` 批量处理调度器：安全解压 ZIP（内置 zip slip 路径穿越防护，并兼容 Windows 下中文文件名编码问题，UTF-8 失败时自动回退 `cp437 → GBK` 解码）；按扩展名自动分流到 Python / Java 解析器；使用 `ThreadPoolExecutor` 并发调用 LLM，显著降低多文件总耗时；保持原目录结构写出注释后的源码文件，便于用户直接覆盖。
- 结果 ZIP 自动包含：所有源文件的注释版（保持目录结构）、`processing.log`（按文件逐行记录跳过 / 生成 / 翻译 / 失败明细）、`API_DOCS_ALL.md`（所有文件 API 文档的聚合版本，代码块内嵌注释同步到最终语言）。
- 新增批量处理 UI 区域：批量上传组件、批量生成按钮、批量下载按钮与批量日志文本框，文案跟随界面语言三语翻译。
- 修复翻译与 Markdown 文档一致性问题：修复翻译注释时按原行号升序插入导致的后续节点 `lineno` 错位与部分函数插入失败的问题，改为与生成流程一致的行号倒序插入；修复 `build_markdown_docs` / `build_java_markdown_docs` 中硬编码中文标题导致 EN / JA 界面聚合文档语言检测失败的问题，改为通用英文标题；修复聚合文档内嵌代码块保留原始中文注释的问题，改为在注释插入完成后统一从最终注释代码重新解析结构并刷新每个文档条目的代码块，确保 Markdown 与最终源码一致。

### V2.2.0 — 2026-08-07（大版本：多语言 i18n 底层能力）

**多语言支持（i18n）**

- 右上角新增语言切换下拉框（中文 / English / 日本語），一键切换整个界面语言。
- 生成的注释语言跟随界面语言：英文界面生成英文注释，日文界面生成日文注释。
- 已有注释自动翻译：增量模式下自动检测注释语言，若与目标语言不一致则调用 LLM 翻译为对应语言。
- 字符集智能检测：支持中日英（汉字 / 假名 / 拉丁字符）自动判定是否需要翻译。
- 修复多语言下下载按钮标签不更新、输出代码框标签未翻译等问题。

**交互优化**

- 增量更新模式改为默认永久开启，移除界面勾选框，操作更简洁。
- 点击「生成注释与文档」自动跳转到「带注释的代码」标签页；点击「分析代码」自动跳转到「代码分析」标签页。
- 移除遮挡滚动条的原生下载 / 复制按钮，改为输出下方并排的「下载注释后的代码」与「下载文档」两个美化按钮。

### V2.1.1 — 2026-08-06（v2.1.0 小更新 #1）

**前端界面重构**

- 代码编辑器统一为白底、深色文字、中性灰边框的亮色主题，并支持显示滚动条，长代码不再被拉伸。
- 优化整体布局与样式：卡片容器、Tab 导航、按钮、滚动条全面美化。
- 修复 Gradio 6.0 下代码编辑器显示「错误」以及 Java 编辑器切换语言时显示「错误」的问题。

**代码有效性验证**

- 新增代码有效性校验：分析前先验证代码结构（函数 / 类 / 导入 / 控制流 / 赋值）。
- 无效或无意义的代码（如纯字符串）直接返回友好提示，不再触发 LLM，避免幻觉内容。

**测试与结构**

- 新增端到端测试用例（上传、分析、注释、下载、无效代码验证）。
- 精简目录结构，删除冗余开发脚本，核心模块收敛为 `main.py`、`ui.py`、`processor.py`、`llm_service.py`、`config.py`、`i18n.py`。

### V2.1.0 — 2026-08-06（大版本：Java 语言 + 目录结构分语言）

**Java 语言支持**

- 新增 Java 代码解析器，支持类、方法、构造器、枚举、内部类与匿名类（并排除匿名类实例化误判）。
- 新增 Javadoc 注释自动生成，支持 `@param`、`@return`、`@throws` 标签。
- 支持复杂嵌套 Java 代码（接口、泛型、静态嵌套类、Lambda 等）。
- 新增 Java 代码有效性验证（大括号匹配校验，并屏蔽字符串中的括号）。

**目录结构优化**

- 按语言和功能分文件夹组织：`Py/`（Python 解析 / 注释 / 分析）、`Java/`（Java 解析 / 注释）。
- 修复 Java 解析器排除匿名类实例化（`new ClassName() { ... }`）的问题。

### V2.0.0 — 2026-08-05（大版本：架构重构 + 并发生成 + 代码质量体系）

**架构重构**

- 将单文件 `main.py`（549 行）拆分为 8 个职责清晰的模块：`config.py`（配置外置：API Key、模型参数、重试与并发配置）、`parser.py`（AST 解析）、`llm_service.py`（LLM 调用：docstring 生成与代码摘要）、`annotator.py`（注释插入与 Markdown 文档生成）、`analyzer.py`（代码质量分析与类型注解检查）、`processor.py`（主处理逻辑：并发生成与串行插入）、`ui.py`（Gradio 界面构建）、`main.py`（入口，仅 19 行）。

**新增功能**

- 增量更新模式：跳过已有 docstring 的函数，节省 API 调用。
- 并发调用优化：使用 `ThreadPoolExecutor` 并发调用 LLM，处理时间从 30 秒缩短至 7 秒。
- 代码质量分析：圈复杂度、嵌套深度、函数长度、参数数量检测。
- 类型注解检查：识别缺失类型注解的参数与返回值。
- 代码摘要生成：调用 LLM 生成模块功能摘要。
- LLM 调用重试机制：API 失败时自动重试 3 次（带退避）。

**Bug 修复**

- 修复 `__init__` 方法返回值注解误报问题。
- 修复 `match` / `case` 语句不计入圈复杂度的问题（Python 3.10+）。
- 修复 Gradio 6.0 的 `css` 参数警告（移至 `launch()` 方法）。
- 修复 `_clean_docstring` 三引号清理正则未按行匹配的问题（添加 `re.MULTILINE`）。
- 修复中文注释未正确包裹在三引号中导致语法错误的问题。
- 修复代码过长时文本框被拉长的问题（添加滚动条）。
- 修复类型注解检查误判 `self` / `cls` 参数的问题。

### V1.0.0 — 2026-08-05（初始版本）

- 基础功能：AST 解析、LLM 注释生成、Gradio 界面。
- 支持文件上传与下载。
- Markdown API 文档生成。

## Engineering Documentation

- `docs/development/`：Phase Development Reports 与 Release Engineering Gates
- `docs/qa/`：独立 QA Reports
- `docs/release/`：Release Notes
- `PROJECT_CONTEXT.md`：当前架构、边界、已知债务与版本规划
