# -*- coding: utf-8 -*-
"""代码分析模块：质量分析、类型注解检查"""
import ast


def _calc_complexity(node) -> int:
    """计算圈复杂度（McCabe）：分支点数量 +1

    Args:
        node: AST 节点

    Returns:
        int: 圈复杂度值
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.Try, ast.ExceptHandler, ast.With, ast.AsyncWith,
                              ast.Match)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def _calc_max_depth(node, current: int = 0) -> int:
    """计算最大嵌套深度

    Args:
        node: AST 节点
        current: 当前深度

    Returns:
        int: 最大嵌套深度
    """
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
    """代码质量分析：圈复杂度、嵌套深度、函数长度、参数数量，标记坏味道

    Args:
        source: Python 源代码字符串

    Returns:
        str: Markdown 格式的质量分析报告
    """
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
    """类型注解检查：识别缺失类型注解的参数和返回值

    Args:
        source: Python 源代码字符串

    Returns:
        str: Markdown 格式的类型注解检查报告
    """
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
