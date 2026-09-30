# -*- coding: utf-8 -*-
"""AST 解析模块：提取函数和类定义"""
import ast


def split_physical_lines(source: str) -> list[str]:
    """Split Python physical lines using the tokenizer's newline model.

    Python AST line numbers advance on LF, CRLF, and CR.  Other Unicode/control
    separators can occur inside source text without advancing an AST line.
    """
    return source.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def get_defined_functions(source: str):
    """使用 AST 提取所有函数和类定义（递归包含类内部方法）

    Args:
        source: Python 源代码字符串

    Returns:
        list[dict]: 每个元素包含 node/name/type/code/lineno/end_lineno/has_docstring
    """
    tree = ast.parse(source)
    items = []

    def _collect(nodes, class_context=None):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno
                code_lines = split_physical_lines(source)[start_line-1:end_line]
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
