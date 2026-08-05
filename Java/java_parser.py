# -*- coding: utf-8 -*-
"""Java 解析模块：用正则和括号匹配提取类和方法定义（不依赖 Python AST）"""
import re

# 控制流关键字（不视为方法）
CONTROL_KEYWORDS = {'if', 'for', 'while', 'switch', 'try', 'catch', 'do', 'else',
                    'synchronized', 'return', 'new'}


def _mask_strings_and_comments(source: str) -> str:
    """将字符串/字符字面量和注释替换为等长空格（保留换行），便于正则匹配

    Args:
        source: Java 源代码字符串

    Returns:
        str: 屏蔽字面量和注释后的代码（仅保留代码结构）
    """
    def repl(m):
        s = m.group(0)
        return ''.join('\n' if c == '\n' else ' ' for c in s)
    pattern = re.compile(
        r'//[^\n]*'                # 行注释
        r'|/\*[\s\S]*?\*/'        # 块注释（含 Javadoc）
        r'|"(?:\\.|[^"\\])*"'     # 字符串字面量
        r"|'(?:\\.|[^'\\])*'"     # 字符字面量
    )
    return pattern.sub(repl, source)


def _find_javadoc_ranges(source: str):
    """找出所有 Javadoc 注释的行范围

    Args:
        source: Java 源代码字符串

    Returns:
        list[tuple[int, int]]: 每个元素为 (start_line, end_line)，1-based
    """
    ranges = []
    for m in re.finditer(r'/\*\*[\s\S]*?\*/', source):
        start_line = source[:m.start()].count('\n') + 1
        end_line = source[:m.end()].count('\n') + 1
        ranges.append((start_line, end_line))
    return ranges


def _find_matching_brace(masked: str, open_pos: int) -> int:
    """从开花括号位置开始，找到匹配的闭花括号位置

    Args:
        masked: 屏蔽字面量和注释后的代码
        open_pos: 开花括号的字符位置

    Returns:
        int: 闭花括号的字符位置，未找到返回 -1
    """
    depth = 0
    i = open_pos
    n = len(masked)
    while i < n:
        if masked[i] == '{':
            depth += 1
        elif masked[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _line_of(source: str, pos: int) -> int:
    """根据字符位置返回行号（1-based）

    Args:
        source: 源代码字符串
        pos: 字符位置

    Returns:
        int: 行号
    """
    return source[:pos].count('\n') + 1


def _find_decl_start(masked: str, brace_pos: int) -> int:
    """找到声明文本的起始位置（回溯到上一个 ; } { 之后）

    Args:
        masked: 屏蔽后的代码
        brace_pos: 花括号位置

    Returns:
        int: 声明文本起始的字符位置（可能包含前导空白和被屏蔽的注释）
    """
    i = brace_pos - 1
    # 跳过紧邻花括号的空白
    while i >= 0 and masked[i] in ' \t\n\r':
        i -= 1
    # 回溯直到遇到 ; } { 或文件开头
    while i >= 0 and masked[i] not in ';}{':
        i -= 1
    return i + 1


def _skip_leading_whitespace(masked: str, pos: int) -> int:
    """跳过声明文本前导的空白（包括被屏蔽为空格的注释），找到实际声明的起始位置

    Args:
        masked: 屏蔽后的代码
        pos: 声明文本起始位置

    Returns:
        int: 实际声明（修饰符/注解/返回类型）的起始位置
    """
    i = pos
    n = len(masked)
    while i < n and masked[i] in ' \t\n\r':
        i += 1
    return i


def _parse_declaration(decl_text: str):
    """解析声明文本，判断是类还是方法

    Args:
        decl_text: 花括号前的声明文本

    Returns:
        tuple: ('class', name) 或 ('method', name) 或 None
    """
    if not decl_text or not decl_text.strip():
        return None
    # 排除含 new 关键字的语句（匿名类实例化、字段初始化等，非方法声明）
    if re.search(r'\bnew\b', decl_text):
        return None
    # 类/接口/枚举
    m = re.search(r'\b(class|interface|enum)\s+(\w+)', decl_text)
    if m:
        return ('class', m.group(2))
    # 方法/构造器：匹配 name(params) [throws ...] 结尾
    m = re.search(r'(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w.\s,]+)?$', decl_text)
    if m:
        name = m.group(1)
        if name in CONTROL_KEYWORDS:
            return None
        return ('method', name)
    return None


def _find_javadoc_above(lineno: int, lines: list, javadoc_ranges: list):
    """检查声明上方是否有 Javadoc 注释（跳过空行和注解行）

    Args:
        lineno: 声明起始行号
        lines: 源代码行列表
        javadoc_ranges: Javadoc 行范围列表

    Returns:
        tuple: (start_line, end_line) 或 None
    """
    check_line = lineno - 1
    while check_line >= 1:
        line = lines[check_line - 1].strip() if check_line - 1 < len(lines) else ''
        if line == '':
            check_line -= 1
            continue
        if line.startswith('@'):
            check_line -= 1
            continue
        # 检查该行是否是某个 Javadoc 的结束行
        for (js, je) in javadoc_ranges:
            if je == check_line:
                return (js, je)
        break
    return None


def get_defined_functions(source: str):
    """使用正则和括号匹配提取所有 Java 类和方法定义

    Args:
        source: Java 源代码字符串

    Returns:
        list[dict]: 每个元素包含 node/name/type/code/lineno/end_lineno/
                    has_docstring/existing_javadoc
    """
    masked = _mask_strings_and_comments(source)
    javadoc_ranges = _find_javadoc_ranges(source)
    lines = source.splitlines()

    items = []
    seen = set()

    # 遍历所有花括号，找出类和方法声明
    for i, ch in enumerate(masked):
        if ch != '{':
            continue
        decl_start = _find_decl_start(masked, i)
        if decl_start in seen:
            continue
        decl_text = masked[decl_start:i]
        parsed = _parse_declaration(decl_text)
        if parsed is None:
            continue
        seen.add(decl_start)

        decl_type, name = parsed
        # 跳过前导空白和被屏蔽的注释，找到实际声明的起始位置
        actual_start = _skip_leading_whitespace(masked, decl_start)
        lineno = _line_of(source, actual_start)
        close_pos = _find_matching_brace(masked, i)
        if close_pos == -1:
            end_lineno = len(lines)
        else:
            end_lineno = _line_of(source, close_pos)

        code_lines = lines[lineno - 1: end_lineno]
        code = "\n".join(code_lines)

        existing_javadoc = _find_javadoc_above(lineno, lines, javadoc_ranges)

        items.append({
            "node": {
                "decl_start": decl_start,
                "brace_pos": i,
                "close_pos": close_pos,
            },
            "name": name,
            "type": decl_type,
            "code": code,
            "lineno": lineno,
            "end_lineno": end_lineno,
            "has_docstring": existing_javadoc is not None,
            "existing_javadoc": existing_javadoc,
        })

    items.sort(key=lambda x: x["lineno"])
    return items
