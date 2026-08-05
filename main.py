import os
import ast
import re
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
import gradio as gr
from dotenv import load_dotenv

# ==================== 配置 ====================
# 从 .env 文件或环境变量中读取 API Key，避免硬编码泄露
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise EnvironmentError(
        "未检测到 DEEPSEEK_API_KEY 环境变量。"
        "请复制 .env.example 为 .env 并填入你的 DeepSeek API Key。"
    )


client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)
MODEL = "deepseek-chat"
TEMPERATURE = 0.2
MAX_TOKENS = 1024

# ==================== 核心功能 ====================

def get_defined_functions(source: str):
    """使用 AST 提取所有函数和类定义（递归包含类内部方法）"""
    tree = ast.parse(source)
    items = []

    def _collect(nodes, class_context=None):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno
                code_lines = source.splitlines()[start_line-1:end_line]
                func_code = "\n".join(code_lines)
                # 判断是否已有 docstring（body 首条语句为字符串字面量）
                has_doc = (
                    len(node.body) > 0
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )
                items.append({
                    "node": node,
                    "name": node.name,
                    "type": "class" if isinstance(node, ast.ClassDef) else "function",
                    "code": func_code,
                    "lineno": start_line,
                    "end_lineno": end_line,
                    "has_docstring": has_doc
                })
                # 递归：如果是类，继续提取类内部的方法
                if isinstance(node, ast.ClassDef):
                    _collect(node.body, class_context=node.name)

    _collect(ast.iter_child_nodes(tree))
    return items

PROMPT_TEMPLATE = (
    "你是一位资深 Python 开发工程师。请为以下{func_type}生成中文文档字符串（docstring）的内容。\n"
    "\n"
    "⚠️ 极其重要的格式要求（不遵守会导致Python语法错误）：\n"
    "1. 不要在开头和结尾添加任何三引号（\u0022\u0022\u0022或\u0027\u0027\u0027），我会在生成后自动包裹。\n"
    "2. 不要使用任何Markdown代码块标记（不要 ``` ）。\n"
    "3. 只输出文档字符串的纯文本内容，不要包含任何代码。\n"
    "4. 内容内部如果需要出现引号，请使用单引号或转义，绝对不要出现连续三个双引号。\n"
    "\n"
    "文档内容要求（Google 风格）：\n"
    "- 第一行：一句话功能描述（简洁明确）\n"
    "- Args：参数名 + 类型 + 说明\n"
    "- Returns：返回类型 + 说明\n"
    "- Raises：可能抛出的异常 + 触发条件\n"
    "- 重要逻辑或算法请简要说明\n"
    "\n"
    "{func_type}名：{name}\n"
    "源代码：\n"
    "{code}\n"
)

def generate_docstring(item: dict) -> str:
    """调用 LLM 生成文档字符串"""
    prompt = PROMPT_TEMPLATE.format(
        func_type="类" if item["type"] == "class" else "函数",
        name=item["name"],
        code=item["code"]
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )
    docstring = response.choices[0].message.content.strip()

    # 彻底清理：去除所有可能的三引号包裹（防止 LLM 不听话）
    # 注意：正则写法刻意避免三引号与字符串边界冲突
    triple_double = chr(34) * 3   # """
    triple_single = chr(39) * 3   # '''
    docstring = re.sub(r'^' + triple_double, '', docstring)   # 开头的 """
    docstring = re.sub(triple_double + r'$', '', docstring)   # 结尾的 """
    docstring = re.sub(r'^' + triple_single, '', docstring)   # 开头的 '''
    docstring = re.sub(triple_single + r'$', '', docstring)   # 结尾的 '''
    docstring = re.sub(r'^```.*?\n', '', docstring)           # 开头的 markdown 代码块
    docstring = re.sub(r'\n```$', '', docstring)              # 结尾的 markdown 代码块
    docstring = re.sub(r'^```', '', docstring)                # 开头单独的 ```
    docstring = re.sub(r'```$', '', docstring)                # 结尾单独的 ```

    # 清理内容中残留的独立三引号行（避免破坏docstring边界）
    cleaned_lines = []
    bad_markers = (triple_double, triple_single)
    for line in docstring.split('\n'):
        stripped = line.strip()
        if stripped in bad_markers:
            continue
        cleaned_lines.append(line)
    docstring = "\n".join(cleaned_lines)

    return docstring.strip()

def insert_docstring_into_code(source: str, item: dict, docstring: str) -> str:
    """将文档字符串插入到函数/类定义体的第一行（签名结束后）"""
    lines = source.splitlines()
    node = item["node"]
    indent = len(lines[item["lineno"] - 1]) - len(lines[item["lineno"] - 1].lstrip())
    inner_indent = ' ' * (indent + 4)

    formatted_doc = _format_docstring(docstring, inner_indent)

    # 判断是否已有 docstring（第一条语句是字符串字面量）
    has_existing_doc = (
        len(node.body) > 0
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    )

    if has_existing_doc:
        # 替换旧 docstring：node.body[0] 是 docstring 节点（ast.Expr）
        doc_node = node.body[0]
        start_idx = doc_node.lineno - 1       # 0-based，旧 docstring 首行
        end_idx = doc_node.end_lineno         # 0-based slice，旧 docstring 之后的行
        new_lines = lines[:start_idx] + [formatted_doc] + lines[end_idx:]
    else:
        # 没有 docstring：插入到函数体第一条语句之前
        if node.body:
            insert_idx = node.body[0].lineno - 1
        else:
            # 空函数体（如 pass）：插入到 end_lineno 之前
            insert_idx = node.end_lineno - 1
        new_lines = lines[:insert_idx] + [formatted_doc] + lines[insert_idx:]

    result = "\n".join(new_lines)

    # 安全校验：尝试 AST 解析，失败则回退不修改
    try:
        ast.parse(result)
    except SyntaxError:
        # 打印到日志（这里通过异常让调用方知道）
        raise SyntaxError(f"插入 docstring 后语法错误，已跳过: {item['name']}")

    return result


def _format_docstring(docstring: str, inner_indent: str) -> str:
    """格式化 docstring：统一换行、缩进和三引号包裹"""
    # 先清理内容两端空白
    docstring = docstring.strip()
    # 逐行按 inner_indent 缩进
    body_lines = []
    for line in docstring.split('\n'):
        body_lines.append(f"{inner_indent}{line}")
    body = "\n".join(body_lines)
    return f'{inner_indent}"""\n{body}\n{inner_indent}"""'

def build_markdown_docs(doc_entries: list) -> str:
    """生成 Markdown API 文档"""
    md = "# API 文档\n\n"
    for entry in doc_entries:
        md += f"## {entry['name']} ({'类' if entry['type']=='class' else '函数'})\n\n"
        md += f"```python\n{entry['code']}\n```\n\n"
        md += f"{entry['docstring']}\n\n"
        if entry["type"] == "class":
            md += "*(类文档，方法细节请见源码)*\n\n"
        md += "---\n\n"
    return md

# ==================== 代码分析功能 ====================

def _calc_complexity(node) -> int:
    """计算圈复杂度（McCabe）：分支点数量 +1"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.Try, ast.ExceptHandler, ast.With, ast.AsyncWith,
                              ast.Match)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # and/or 每增加一个操作数 +1
            complexity += len(child.values) - 1
    return complexity

def _calc_max_depth(node, current: int = 0) -> int:
    """计算最大嵌套深度"""
    max_d = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.Try, ast.With, ast.AsyncWith)):
            d = _calc_max_depth(child, current + 1)
        else:
            d = _calc_max_depth(child, current)
        if d > max_d:
            max_d = d
    return max_d

def analyze_code_quality(source: str) -> str:
    """代码质量分析：圈复杂度、嵌套深度、函数长度、参数数量，标记坏味道"""
    tree = ast.parse(source)
    rows = []
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            node_type = "类" if isinstance(node, ast.ClassDef) else "函数"
            length = node.end_lineno - node.lineno + 1
            complexity = _calc_complexity(node)
            depth = _calc_max_depth(node)
            params = len(node.args.args) if hasattr(node, 'args') else 0

            marks = []
            if complexity > 10:
                marks.append("⚠️复杂度过高")
            elif complexity > 5:
                marks.append("⚡复杂度较高")
            if depth > 4:
                marks.append("⚠️嵌套过深")
            if length > 50:
                marks.append("⚠️函数过长")
            if params > 5:
                marks.append("⚠️参数过多")
            if not marks:
                marks.append("✅良好")

            eval_str = " ".join(marks)
            rows.append(f"| {name} | {node_type} | {length} | {complexity} | {depth} | {params} | {eval_str} |")

            for m in marks:
                if "⚠️" in m:
                    issues.append(f"- **{name}** (行 {node.lineno}): {m[1:]}，建议重构")

    report = "### 📊 代码质量分析报告\n\n"
    report += "| 函数/类 | 类型 | 行数 | 圈复杂度 | 嵌套深度 | 参数数 | 评估 |\n"
    report += "|---------|------|------|----------|----------|--------|------|\n"
    report += "\n".join(rows) if rows else "| (无函数/类) | - | - | - | - | - | - |"
    report += "\n\n"
    if issues:
        report += "### 🚨 需要关注的问题\n\n"
        report += "\n".join(issues)
    else:
        report += "### ✅ 代码质量良好，未发现明显问题"
    return report

def check_type_annotations(source: str) -> str:
    """类型注解检查：识别缺失类型注解的参数和返回值"""
    tree = ast.parse(source)
    sections = []
    missing_count = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            issues = []
            for arg in node.args.args:
                # self/cls 是约定参数，不需要类型注解
                if arg.annotation is None and arg.arg not in ('self', 'cls'):
                    issues.append(f"参数 `{arg.arg}` 缺少类型注解")
                    missing_count += 1
            # __init__ 约定返回 None，不需要显式返回值注解
            if node.returns is None and node.name != "__init__":
                issues.append("返回值缺少类型注解")
                missing_count += 1
            if issues:
                sections.append(f"**{name}** (行 {node.lineno}):\n" + "\n".join(f"  - {i}" for i in issues))

    report = "### 🏷️ 类型注解检查报告\n\n"
    if missing_count == 0:
        report += "✅ 所有函数的类型注解完整"
    else:
        report += f"共发现 **{missing_count}** 处缺失的类型注解：\n\n"
        report += "\n\n".join(sections)
    return report

def generate_code_summary(source: str) -> str:
    """调用 LLM 生成代码摘要：模块功能、核心类、依赖关系"""
    prompt = (
        "请分析以下 Python 代码，生成一段简洁的中文摘要（200字以内）。\n"
        "摘要应包含：\n"
        "1. 模块整体功能\n"
        "2. 核心类和函数\n"
        "3. 主要依赖关系\n"
        "\n"
        "只输出摘要文本，不要使用 Markdown 标题或代码块。\n"
        "\n"
        "源代码：\n"
        f"{source}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()

def analyze_code(source_code: str):
    """主分析函数，返回质量报告、类型注解报告、摘要、日志"""
    if not source_code or not source_code.strip():
        return "未输入代码", "未输入代码", "未输入代码", "日志：无处理对象。"

    log = []
    log.append("=== 代码质量分析 ===")
    try:
        quality_report = analyze_code_quality(source_code)
        log.append("✓ 质量分析完成")
    except Exception as e:
        quality_report = f"分析失败: {e}"
        log.append(f"✗ 质量分析失败: {e}")

    log.append("=== 类型注解检查 ===")
    try:
        annotation_report = check_type_annotations(source_code)
        log.append("✓ 类型注解检查完成")
    except Exception as e:
        annotation_report = f"检查失败: {e}"
        log.append(f"✗ 类型注解检查失败: {e}")

    log.append("=== 代码摘要生成（调用 LLM）===")
    try:
        summary = generate_code_summary(source_code)
        log.append("✓ 摘要生成完成")
    except Exception as e:
        summary = f"摘要生成失败: {e}"
        log.append(f"✗ 摘要生成失败: {e}")

    return quality_report, annotation_report, summary, "\n".join(log)

def handle_file_upload(uploaded_file):
    """读取上传的 .py 文件内容，填充到代码输入框"""
    if uploaded_file is None:
        return ""
    # 兼容字符串路径或文件对象
    file_path = uploaded_file.name if hasattr(uploaded_file, "name") else uploaded_file
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def process_code(source_code: str, incremental: bool = False):
    """主处理函数，返回注释后的代码、文档、日志、.md 下载路径、.py 下载路径

    Args:
        source_code: 源代码字符串
        incremental: 增量更新模式，True 时跳过已有 docstring 的函数（节省 API 调用）
    """
    if not source_code or not source_code.strip():
        return "", "未输入代码", "日志：无处理对象。", None, None

    items = get_defined_functions(source_code)
    if not items:
        return source_code, "未检测到函数或类", "日志：无处理对象。", None, None

    log = []
    annotated_code = source_code
    doc_entries = []

    # 增量更新模式：跳过已有 docstring 的函数
    to_process = []
    skipped = 0
    for item in items:
        if incremental and item["has_docstring"]:
            skipped += 1
            log.append(f"⊘ {item['name']} 已有 docstring，跳过")
            # 仍将现有 docstring 纳入 Markdown 文档，保证文档完整
            existing = ast.get_docstring(item["node"])
            if existing:
                item["docstring"] = existing
                doc_entries.append(item)
        else:
            to_process.append(item)

    if skipped > 0:
        log.append(f"--- 增量模式：跳过 {skipped} 个已有注释的节点 ---")

    if not to_process:
        log.append("所有节点均已有注释，无需调用 LLM。")
    else:
        # ========== 阶段 1：并发调用 LLM 生成 docstring ==========
        # OpenAI 客户端线程安全，可用线程池并发；LLM 调用为 IO 密集型，线程池即可
        MAX_WORKERS = 5
        log.append(f"=== 并发生成 docstring（{len(to_process)} 个节点，{MAX_WORKERS} 并发）===")
        t0 = time.time()

        results = {}  # name -> docstring
        errors = {}   # name -> exception

        def _gen(item):
            """线程任务：调用 LLM 生成 docstring"""
            try:
                doc = generate_docstring(item)
                return item["name"], doc, None
            except Exception as e:
                return item["name"], None, e

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(_gen, item): item for item in to_process}
            for future in as_completed(futures):
                name, doc, err = future.result()
                if err:
                    errors[name] = err
                    log.append(f"✗ {name} 生成失败: {err}")
                else:
                    results[name] = doc
                    log.append(f"✓ {name} 生成完成")

        elapsed = time.time() - t0
        log.append(f"=== LLM 并发阶段完成，耗时 {elapsed:.1f} 秒 ===")

        # ========== 阶段 2：按行号从大到小串行插入 docstring ==========
        # 必须串行：后一个插入依赖前一个插入后的代码；从底向上避免行号漂移
        sorted_items = sorted(to_process, key=lambda x: x["lineno"], reverse=True)
        for item in sorted_items:
            if item["name"] not in results:
                continue
            try:
                doc = results[item["name"]]
                item["docstring"] = doc
                doc_entries.append(item)
                annotated_code = insert_docstring_into_code(annotated_code, item, doc)
            except SyntaxError as e:
                log.append(f"✗ {item['name']} 插入失败: {e}")

    # 按原始顺序排序 doc_entries 用于文档生成
    doc_entries.sort(key=lambda x: x["lineno"])
    markdown_doc = build_markdown_docs(doc_entries)

    # 确保 .py 文件包含 UTF-8 编码声明，Windows 下 PyCharm 才能正确识别中文
    if annotated_code and not annotated_code.startswith('# -*- coding:'):
        annotated_code = '# -*- coding: utf-8 -*-\n' + annotated_code

    # 保存为临时 .md 文件，供下载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    # 保存注释后的 .py 文件（含 UTF-8 编码声明），供下载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        py_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, py_temp_path

# ==================== Gradio 界面 ====================
custom_css = """
/* 限制 Code 组件的高度，强制内部内容滚动 */
.code-container .cm-editor,
.code-container .cm-scroller {
    max-height: 500px !important;
    overflow-y: auto !important;
}

/* 限制 Markdown 组件的高度，强制内容滚动 */
.scrollable-md .prose,
.scrollable-md .markdown-body {
    max-height: 500px !important;
    overflow-y: auto !important;
}

/* 统一左右栏宽度 */
.equal-width > div {
    flex: 1 !important;
}
"""
with gr.Blocks(title="代码注释与文档生成Agent") as demo:
    gr.Markdown("## 📝 代码注释与 API 文档自动生成 Agent")
    gr.Markdown("粘贴 Python 代码或上传 .py 文件，自动生成中文注释和 Markdown API 文档。")

    # 顶部：输入区
    with gr.Row(equal_height=True):
        with gr.Column(elem_classes="equal-width"):
            file_upload = gr.File(label="📤 上传 Python 文件 (.py)", file_types=[".py"])
        with gr.Column(elem_classes="equal-width"):
            input_box = gr.Code(
                label="✏️ 输入代码（粘贴或上传文件后自动填充）",
                language="python", lines=20, max_lines=20,
                elem_classes="code-container"
            )

    # 中间：操作按钮
    with gr.Row():
        btn = gr.Button("🚀 生成注释与文档", variant="primary", size="lg")
        analyze_btn = gr.Button("🔍 分析代码", variant="secondary", size="lg")
    with gr.Row():
        incremental_chk = gr.Checkbox(
            label="增量更新模式（跳过已有注释的函数，节省 API 调用）",
            value=False
        )

    # 底部：输出区（Tab 分页）
    with gr.Tabs():
        with gr.Tab("📄 带注释的代码"):
            output_code = gr.Code(
                label="带注释的代码",
                language="python", lines=20, max_lines=20,
                elem_classes="code-container"
            )
            download_py = gr.File(label="⬇️ 下载注释后的代码 (.py)")
        with gr.Tab("📚 API 文档"):
            output_docs = gr.Markdown(label="生成的 API 文档", elem_classes="scrollable-md")
            download_md = gr.File(label="⬇️ 下载 API 文档 (.md)")
        with gr.Tab("🔍 代码分析"):
            gr.Markdown("### 代码质量分析、类型注解检查与摘要生成")
            quality_output = gr.Markdown(label="代码质量分析", elem_classes="scrollable-md")
            annotation_output = gr.Markdown(label="类型注解检查", elem_classes="scrollable-md")
            summary_output = gr.Markdown(label="代码摘要", elem_classes="scrollable-md")
            analyze_log = gr.Textbox(label="分析日志", lines=5, max_lines=5)
        with gr.Tab("📋 处理日志"):
            output_log = gr.Textbox(label="处理日志", lines=10, max_lines=10)

    # 绑定事件
    file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=input_box)
    btn.click(
        fn=process_code,
        inputs=[input_box, incremental_chk],
        outputs=[output_code, output_docs, output_log, download_md, download_py]
    )
    analyze_btn.click(
        fn=analyze_code,
        inputs=input_box,
        outputs=[quality_output, annotation_output, summary_output, analyze_log]
    )

if __name__ == "__main__":
    demo.launch(css=custom_css)