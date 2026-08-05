# 代码注释与 API 文档自动生成 Agent

基于 DeepSeek 大模型 + Gradio 构建的 Python 代码自动注释工具。通过 AST 解析提取函数和类定义，调用 LLM 生成 Google 风格中文文档字符串（docstring），并自动生成 Markdown API 文档。

## 功能特性

### 核心功能
- **自动注释**：为 Python 函数和类生成 Google 风格中文 docstring
- **AST 解析**：精准提取顶级函数、异步函数和类定义（递归包含类内部方法）
- **双模式输入**：支持直接粘贴代码或上传 `.py` 文件
- **文件下载**：支持下载注释后的 `.py` 文件和 Markdown API 文档
- **实时日志**：处理过程可视化，显示每个函数/类的注释状态

### 性能优化
- **并发调用**：使用线程池并发调用 LLM，10 个节点处理时间从 30 秒缩短至 7 秒
- **增量更新模式**：跳过已有 docstring 的函数，避免重复处理，节省 API 调用
- **LLM 调用重试**：API 失败时自动重试 3 次（带退避），避免网络抖动导致处理失败

### 代码分析
- **代码质量分析**：圈复杂度、嵌套深度、函数长度、参数数量检测，标记"坏味道"代码
- **类型注解检查**：识别缺失类型注解的参数和返回值（自动排除 `self`/`cls`/`__init__`）
- **代码摘要生成**：调用 LLM 为整个 .py 文件生成模块功能、核心类、依赖关系的摘要

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek Chat API |
| Web 框架 | Gradio |
| 代码解析 | Python AST 模块 |
| 并发处理 | ThreadPoolExecutor |
| 环境管理 | python-dotenv |

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://gitee.com/GuowangKako/code-comments---agent.git
cd code-comments---agent

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# Linux/macOS
source .venv/bin/activate

# 安装依赖
pip install openai gradio python-dotenv
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，并填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

```env
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

> API Key 申请地址：https://platform.deepseek.com/

### 3. 启动程序

```bash
python main.py
```

启动后浏览器访问 `http://127.0.0.1:7860` 即可使用。

## 使用说明

1. **上传文件**：点击左侧"上传 Python 文件 (.py)"按钮，选择 `.py` 文件，代码自动填充到输入框
2. **粘贴代码**：也可以直接在代码输入框中粘贴 Python 代码
3. **生成注释**：点击"生成注释与文档"按钮
   - 可勾选"增量更新模式"跳过已有注释的函数
4. **分析代码**：点击"分析代码"按钮，查看质量报告、类型注解检查、代码摘要
5. **查看结果**：
   - 📄 带注释的代码（可下载 .py）
   - 📚 API 文档（可下载 .md）
   - 🔍 代码分析（质量报告 + 类型注解 + 摘要）
   - 📋 处理日志
6. **下载文件**：
   - 下载注释后的 `.py` 文件
   - 下载 API 文档 `.md` 文件

## 项目结构

```
code-comments---agent/
├── main.py            # 入口文件（启动 Gradio 服务）
├── config.py          # 配置模块（API Key、模型参数、重试/并发配置）
├── parser.py          # AST 解析模块（提取函数/类定义）
├── llm_service.py     # LLM 调用模块（docstring 生成、代码摘要，含重试）
├── annotator.py       # 注释插入模块（docstring 插入 + Markdown 文档生成）
├── analyzer.py        # 代码分析模块（质量分析 + 类型注解检查）
├── processor.py       # 主处理模块（并发生成 + 串行插入 + 文件处理）
├── ui.py              # Gradio 界面模块
├── .env.example       # 环境变量示例
├── .env               # 环境变量（需自行创建，不入库）
├── .gitignore         # Git 忽略规则
└── README.md          # 项目文档
```

## 工作流程

```
输入代码/上传.py文件
       │
       ▼
  AST 解析提取函数/类定义
       │
       ▼
  增量过滤（跳过已有 docstring 的节点）  ← 可选
       │
       ▼
  并发调用 LLM 生成 docstring（线程池，5 并发）
       │
       ▼
  按行号从大到小串行插入 docstring（避免行号漂移）
       │
       ▼
  输出：带注释的代码 + Markdown API 文档
       │
       ▼
  提供下载：.py 文件 + .md 文件
```

## 更新日志

### v2.0.0 — 2026-08-05

#### 架构重构
- 将单文件 `main.py`（549 行）拆分为 8 个职责清晰的模块：
  - `config.py` — 配置外置（API Key、模型参数、重试/并发配置）
  - `parser.py` — AST 解析（提取函数/类定义）
  - `llm_service.py` — LLM 调用（docstring 生成、代码摘要）
  - `annotator.py` — 注释插入与 Markdown 文档生成
  - `analyzer.py` — 代码质量分析与类型注解检查
  - `processor.py` — 主处理逻辑（并发生成 + 串行插入）
  - `ui.py` — Gradio 界面构建
  - `main.py` — 入口文件（仅 19 行）

#### 新增功能
- **增量更新模式**：跳过已有 docstring 的函数，节省 API 调用
- **并发调用优化**：使用 ThreadPoolExecutor 并发调用 LLM，处理时间从 30 秒缩短至 7 秒
- **代码质量分析**：圈复杂度、嵌套深度、函数长度、参数数量检测
- **类型注解检查**：识别缺失类型注解的参数和返回值
- **代码摘要生成**：调用 LLM 生成模块功能摘要
- **LLM 调用重试机制**：API 失败时自动重试 3 次（带退避）

#### Bug 修复
- 修复 `__init__` 方法返回值注解误报问题（约定返回 None，无需注解）
- 修复 `match/case` 语句不计入圈复杂度的问题（Python 3.10+）
- 修复 Gradio 6.0 的 `css` 参数警告（移至 `launch()` 方法）
- 修复 `_clean_docstring` 三引号清理正则未按行匹配的问题（添加 `re.MULTILINE`）
- 修复中文注释未正确包裹在三引号中导致语法错误的问题
- 修复代码过长时文本框被拉长的问题（添加滚动条）
- 修复类型注解检查误判 `self`/`cls` 参数的问题

### v1.0.0 — 初始版本
- 基础功能：AST 解析、LLM 注释生成、Gradio 界面
- 支持文件上传与下载
- Markdown API 文档生成
