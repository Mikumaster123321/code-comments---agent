# -*- coding: utf-8 -*-
"""Java 注释插入模块：将 Javadoc 注释插入 Java 代码并生成 Markdown 文档"""
import re

from java_parser import _mask_strings_and_comments


def _format_javadoc(docstring: str, indent: str) -> str:
    """格式化 Javadoc：统一换行、缩进和 /** */ 包裹

    Args:
        docstring: Javadoc 文本
        indent: 缩进字符串（如 4 个空格）

    Returns:
        str: 格式化后的 Javadoc 注释（含 /** */ 包裹和缩进）
    """
    docstring = docstring.strip()
    body_lines = []
    for line in docstring.split('\n'):
        if line.strip():
            body_lines.append(f"{indent} * {line}")
        else:
            body_lines.append(f"{indent} *")
    body = "\n".join(body_lines)
    return f"{indent}/**\n{body}\n{indent} */"


def _validate_braces(source: str):
    """简单语法校验：检查大括号是否匹配（屏蔽字符串和注释后）

    Args:
        source: Java 源代码字符串

    Raises:
        SyntaxError: 大括号不匹配时抛出
    """
    masked = _mask_strings_and_comments(source)
    depth = 0
    for ch in masked:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0:
                raise SyntaxError("Java 大括号不匹配：多余的 '}'")
    if depth != 0:
        raise SyntaxError(f"Java 大括号不匹配：缺少 {depth} 个 '}}'")


def insert_javadoc_into_code(source: str, item: dict, docstring: str) -> str:
    """将 Javadoc 注释插入到 Java 类/方法声明上方

    若已存在 Javadoc 则替换，否则在声明上方插入新 Javadoc。

    Args:
        source: 源代码字符串
        item: 方法/类信息字典，需包含 lineno/existing_javadoc
        docstring: Javadoc 文本

    Returns:
        str: 插入 Javadoc 后的完整代码

    Raises:
        SyntaxError: 插入后大括号校验失败时抛出
    """
    lines = source.splitlines()
    lineno = item["lineno"]
    indent = len(lines[lineno - 1]) - len(lines[lineno - 1].lstrip())
    indent_str = ' ' * indent

    javadoc = _format_javadoc(docstring, indent_str)

    existing = item.get("existing_javadoc")
    if existing:
        start, end = existing
        new_lines = lines[:start - 1] + [javadoc] + lines[end:]
    else:
        new_lines = lines[:lineno - 1] + [javadoc] + lines[lineno - 1:]

    result = "\n".join(new_lines)

    # 安全校验：大括号匹配
    try:
        _validate_braces(result)
    except SyntaxError:
        raise SyntaxError(f"插入 Javadoc 后语法错误，已跳过: {item['name']}")

    return result


def extract_existing_javadoc(lines: list, start_line: int, end_line: int) -> str:
    """从源代码行中提取已有的 Javadoc 文本（去除 /** */ 和行首 * 标记）

    Args:
        lines: 源代码行列表
        start_line: Javadoc 起始行号（1-based）
        end_line: Javadoc 结束行号（1-based）

    Returns:
        str: 清理后的 Javadoc 纯文本
    """
    javadoc_lines = lines[start_line - 1: end_line]
    text = '\n'.join(javadoc_lines)
    text = re.sub(r'^\s*/\*\*', '', text)
    text = re.sub(r'\*/\s*$', '', text)
    cleaned = [re.sub(r'^\s*\*\s?', '', line) for line in text.split('\n')]
    return '\n'.join(cleaned).strip()


def build_java_markdown_docs(doc_entries: list) -> str:
    """生成 Java API Markdown 文档

    Args:
        doc_entries: 文档条目列表，每个条目需包含 name/type/code/docstring

    Returns:
        str: Markdown 格式的 API 文档
    """
    md = "# Java API 文档\n\n"
    for entry in doc_entries:
        md += f"## {entry['name']} ({'类' if entry['type']=='class' else '方法'})\n\n"
        md += f"```java\n{entry['code']}\n```\n\n"
        md += f"{entry['docstring']}\n\n"
        if entry["type"] == "class":
            md += "*(类文档，方法细节请见源码)*\n\n"
        md += "---\n\n"
    return md
