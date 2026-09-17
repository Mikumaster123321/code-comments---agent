# Code Comments Agent

**当前版本：V3.0.0 RC1（`3.0.0-rc1`）**

Code Comments Agent 正在演进为面向项目级代码理解与智能维护的 **LLM-assisted Software Maintenance Platform**。V3.0.0 RC1 的定位是 **Project-level Maintenance Core Foundation**：在保留 V2 用户能力的同时，提供稳定的项目扫描、关系图、快照、确定性分析和 BYOK Provider 基础。

V3.0.0 仍是 Release Candidate，不是完整的 Autonomous Multi-Agent IDE。

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

当前 V3.0.0 RC1 基线：**129 passed**。

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
│   └── qa/
└── .github/workflows/
```

`Py/` 和 `Java/` 仍是 legacy-compatible Processor 与 V3 Adapter 使用的生产模块，并未被 `code_maintenance/` 替代。

## Roadmap / Planned

以下能力均为 **Planned**，不属于 V3.0.0 RC1 的已实现功能。

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

以上均未在 V3.0.0 RC1 实现。

### Later Planned Versions

- **V3.1 — Project Intelligence / RAG** — Planned
- **V3.2 — Controlled Multi-Agent Collaboration** — Planned
- **V3.3 — Data-driven Multi-Model Router** — Planned
- **V3.4 — VS Code Integration + Secure Credential UI** — Planned

## Version History

从 V3 开始，README 保留简洁的永久版本记录。正式的 Major / Minor 版本条目可列出主要 Phase、Capability、Main changes 和 Tests；Patch 版本只记录主要修复、小功能和 Tests。完整过程继续保存在 Development Reports、QA Reports 和 Release Notes 中。

### V3.0.0 RC1

**Project-level Maintenance Core Foundation**

主要 Phase：

- Phase 0 — Engineering Baseline
- Phase 1 — Domain Core
- Phase 1.1 — Stable Symbol Identity
- Phase 2 — Processor Migration
- Phase 3.1 — Project Scanner
- Phase 3.2 — Project Graph
- Phase 3.3 — Project Snapshot
- Phase 4 — Project Analysis Engine
- Phase 4.1 — Provider / BYOK Foundation

主要更新：Engineering baseline、Stable `SymbolId`、Project Scanner、Project Graph、Project Snapshot、Deterministic Analysis Engine、BYOK 和 Task-scoped Provider isolation。

Tests: **129 passed**。

### Historical Releases

以下记录属于 V2 历史版本，不代表当前 V3 测试基线。

- **V2.4.1**：macOS 与移动端响应式适配；历史回归记录为 **139 tests passed**。
- **V2.4.0**：多 Provider / 多模型动态切换与运行时 API Key 管理。
- **V2.3.x**：Diff、进度与取消、导航大纲、API 预检与成本估算、批量输出命名、工作区和风格检查。
- **V2.2.x**：多语言 UI、注释翻译、批量处理和注释风格模板。
- **V2.1.x**：Java 支持、分语言目录与前端交互改进。
- **V2.0.0**：模块化重构、并发生成和基础质量分析。
- **V1.0.0**：初始 Python 注释与 Markdown API 文档生成版本。

## Engineering Documentation

- `docs/development/`：Phase Development Reports 与 Release Engineering Gates
- `docs/qa/`：独立 QA Reports
- `PROJECT_CONTEXT.md`：当前架构、边界、已知债务与版本规划
