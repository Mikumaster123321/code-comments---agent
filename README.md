# 代码注释与 API 文档自动生成 Agent

基于 DeepSeek 大模型 + Gradio 构建的 Python 代码自动注释工具。通过 AST 解析提取函数和类定义，调用 LLM 生成 Google 风格中文文档字符串（docstring），并自动生成 Markdown API 文档。

## 功能特性

- **自动注释**：为 Python 函数和类生成 Google 风格中文 docstring
- **AST 解析**：精准提取顶级函数、异步函数和类定义
- **双模式输入**：支持直接粘贴代码或上传 `.py` 文件
- **文件下载**：支持下载注释后的 `.py` 文件和 Markdown API 文档
- **实时日志**：处理过程可视化，显示每个函数/类的注释状态

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek Chat API |
| Web 框架 | Gradio |
| 代码解析 | Python AST 模块 |
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
4. **查看结果**：
   - 右侧显示带注释的代码
   - 下方显示生成的 Markdown API 文档
   - 处理日志显示注释进度
5. **下载文件**：
   - 下载注释后的 `.py` 文件
   - 下载 API 文档 `.md` 文件

## 测试

项目包含测试文件 `test_sample.py`，涵盖多种场景：

| 测试项 | 类型 | 说明 |
|--------|------|------|
| `is_prime` | 函数 | 类型注解 + 算法逻辑 |
| `quick_sort` | 递归函数 | 递归算法 + 列表推导式 |
| `format_currency` | 函数 | 默认参数 + 字符串格式化 |
| `LinkedList` | 类 | 类定义 + 多方法 + 异常处理 |
| `read_config` | 函数 | 异常处理 + 配置解析 |
| `retry` | 装饰器 | 闭包 + 可变参数 |

## 项目结构

```
code-comments---agent/
├── main.py            # 主程序（核心逻辑 + Gradio 界面）
├── test_sample.py     # 测试文件
├── Test.txt           # 测试用例
├── .env.example       # 环境变量示例
├── .env               # 环境变量（需自行创建，不入库）
└── .gitignore         # Git 忽略规则
```

## 工作流程

```
输入代码/上传.py文件
       │
       ▼
  AST 解析提取函数/类定义
       │
       ▼
  遍历每个函数/类 ──→ 调用 DeepSeek API 生成 docstring
       │                        │
       │                        ▼
       │               插入 docstring 到原代码
       │
       ▼
  输出：带注释的代码 + Markdown API 文档
       │
       ▼
  提供下载：.py 文件 + .md 文件
```
