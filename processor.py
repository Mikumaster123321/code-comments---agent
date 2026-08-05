# -*- coding: utf-8 -*-
"""主处理模块：协调解析、LLM 调用、注释插入，提供 process_code 和 analyze_code"""
import ast
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from parser import get_defined_functions
from llm_service import generate_docstring, generate_code_summary
from annotator import insert_docstring_into_code, build_markdown_docs
from analyzer import analyze_code_quality, check_type_annotations
from config import MAX_WORKERS


def handle_file_upload(uploaded_file):
    """读取上传的 .py 文件内容，填充到代码输入框

    Args:
        uploaded_file: Gradio 文件对象或文件路径字符串

    Returns:
        str: 文件内容
    """
    if uploaded_file is None:
        return ""
    file_path = uploaded_file.name if hasattr(uploaded_file, "name") else uploaded_file
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def process_code(source_code: str, incremental: bool = False):
    """主处理函数，返回注释后的代码、文档、日志、.md 下载路径、.py 下载路径

    Args:
        source_code: 源代码字符串
        incremental: 增量更新模式，True 时跳过已有 docstring 的函数（节省 API 调用）

    Returns:
        tuple: (annotated_code, markdown_doc, log_text, md_path, py_path)
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
        log.append(f"=== 并发生成 docstring（{len(to_process)} 个节点，{MAX_WORKERS} 并发）===")
        t0 = time.time()

        results = {}
        errors = {}

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

    # 确保 .py 文件包含 UTF-8 编码声明
    if annotated_code and not annotated_code.startswith('# -*- coding:'):
        annotated_code = '# -*- coding: utf-8 -*-\n' + annotated_code

    # 保存为临时文件供下载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        py_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, py_temp_path


def analyze_code(source_code: str):
    """主分析函数，返回质量报告、类型注解报告、摘要、日志

    Args:
        source_code: 源代码字符串

    Returns:
        tuple: (quality_report, annotation_report, summary, log_text)
    """
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
