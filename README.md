# 代码注释与 API 文档自动生成 Agent

**当前版本：v2.3.4**（2026-08-07 · v2.3.0 的小更新 · Java 有效性检测严格化 + 注释后语法二次校验）

基于 DeepSeek 大模型 + Gradio 构建的 Python 代码自动注释工具。通过 AST 解析提取函数和类定义，调用 LLM 生成多种风格（Python：Google/NumPy/reStructuredText；Java：标准 Javadoc/极简行内注释）的中文文档字符串（docstring），并自动生成 Markdown API 文档。

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

> **版本号规则**：大版本 `vX.Y.0` 仅记录"技术含量极强/新增底层架构能力"的重要更新；小更新 `vX.Y.1`、`vX.Y.2` … 不单独占据"大版本位"，归入最近一次大版本的"小更新"子节按时间倒序排列。大版本列表：v1.0.0（初始）→ v2.0.0（架构重构+并发+质量分析）→ v2.1.0（Java 支持+目录结构分语言）→ v2.2.0（i18n 三语+注释翻译）→ v2.3.0（Diff Split 视图）。

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
