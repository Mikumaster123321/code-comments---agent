# 代码注释与 API 文档自动生成 Agent

**当前版本：v2.4.1**（2026-08-12 · v2.4.0 的小更新 · macOS + 手机端响应式自适应）

基于 **多 LLM Provider（DeepSeek / OpenAI / Azure / 阿里百炼 / 月之暗面 / 自定义 OpenAI 兼容网关）** + Gradio 构建的 Python & Java 代码自动注释工具。通过 AST/正则解析提取函数和类定义，调用 LLM 生成多种风格（Python：Google/NumPy/reStructuredText；Java：标准 Javadoc/极简行内注释）的文档字符串（docstring/Javadoc），并自动生成 Markdown API 文档。

## 功能特性

### 核心功能
- **自动注释**：为 Python 函数/类 和 Java 类/方法生成 docstring / Javadoc
- **多风格模板选择**：通过预定义 Prompt 模板切换注释风格，Python 支持 Google 风格 / NumPy 风格 / reStructuredText；Java 支持标准 Javadoc / 极简行内注释；翻译重组时也按目标风格输出
- **代码差异 Diff 视图**：新增并排 Split Diff（GitHub 风格）Tab，左栏 Before（注释前原始代码）/ 右栏 After（注释后），新增行绿色高亮、删除行红色高亮、行号对齐、顶部显示 +N 插入 / -M 删除 / K 未变统计，一目了然哪些函数被加了注释
- **双语言支持**：同一套工具支持 Python & Java 两种主流语言，代码结构自动识别
- **双模式输入**：支持直接粘贴代码或上传 `.py` / `.java` 文件
- **批量文件处理**：支持一次上传多个 `.py`/`.java` 文件或整个 ZIP 压缩包（含递归子目录），批量生成注释后打包 ZIP 下载
- **文件下载**：支持下载注释后的源码文件和 Markdown API 文档；批量处理额外提供聚合文档 `API_DOCS_ALL.md`
- **实时日志**：处理过程可视化，显示每个函数/类/方法的注释与翻译状态
- **实时进度条 & 可取消任务**：`gr.Progress` 内置进度条实时显示百分比 + 阶段描述（解析 / 翻译 / 调用 LLM / 插入 / 构建 / 打包）；随时点击"取消任务"按钮立即停止，取消后仍保留并打包已完成部分，不丢已处理结果
  - 单文件 & 批量任务均支持进度条 + 取消按钮（variant=stop）
  - 取消时立即对所有未完成的 LLM 调用调用 `future.cancel()` + `shutdown(wait=False)`，避免浪费 token

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
| LLM Provider | DeepSeek / OpenAI / Azure / 阿里百炼（DashScope） / 月之暗面（Moonshot Kimi） / **自定义 OpenAI 兼容网关**（Ollama / vLLM / OneAPI / LM Studio 等） |
| Web 框架 | Gradio |
| 代码解析 | Python AST 模块 / Java 正则解析 |
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

### 2. 配置 Provider / Model / API Key

复制 `.env.example` 为 `.env`，选择你使用的 Provider 并填入对应 API Key（也可在 UI 中运行时切换，不写入文件）：

```bash
cp .env.example .env
```

#### 启动默认 Provider / Model（.env 全局默认，启动后 UI 可随时切换）

```env
# 可选：deepseek | openai | azure | dashscope | moonshot | custom
PROVIDER=deepseek
# 模型名可留空（取对应 Provider 的第一个默认）；UI 切换覆盖此值
MODEL=deepseek-chat
```

#### 各 Provider 的 API Key（按优先级，第一个非空生效）

| Provider | 环境变量名（优先级从高到低） | 官网 / 获取地址 |
| --- | --- | --- |
| **DeepSeek**（默认推荐） | `DEEPSEEK_API_KEY` → `OPENAI_API_KEY` | https://platform.deepseek.com |
| **OpenAI 官方** | `OPENAI_API_KEY` | https://platform.openai.com |
| **Azure OpenAI** | `AZURE_OPENAI_API_KEY` → `OPENAI_API_KEY` | https://portal.azure.com → Azure OpenAI → Keys and Endpoint<br/>**必须配置 `BASE_URL`**：`https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOYMENT` |
| **阿里百炼 / Qwen** | `DASHSCOPE_API_KEY` → `ALIBABA_API_KEY` → `OPENAI_API_KEY` | https://bailian.console.aliyun.com |
| **月之暗面 / Kimi** | `MOONSHOT_API_KEY` → `KIMI_API_KEY` → `OPENAI_API_KEY` | https://platform.moonshot.cn |
| **Custom（本地/自建网关）** | `OPENAI_API_KEY` | Ollama / vLLM / LM Studio / OneAPI 等本地/内网 OpenAI 兼容网关<br/>**必须配置** `BASE_URL=http://localhost:8000/v1` + `CUSTOM_MODEL_NAME=qwen2.5-72b-instruct` |

> 🔐 **安全提示**：UI 中「🔑 API Key」输入框仅运行时内存覆盖，**绝不会写入 .env 或 tempfile 工作区**（会话持久化保存白名单也排除了 api_key 字段）。

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

> **版本号规则**：大版本 `vX.Y.0` 仅记录"技术含量极强/新增底层架构能力"的重要更新；小更新 `vX.Y.1`、`vX.Y.2` … 不单独占据"大版本位"，归入最近一次大版本的"小更新"子节按时间倒序排列。大版本列表：v1.0.0（初始）→ v2.0.0（架构重构+并发+质量分析）→ v2.1.0（Java 支持+目录结构分语言）→ v2.2.0（i18n 三语+注释翻译）→ v2.3.0（Diff Split 视图）→ **v2.4.0（多 Provider / 多模型切换底层能力）**。

### v2.4.1 — 2026-08-12（v2.4.0 小更新 #1）

#### 📱 macOS + 手机端响应式自适应
旧版 CSS 仅针对桌面端 Windows 高分屏设计，在 macOS 和手机浏览器上字体回退不美观、滚动条偏粗、布局元素溢出。本次更新为 CSS 纯注入，零新增依赖、零组件结构变更。

##### 1. macOS 字体栈优化
- **全局字体**：`-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'PingFang SC', 'Hiragino Sans GB'` 优先于 `'Segoe UI', 'Microsoft YaHei'`，macOS 上自动使用 San Francisco / 苹方，Windows 回退 Segoe UI / 雅黑
- **代码等宽字体**：`'SF Mono', 'Monaco', 'Menlo'` 优先于 `'Fira Code', 'Consolas'`，macOS 上使用 SF Mono，Windows 回退 Consolas
- **大纲折叠区 code 标签**：同步更新等宽字体栈

##### 2. macOS 滚动条适配
- `@media (-webkit-min-device-pixel-ratio: 1) and (pointer: fine)` 媒体查询下，滚动条宽度从 10px 细化为 8px
- `.cm-scroller::-webkit-scrollbar:vertical` 添加 `-webkit-appearance: none`，让 macOS overlay 滚动条不与自定义样式冲突

##### 3. 三档断点响应式布局

| 断点 | 适用设备 | 主要调整 |
| --- | --- | --- |
| `max-width: 1024px` | iPad / 平板 | 容器全宽 / header 内边距缩小 / 代码编辑器 500px / 语言切换器 140px |
| `max-width: 768px` | 手机横屏 / 大手机竖屏 | header 垂直堆叠 / 等宽列垂直排列 / 编辑器 380px / 按钮全宽垂直 / Tab 水平滚动 / 下载按钮垂直 / 卡片圆角缩小 |
| `max-width: 480px` | iPhone SE / Android compact | 进一步压缩：header 17px / 编辑器 300px 12px 字号 / 卡片 8px 圆角 / Tab 12px 字号 |

##### 4. 触控设备优化
`@media (hover: none) and (pointer: coarse)` 媒体查询下（触控手机/平板）：
- 禁用 `.card-section:hover` 的 transform 和阴影增强（避免误触闪烁）
- 禁用 `.action-btn:hover` / `.dl-download-btn:hover` 的悬浮位移
- 禁用 `.outline-sidebar summary:hover` 的背景色变化

##### 兼容性
- **纯 CSS 注入**，零 Python 代码变更、零新增第三方依赖
- 所有 Gradio 组件 id / class / 事件绑定零修改，已有测试零侵入
- py_compile（ui.py）0 SyntaxError
- 139 条测试全部通过，0 Failing

##### 测试覆盖
回归测试：`test_provider_model (52) + test_style_lint (31) + test_workspace_persistence (25) + test_outline_collapsible (15) + test_batch_naming (16)` = **139 条全通过，0 Failing**。

### v2.4.0 — 2026-08-11（大版本：多 Provider / 多模型切换 + 运行时 API Key 管理）

> 用户不止一个 API Key，或想在 DeepSeek / GPT / Qwen / Kimi 之间切换测试不同注释质量；之前 `config.py` 硬编码只有 DeepSeek，扩展性受限。

#### 1. config.py 底层重构：`PROVIDERS` 统一字典 + 动态 client 工厂

集中定义 **6 种 OpenAI 兼容协议 Provider**（DeepSeek / OpenAI / Azure / 阿里百炼 DashScope / 月之暗面 Moonshot Kimi / Custom），每项包含完整元数据：

| 字段 | 说明 |
| --- | --- |
| `label_zh / label_en / label_ja` | 三语显示名，UI 下拉框本地化 |
| `api_key_env` | list[str]，按优先级查找环境变量；第一个非空生效 |
| `base_url` | 默认 API Endpoint；Azure/Custom 支持用户自定义 |
| `models` | dict[model_name→显示名]，UI 联动刷新 |
| `price_input_per_m / price_output_per_m` | 输入/输出单价（元 / 1M tokens）；Token 成本估算按当前 Provider 动态取值 |
| `customizable_base_url` | bool；仅 Azure / Custom 允许改 base_url，其余强制走官方 Endpoint |

**线程安全的运行时状态**：`_lock = threading.RLock()` 保护 `_active_provider / _active_model / _active_api_key / _active_base_url / _custom_model_name`；切换时调用 `_rebuild_client()` 重建 `openai.OpenAI` client 实例。

**公开 API（UI 与 llm_service 只调这里，禁止直接改模块全局）**：

| 函数 | 用途 |
| --- | --- |
| `get_providers(lang)` | 返回 [(label, key)] 下拉框数据（按 lang 本地化 label） |
| `get_models_for_provider(pkey, lang)` | 指定 Provider 的模型列表；Custom 下带 ✏️ 用户自定义模型首项 |
| `switch_provider(pkey, model_key, api_key, base_url, custom_model_name)` | 原子切换；返回 `(ok, msg)` |
| `set_api_key(key)` / `set_custom_base_url(url)` | 单独更新 API Key / Base URL |
| `get_active_provider/model/client/base_url()` | 活动 getter；`get_active_client()` 每次调用都拿最新实例，保证 UI 切换后下一次请求立即生效 |
| `get_price_input_per_m()` / `get_price_output_per_m()` | 当前 Provider 单价（成本估算用） |
| `is_active_provider_customizable()` | 判断当前 Provider 是否允许改 base_url（UI 锁定/解锁 `base_url_tb` + `custom_model_tb`） |

**启动期 .env 初始化**：读 `PROVIDER`（非法值回退 deepseek 不报错）→ 读 `MODEL`（不在列表回退默认第一个）→ 读 `BASE_URL`（仅 customizable Provider 生效）→ 读 `CUSTOM_MODEL_NAME`（仅 custom）。

**向后兼容 `__getattr__`**：仍暴露 `client` / `MODEL` / `PRICE_INPUT_PER_M` / `PRICE_OUTPUT_PER_M` 等顶层名字（模块级 getattr 动态计算），保证 `from config import client, MODEL` 的旧代码零修改运行。

#### 2. llm_service 去常量：全部动态 getter

`llm_service.py` 不再 `from config import client, MODEL, PRICE_*`，改为：
- `client` → `_cfg.get_active_client()`
- `MODEL` → `_cfg.get_active_model()`
- `PRICE_INPUT_PER_M / PRICE_OUTPUT_PER_M` → `_cfg.get_price_input_per_m() / get_price_output_per_m()`
- 结果：**UI 切换 Provider/Model/单价 → 下一次 LLM 请求立即生效，无需重启进程**
- `ping_api_key` 错误提示从「请检查 DEEPSEEK_API_KEY」升级为更通用的「请检查对应 Provider 的 API Key 环境变量」

#### 3. UI 新增「🔐 Provider / 模型切换」独立区块

在「注释风格选择」card 正下方、「代码输入」card 正上方新增 6 个组件（三语 i18n + 联动事件）：

| 组件 | 类型 | 说明 |
| --- | --- | --- |
| `provider_section_md` | Markdown | 小节标题 |
| `provider_dd` | Dropdown（6 选 1，不可自定义值） | Provider 切换；.change 联动刷新 model_dd + base_url_tb（interactive + 默认值） + custom_model_tb（interactive） + provider_info_md |
| `model_dd` | Dropdown（可自定义值） | 模型名；跟随 provider_dd 自动刷新 choices；Custom 下若填入自定义名后通过 apply 会成为下拉首项 |
| `api_key_tb` | Textbox（password 类型） | 留空 → 使用 .env 环境变量；非空 → 仅运行时内存覆盖（**不写文件**） |
| `base_url_tb` | Textbox | 仅 Azure / Custom 可编辑；其余 Provider 灰掉并显示官方默认 Endpoint |
| `custom_model_tb` | Textbox | 仅 Custom Provider 可编辑；填写后 apply 成为模型名 |
| `apply_provider_btn` | Button（primary） | 点击调用 `config.switch_provider(...)`，返回结果写 `provider_status_md`；成功后同步 model_dd.choices/value 和 base_url/custom_model 锁定状态 |
| `provider_status_md` | Markdown | ✅ 成功 / ❌ 失败消息 |
| `provider_info_md` | Markdown | 实时显示「Provider=`x` · Model=`y` · Endpoint=`z`」 |

**ui_lang 切换同步**：`_apply_ui_language` 返回列表追加 43-51 号（共 9 项），`ui_lang.change(outputs=...)` 同步追加 9 个组件引用。

#### 4. .env.example 大更新 + Provider 文档表

`.env.example` 从单行 `DEEPSEEK_API_KEY=` 扩展为 5 大部分：
1. `PROVIDER` / `MODEL` / `BASE_URL` / `CUSTOM_MODEL_NAME` 全局默认变量说明 + 每个 Provider 的可选模型名列表
2. 按 Provider 分段的 API Key 环境变量（DEEPSEEK/OPENAI/AZURE/DASHSCOPE/MOONSHOT），每个变量注明官网获取地址

#### 5. i18n 三语 16 个新增 key

`provider_section` / `provider_label` / `model_label` / `api_key_label` / `api_key_placeholder` / `base_url_label` / `base_url_placeholder` / `custom_model_label` / `apply_provider_btn` / `provider_status_ok` / `provider_status_err` / `current_provider_info` / `api_key_status_ok` / `api_key_status_err` — 中文 / English / 日本語 全覆盖。

#### 兼容性

- **零破坏性改动**：所有旧 API 保持签名不变；`__getattr__` 兼容层保证旧 import 语句正常工作
- `analyze_code` 返回 5 元组、processor 批量命名策略、会话持久化等 v2.3.x 功能零侵入
- py_compile（config / llm_service / i18n / ui / processor）0 SyntaxError
- 87 条已有测试全部通过（test_workspace_persistence + test_style_lint + test_batch_naming + test_outline_collapsible）

#### 测试覆盖（`test_provider_model.py` 共 **52** 用例，全通过）

| 类（9 个） | 用例数 | 覆盖范围 |
| --- | --- | --- |
| TestProvidersDict | 6 | 6 个 Provider key 存在 / 每个 9 字段齐全 / 单价非负 / models 非空 / customizable 只有 azure+custom / api_key_env list 非空 |
| TestProviderLabelLocalization | 4 | 中/英/日三语 label / 未知 Provider 回退 key 本身 |
| TestPublicGetters | 10 | get_providers 结构 / EN 标签 / 各 Provider 模型 / 未知 Provider 空 / 默认 provider / 默认 model / 默认 base_url / customizable false / 单价匹配 |
| TestSwitchProvider | 9 | 切 openai 成功 / 指定 model / 非法 Provider 失败不变更 / 切 azure 更新 base_url / custom + base_url + 自定义模型名 / api_key='' 重置 env / 非 customizable 传 base_url 被忽略 / moonshot 单价 / dashscope 单价 |
| TestSetApiKeyAndBaseUrl | 6 | 正常 set_api_key / 空串重置 / deepseek 改 base_url 拒绝 / azure 改 base_url 成功 / None 回退默认 / 末尾斜杠去除 |
| TestCompatGetAttr | 7 | client 是 openai.OpenAI 实例 / MODEL 与 getter 一致 / 切换后 MODEL 变化 / PRICE_INPUT / PRICE_OUTPUT / 切 moonshot 单价同步 / 未知属性抛 AttributeError |
| TestLLMServiceDynamic | 5 | 切换 Provider 后 estimate 成本变化（Moonshot < DeepSeek） / 0 items 零向量 / -10 items 零向量 / Custom 零单价 / 自定义 avg_tokens |
| TestCustomProviderModels | 2 | 默认无自定义模型首项 / 切换后首项带 ✏️ 前缀 |
| TestProviderMeta | 3 | get_active_client 同一实例缓存 / _lock 是 RLock 实例 / 切换后 client 实例不同 |

**回归测试**：`test_provider_model (52) + test_style_lint (31) + test_workspace_persistence (25) + test_outline_collapsible (15) + test_batch_naming (16)` = **139 条全通过，0 Failing**。

### v2.3.8 — 2026-08-10（v2.3.0 小更新 #8）

#### 🛑 代码风格检查（PEP8 / Google Java Style）
在「代码分析」Tab 新增「代码风格」区块，分析代码时自动检测风格问题并以 Markdown 表格展示。

##### Python 侧（PEP8）
- **优先使用 `pycodestyle`**（如已安装）：专业 PEP8 检查器，覆盖 E1xx/E2xx/E3xx/E5xx/W1xx/W2xx 等全部规则
- **降级方案**（pycodestyle 不可用时）：`_lint_python_basic` 正则近似检查：
  - `E501` 行过长（>100 字符）
  - `W291` 尾随空格
  - `W292` 文件末尾无换行符
  - `W191` Tab 缩进（应使用 4 空格）
  - `E221` 多余空格（连续 2+ 空格）
  - `E303` 空行过多（>2 连续空行）
- 报告中标注实际使用的工具名（`pycodestyle (PEP8)` 或 `PEP8 basic (regex fallback)`）

##### Java 侧（Google Java Style 正则近似，无 JDK 依赖）
`_lint_java_regex` 检查 7 类规则：

| 规则 | 描述 |
| --- | --- |
| GJL001 | 行过长（>100 字符） |
| GJL002 | 尾随空格 |
| GJL003 | Tab 缩进（Google Style 要求 2 空格） |
| GJL004 | 逗号/分号后缺少空格 |
| GJL005 | 大括号前缺少空格（如 `if(){` → `if () {`） |
| GJL006 | 空行过多（>2 连续空行） |
| GJL007 | 文件末尾无换行符 |

##### 集成方式
- `analyze_code` 返回值从 **4 元组 → 5 元组**：`(quality_report, annotation_report, summary, style_report, log_text)`
- 风格检查在质量分析和类型注解检查之后、LLM 摘要生成之前执行（非 LLM 调用，零延迟）
- `_analyze_java` 同步改造，Java 代码无效时 style_report 返回「跳过风格检查」占位
- UI 分析 Tab 在 `annotation_output` 与 `summary_output` 之间新增 `style_title_md` + `style_output`
- `analyze_btn.click` outputs 从 4 → 5（追加 `style_output`）
- `_apply_ui_language` 和 `ui_lang.change` outputs 同步追加 `style_title_md`（index 16），后续所有索引 +1

##### i18n
- 新增 `style_title` key 三语文案

##### 兼容性
- `pycodestyle` 为可选依赖（`pip install pycodestyle`），不可用时自动降级，不报错
- 零新增必需第三方依赖
- `analyze_code` 返回值从 4→5 元组：所有调用方需适配（UI 已同步更新）

##### 测试覆盖（`test_style_lint.py` 共 31 用例，全通过）
| 类 | 用例数 | 覆盖 |
| --- | --- | --- |
| T1_PythonStyleLint | 10 | 行过长 / 尾随空格 / Tab 缩进 / 缺换行 / 空行过多 / 标题 / 工具名 / 空源码 / English / 日本語 |
| T2_JavaStyleLint | 8 | Tab 缩进 / 逗号缺空格 / 大括号缺空格 / 行过长 / 缺换行 / 工具名 / 直接测 _lint_java_regex 结构 / 空行过多 |
| T3_CleanCode | 2 | Python 干净代码 0 issues / Java 干净代码 0 issues |
| T4_AnalyzeCodeReturn5 | 6 | Python/Java/空代码/无效 Python/无效 Java 均返回 5 元组 + 风格报告内容正确 |
| T5_I18n | 1 | style_title 三语存在非空 |
| T6_UiComponents | 4 | ui.py 声明组件 / analyze_btn 5 outputs / _apply_ui_language 引用 / ui_lang.change 引用 |

**回归测试**：`test_style_lint (31) + test_workspace_persistence (25) + test_outline_collapsible (15) + test_batch_naming (16)` = 87 条全通过，0 Failing。

### v2.3.7 — 2026-08-10（v2.3.0 小更新 #7）

#### 💾 保存/加载用户工作区（会话持久化）
用户做到一半关浏览器不用重来；下次打开点「恢复上次会话」即可恢复代码、注释风格、语言选择、批量命名策略等完整工作区状态。

##### 持久化方案
- **主存储：服务端 tempfile JSON**（跨浏览器通用）
  - 路径：`<tempdir>/<8位用户名MD5>_code_comments_agent_workspace.json`
  - 多用户共享 temp 目录场景：前 8 位用户名 hash 分离各 workspace，避免互相覆盖
  - 原子写入：`write tmp + os.replace()`，中途断电/崩掉也不会把原文件写坏
- **可选兜底：浏览器 localStorage**（UI 层可扩展；当前主方案已满足通用要求）

##### 白名单字段 + 安全保护
- `WS_ALLOWED_FIELDS` 为 `frozenset`（不可变），只允许 6 个字段持久化：
  `source_code` / `language` / `ui_lang` / `python_style` / `java_style` / `naming_strategy`
- **API Key、api_base_url、password 等敏感字段绝不会被写入**（`save_workspace` 白名单过滤 + `load_workspace` 白名单二次过滤）
- `None` 值字段跳过，保持 JSON 精简
- 即使磁盘上的文件被人工注入脏字段，`load_workspace` 仍按白名单过滤（`{}` 默认安全），不会回传任意内容

##### 容错设计（`load_workspace` 所有异常都不抛，统一返回 False + 空 dict）
- 文件不存在 → 返回「未找到上次保存的会话」
- 空文件 → `UnicodeDecodeError` 分支 → 格式错误
- 非法 JSON → `JSONDecodeError` → 「文件已损坏」提示
- 顶层为 list / 缺少 `data` key / `data` 非 dict → 格式异常
- 非 UTF-8 编码 → 「编码错误」

##### UI 与 i18n
- **批量区新增「会话持久化」小节**（命名策略正下方、`batch_log` 正上方）：
  - `workspace_title_md` 标题
  - Row 放三按钮：`💾 保存会话` / `🔄 恢复上次会话` / `🗑️ 清除已保存会话`
  - `ws_tip_md` 安全提示：`⚠️ API Key 不会被保存`
- **事件链路闭环**：
  - `ws_save_btn.click`：收集 `[input_box, language, ui_lang, python_style, java_style, naming_strategy]` → 调用 `save_workspace` → 更新 `output_log` 显示成功/失败
  - `ws_restore_btn.click`：`load_workspace` → 输出 6 个组件 value + log 消息（7 outputs，顺序严格对应）
  - `ws_clear_btn.click` → `clear_workspace` → 更新 log
- **ui_lang 切换时同步更新 5 个组件文案**（`_apply_ui_language` 追加 37-41 号返回；`ui_lang.change outputs` 追加 workspace_title_md/ws_save_btn/ws_restore_btn/ws_clear_btn/ws_tip_md）
- **i18n 5 个 key**：`workspace_title` / `workspace_save_btn` / `workspace_restore_btn` / `workspace_clear_btn` / `workspace_tip`，中文 / English / 日本語 三语

##### 兼容性
- 零新增第三方依赖；纯 Python 标准库（json / tempfile / getpass / hashlib / os.replace）
- 旧版 processor 调用不受影响；三个 API 函数加 `path` 可选参数，单元测试与生产解耦
- UI 新增组件位于独立 card-section，不影响原有批量区/输出区布局与顺序

##### 测试覆盖（`test_workspace_persistence.py` 共 25 用例，全通过）
| 类 | 用例数 | 覆盖 |
| --- | --- | --- |
| T1_SaveLoadRoundTrip | 4 | 全字段往返 / 部分字段 / 多轮覆盖 / 元数据 (_version, _saved_at) |
| T2_WhitelistSecurity | 4 | save 时 api_key/password 过滤 / None 跳过 / load 时脏注入二次过滤 / WS_ALLOWED_FIELDS 是 frozenset 且不可变 |
| T3_FileFormatTolerance | 7 | 不存在 / 空文件 / 非法 JSON / list 顶层 / 缺 data / 非 UTF-8 / data=None 不崩 |
| T4_ClearAndNonexistent | 3 | clear 存在 / clear 不存在 / clear→load False |
| T5_DefaultPathStable | 3 | 在 tempdir 下 / 多次调用一致 / 文件名 8 位 hex hash 前缀 |
| T6_I18nKeys | 1 | 5 个 workspace_* key × 3 lang 存在非空 |
| T7_UiComponents | 3 | ui.py 声明 5 组件 / 3 按钮 .click 事件 / 引用 processor 3 个函数 |

**回归测试**：`test_workspace_persistence (25) + test_outline_collapsible (15) + test_batch_naming (16)` = 56 条全通过，0 Failing。

### v2.3.6 — 2026-08-10（v2.3.0 小更新 #6）

#### 🔍 代码编辑器搜索替换 + 大纲折叠
处理大文件（>500 行）时，用户需要直接在输出代码框里搜函数名 + 折叠大纲，而不是在大文件里来回滚动。Gradio 6.x Code 组件底层是 CodeMirror 6，已内置 `@codemirror/search` 扩展（Ctrl+F / Cmd+F 触发），只需 CSS 注入确保面板可见并美化；函数大纲已有 `build_outline_markdown`，改造为 `<details>` 折叠结构即可。

##### 1. CodeMirror 搜索面板 CSS 注入（`ui.py` custom_css）
- **`.cm-panels`** 容器：`display: flex`、`order: -1`（搜索面板显示在编辑器顶部，而非默认底部）、灰底圆角
- **`.cm-textfield`** 输入框：圆角 + focus 时 indigo 高亮边框 + `box-shadow` 光环
- **`.cm-button`** 按钮：圆角 + hover 浅灰背景
- **`.cm-searchMatch`** 匹配高亮：黄色半透明背景；`.cm-searchMatch-selected`（当前选中匹配）：橙色高亮 + 白字
- **`.cm-panel label`** 标签：灰色小字
- **隐藏按钮选择器安全**：`.cm-editor-header button` 与 `.cm-panels button` 是平级独立容器，不会误伤搜索面板按钮

##### 2. 大纲折叠结构（`processor.build_outline_markdown` 加 `collapsible` 参数）
- **`collapsible=True`（新默认）**：输出 `<details>` + `<summary>` HTML 折叠结构
  - **class 条目**：`<details open>`（默认展开），方法作为 `<ul><li>` 嵌套在 class 的 details 内
  - **顶级 function/method**：`<details>`（默认折叠），各自独立
  - 折叠箭头：CSS `summary::before` 伪元素 `▶` → 展开 `rotate(90deg)` → indigo 色
  - 层级推断：基于 `lineno` / `end_lineno` 范围包含判断 method 属于哪个 class
- **`collapsible=False`（向后兼容）**：保持旧版平铺 Markdown 无序列表格式
- **slug 分配顺序不变**：始终按 items 原始顺序（lineno 排序）分配 slug，与 annotator `build_markdown_docs` / `build_java_markdown_docs` 的 `<a id="...">` 完全一致 → 锚点跳转有效

##### 3. i18n 搜索提示（`i18n.py`）
- 新增 `search_hint` key 三语文案，附加到 `output_code` 组件 label 后缀（`·  💡 Ctrl+F 搜索 / 替换代码`）

##### 兼容性
- `build_outline_markdown` 签名加 `collapsible: bool = True`，旧调用者不传此参数自动获得折叠版（行为更优）；显式传 `False` 恢复旧格式
- 锚点 slug 一致性由 `T3_SlugConsistency` 3 条用例保证（Python / Java / collapsible vs flat 三方对比）
- CSS 纯注入，无 JS、无新增第三方依赖
- py_compile（processor / ui / i18n / test_outline_collapsible）0 SyntaxError

##### 测试覆盖（`test_outline_collapsible.py` 共 15 用例，全通过）
| 类 | 用例数 | 覆盖 |
| --- | --- | --- |
| T1_CollapsibleStructure | 7 | Python class+method+顶级函数 / Java class+method / 无 class 纯函数 / 空源码 / 语法错误 / 无定义 / class children 嵌套在 details 内 |
| T2_BackwardCompatFlatFormat | 2 | collapsible=False 输出旧版平铺格式（Python + Java） |
| T3_SlugConsistency | 3 | Python slug 匹配 annotator / Java slug 匹配 annotator / collapsible 与 flat 锚点集合完全相同 |
| T4_I18nSearchHint | 1 | search_hint 三语存在非空 + 含 Ctrl+F |
| T5_CSSInjection | 2 | CSS 含搜索面板选择器（.cm-panels/.cm-textfield/.cm-button/.cm-searchMatch） + 折叠选择器（.outline-sidebar details/summary/details[open]/summary::before/details>ul） |

### v2.3.5 — 2026-08-07（v2.3.0 小更新 #5）

#### 📁 输出 ZIP 保持文件名匹配 + 结构可配置
用户反馈：批量下载的 ZIP 内部原先直接按"上传时的文件名（无父目录）"平铺写入，解压后需要手动改名/覆盖到原工程目录；同时对于 CI 场景希望要么"直接同名覆盖"、要么"统一放子目录 annotated/ "，而不是每次都手工整理。

##### 3 种命名策略（processor.NAMING_SAME / NAMING_SUFFIX / NAMING_SUBDIR）
在批量区新增下拉框「ZIP 输出命名策略」（中文 / English / 日本語 三语），用户可直接选：

| 策略值 | UI 显示 | 效果（以 `src/pkg/utils.py` 为例） | 典型场景 |
| --- | --- | --- | --- |
| `same` | 同名覆盖（保留原文件名） | `src/pkg/utils.py`（原样） | CI 流水线：解压后直接覆盖源文件 |
| `suffix`（默认） | 添加 `_annotated` 后缀 | `src/pkg/utils_annotated.py` | 人工对比：不覆盖源文件，方便 diff |
| `subdir` | 放到 `annotated/` 子目录 | `annotated/src/pkg/utils.py` | 目录整洁：所有结果放一个顶层文件夹 |

- **`processing.log` / `API_DOCS_ALL.md` 始终在 ZIP 根**，不受命名策略影响（3 种策略均一致）。
- 非法值自动降级到 `suffix`，不会抛异常阻断下载。

##### 关键实现细节
1. **`_apply_naming_strategy(rel_path, strategy)` 独立纯函数**：输入 POSIX 相对路径，输出命名后的归档相对路径；覆盖 3 策略 × 无子目录 / 有子目录 / Windows 反斜杠输入共 8 条分支；`T1_ApplyNamingStrategy` 8 条单元测试 100% 覆盖。
2. **`_build_batch_zip(output_stage, ..., naming_strategy)` 打包时应用策略**：只对源码文件（`.py`/`.java`）走 `_apply_naming_strategy`，`processing.log`/`API_DOCS_ALL.md` 直接写根；`T2_BuildBatchZipMemberNames` 3 条用例校验 SAME / SUFFIX / SUBDIR 三类成员名一致。
3. **`process_batch_files` 与 `process_batch_with_progress` 同时加 `naming_strategy` 参数**，签名保持向后兼容（默认 `NAMING_SUFFIX`）；内部重构"非 zip 单文件上传"路径：不再简单把 `basename` 当作 rel_path 打平，而是收集全部原始源路径后：
   - 按 `Path.parts` 求最长公共前缀 → 公共父级 → 再向上退一层（common_len>1 时 -1）→ 对每个源文件做 `os.path.relpath(src_abs, common_parent)`；
   - 跨盘符无公共前缀时退化为 `basename`，不会报错。
   - 保证上传 `src/pkg/utils.py + src/pkg/Helper.java` 时 ZIP 内仍保有 `pkg/utils.py / pkg/Helper.java` 的层级关系，而非平铺 `utils.py`。
4. **UI 层** (`ui.py`)：
   - 批量区（紧靠 batch_log 前）新增 `naming_section_md` 说明 + `naming_strategy` Dropdown（3 个策略以"显示名→值"元组注册，默认选中 NAMING_SUFFIX）；
   - `_apply_ui_language` 返回列表追加 35/36 两项，`ui_lang.change(outputs=...)` 同步增加；
   - `_batch_gen_progress` 新增 `naming` 第 5 个入参并透传到 `process_batch_with_progress(naming_strategy=naming)`；
   - `batch_gen_btn.click(inputs=...)` 追加 `naming_strategy` 组件入参。
5. **i18n** (`i18n.py` TRANSLATIONS)：新增 5 个 key 三语文案——`naming_section`（小节标题说明）、`naming_label`（下拉框 label）、`naming_same_label` / `naming_suffix_label` / `naming_subdir_label`（3 个选项显示名）；`T4_I18n` 校验均存在且非空。

##### 兼容性
- `processor.process_batch_files` / `process_batch_with_progress` 旧签名调用者（无 naming_strategy）零侵入：默认 `suffix`，行为与旧版一致（旧版同样是 `processing.log`/`API_DOCS_ALL.md` + 平铺源码，现在默认策略仅多一个 `_annotated` 后缀保护源文件、更安全）。
- `processor.py` 顶部补 `from pathlib import Path`（此前只在局部使用，import 合规）。
- `ui.py` / `i18n.py` 仅新增字段与返回项，无旧组件 id 变更、无 layout 调整冲突。
- 无新增第三方依赖。

##### 测试覆盖（`test_batch_naming.py` 共 16 用例，全通过）
| 类 | 用例数 | 覆盖 |
| --- | --- | --- |
| T1_ApplyNamingStrategy | 8 | same/suffix/subdir × 无子目录/有子目录 + 非法值降级 + Windows 反斜杠归一化 |
| T2_BuildBatchZipMemberNames | 3 | same/suffix/subdir 打包结果成员名（源码 + log + aggregate doc） |
| T3_ProcessBatchFilesEndToEnd | 4 | py 单文件 suffix + java 单文件 same + 多文件 subdir（含 AST 校验） + 非法值降级 |
| T4_I18n | 1 | naming_* 5 个 key 三语存在非空 |

### v2.3.4 — 2026-08-07（v2.3.0 小更新 #4）

#### 修复 v2.3.3 端到端测试报告中的潜在问题
v2.3.3 完整端到端测试（49 用例全通过）后，测试报告列出 4 项潜在问题；本次修复其中可落地的 2 项（另 2 项为"mock LLM 难以验证翻译质量"和"无 Gradio UI 交互测试"，属测试基础设施限制，非产品缺陷，不在本次范围）。

##### 1. Java 有效性检测宽松（修复）
- **问题**：旧版 `_is_valid_java` 只要源码出现 1 个 Java 关键字或 2 个大括号即判为有效，导致 `"hello class world"`、`"int x = 1; print(x);"` 等无意义文本被误判为有效 Java 代码并触发后续 LLM 调用，可能产生幻觉输出。
- **修复**：`processor._is_valid_java` 改为严格化三重校验：
  1. 必须有非空非注释行（保留）；
  2. 必须包含 Java 类型声明关键字 `class` / `interface` / `enum` / `record` 作为独立词（正则 `\b(?:class|interface|enum|record)\b` 词边界匹配，避免 `class` 出现在普通文本中误判）；
  3. 必须有至少 1 对大括号且大括号匹配（调用现有 `Java.java_annotator._validate_braces`，屏蔽字符串/注释后校验，多余 `}` 或缺少 `}` 均判为无效）。
- **验证**：13 条边界用例全部通过——`"hello class world"` / `"just some text"` / `"{}"` / `"class Foo {"` / `"// only comment"` / `"int x = 1; print(x);"` → False；`"class Foo {}"` / `"public class Foo { void bar() {} }"` / `"interface Bar { void run(); }"` / `"enum Color { RED, GREEN }"` → True。

##### 2. 缺少 javac 语法验证 + 注释后无二次校验（修复）
- **问题**：旧版 Python 注释生成后通过 `ast.parse` 隐式保证语法正确（insert 失败会抛 `SyntaxError`），但 Java 端只在 `_analyze_java` 阶段做了一次 `_validate_braces` 大括号校验，注释插入后的代码完整性没有二次验证，且从未调用 `javac` 做真实语法检查，存在"插入 Javadoc 后大括号错位但用户无感知"的风险。
- **修复**：新增 `processor._verify_java_annotated_code(annotated_code, log)` 辅助函数，在 `_process_java` 与 `_process_java_with_progress` 写临时文件前调用：
  1. **大括号匹配二次校验**：调用 `_validate_braces(annotated_code)`，失败时日志追加 `⚠️ 注释后大括号匹配失败: ...`（不阻断下载，让用户能看到问题）；
  2. **可选 javac 真实语法验证**：通过 `shutil.which("javac")` 探测系统 PATH，若存在 javac 则写入临时文件后调用 `javac -Xlint:none -encoding UTF-8 <file>`（`subprocess.run` + `timeout=15s`），返回码非 0 时取 stderr 首行作为 `⚠️ javac 语法校验失败: ...` 日志警告；超时则提示 `⚠️ javac 语法校验超时（15s）`；无 javac 时优雅跳过、不影响主流程。
- **设计原则**：失败仅日志警告、不抛异常、不阻断下载，符合"取消任务也要保留已完成结果"的产品约定；javac 可用性自动探测，零环境依赖（无 javac 的 Windows 开发机与有 javac 的 CI 环境均正常）。
- **验证**：3 条用例通过——合法 Java 代码 → `✓ 注释后大括号匹配校验通过`；缺右括号 → `⚠️ ... 缺少 2 个 '}'`；含注释行 → `✓ ... 通过`；当前环境无 javac，第 2 步自动跳过。

##### 兼容性
- `processor.py` 顶部新增 `import re` / `import subprocess`（`shutil` 已存在），无新增第三方依赖
- `_is_valid_java` 签名与返回类型不变，所有调用点（`process_code` / `process_code_with_progress` / `_analyze_java`）零侵入
- `_verify_java_annotated_code` 为新增函数，仅在 Java 流程末尾调用，Python 流程不受影响
- py_compile 全部 13 个 .py 文件（root + Py + Java）0 SyntaxError

### v2.3.3 — 2026-08-07（v2.3.0 小更新 #3）

#### 🧪 API Key 有效性预检（1-token 心跳）+ Token 用量 / 成本估算
- **config 新增 5 个常量**（DeepSeek 官方参考价，2026 参考值）：`PRICE_INPUT_PER_M=0.27`（¥0.27 / 1M 输入 tokens）、`PRICE_OUTPUT_PER_M=1.10`（¥1.10 / 1M 输出 tokens）、`AVG_TOKENS_PER_ITEM=350`（每个函数/方法实测经验值：150 prompt 模板 + 200 docstring 产出）、`INPUT_RATIO=0.43` / `OUTPUT_RATIO=0.57`（更精准拆分估算）
- **`llm_service.ping_api_key(timeout=6.0)`**：独立 1-token 心跳请求。参数：`model=deepseek-chat`、`temperature=0.0`、**`max_tokens=1`（严格要求）**、`messages=[{role:user, content:"ping"}]`、`timeout=6s`。覆盖 8 种错误：`AuthenticationError→API Key 无效`、`PermissionDeniedError→无权限`、`RateLimitError→频率超限/余额不足`、`NotFoundError→模型或 base_url 错误`、`APITimeoutError→超时`、`Exception→兜底 Name+首行消息`；返回 `(ok, msg)` 2 元组，ok=False 时 msg 为人类可读提示
- **`llm_service.estimate_tokens_cost(num_items, avg_tokens_per_item=None)`**：4 元组数学计算 `(total_tokens, input_est, output_est, cost_rmb)`；num_items ≤ 0 直接返回 0 向量；成本公式 `(in/1e6)*0.27 + (out/1e6)*1.10`，精度 4 位小数
- **`processor.preflight_check(source_code, language, ui_lang, do_ping, avg_per_item)`** 组合入口（3 元组 `(ok, preflight_md, estimate_md)`）：
  - 先根据 ui_lang 从 `_I18N_PREFLIGHT` 三语模板字典（3 语种 × 12 键完整覆盖）选择对应语言
  - do_ping=True → 调 `ping_api_key`；do_ping=False → 跳过网络（input_box.change 实时估算、最终帧补估算时使用，避免多余心跳）
  - source 空 → 返回"暂无源代码"提示；语法异常吞掉不抛；AST 解析结果 0 条 → 返回"未检测到函数或类定义"
  - 统计 n_funcs / n_classes / n_total，调用 `estimate_tokens_cost`，渲染 Markdown 5 行：分析计数 / 总 tokens + 每条均值 / 入出力拆分 / ¥ 成本 + 价格档位说明
  - 额外提供 `estimate_markup_cost(num_items, lang, avg)` 无网络快速封装
- **UI 绑定**：
  - 操作行按钮右侧新增第 4 位 `preflight_btn = gr.Button(🔍 预检 API Key + 估算 Tokens)`（点击 do_ping=True）
  - 按钮下方新增 2 个 Markdown：`preflight_result_md`（🛡️ 预检区域）、`cost_estimate_md`（💰 成本估算区域）
  - ui_lang change → `_apply_ui_language` outputs 32→35：第 32 位预检按钮 value、第 33/34 位 2 个 Markdown label 翻译
  - **btn.click 生成器 9→11 元组末 2 位**：第 10 位 `preflight_result_md`、第 11 位 `cost_estimate_md`；首帧前先 `preflight_check(do_ping=True)`，**失败则直接 yield 11 元组 + return，绝不进入主生成循环**（避免跑到一半因为 Key 无效白花 token 和时间）；中间帧 yield None 继承上一帧不闪烁；最终帧再 do_ping=False 补算一次保证最新
  - `input_box / language / ui_lang / python_style / java_style / file_upload` 共 6 个组件 `.change` → 全部绑定 `_estimate_only`（do_ping=False，无网络）→ 粘贴代码或切语言时 100ms 级别实时刷新估算
- **i18n 三语新增 3 键**：`preflight_btn`（🔍 预检 API Key + 估算 Tokens / Check API Key + Estimate Tokens / API Key 事前検証 + トークン概算）、`estimate_label`（💰 用量/成本（贴代码自动估算）/ 💰 Usage / Cost / 💰 使用量・費用）、`preflight_label`（🛡️ API Key 预检（生成前 1-token 心跳）/ Preflight / API Key 事前検証）
- **新增 test_cost_preflight.py 12 条（100% 通过）**：
  - `EstimateTokensCostTests 3/3`：0/N 向量、默认 350 × 10 = 3500 tokens + 0.43/0.57 比例 ≤ ¥0.1 粗略 + 自定义 1000/item 验证
  - `PingAPIKeyParameterTests 2/2`：**断言传参 max_tokens=1 / temperature=0 / ping message / timeout=3.5 / model=deepseek-chat**；6 种 openai 异常 + RuntimeError 兜底全部 ok=False 且包含关键词友好错误
  - `PreflightCheckBoundaryTests 6/6`：空代码提示 / 0 函数无类检测 / Python 代码含 ¥ 元 / Java 代码 / EN 语言出现 "Total items & Estimated cost" / JA 出现 "合計エントリ数 & 推定費用" / Deutsch 回退中文
  - `I18nKeysTests 1/1`：3 键 × 3 语种非空
- **全流程验证（82/82 通过）**：
  - py_compile 全自有 .py：0 SyntaxError
  - 5 个独立进程 unittest：`test_styles 21/21` ✅ + `test_smoke_comprehensive 24/24` ✅ + `test_progress_cancel 16/16` ✅ + `test_outline_navigation 9/9` ✅ + `test_cost_preflight 12/12` ✅ = **82 条全部通过**

### v2.3.2 — 2026-08-07（v2.3.0 小更新 #2）

#### 函数/类导航大纲 Sidebar（一键跳转锚点）
- **`tab_annotated` 顶部大纲栏**：在「带注释的代码」Tab 的 Code 组件上方新增 `outline_md`（`gr.Markdown` 大纲），渲染内容来自新增的 `processor.build_outline_markdown(source, language, title)`：解析 `Py.parser.get_defined_functions` / `Java.java_parser.get_defined_functions` 结果转成可点击 Markdown 列表，每项为 `- 🧩/🔧 [`name` (Class/Function/Method) ](#slug-id) — *Llineno*`，并附带提示"💡 点击条目跳转至「API 文档」Tab 对应章节"
- **`tab_docs` 顶部目录栏**：在「API 文档」Tab 顶部再新增 `docs_toc_md`（与大纲内容一致，方便切到 Docs Tab 后也立即有目录可点）；`ui._apply_ui_language` 新增第 30、31 位 2 个占位 `gr.update()`（切换 UI 语言时大纲内容继承最新）
- **`btn.click` outputs 7→9 元组**：新增第 8 位 `outline_md`、第 9 位 `docs_toc_md`；`_gen_real` 所有分支（首帧 / 中间帧 / 最终帧 / 无最终帧取消帧）严格 yield 9 项，**中间帧返回 None 继承上一帧不闪烁**，首帧立即先渲染 `early_outline`（保证点击生成按钮瞬间就能看到函数/类列表，不必等 LLM），最终帧再用最新 UI 语言再渲染一次
- **API 文档内置 TOC + 锚点 Heading**：
  - `Py.annotator.build_markdown_docs` 升级：新增 `_slugify(name, prefix, used)`（字母/数字/连字符/下划线保留，其余转 `-`，重名自动 `-2`/`-3` 去重）；先遍历分配 `cls-` / `fn-` 前缀的 `slug_id` 写入每个 doc_entry；顶部追加 `## 📑 Table of Contents` 目录段；每条详情的 `##` Heading 改为 `## 🧩/🔧 name (Type) — Llineno <a id="slug_id"></a>`
  - `Java.java_annotator.build_java_markdown_docs` 同步升级：类前缀 `cls-`、方法前缀 `m-`（区别 Python 的 `fn-` 避免命名空间冲突）；同样的 TOC + Heading 锚点结构
  - 两个 `annotator.py` 顶部新增 `from __future__ import annotations`，保证 Python 3.8 下 `set | None` 联合类型注解不抛 `TypeError`
- **processor 层独立 API**：
  - `processor._slugify_name(name, prefix, used)`：processor 内部版本 slug 器（局部 `import re`，避免在顶部 import 顺序上与 annotator 产生不一致）
  - `processor.build_outline_markdown(source, language="Python", title="📋 函数/类导航大纲")`：独立入口（**不依赖 llm_service 运行期调用**，import 期只依赖 parser，测试无需 LLM mock 就能跑）；`language=="Java"` 自动走 `get_java_functions`；空源/语法错误异常吞掉返回空字符串
- **锚点一致性保证（最关键）**：processor 与 annotator 各自 slug 规则完全一致——相同 name / type / 相同 used 集合插入顺序 → 相同 slug_id；`test_outline_slugs_match_annotator_slugs_python` 用真实 1 个 Class + 2 个 Method + helper/main 函数验证：`doc_entries[*].slug_id` 既出现在 `build_markdown_docs` 的 `<a id="..."></a>`，也出现在 `build_outline_markdown` 的 `#slug_id` 链接中
- **i18n 三语**：新增 `outline_title`：中文「📋 函数/类导航大纲（点击跳转至 API 文档对应章节）」/ 英文「📋 Functions / Classes Outline (click to jump in API Docs tab)」/ 日文「📋 関数/クラス目次（クリックでAPIドキュメントへジャンプ）」

#### 新增测试 + 回归（4 进程独立，合计 70/70 通过）
- **新增 `test_outline_navigation.py` 9 条**：`SlugifyTests`（2 条：基础 slug 规则 + 重名去重）、`BuildOutlineMarkdownTests`（4 条：非空 Python 大纲含 fn-/cls- 前缀 & 行号 & 提示 / 空源空 / 语法错空不抛异常 / outline slug 与 annotator doc_entries slug 完全对齐）、`BuildMarkdownDocsTOCTests`（2 条：Python docs TOC 段存在 + 锚点 Heading & 行号 / Java docs `cls-` + `m-` 前缀 TOC + 锚点）、`I18nOutlineTitleTests`（1 条：三语翻译齐全且中文包含「大纲」）
- **py_compile 全自有 .py（root + Py + Java）**：语法 0 错误
- **独立进程 unittest 4 套件**：`test_styles 21/21` ✅ + `test_smoke_comprehensive 24/24` ✅ + `test_progress_cancel 16/16` ✅ + `test_outline_navigation 9/9` ✅ = **70/70 全部通过**
- 注：同进程 `discover -p test_*.py` 下 `test_styles` 与 `test_smoke_comprehensive` 各自对 `sys.modules["openai"].OpenAI` 注入顺序不兼容，会报 `capture.prompts[0]` 空 IndexError（**v2.3.1 既有问题，与本改动无关**），生产执行请分文件或分进程跑（各自独立进程 100% 通过）

### v2.3.1 — 2026-08-07（v2.3.0 小更新 #1）

#### 实时进度条 + 可取消任务
- **单文件生成**：`btn.click` 改用生成器函数 `_gen_real(progress=gr.Progress())`，每一步更新 UI 内置进度条的百分比（0.05 ~ 1.00）和阶段描述（"解析代码结构" / "翻译已有注释" / "调用 LLM 生成注释..." / "插入注释到源码" / "构建 API 文档" / "完成"）
- **批量处理**：`batch_gen_btn.click` 改用生成器函数 `_batch_gen_progress(progress=gr.Progress())`，每个文件处理完成后更新 `x/N 处理 xxx.py` 描述，0%~5% 展开 ZIP，5%~95% 按文件数线性推进，95% 后打包 ZIP
- **取消按钮**：在"生成注释"和"批量生成"右侧新增红色停止样式按钮（`variant="stop"`）：
  - `cancel_btn` 单文件取消：`CancelToken.cancel()` 立即置位，核心 processor 循环中每步检测 `is_canceled()`，检测到后立即对所有排队中/运行中的 LLM future 调用 `.cancel()` + `executor.shutdown(wait=False)`，节省 API token
  - `batch_cancel_btn` 批量取消：处理完当前文件后不再推进后续，已成功处理的文件照常打包 ZIP 返回，不浪费已产生的结果
- **取消不丢结果**：取消流程不提前 return，继续执行到"构建 Markdown + 写临时文件"阶段，md_path / src_path / zip_path 均为有效路径，用户仍能下载取消前已完成部分
- **processor 层 API（核心生成器，保持原同步函数兼容）**：
  - `processor.CancelToken`：线程安全取消标志位（`cancel()` / `reset()` / `is_canceled()`）
  - `_process_python_with_progress` / `_process_java_with_progress`：双语生成器版，每步 yield 5 元组中间态
  - `process_code_with_progress(source, incremental, language, ..., cancel_token, progress_cb)`：入口生成器，统一边界处理 + 路由
  - `process_batch_with_progress(files, ..., cancel_token, progress_cb)`：批量生成器，每次 yield `(log_text, zip_path | None)`
  - **保持向后兼容**：原有同步函数 `process_code` / `process_batch_files` 签名和行为完全未变，测试套件、老调用方零侵入
- **Python 3.8 兼容**：新增 `_shutdown_executor_safe(executor, futures_map)`，try/except 捕获 `TypeError`（`cancel_futures` 参数仅 Python 3.9+），降级为"先手动 cancel 每个 future 再 `shutdown(wait=False)`"，Windows 自带 Python 3.8 下正常运行
- **i18n 三语新增**：`cancel_btn`（⏹️ 取消任务 / Cancel Task / タスクをキャンセル）、`batch_cancel_btn`（⏹️ 取消批量任务 / Cancel Batch / 一括処理をキャンセル）
- **新增 16 条测试 `test_progress_cancel.py`**：CancelToken 线程安全（4 线程×10000 次并发 cancel/reset）、边界单 yield、有效代码多帧 yield+最终帧非空路径、progress_cb 最终 ratio=1.0、取消场景 md_p/src_p 仍为文件路径、批量空输入/非法路径、两个新增 i18n key 三语齐全 — 全部 16/16 通过
- **回归测试**：原 21+24=45 条老用例一次通过，无破坏性改动

### v2.3.0 — 2026-08-07（大版本：代码差异对比底层能力）

#### 代码对比 Diff 视图（GitHub 风格并排 Split）
- 输出区新增第 5 个 Tab **🆚 代码差异 (Diff)**，在"注释后的代码"Tab 之后，用户生成完成后可直接切 Tab 查看差异
- 左右分栏并排显示：Before（左，注释前原始代码）/ After（右，注释后代码），各自独立行号，视觉对齐
- **行级高亮**：新增行绿底（`#e6ffec`）、删除行红底（`#ffebe9`）、未变行白底；行号列同步着色
- 顶部统计条：`+N 插入 / -M 删除 / K 未变`，完全相同代码自动提示"✅ 未检测到代码差异"
- `processor.build_split_diff_html` 核心函数：基于 `difflib.SequenceMatcher` 的 opcodes 直接逐行渲染；自动 HTML escape `<>&"` 等特殊字符，避免 XSS 与样式错乱
- 三语 i18n：Diff Tab 标签支持 中文 / English / 日本語 跟随 UI 语言切换
- 事件绑定：`btn.click → .then(build_split_diff_html, inputs=[input_box, output_code, language], outputs=[diff_html])`，生成完注释后自动异步计算 Diff，不阻塞原有 UI 跳转
- 新增 7 条 Diff 单元测试（`TestDiffView`），覆盖：同文无差异、纯插入 docstring、纯删除、替换行、空输入、语言标签传递、HTML 特殊字符 escape（全部通过）
- Diff Tab 未破坏原 process_code 签名：ui 层直接以 `input_box.value`（原始输入）和 `output_code.value`（注释后输出）为输入，processor 零侵入

### v2.2.2 — 2026-08-07（v2.2.0 小更新 #2）

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

### v2.2.1 — 2026-08-07（v2.2.0 小更新 #1）

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

### v2.2.0 — 2026-08-07（大版本：多语言 i18n 底层能力）

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

### v2.1.1 — 2026-08-06（v2.1.0 小更新 #1）

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

### v2.1.0 — 2026-08-06（大版本：Java 语言 + 目录结构分语言）

#### Java 语言支持
- 新增 Java 代码解析器，支持类、方法、构造器、枚举、内部类、匿名类（排除匿名类实例化误判）
- 新增 Javadoc 注释自动生成，支持 `@param`、`@return`、`@throws` 标签
- 支持复杂嵌套 Java 代码（接口、泛型、静态嵌套类、Lambda 等）
- 新增 Java 代码有效性验证（大括号匹配校验，屏蔽字符串中的括号）

#### 目录结构优化
- 按语言和功能分文件夹组织：`Py/`（Python 解析/注释/分析）、`Java/`（Java 解析/注释）
- 修复 Java 解析器排除匿名类实例化（`new ClassName() { ... }`）的问题

### v2.0.0 — 2026-08-05（大版本：架构重构 + 并发生成 + 代码质量体系）

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
