# -*- coding: utf-8 -*-
"""主处理模块：协调解析、LLM 调用、注释插入，提供 process_code 和 analyze_code"""
import ast
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from Py.parser import get_defined_functions
from llm_service import (
    generate_docstring, generate_code_summary,
    generate_javadoc, generate_java_summary,
)
from Py.annotator import insert_docstring_into_code, build_markdown_docs
from Java.java_parser import get_defined_functions as get_java_functions
from Java.java_annotator import (
    insert_javadoc_into_code, build_java_markdown_docs,
    extract_existing_javadoc, _validate_braces,
)
from Py.analyzer import analyze_code_quality, check_type_annotations
from config import MAX_WORKERS


def handle_file_upload(uploaded_file):
    """读取上传的源代码文件内容，根据扩展名自动识别语言

    Args:
        uploaded_file: Gradio 文件对象、文件路径字符串或文件信息字典

    Returns:
        tuple: (文件内容, 识别的语言 "Python" / "Java")
    """
    if uploaded_file is None:
        return "", "Python"
    # 兼容多种输入格式：Gradio文件对象（有.name）、字符串路径、字典对象
    if hasattr(uploaded_file, "name"):
        file_path = uploaded_file.name
    elif isinstance(uploaded_file, dict):
        # Gradio 6.x 可能传递 {"path": ..., "url": ..., "orig_name": ...}
        file_path = uploaded_file.get("path") or uploaded_file.get("name") or uploaded_file.get("orig_name", "")
    else:
        file_path = str(uploaded_file)
    if not file_path:
        return "", "Python"
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    language = "Java" if ext == "java" else "Python"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), language
    except (IOError, OSError):
        return "", language


def _process_python(source_code: str, incremental: bool, comment_language: str = "中文"):
    """Python 代码处理流程：解析 → 并发生成 docstring → 串行插入

    Args:
        source_code: Python 源代码字符串
        incremental: 增量更新模式
        comment_language: 注释语言（如"中文"、"English"、"日本語"）

    Returns:
        tuple: (annotated_code, markdown_doc, log_text, md_path, py_path)
    """
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
        log.append(f"=== 并发生成 docstring（{len(to_process)} 个节点，{MAX_WORKERS} 并发）===")
        t0 = time.time()

        results = {}
        errors = {}

        def _gen(item):
            """线程任务：调用 LLM 生成 docstring"""
            try:
                doc = generate_docstring(item, comment_language)
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

    doc_entries.sort(key=lambda x: x["lineno"])
    markdown_doc = build_markdown_docs(doc_entries)

    if annotated_code and not annotated_code.startswith('# -*- coding:'):
        annotated_code = '# -*- coding: utf-8 -*-\n' + annotated_code

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        py_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, py_temp_path


def _process_java(source_code: str, incremental: bool, comment_language: str = "中文"):
    """Java 代码处理流程：解析 → 并发生成 Javadoc → 串行插入

    Args:
        source_code: Java 源代码字符串
        incremental: 增量更新模式
        comment_language: 注释语言（如"中文"、"English"、"日本語"）

    Returns:
        tuple: (annotated_code, markdown_doc, log_text, md_path, java_path)
    """
    items = get_java_functions(source_code)
    if not items:
        return source_code, "未检测到类或方法", "日志：无处理对象。", None, None

    log = []
    annotated_code = source_code
    doc_entries = []
    source_lines = source_code.splitlines()

    # 增量更新模式：跳过已有 Javadoc 的方法
    to_process = []
    skipped = 0
    for item in items:
        if incremental and item["has_docstring"]:
            skipped += 1
            log.append(f"⊘ {item['name']} 已有 Javadoc，跳过")
            existing_range = item.get("existing_javadoc")
            if existing_range:
                existing_text = extract_existing_javadoc(
                    source_lines, existing_range[0], existing_range[1]
                )
                item["docstring"] = existing_text
                doc_entries.append(item)
        else:
            to_process.append(item)

    if skipped > 0:
        log.append(f"--- 增量模式：跳过 {skipped} 个已有注释的节点 ---")

    if not to_process:
        log.append("所有节点均已有注释，无需调用 LLM。")
    else:
        log.append(f"=== 并发生成 Javadoc（{len(to_process)} 个节点，{MAX_WORKERS} 并发）===")
        t0 = time.time()

        results = {}
        errors = {}

        def _gen(item):
            """线程任务：调用 LLM 生成 Javadoc"""
            try:
                doc = generate_javadoc(item, comment_language)
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

        sorted_items = sorted(to_process, key=lambda x: x["lineno"], reverse=True)
        for item in sorted_items:
            if item["name"] not in results:
                continue
            try:
                doc = results[item["name"]]
                item["docstring"] = doc
                doc_entries.append(item)
                annotated_code = insert_javadoc_into_code(annotated_code, item, doc)
            except SyntaxError as e:
                log.append(f"✗ {item['name']} 插入失败: {e}")

    doc_entries.sort(key=lambda x: x["lineno"])
    markdown_doc = build_java_markdown_docs(doc_entries)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        java_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, java_temp_path


def process_code(source_code: str, incremental: bool = False, language: str = "Python", comment_language: str = "中文"):
    """主处理函数，返回注释后的代码、文档、日志、.md 下载路径、源码下载路径

    Args:
        source_code: 源代码字符串
        incremental: 增量更新模式，True 时跳过已有注释的函数（节省 API 调用）
        language: 编程语言（"Python" 或 "Java"）
        comment_language: 注释语言（如"中文"、"English"、"日本語"）

    Returns:
        tuple: (annotated_code, markdown_doc, log_text, md_path, src_path)
    """
    if not source_code or not source_code.strip():
        return "", "未输入代码", "日志：无处理对象。", None, None

    # 代码有效性验证
    if language == "Python" and not _is_valid_python(source_code):
        return source_code, "代码无效，无法生成注释。", "日志：代码无效（语法解析失败），请检查输入。", None, None
    if language == "Java" and not _is_valid_java(source_code):
        return source_code, "代码无效，无法生成注释。", "日志：代码无效（非有效 Java 代码），请检查输入。", None, None

    if language == "Java":
        return _process_java(source_code, incremental, comment_language)
    return _process_python(source_code, incremental, comment_language)


def _is_valid_python(source_code: str) -> bool:
    """检查 Python 代码是否为有意义的代码（非纯标识符/无意义文本）

    Args:
        source_code: Python 源代码字符串

    Returns:
        bool: 是否为有意义的 Python 代码
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return False

    # 检查代码是否包含有意义的结构
    has_def = any(isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))
                  for n in ast.walk(tree))
    has_import = any(isinstance(n, (ast.Import, ast.ImportFrom))
                     for n in ast.walk(tree))
    has_control = any(isinstance(n, (ast.For, ast.While, ast.If, ast.Try, ast.With))
                      for n in ast.walk(tree))
    has_assign = any(isinstance(n, ast.Assign) for n in ast.walk(tree))

    # 至少包含一种代码结构才认为是有意义的代码
    if has_def or has_import or has_control or has_assign:
        return True

    # 对于简单表达式（如 x = 1, print("hello")），检查是否有实际的语句
    lines = [l.strip() for l in source_code.strip().split('\n') if l.strip() and not l.strip().startswith('#')]
    if len(lines) >= 2:
        return True

    # 单行但包含关键字的也算有效
    keywords = ['def ', 'class ', 'import ', 'from ', 'for ', 'while ', 'if ', 'try:', 'with ', 'return ', 'print(', 'lambda ']
    code_lower = source_code.lower()
    return any(kw in code_lower for kw in keywords)


def _is_valid_java(source_code: str) -> bool:
    """检查 Java 代码是否包含基本的 Java 语法特征

    Args:
        source_code: Java 源代码字符串

    Returns:
        bool: 是否可能为有效 Java 代码
    """
    java_keywords = ['class', 'public', 'private', 'protected', 'void', 'int', 'String',
                     'boolean', 'new', 'return', 'import', 'package', 'interface', 'extends']
    lines = source_code.strip().split('\n')
    meaningful_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]
    if not meaningful_lines:
        return False
    matched = sum(1 for kw in java_keywords if kw in source_code)
    brace_count = source_code.count('{') + source_code.count('}')
    return matched >= 1 or brace_count >= 2


def _analyze_java(source_code: str, comment_language: str = "中文"):
    """Java 代码分析：大括号校验 + 代码摘要

    Args:
        source_code: Java 源代码字符串
        comment_language: 摘要语言（如"中文"、"English"、"日本語"）

    Returns:
        tuple: (quality_report, annotation_report, summary, log_text)
    """
    log = []

    # 验证代码有效性
    if not _is_valid_java(source_code):
        return (
            "### ❌ 代码无效\n\n输入的内容不是有效的 Java 代码，无法进行分析。",
            "### ❌ 代码无效\n\n请输入有效的 Java 代码。",
            "代码无效，跳过摘要生成。",
            "日志：代码无效，分析前验证未通过。"
        )

    quality_report = "### 📊 Java 代码质量分析\n\n"

    log.append("=== 大括号匹配校验 ===")
    try:
        _validate_braces(source_code)
        quality_report += "✅ 大括号匹配正常"
        log.append("✓ 大括号匹配正常")
    except SyntaxError as e:
        quality_report += f"❌ {e}"
        log.append(f"✗ 大括号校验失败: {e}")

    annotation_report = "### 🏷️ 类型注解检查\n\nJava 是静态类型语言，类型声明在编译期检查，无需额外分析。"

    log.append("=== 代码摘要生成（调用 LLM）===")
    try:
        summary = generate_java_summary(source_code, comment_language)
        log.append("✓ 摘要生成完成")
    except Exception as e:
        summary = f"摘要生成失败: {e}"
        log.append(f"✗ 摘要生成失败: {e}")

    return quality_report, annotation_report, summary, "\n".join(log)


def analyze_code(source_code: str, language: str = "Python", comment_language: str = "中文"):
    """主分析函数，返回质量报告、类型注解报告、摘要、日志

    Args:
        source_code: 源代码字符串
        language: 编程语言（"Python" 或 "Java"）
        comment_language: 摘要语言（如"中文"、"English"、"日本語"）

    Returns:
        tuple: (quality_report, annotation_report, summary, log_text)
    """
    if not source_code or not source_code.strip():
        return "未输入代码", "未输入代码", "未输入代码", "日志：无处理对象。"

    if language == "Java":
        return _analyze_java(source_code, comment_language)

    # Python 代码有效性验证
    if not _is_valid_python(source_code):
        return (
            "### ❌ 代码无效\n\n输入的内容不是有效的 Python 代码，无法进行分析。\n\n请检查语法或粘贴正确的 Python 代码。",
            "### ❌ 代码无效\n\n请输入有效的 Python 代码。",
            "代码无效，跳过摘要生成。",
            "日志：代码无效（语法解析失败），分析前验证未通过。"
        )

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
        summary = generate_code_summary(source_code, comment_language)
        log.append("✓ 摘要生成完成")
    except Exception as e:
        summary = f"摘要生成失败: {e}"
        log.append(f"✗ 摘要生成失败: {e}")

    return quality_report, annotation_report, summary, "\n".join(log)
