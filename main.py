import os
import ast
import re
import tempfile
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
    """使用 AST 提取所有顶级函数和类定义"""
    tree = ast.parse(source)
    items = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = node.end_lineno
            code_lines = source.splitlines()[start_line-1:end_line]
            func_code = "\n".join(code_lines)
            items.append({
                "node": node,
                "name": node.name,
                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                "code": func_code,
                "lineno": start_line,
                "end_lineno": end_line
            })
    return items

PROMPT_TEMPLATE = """你是一位资深 Python 开发工程师。请为以下{func_type}生成中文文档字符串（docstring）。
要求：
1. 使用 Google 风格文档字符串。
2. 必须包含：功能描述、Args（参数名、类型、说明）、Returns（类型、说明）、可能抛出的异常。
3. 如果函数/类内有重要逻辑或算法，请在注释中简要说明。
4. 只输出文档字符串本身，不要包含代码，不要使用代码块标记（不要 ``` ）。

{func_type}名：{name}
源代码：
{code}
"""

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
    # 清理可能的 markdown 代码块标记
    docstring = re.sub(r'^```.*', '', docstring)
    docstring = re.sub(r'```$', '', docstring)
    return docstring.strip()

def insert_docstring_into_code(source: str, item: dict, docstring: str) -> str:
    """将文档字符串插入到原函数定义之后"""
    lines = source.splitlines()
    func_line = lines[item["lineno"] - 1]
    indent = len(func_line) - len(func_line.lstrip())
    base_indent = ' ' * indent
    inner_indent = ' ' * (indent + 4)

    # 格式化 docstring
    formatted_doc = f'{inner_indent}"""\n'
    for line in docstring.split('\n'):
        formatted_doc += f'{inner_indent}{line}\n'
    formatted_doc += f'{inner_indent}"""'

    insert_pos = item["lineno"]  # 在定义行之后插入
    new_lines = lines[:insert_pos] + [formatted_doc] + lines[insert_pos:]
    return "\n".join(new_lines)

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

def handle_file_upload(uploaded_file):
    """读取上传的 .py 文件内容，填充到代码输入框"""
    if uploaded_file is None:
        return ""
    # 兼容字符串路径或文件对象
    file_path = uploaded_file.name if hasattr(uploaded_file, "name") else uploaded_file
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def process_code(source_code: str):
    """主处理函数，返回注释后的代码、文档、日志、.md 下载路径、.py 下载路径"""
    if not source_code or not source_code.strip():
        return "", "未输入代码", "日志：无处理对象。", None, None

    items = get_defined_functions(source_code)
    if not items:
        return source_code, "未检测到函数或类", "日志：无处理对象。", None, None

    log = []
    annotated_code = source_code
    doc_entries = []

    for item in items:
        try:
            log.append(f"正在处理: {item['name']}...")
            doc = generate_docstring(item)
            item["docstring"] = doc
            doc_entries.append(item)
            annotated_code = insert_docstring_into_code(annotated_code, item, doc)
            log.append(f"✓ {item['name']} 完成")
        except Exception as e:
            log.append(f"✗ {item['name']} 失败: {str(e)}")

    markdown_doc = build_markdown_docs(doc_entries)

    # 保存为临时 .md 文件，供下载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    # 保存注释后的 .py 文件，供下载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        py_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, py_temp_path

# ==================== Gradio 界面 ====================
with gr.Blocks(title="代码注释与文档生成Agent") as demo:
    gr.Markdown("## 📝 代码注释与 API 文档自动生成 Agent")
    gr.Markdown("粘贴 Python 代码或上传 .py 文件，自动生成中文注释和 Markdown API 文档。")

    with gr.Row():
        with gr.Column():
            file_upload = gr.File(label="上传 Python 文件 (.py)", file_types=[".py"])
            input_box = gr.Code(label="输入代码（可直接粘贴或上传文件后自动填充）", language="python", lines=20)
        with gr.Column():
            output_code = gr.Code(label="带注释的代码", language="python", lines=20)
            output_docs = gr.Markdown(label="生成的 API 文档")
            output_log = gr.Textbox(label="处理日志", lines=5)
            with gr.Row():
                download_py = gr.File(label="下载注释后的代码 (.py)")
                download_md = gr.File(label="下载 API 文档 (.md)")

    # 上传文件后自动填充到代码输入框
    file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=input_box)

    btn = gr.Button("生成注释与文档", variant="primary")
    btn.click(fn=process_code,
              inputs=input_box,
              outputs=[output_code, output_docs, output_log, download_md, download_py])

if __name__ == "__main__":
    demo.launch()