# Code Comments Agent

**当前版本：V3.0.1（`3.0.1`）— Stable Release**

Code Comments Agent 正在演进为面向项目级代码理解与智能维护的 **LLM-assisted Software Maintenance Platform**。V3.0.1 在 V3 项目级维护核心上增加可选的 Managed AI Access 与 Credits 基础设施，同时完整保留 BYOK。当前版本是正式稳定版。

## Available Features

### 用户与开发者能力

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
- **Deterministic Analysis Engine**：基于 Snapshot / Graph 执行结构、复杂度和依赖分析；不调用 LLM
- **Task-scoped Provider isolation**：任务开始时固定 Provider / Client，避免运行时配置变化影响已开始任务

### V3.0.1：Optional Managed AI Access

- Append-only Credits ledger 与标准库 `sqlite3` 持久化
- Managed request reservation、幂等与失败状态管理
- Provider、Model、输入/输出 Token 与最终 Credits 的 Usage Metering
- Flat / token-based `PricingPolicy`，支持确定性预留与实际用量结算
- Trusted server-side `AdminCreditService`，支持 Grant、Adjustment、Balance 与 History
- Platform Credential 隔离在可信服务端运行时

Managed AI Access 是软件维护平台的 AI access infrastructure，不是独立 Billing、Payment 或 SaaS 产品。

## BYOK

**BYOK = Bring Your Own Key。** BYOK 仍是一等能力。用户可以配置自己的 Provider、Model 和 Credential；BYOK 不需要 Credits、不扣除 Credits，也不依赖 Admin Operations。

当前 Registry 支持 DeepSeek、OpenAI、Azure OpenAI、DashScope、Moonshot 和 Custom OpenAI-compatible Provider。

BYOK 安全边界：

- `ModelConfig` 只保存 Provider、Model 和 Base URL，不含 Credential。
- `RuntimeCredential` 只用于运行时 Provider 构造，不支持普通序列化。
- Workspace 持久化白名单不保存 Credential。
- Task 开始时固定 Provider / Client；之后切换全局 Provider 只影响未来 Task。
- `.env` 是已被 Git 忽略的本地配置；Gradio 中输入的 API Key 只覆盖当前运行时设置。

## Managed AI Access

Managed AI Access 是 BYOK 之外的可选路径：可信服务端 Provider 可代表用户执行 LLM 请求，并配合 Credits、Reservation、Usage Metering 和 Pricing 完成结算。Platform Credential 只存在于 server-side runtime，不进入 Client、Workspace、普通配置、SQLite billing records 或 Logs。

Credits 由不可变 `CreditAccount`、append-only `CreditLedger` 和 `ADMIN_GRANT`、`USAGE`、`REFUND`、`ADJUSTMENT` 交易类型构成。当前可信 Admin surface 只开放 Grant 与 Adjustment，以及 Balance / History 查询；底层 `REFUND` 是会计原语，用户退款流程尚未实现。

Managed Usage 可持久化 Provider、Model、Input Tokens、Output Tokens 和 Final Credits；不会记录 Prompt、Completion、Raw Response 或 Credential。`TokenPricingPolicy` 使用 `Decimal`、`ROUND_CEILING`、Reservation upper bound 和 actual usage reconciliation。Rates 是定价抽象，不是任何厂商的商业价格表。

V3.0.1 提供本地、进程内的服务边界，未实现 production HTTP backend。

## Architecture Overview

以下为逻辑关系，不代表真实部署网络架构：

```text
BYOK Path
User Credential -> Task-scoped Provider -> LLM

Managed Path
Trusted Admin Grant -> Credits -> Managed Request -> Reservation
                    -> Provider -> Usage -> Pricing -> USAGE Ledger

Project Maintenance Core
Scanner -> Graph -> Snapshot -> Analysis Engine
```

`code_maintenance/` 不依赖 Provider、Credential、Credits 或 Managed Access。Managed Access 可以使用 Credits 与既有 Provider 基础设施；BYOK 路径与 Credits 相互独立。

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

SQLite 由 Python 标准库 `sqlite3` 提供，不需要单独安装数据库。某些 Anaconda Python 3.13 主机可能遇到 Gradio / IPython 兼容问题；遇到时请使用标准 CPython 与独立 `venv`。

## Configuration

复制环境变量示例，并用自己的 BYOK 配置替换占位值：

```bash
cp .env.example .env
```

```env
PROVIDER=deepseek
MODEL=deepseek-chat
DEEPSEEK_API_KEY=your-api-key-here
```

`.env.example` 列出了各 Provider 的变量名以及 Azure / Custom Base URL 配置。也可以在 Gradio 运行时设置中选择 Provider、Model、API Key 和允许自定义的 Base URL。

BYOK Credential 属于用户运行时配置；platform-managed Credential 属于可信 server-side runtime，两者是不同安全边界。Platform Credential 不应写入普通 `.env` 示例、Workspace 或 SQLite billing data。项目不提供 Secure Credential Store。

## Quick Start

1. Clone 仓库并创建、激活 `.venv`。
2. 运行 `python -m pip install -r requirements.txt`。
3. 通过 `.env` 或 Gradio 运行时设置配置 BYOK Provider / API Key。
4. 启动：

```bash
python main.py
```

默认访问地址为 `http://127.0.0.1:7860`。当前 Gradio UI 没有 Managed Credits 或 Admin 操作入口。

## Testing

当前 V3.0.1 Stable Release 基线：**414 passed**。

```bash
python -m pytest
```

`python -m pytest -p no:debugging` 仅是已记录的 Anaconda Python 3.13.5 主机专用 workaround，不是标准测试命令。测试不会调用真实 LLM Provider，也不需要真实 API Key。

## Directory Structure

```text
code-comments---agent/
├── main.py
├── ui.py
├── processor.py
├── config.py
├── llm_service.py
├── code_maintenance/       # V3 project maintenance core
├── credits/
│   ├── domain.py
│   ├── ledger.py
│   └── sqlite_ledger.py
├── managed_access/
│   ├── domain.py
│   ├── pricing.py
│   └── service.py
├── admin_operations/
│   ├── domain.py
│   └── service.py
├── Py/                     # legacy-compatible Python processor modules
├── Java/                   # legacy-compatible Java processor modules
├── tests/
└── docs/
    ├── development/
    ├── qa/
    └── release/
```

## Not Included in V3.0.1

- Admin UI、Authentication / RBAC、Login、Password 或 OAuth
- Payment、Recharge、`PURCHASE` 或用户 Refund workflow
- Production SaaS / HTTP backend
- RAG、Multi-Agent、Router 或 VS Code Integration

## Roadmap / Planned

- **V3.0.1 — Managed AI Access & Credits**：Released / Stable Release
- **V3.0.2 — Commercial infrastructure enhancement track**：Deferred / optional；Admin UI、Payment interface、Recharge、Auth / RBAC 均未实现
- **V3.1 — Project Intelligence / RAG**：Planned，论文主线优先
- **V3.2 — Controlled Multi-Agent Collaboration**：Planned，论文主线优先
- **V3.3 — Data-driven Multi-Model Router**：Planned
- **V3.4 — VS Code Integration**：Planned

## Version History

从 V3 开始，README 为每个正式版本及当前候选版本保留 Version、Status、Phase Summary、Major Updates 和 Test Baseline。详细工程过程位于 `docs/development/`、`docs/qa/` 和 `docs/release/`。

### V3.0.1

**Managed AI Access & Credits — Released / Stable Release（`3.0.1`）**

Phase Summary：

- Phase 0 — Architecture & Scope
- Phase 1 — Credits Domain
- Phase 2 — Managed Access Foundation
- Phase 3 — Usage Metering & PricingPolicy
- Phase 4 — Admin Operations Surface

Major Updates：Optional Managed AI Access、Credits ledger、SQLite persistence、Reservation / Idempotency、Usage Metering、Token Pricing、Admin Grant / Adjustment、BYOK preservation 与 Credential isolation。

Tests: **414 passed**。

### V3.0.0

**Project-level Maintenance Core Foundation — Released / Stable Release**

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

主要更新：Engineering baseline、Stable `SymbolId`、Processor 的 `SymbolId` 迁移、Project Scanner、Project Graph、Project Snapshot / SnapshotDiff、Deterministic Project Analysis Engine、Provider / BYOK Foundation、Task-scoped Provider isolation，以及 release engineering / QA / documentation gates。

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
- `docs/release/`：Release Notes
- `PROJECT_CONTEXT.md`：当前架构、边界、已知债务与版本规划
