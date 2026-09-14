# -*- coding: utf-8 -*-
from __future__ import annotations
"""注释插入模块：将 docstring 插入代码并生成 Markdown 文档"""
import ast
import re


def _slugify(name: str, prefix: str = "", used: set | None = None) -> str:
    """将任意名称转成 URL 友好的 Markdown 锚点 id，并保证不重复

    规则：只保留字母/数字/连字符/下划线；其余字符用 '-' 替换；保证小写开头
    """
    if not name:
        name = "item"
    base = prefix + re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-_").lower()
    if not base:
        base = (prefix or "item") + "-unknown"
    if used is None:
        return base
    # 去重：如果重复，自动加 -2 / -3 后缀
    final = base
    i = 2
    while final in used:
        final = f"{base}-{i}"
        i += 1
    used.add(final)
    return final


def build_markdown_docs(doc_entries: list) -> str:
    """生成 Markdown API 文档（顶部带目录 TOC，每个条目有锚点）

    Args:
        doc_entries: 文档条目列表，每个条目需包含 name/type/code/docstring/lineno

    Returns:
        str: Markdown 格式的 API 文档（含 TOC 和锚点）
    """
    md = "# API Documentation\n\n"
    used_ids: set[str] = set()
    # 1. 先遍历一遍，给每个条目分配唯一 slug_id
    for entry in doc_entries:
        slug_id = entry.get("slug_id")
        if slug_id and slug_id not in used_ids:
            used_ids.add(slug_id)
        else:
            prefix = "cls-" if entry.get("type") == "class" else "fn-"
            entry["slug_id"] = _slugify(entry["name"], prefix=prefix, used=used_ids)

    # 2. 顶部 Table of Contents 目录
    has_entries = bool(doc_entries)
    if has_entries:
        md += "## 📑 Table of Contents\n\n"
        for entry in doc_entries:
            t = "Class" if entry["type"] == "class" else "Function"
            icon = "🧩" if entry["type"] == "class" else "🔧"
            line = f"  *L{entry.get('lineno', '?')}*"
            md += f"- {icon} [`{entry['name']}` ({t})](#{entry['slug_id']}) — {line}\n"
        md += "\n---\n\n"

    # 3. 各条目详情（每个 heading 后追加 <a id="..."></a> 锚点）
    for entry in doc_entries:
        type_label = "Class" if entry["type"] == "class" else "Function"
        icon = "🧩" if entry["type"] == "class" else "🔧"
        line = f"L{entry.get('lineno', '?')}"
        md += f"## {icon} {entry['name']} ({type_label}) — {line} <a id=\"{entry['slug_id']}\"></a>\n\n"
        md += f"```python\n{entry['code']}\n```\n\n"
        md += f"{entry['docstring']}\n\n"
        if entry["type"] == "class":
            md += "*(Class-level documentation; method-level details are in source code)*\n\n"
        md += "---\n\n"
    return md


def _format_docstring(docstring: str, inner_indent: str) -> str:
    """格式化 docstring：统一换行、缩进和三引号包裹

    Args:
        docstring: docstring 文本
        inner_indent: 缩进字符串（如 4 个空格）

    Returns:
        str: 格式化后的 docstring（含三引号包裹和缩进）
    """
    docstring = docstring.strip()
    body_lines = []
    for line in docstring.split('\n'):
        body_lines.append(f"{inner_indent}{line}")
    body = "\n".join(body_lines)
    return f'{inner_indent}"""\n{body}\n{inner_indent}"""'


def insert_docstring_into_code(source: str, item: dict, docstring: str) -> str:
    """将文档字符串插入到函数/类定义体的第一行（签名结束后）

    Args:
        source: 源代码字符串
        item: 函数/类信息字典，需包含 node/lineno/name
        docstring: docstring 文本

    Returns:
        str: 插入 docstring 后的完整代码

    Raises:
        SyntaxError: 插入后语法校验失败时抛出
    """
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
        start_idx = doc_node.lineno - 1
        end_idx = doc_node.end_lineno
        new_lines = lines[:start_idx] + [formatted_doc] + lines[end_idx:]
    else:
        # 没有 docstring：插入到函数体第一条语句之前
        if node.body:
            insert_idx = node.body[0].lineno - 1
        else:
            insert_idx = node.end_lineno - 1
        new_lines = lines[:insert_idx] + [formatted_doc] + lines[insert_idx:]

    result = "\n".join(new_lines)

    # 安全校验：尝试 AST 解析，失败则抛出异常
    try:
        ast.parse(result)
    except SyntaxError:
        raise SyntaxError(f"插入 docstring 后语法错误，已跳过: {item['name']}")

    return result

