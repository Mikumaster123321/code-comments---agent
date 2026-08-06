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

### v2.3.0 — 2026-08-07

#### 多语言支持（i18n）
- 右上角新增语言切换下拉框（中文 / English / 日本語），一键切换整个界面语言
- 生成的注释语言跟随界面语言：英文界面生成英文注释，日文界面生成日文注释
- 已有注释自动翻译：增量模式下自动检测注释语言，若与目标语言不一致则调用 LLM 翻译为对应语言
- 字符集智能检测：支持中日英（汉字 / 假名 / 拉丁字符）自动判定是否需要翻译
- 修复多语言下 DownloadButton 标签不更新、输出代码框标签未翻译等问题

#### 交互优化
- 增量更新模式改为默认永久开启，移除界面勾选框，操作更简洁
- 点击"生成注释与文档"自动跳转到"带注释的代码"标签页
- 点击"分析代码"自动跳转到"代码分析"标签页
- 移除遮挡滚动条的原生下载/复制按钮，改为输出下方并排的"下载注释后的代码"与"下载文档"两个美化按钮

### v2.2.0 — 2026-08-06

#### 前端界面重构
- 代码编辑器统一为白底、深色文字、中性灰边框的亮色主题
- 编辑器支持显示滚动条（overflow: auto），长代码不再被拉伸
- 优化整体布局与样式：卡片容器、Tab 导航、按钮、滚动条全面美化
- 修复 Gradio 6.0 下代码编辑器显示"错误"、Java 编辑器切换语言显示"错误"的问题

#### 代码有效性验证
- 新增代码有效性校验：分析前先验证代码结构（函数/类/导入/控制流/赋值）
- 无效或无意义的代码（如纯字符串）直接返回友好提示，不再触发 LLM，避免幻觉内容（如 SVM 误判）

#### 测试与结构
- 新增端到端测试用例（上传、分析、注释、下载、无效代码验证）
- 精简目录结构，删除冗余开发脚本，核心模块收敛为 `main.py`、`ui.py`、`processor.py`、`llm_service.py`、`config.py`、`i18n.py`

### v2.1.0 — 2026-08-06

#### Java 语言支持
- 新增 Java 代码解析器，支持类、方法、构造器、枚举、内部类、匿名类（排除匿名类实例化误判）
- 新增 Javadoc 注释自动生成，支持 `@param`、`@return`、`@throws` 标签
- 支持复杂嵌套 Java 代码（接口、泛型、静态嵌套类、Lambda 等）
- 新增 Java 代码有效性验证（大括号匹配校验，屏蔽字符串中的括号）

#### 目录结构优化
- 按语言和功能分文件夹组织：`Py/`（Python 解析/注释/分析）、`Java/`（Java 解析/注释）
- 修复 Java 解析器排除匿名类实例化（`new ClassName() { ... }`）的问题

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
