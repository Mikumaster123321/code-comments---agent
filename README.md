# 代码注释与 API 文档自动生成 Agent

基于 DeepSeek 大模型 + Gradio 构建的 Python 代码自动注释工具。通过 AST 解析提取函数和类定义，调用 LLM 生成多种风格（Python：Google/NumPy/reStructuredText；Java：标准 Javadoc/极简行内注释）的中文文档字符串（docstring），并自动生成 Markdown API 文档。

## 功能特性

### 核心功能
- **自动注释**：为 Python 函数/类 和 Java 类/方法生成 docstring / Javadoc
- **多风格模板选择**：通过预定义 Prompt 模板切换注释风格，Python 支持 Google 风格 / NumPy 风格 / reStructuredText；Java 支持标准 Javadoc / 极简行内注释；翻译重组时也按目标风格输出
- **双语言支持**：同一套工具支持 Python & Java 两种主流语言，代码结构自动识别
- **双模式输入**：支持直接粘贴代码或上传 `.py` / `.java` 文件
- **批量文件处理**：支持一次上传多个 `.py`/`.java` 文件或整个 ZIP 压缩包（含递归子目录），批量生成注释后打包 ZIP 下载
- **文件下载**：支持下载注释后的源码文件和 Markdown API 文档；批量处理额外提供聚合文档 `API_DOCS_ALL.md`
- **实时日志**：处理过程可视化，显示每个函数/类/方法的注释与翻译状态

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

### 单文件模式
1. **上传文件**：点击左侧"上传源代码文件"按钮，选择 `.py` 或 `.java` 文件，代码自动填充到输入框
2. **粘贴代码**：也可以直接在代码输入框中粘贴 Python/Java 代码，手动切换对应的编程语言
3. **切换界面语言**：右上角下拉框选择 `中文` / `English` / `日本語`，生成/翻译的注释语言自动跟随
4. **生成注释**：点击"🚀 生成注释与文档"按钮（默认开启增量更新模式，跳过已是目标语言的注释）
5. **分析代码**：点击"🔍 分析代码"按钮，查看质量报告、类型注解检查、代码摘要
6. **查看结果**：
   - 📄 带注释的代码（可下载源码文件）
   - 📚 API 文档（可下载 `.md` 文件）
   - 🔍 代码分析（质量报告 + 类型注解 + 摘要）
   - 📋 处理日志
7. **下载文件**：
   - 下载注释后的源码文件
   - 下载 Markdown 文档

### 批量处理模式（多文件 / ZIP）
1. **批量上传**：在"📦 批量处理（多文件 / ZIP 压缩包）"区域点击批量上传按钮
   - 方式 A：一次选择多个 `.py` / `.java` 文件
   - 方式 B：选择一个 `.zip` 压缩包（内部可含嵌套子目录，自动递归扫描）
   - 两种方式可混合使用（已上传文件 + ZIP）
2. **切换界面语言**（可选）：右上角切换语言，批量生成/翻译的注释语言同步跟随
3. **批量生成**：点击"🚀 批量生成注释并打包下载"按钮，工具会：
   - 自动解压 ZIP（含 Windows 中文文件名编码修复，防止 zip slip 路径穿越）
   - 按 `.py` / `.java` 扩展名分类
   - 使用线程池并发调用 LLM 生成或翻译注释
   - 所有文件处理完成后自动打包结果 ZIP
4. **下载结果**：点击"📥 下载批量处理结果 (ZIP)"下载 ZIP 包，其中包含：
   - 每个源文件对应的注释版源码（保持原目录结构）
   - `processing.log`：每个文件的详细处理日志（跳过/生成/翻译/失败）
   - `API_DOCS_ALL.md`：所有文件的 API 文档聚合版（含翻译后的注释代码片段）

## 项目结构

```
code-comments---agent/
├── main.py            # 入口文件（启动 Gradio 服务）
├── config.py          # 配置模块（API Key、模型参数、重试/并发配置）
├── llm_service.py     # LLM 调用模块（docstring/Javadoc 生成、翻译、摘要；含重试）
├── processor.py       # 主处理模块（单文件调度 + 批量处理/ZIP 打包下载）
├── ui.py              # Gradio 界面模块（布局、事件绑定、i18n 语言切换）
├── i18n.py            # 国际化模块（中/英/日 三种界面语言文案）
├── Py/                # Python 专用模块
│   ├── parser.py      # AST 解析（提取函数/类定义）
│   ├── annotator.py   # docstring 插入 + Markdown 文档生成
│   └── analyzer.py    # 代码质量分析 + 类型注解检查
├── Java/              # Java 专用模块
│   ├── java_parser.py    # 正则解析（提取类/方法/构造器/内部类/匿名类）
│   └── java_annotator.py # Javadoc 插入 + Java API Markdown 文档生成
├── .env.example       # 环境变量示例
├── .env               # 环境变量（需自行创建，不入库）
├── .gitignore         # Git 忽略规则
└── README.md          # 项目文档
```

## 工作流程

### 单文件模式

```
输入代码/上传.py/.java文件
       │
       ▼
  AST/正则 解析提取函数/类定义（按文件类型选择解析器）
       │
       ▼
  增量过滤（跳过已是目标语言的注释节点）  ← 默认开启
       │
       ├─ 无注释 → 并发调用 LLM 生成注释
       │
       └─ 已有注释语言不匹配 → 调用 LLM 翻译为目标语言
       │
       ▼
  按行号从大到小串行插入 docstring/Javadoc（避免行号漂移）
       │
       ▼
  输出：带注释的代码 + Markdown API 文档
       │
       ▼
  提供下载：源码文件 + .md 文件
```

### 批量处理模式（多文件 / ZIP）

```
多文件 + ZIP 上传
       │
       ▼
  安全解压 ZIP（路径穿越防护 + 中文文件名编码修复）
       │
       ▼
  递归扫描所有 .py/.java 文件（保持原目录结构）
       │
       ▼
  线程池并发处理文件（每个文件走单文件流程）
       │
       ▼
  收集：注释后源码 + 每个文件的 API 文档 → 合并到聚合文档 API_DOCS_ALL.md
       │
       ▼
  打包所有结果为 ZIP（含 processing.log）
       │
       ▼
  一键下载 ZIP 包
```

## 更新日志

### v2.5.0 — 2026-08-07

#### 注释风格模板选择（Python 3 种 + Java 2 种）
- 新增 5 种注释风格，通过预定义 Prompt 模板灵活切换：
  - **Python**：Google 风格（Args/Returns/Raises）/ NumPy 风格（Parameters/Returns + 类型短横线分隔）/ reStructuredText（:param/:type/:return/:rtype）
  - **Java**：标准 Javadoc（/** ... */ + @param/@return/@throws）/ 极简行内注释（单行短注释 `// xxx`，用于小型项目快速生成）
- `llm_service.py` 提供 `PYTHON_STYLE_*` / `JAVA_STYLE_*` 风格常量，生成与翻译流程统一走风格规则注入：
  - 生成时按目标风格追加格式要求；翻译/重组时按目标风格重排输出结构
  - 默认风格保持不变（Python 默认为 Google 风格，Java 默认为标准 Javadoc），向下兼容 v2.x API
- `processor.process_code` 与 `process_batch_files` 新增 `python_style` / `java_style` 可选参数，风格信息从 UI 一路透传到 LLM 层
- Gradio UI 新增"注释风格选择"分区：两个并列下拉框（Python 风格 / Java 风格），三语 i18n 文案同步更新
- 新增 `test_styles.py` 单元测试（14 条），离线 mock LLM 调用即可验证：5 种风格 prompt 关键词注入、翻译规则适配、默认风格行为、processor 参数链路不报错（全部通过）

#### 兼容性
- 修复 Python 3.8 类型注解问题：`llm_service.py` / `processor.py` 顶部添加 `from __future__ import annotations`，并把 `str | None` 改为 `Optional[str]`，在 3.8 环境下正常 import

### v2.4.0 — 2026-08-07

#### 批量文件/文件夹处理功能
- 新增批量上传入口：支持一次选择多个 `.py` / `.java` 文件，或上传整个 `.zip` 压缩包（支持递归子目录）；两种方式可混合使用
- 新增 `process_batch_files` 批量处理调度器：
  - 安全解压 ZIP（内置 zip slip 路径穿越防护，兼容 Windows 下中文文件名编码问题：UTF-8 失败时自动回退 `cp437 → GBK` 解码）
  - 按扩展名自动分流到 Python / Java 解析器
  - 使用 `ThreadPoolExecutor` 并发调用 LLM，多文件总耗时显著降低
  - 保持原目录结构写出注释后的源码文件，方便用户直接覆盖
- 结果打包 ZIP 自动包含：
  - 所有源文件的注释版（保持目录结构）
  - `processing.log`：按文件逐行记录跳过 / 生成 / 翻译 / 失败明细
  - `API_DOCS_ALL.md`：所有文件 API 文档的聚合版，代码块内嵌注释同步到最终语言
- 新增批量处理 UI 区域：批量上传组件、批量生成按钮、批量下载按钮、批量日志文本框，UI 文案跟随界面语言三语翻译

#### 翻译与 Markdown 文档一致性修复
- 修复翻译注释时按原行号升序插入导致的后续节点 `lineno` 错位、`clean_text/__init__/register/login` 等函数插入失败的 bug：改为与生成流程一致的**行号倒序**插入
- 修复 `build_markdown_docs` / `build_java_markdown_docs` 中硬编码中文标题（"API 文档"、"类"、"函数"、"方法"）导致 EN/JA 界面聚合文档语言检测失败的问题：改为通用英文标题
- 修复聚合文档 `API_DOCS_ALL.md` 内嵌代码块保留原始中文注释问题：所有注释插入完成后，统一从最终 `annotated_code` 重新解析 AST / Java 结构并刷新每个 `doc_entries[i].code`，确保 Markdown 代码块与最终源码一致

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
