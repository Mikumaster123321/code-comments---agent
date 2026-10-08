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


_ANALYSIS_LABELS = {
    "中文": {
        "title": "代码质量分析报告", "class": "类", "function": "函数", "name": "函数/类",
        "type": "类型", "lines": "行数", "complexity": "圈复杂度", "depth": "嵌套深度",
        "params": "参数数", "assessment": "评估", "high": "复杂度过高", "raised": "复杂度较高",
        "deep": "嵌套过深", "long": "函数过长", "many": "参数过多", "good": "良好",
        "issues": "需要关注的问题", "all_good": "代码质量良好，未发现明显问题", "none": "无函数/类",
        "line": "行",
    },
    "English": {
        "title": "Code Quality Analysis", "class": "Class", "function": "Function", "name": "Function/Class",
        "type": "Type", "lines": "Lines", "complexity": "Cyclomatic Complexity", "depth": "Nesting Depth",
        "params": "Parameters", "assessment": "Assessment", "high": "High complexity", "raised": "Raised complexity",
        "deep": "Deep nesting", "long": "Long function", "many": "Many parameters", "good": "Good",
        "issues": "Items to review", "all_good": "No obvious quality issues found", "none": "No functions/classes",
        "line": "line",
    },
    "日本語": {
        "title": "コード品質分析", "class": "クラス", "function": "関数", "name": "関数/クラス",
        "type": "種類", "lines": "行数", "complexity": "循環的複雑度", "depth": "ネスト深度",
        "params": "引数数", "assessment": "評価", "high": "複雑度が高い", "raised": "複雑度がやや高い",
        "deep": "ネストが深い", "long": "関数が長い", "many": "引数が多い", "good": "良好",
        "issues": "確認項目", "all_good": "明らかな品質上の問題はありません", "none": "関数/クラスなし",
        "line": "行",
    },
}


def analyze_code_quality(source: str, presentation_lang: str = "中文") -> str:
    """代码质量分析：圈复杂度、嵌套深度、函数长度、参数数量，标记坏味道

    Args:
        source: Python 源代码字符串

    Returns:
        str: Markdown 格式的质量分析报告
    """
    labels = _ANALYSIS_LABELS.get(presentation_lang, _ANALYSIS_LABELS["中文"])
    tree = ast.parse(source)
    rows = []
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            node_type = labels["class"] if isinstance(node, ast.ClassDef) else labels["function"]
            length = node.end_lineno - node.lineno + 1
            complexity = _calc_complexity(node)
            depth = _calc_max_depth(node)
            params = len(node.args.args) if hasattr(node, 'args') else 0

            marks = []
            if complexity > 10:
                marks.append(f"⚠️{labels['high']}")
            elif complexity > 5:
                marks.append(f"⚡{labels['raised']}")
            if depth > 4:
                marks.append(f"⚠️{labels['deep']}")
            if length > 50:
                marks.append(f"⚠️{labels['long']}")
            if params > 5:
                marks.append(f"⚠️{labels['many']}")
            if not marks:
                marks.append(f"✅{labels['good']}")

            eval_str = " ".join(marks)
            rows.append(f"| {name} | {node_type} | {length} | {complexity} | {depth} | {params} | {eval_str} |")

            for m in marks:
                if "⚠️" in m:
                    issues.append(f"- **{name}** ({labels['line']} {node.lineno}): {m[1:]}")

    report = f"### 📊 {labels['title']}\n\n"
    report += f"| {labels['name']} | {labels['type']} | {labels['lines']} | {labels['complexity']} | {labels['depth']} | {labels['params']} | {labels['assessment']} |\n"
    report += "|---------|------|------|----------|----------|--------|------|\n"
    report += "\n".join(rows) if rows else f"| ({labels['none']}) | - | - | - | - | - | - |"
    report += "\n\n"
    if issues:
        report += f"### 🚨 {labels['issues']}\n\n"
        report += "\n".join(issues)
    else:
        report += f"### ✅ {labels['all_good']}"
    return report


def check_type_annotations(source: str, presentation_lang: str = "中文") -> str:
    """类型注解检查：识别缺失类型注解的参数和返回值

    Args:
        source: Python 源代码字符串

    Returns:
        str: Markdown 格式的类型注解检查报告
    """
    labels_by_lang = {
        "中文": ("类型注解检查报告", "参数", "缺少类型注解", "返回值缺少类型注解", "所有函数的类型注解完整", "共发现", "处缺失的类型注解", "行"),
        "English": ("Type Annotation Check", "Parameter", "is missing a type annotation", "Return value is missing a type annotation", "All function type annotations are complete", "Found", "missing type annotations", "line"),
        "日本語": ("型アノテーション確認", "引数", "に型アノテーションがありません", "戻り値に型アノテーションがありません", "すべての関数の型アノテーションは完全です", "不足している型アノテーション", "件", "行"),
    }
    title, param, missing, return_missing, complete, found, unit, line_label = labels_by_lang.get(
        presentation_lang, labels_by_lang["中文"]
    )
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
                    issues.append(f"{param} `{arg.arg}` {missing}")
                    missing_count += 1
            # __init__ 约定返回 None，不需要显式返回值注解
            if node.returns is None and node.name != "__init__":
                issues.append(return_missing)
                missing_count += 1
            if issues:
                sections.append(f"**{name}** ({line_label} {node.lineno}):\n" + "\n".join(f"  - {i}" for i in issues))

    report = f"### 🏷️ {title}\n\n"
    if missing_count == 0:
        report += f"✅ {complete}"
    else:
        report += f"{found} **{missing_count}** {unit}:\n\n"
        report += "\n\n".join(sections)
    return report
