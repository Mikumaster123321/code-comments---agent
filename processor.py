# -*- coding: utf-8 -*-
from __future__ import annotations
"""主处理模块：协调解析、LLM 调用、注释插入，提供 process_code / analyze_code / 批量处理

同时提供 *_with_progress 生成器版本，用于 Gradio 实时进度条 + 取消任务。
"""
import ast
import os
import io
import re
import sys
import time
import shutil
import zipfile
import datetime
import tempfile
import difflib
import html
import threading
import math
import subprocess
from pathlib import Path
from typing import Optional, Iterator, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from Py.parser import get_defined_functions
from llm_service import (
    generate_docstring, generate_code_summary,
    generate_javadoc, generate_java_summary,
    translate_docstring, translate_javadoc,
    ping_api_key, estimate_tokens_cost,
)
from config import (
    PRICE_INPUT_PER_M as _PI,
    PRICE_OUTPUT_PER_M as _PO,
    INPUT_RATIO as _IR,
    OUTPUT_RATIO as _OR,
)
from Py.annotator import insert_docstring_into_code, build_markdown_docs
from Java.java_parser import get_defined_functions as get_java_functions
from Java.java_annotator import (
    insert_javadoc_into_code, build_java_markdown_docs,
    extract_existing_javadoc, _validate_braces,
)
from Py.analyzer import analyze_code_quality, check_type_annotations
from config import MAX_WORKERS
from i18n import LANG_CODE, needs_translation


# 允许的源文件扩展名
ALLOWED_SRC_EXTS = {".py", ".java"}
# 允许的压缩包扩展名
ALLOWED_ZIP_EXTS = {".zip"}
# 批量处理时忽略的目录名（大小写敏感粗略过滤）
SKIP_DIR_NAMES = {"__pycache__", ".git", ".idea", ".venv", "venv", "node_modules"}

# ===== v2.3.5 批量 ZIP 输出命名策略 =====
# same: 与源文件同名（直接覆盖到项目目录时使用）
# suffix: 文件名 + _annotated 后缀（默认，避免误覆盖原始文件）
# subdir: 按文件名放到 annotated/ 子目录下，保持原目录结构，再下一层是 annotated/
NAMING_SAME = "same"
NAMING_SUFFIX = "suffix"
NAMING_SUBDIR = "subdir"
NAMING_STRATEGIES = {NAMING_SAME, NAMING_SUFFIX, NAMING_SUBDIR}
# 三种策略的 i18n 友好标签（非 UI 展示；UI 走 i18n.py 翻译字典）
NAMING_LABELS = {
    NAMING_SAME: "Same name as source (overwrite friendly)",
    NAMING_SUFFIX: "Add _annotated suffix (default, safe)",
    NAMING_SUBDIR: "Move to annotated/ subdirectory",
}


# ==================================================================
# 进度条 + 取消任务 基础设施
# ==================================================================

class CancelToken:
    """取消标志位封装：线程安全，可在任意线程调用 cancel() 让生成器安全退出"""

    __slots__ = ("_evt",)

    def __init__(self):
        self._evt = threading.Event()

    def cancel(self) -> None:
        self._evt.set()

    def reset(self) -> None:
        self._evt.clear()

    def is_canceled(self) -> bool:
        return self._evt.is_set()


def _progress_emit(log_lines: list[str], final_5tuple: Optional[tuple]) -> tuple:
    """生成器统一 yield 结构：(annotated_code, markdown_doc, log_text, md_path, src_path)

    Args:
        log_lines: 当前日志行列表
        final_5tuple: 若为 None 表示中间状态；否则为最终 5 元组结果
    """
    log_text = "\n".join(log_lines)
    if final_5tuple is None:
        # 中间态：保持前一帧的其他输出不变（UI 只更新 log_text）
        # 这里用特殊占位：annotated/md/md_path/src_path 都不覆盖，由 UI 保留最近值
        return None, None, log_text, None, None
    return final_5tuple


def _shutdown_executor_safe(executor: ThreadPoolExecutor, futures_map: Optional[dict[Future, object]] = None) -> None:
    """兼容 Python 3.8 的线程池安全关闭：
      - Python 3.9+ 可直接用 shutdown(cancel_futures=True)
      - Python 3.8 无 cancel_futures 参数，改为先手动 cancel 每个 future 再 shutdown

    Args:
        executor: 待关闭的 ThreadPoolExecutor
        futures_map: dict[Future, *]，用于对所有仍在排队/运行中的 future 执行 .cancel()
    """
    if futures_map:
        for f in list(futures_map.keys()):
            try:
                if not f.done():
                    f.cancel()
            except Exception:
                pass
    # 兼容所有 Python 版本的参数
    try:
        executor.shutdown(wait=False, cancel_futures=True)
    except TypeError:
        # Python 3.8：cancel_futures 参数不存在，走 fallback
        executor.shutdown(wait=False)


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


def _process_python(source_code: str, incremental: bool, comment_lang: str = "中文", python_style: Optional[str] = None):
    """Python 代码处理流程：解析 → 并发生成 docstring → 串行插入

    Args:
        source_code: Python 源代码字符串
        incremental: 增量更新模式
        comment_lang: 注释语言（"中文" / "English" / "日本語"）
        python_style: Python 注释风格（Google 风格 / NumPy 风格 / reStructuredText）

    Returns:
        tuple: (annotated_code, markdown_doc, log_text, md_path, py_path)
    """
    lang_code = LANG_CODE.get(comment_lang, "zh")
    items = get_defined_functions(source_code)
    if not items:
        return source_code, "未检测到函数或类", "日志：无处理对象。", None, None

    log = []
    annotated_code = source_code
    doc_entries = []

    # 增量更新模式：跳过已有 docstring 的函数，但需翻译非目标语言的注释
    to_process = []
    to_translate = []
    skipped = 0
    for item in items:
        if incremental and item["has_docstring"]:
            existing = ast.get_docstring(item["node"])
            if existing and needs_translation(existing, lang_code):
                # 已有注释但语言不匹配，需翻译
                to_translate.append(item)
            else:
                skipped += 1
                log.append(f"⊘ {item['name']} 已有 docstring，跳过")
                if existing:
                    item["docstring"] = existing
                    doc_entries.append(item)
        else:
            to_process.append(item)

    if skipped > 0:
        log.append(f"--- 增量模式：跳过 {skipped} 个已有注释的节点 ---")

    # 翻译已有注释（非目标语言）
    if to_translate:
        log.append(f"=== 翻译已有注释为 {comment_lang}（{len(to_translate)} 个节点）===")
        # 按行号倒序翻译插入，防止前面替换后行号错位导致后续插入失败
        to_translate_sorted = sorted(to_translate, key=lambda x: x["lineno"], reverse=True)
        for item in to_translate_sorted:
            try:
                existing = ast.get_docstring(item["node"])
                translated = translate_docstring(existing, comment_lang, python_style)
                item["docstring"] = translated
                doc_entries.append(item)
                annotated_code = insert_docstring_into_code(annotated_code, item, translated)
                log.append(f"✓ {item['name']} 注释已翻译为 {comment_lang}")
            except Exception as e:
                log.append(f"✗ {item['name']} 翻译失败: {e}")
                if existing:
                    item["docstring"] = existing
                    doc_entries.append(item)

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
                doc = generate_docstring(item, comment_lang, python_style)
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
    # 刷新 doc_entries 中的 code 字段：用最终 annotated_code 重新提取，
    # 确保 Markdown 文档代码块中显示的是翻译/生成后的注释，而非原始注释
    try:
        new_items_map = {it["name"]: it for it in get_defined_functions(annotated_code)}
        ann_lines = annotated_code.splitlines()
        for entry in doc_entries:
            it = new_items_map.get(entry["name"])
            if it is None:
                continue
            start = it["lineno"] - 1
            end = it["node"].end_lineno
            entry["code"] = "\n".join(ann_lines[start:end])
    except Exception:
        pass
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


def _process_python_with_progress(
    source_code: str,
    incremental: bool,
    comment_lang: str = "中文",
    python_style: Optional[str] = None,
    cancel_token: Optional[CancelToken] = None,
) -> Iterator[tuple]:
    """Python 代码处理流程（生成器版，带实时进度 & 取消）

    阶段进度（非空代码时）：
      0% - 5%  : 解析
      5% - 20% : 翻译已有注释
      20% - 70%: 并发生成 docstring
      70% - 85%: 插入注释
      85% - 95%: 构建 Markdown & 刷新 code
      95% - 100%: 写临时文件 & 最终结果

    Yields:
        tuple: (annotated_code, markdown_doc, log_text, md_path, src_path) — 中间态返回 None 占位，
               最终 yield 完整 5 元组。
    """
    lang_code = LANG_CODE.get(comment_lang, "zh")
    cancel_token = cancel_token or CancelToken()

    # 阶段 0-5%：解析
    items = get_defined_functions(source_code)
    log: list[str] = []
    if not items:
        msg = "未检测到函数或类"
        log.append(f"日志：{msg}")
        yield source_code, msg, "\n".join(log), None, None
        return
    yield _progress_emit(log, None)
    # 取消但未提前退出：继续走到构建 Markdown 阶段（保留已解析/已翻译结果，并写入临时文件方便下载）
    if cancel_token.is_canceled():
        log.append("⚠️ 任务已取消（保留已解析和已翻译的部分）")

    annotated_code = source_code
    doc_entries: list[dict] = []

    to_process: list[dict] = []
    to_translate: list[dict] = []
    skipped = 0
    for item in items:
        if incremental and item["has_docstring"]:
            existing = ast.get_docstring(item["node"])
            if existing and needs_translation(existing, lang_code):
                to_translate.append(item)
            else:
                skipped += 1
                log.append(f"⊘ {item['name']} 已有 docstring，跳过")
                if existing:
                    item["docstring"] = existing
                    doc_entries.append(item)
        else:
            to_process.append(item)

    if skipped > 0:
        log.append(f"--- 增量模式：跳过 {skipped} 个已有注释的节点 ---")

    total_work = max(1, len(to_translate) + len(to_process))
    # 阶段 5-20%：翻译（若有）
    if to_translate and not cancel_token.is_canceled():
        log.append(f"=== 翻译已有注释为 {comment_lang}（{len(to_translate)} 个节点）===")
        yield _progress_emit(log, None)
        to_translate_sorted = sorted(to_translate, key=lambda x: x["lineno"], reverse=True)
        for idx, item in enumerate(to_translate_sorted, 1):
            if cancel_token.is_canceled():
                break
            try:
                existing = ast.get_docstring(item["node"])
                translated = translate_docstring(existing, comment_lang, python_style)
                item["docstring"] = translated
                doc_entries.append(item)
                annotated_code = insert_docstring_into_code(annotated_code, item, translated)
                log.append(f"✓ {item['name']} 注释已翻译为 {comment_lang}")
            except Exception as e:
                log.append(f"✗ {item['name']} 翻译失败: {e}")
                if existing:
                    item["docstring"] = existing
                    doc_entries.append(item)
            yield _progress_emit(log, None)

    if cancel_token.is_canceled():
        log.append("⚠️ 任务已取消，已翻译部分已保留")
        # 仍然打包已有的结果返回
    else:
        # 阶段 20-70%：并发生成 docstring（支持取消已排队的 future）
        if not to_process:
            log.append("所有节点均已有注释，无需调用 LLM。")
            yield _progress_emit(log, None)
        else:
            log.append(f"=== 并发生成 docstring（{len(to_process)} 个节点，{MAX_WORKERS} 并发）===")
            yield _progress_emit(log, None)
            t0 = time.time()

            results: dict[str, str] = {}
            errors: dict[str, Exception] = {}

            def _gen(item: dict) -> tuple[str, Optional[str], Optional[Exception]]:
                try:
                    doc = generate_docstring(item, comment_lang, python_style)
                    return item["name"], doc, None
                except Exception as e:
                    return item["name"], None, e

            # 非 with：取消时可以主动 shutdown(cancel_futures=True)
            executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
            try:
                futures: dict[Future, dict] = {}
                for item in to_process:
                    fut = executor.submit(_gen, item)
                    futures[fut] = item

                done_count = 0
                for future in as_completed(futures):
                    if cancel_token.is_canceled():
                        # 取消尚未完成的 future
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break
                    try:
                        name, doc, err = future.result()
                    except Exception as e:
                        name = futures[future]["name"]
                        doc, err = None, e
                    done_count += 1
                    if err:
                        errors[name] = err
                        log.append(f"✗ {name} 生成失败: {err}")
                    else:
                        results[name] = doc
                        log.append(f"✓ {name} 生成完成")
                    yield _progress_emit(log, None)
            finally:
                _shutdown_executor_safe(executor, futures)

            elapsed = time.time() - t0
            log.append(f"=== LLM 并发阶段完成，耗时 {elapsed:.1f} 秒 ===")
            yield _progress_emit(log, None)

            # 阶段 70-85%：插入注释
            sorted_items = sorted(to_process, key=lambda x: x["lineno"], reverse=True)
            for item in sorted_items:
                if cancel_token.is_canceled():
                    break
                if item["name"] not in results:
                    continue
                try:
                    doc = results[item["name"]]
                    item["docstring"] = doc
                    doc_entries.append(item)
                    annotated_code = insert_docstring_into_code(annotated_code, item, doc)
                    log.append(f"↳ {item['name']} 注释已插入")
                except SyntaxError as e:
                    log.append(f"✗ {item['name']} 插入失败: {e}")
                yield _progress_emit(log, None)

    if cancel_token.is_canceled():
        log.append("⚠️ 任务已取消")

    # 阶段 85-95%：构建 Markdown + 刷新 code
    doc_entries.sort(key=lambda x: x["lineno"])
    try:
        new_items_map = {it["name"]: it for it in get_defined_functions(annotated_code)}
        ann_lines = annotated_code.splitlines()
        for entry in doc_entries:
            it = new_items_map.get(entry["name"])
            if it is None:
                continue
            start = it["lineno"] - 1
            end = it["node"].end_lineno
            entry["code"] = "\n".join(ann_lines[start:end])
    except Exception:
        pass
    markdown_doc = build_markdown_docs(doc_entries)

    if annotated_code and not annotated_code.startswith('# -*- coding:'):
        annotated_code = '# -*- coding: utf-8 -*-\n' + annotated_code

    yield _progress_emit(log, None)

    # 阶段 95-100%：写临时文件 & 最终结果
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        py_temp_path = f.name

    final = (annotated_code, markdown_doc, "\n".join(log), md_temp_path, py_temp_path)
    yield _progress_emit(log, final)


def _process_java(source_code: str, incremental: bool, comment_lang: str = "中文", java_style: Optional[str] = None):
    """Java 代码处理流程：解析 → 并发生成 Javadoc → 串行插入

    Args:
        source_code: Java 源代码字符串
        incremental: 增量更新模式
        comment_lang: 注释语言（"中文" / "English" / "日本語"）
        java_style: Java 注释风格（标准 Javadoc / 极简行内注释）

    Returns:
        tuple: (annotated_code, markdown_doc, log_text, md_path, java_path)
    """
    lang_code = LANG_CODE.get(comment_lang, "zh")
    items = get_java_functions(source_code)
    if not items:
        return source_code, "未检测到类或方法", "日志：无处理对象。", None, None

    log = []
    annotated_code = source_code
    doc_entries = []
    source_lines = source_code.splitlines()

    # 增量更新模式：跳过已有 Javadoc 的方法，但需翻译非目标语言的注释
    to_process = []
    to_translate = []
    skipped = 0
    for item in items:
        if incremental and item["has_docstring"]:
            existing_range = item.get("existing_javadoc")
            existing_text = None
            if existing_range:
                existing_text = extract_existing_javadoc(
                    source_lines, existing_range[0], existing_range[1]
                )
            if existing_text and needs_translation(existing_text, lang_code):
                # 已有注释但语言不匹配，需翻译
                to_translate.append(item)
            else:
                skipped += 1
                log.append(f"⊘ {item['name']} 已有 Javadoc，跳过")
                if existing_text:
                    item["docstring"] = existing_text
                    doc_entries.append(item)
        else:
            to_process.append(item)

    if skipped > 0:
        log.append(f"--- 增量模式：跳过 {skipped} 个已有注释的节点 ---")

    # 翻译已有注释（非目标语言）
    if to_translate:
        log.append(f"=== 翻译已有注释为 {comment_lang}（{len(to_translate)} 个节点）===")
        # 按行号倒序翻译插入，防止前面替换后行号错位导致后续插入失败
        to_translate_sorted = sorted(to_translate, key=lambda x: x["lineno"], reverse=True)
        for item in to_translate_sorted:
            try:
                existing_range = item.get("existing_javadoc")
                existing_text = extract_existing_javadoc(
                    source_lines, existing_range[0], existing_range[1]
                )
                translated = translate_javadoc(existing_text, comment_lang, java_style)
                item["docstring"] = translated
                doc_entries.append(item)
                annotated_code = insert_javadoc_into_code(annotated_code, item, translated)
                log.append(f"✓ {item['name']} 注释已翻译为 {comment_lang}")
            except Exception as e:
                log.append(f"✗ {item['name']} 翻译失败: {e}")
                if existing_text:
                    item["docstring"] = existing_text
                    doc_entries.append(item)

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
                doc = generate_javadoc(item, comment_lang, java_style)
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
    # 刷新 doc_entries 中的 code 字段：用最终 annotated_code 重新提取，
    # 确保 Markdown 文档代码块中显示的是翻译/生成后的注释，而非原始注释
    try:
        new_items_map = {it["name"]: it for it in get_java_functions(annotated_code)}
        ann_lines = annotated_code.splitlines()
        for entry in doc_entries:
            it = new_items_map.get(entry["name"])
            if it is None:
                continue
            start = it["lineno"] - 1
            end = it.get("end_lineno", len(ann_lines))
            entry["code"] = "\n".join(ann_lines[start:end])
    except Exception:
        pass
    markdown_doc = build_java_markdown_docs(doc_entries)

    # v2.3.4：注释插入后语法二次校验（大括号 + 可选 javac）
    _verify_java_annotated_code(annotated_code, log)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        java_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, java_temp_path


def _process_java_with_progress(
    source_code: str,
    incremental: bool,
    comment_lang: str = "中文",
    java_style: Optional[str] = None,
    cancel_token: Optional[CancelToken] = None,
) -> Iterator[tuple]:
    """Java 代码处理流程（生成器版，带实时进度 & 取消）

    阶段进度（非空代码时）：
      0% - 5%  : 解析
      5% - 20% : 翻译已有 Javadoc
      20% - 70%: 并发生成 Javadoc
      70% - 85%: 插入注释
      85% - 95%: 构建 Markdown & 刷新 code
      95% - 100%: 写临时文件 & 最终结果
    """
    lang_code = LANG_CODE.get(comment_lang, "zh")
    cancel_token = cancel_token or CancelToken()

    items = get_java_functions(source_code)
    log: list[str] = []
    if not items:
        msg = "未检测到类或方法"
        log.append(f"日志：{msg}")
        yield source_code, msg, "\n".join(log), None, None
        return
    yield _progress_emit(log, None)
    # 取消但不提前退出：继续走到构建 Markdown 阶段（保留已解析/已翻译结果，并写入临时文件方便下载）
    if cancel_token.is_canceled():
        log.append("⚠️ 任务已取消（保留已解析和已翻译的部分）")

    annotated_code = source_code
    doc_entries: list[dict] = []
    source_lines = source_code.splitlines()

    to_process: list[dict] = []
    to_translate: list[dict] = []
    skipped = 0
    for item in items:
        if incremental and item["has_docstring"]:
            existing_range = item.get("existing_javadoc")
            existing_text = None
            if existing_range:
                existing_text = extract_existing_javadoc(
                    source_lines, existing_range[0], existing_range[1]
                )
            if existing_text and needs_translation(existing_text, lang_code):
                to_translate.append(item)
            else:
                skipped += 1
                log.append(f"⊘ {item['name']} 已有 Javadoc，跳过")
                if existing_text:
                    item["docstring"] = existing_text
                    doc_entries.append(item)
        else:
            to_process.append(item)

    if skipped > 0:
        log.append(f"--- 增量模式：跳过 {skipped} 个已有注释的节点 ---")

    # 阶段 5-20%：翻译
    if to_translate and not cancel_token.is_canceled():
        log.append(f"=== 翻译已有注释为 {comment_lang}（{len(to_translate)} 个节点）===")
        yield _progress_emit(log, None)
        to_translate_sorted = sorted(to_translate, key=lambda x: x["lineno"], reverse=True)
        for item in to_translate_sorted:
            if cancel_token.is_canceled():
                break
            try:
                existing_range = item.get("existing_javadoc")
                existing_text = extract_existing_javadoc(
                    source_lines, existing_range[0], existing_range[1]
                )
                translated = translate_javadoc(existing_text, comment_lang, java_style)
                item["docstring"] = translated
                doc_entries.append(item)
                annotated_code = insert_javadoc_into_code(annotated_code, item, translated)
                log.append(f"✓ {item['name']} 注释已翻译为 {comment_lang}")
            except Exception as e:
                log.append(f"✗ {item['name']} 翻译失败: {e}")
                if existing_text:
                    item["docstring"] = existing_text
                    doc_entries.append(item)
            yield _progress_emit(log, None)

    if cancel_token.is_canceled():
        log.append("⚠️ 任务已取消，已翻译部分已保留")
    else:
        # 阶段 20-70%：并发生成 Javadoc
        if not to_process:
            log.append("所有节点均已有注释，无需调用 LLM。")
            yield _progress_emit(log, None)
        else:
            log.append(f"=== 并发生成 Javadoc（{len(to_process)} 个节点，{MAX_WORKERS} 并发）===")
            yield _progress_emit(log, None)
            t0 = time.time()

            results: dict[str, str] = {}
            errors: dict[str, Exception] = {}

            def _gen(item: dict) -> tuple[str, Optional[str], Optional[Exception]]:
                try:
                    doc = generate_javadoc(item, comment_lang, java_style)
                    return item["name"], doc, None
                except Exception as e:
                    return item["name"], None, e

            executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
            try:
                futures: dict[Future, dict] = {}
                for item in to_process:
                    fut = executor.submit(_gen, item)
                    futures[fut] = item
                for future in as_completed(futures):
                    if cancel_token.is_canceled():
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break
                    try:
                        name, doc, err = future.result()
                    except Exception as e:
                        name = futures[future]["name"]
                        doc, err = None, e
                    if err:
                        errors[name] = err
                        log.append(f"✗ {name} 生成失败: {err}")
                    else:
                        results[name] = doc
                        log.append(f"✓ {name} 生成完成")
                    yield _progress_emit(log, None)
            finally:
                _shutdown_executor_safe(executor, futures)

            elapsed = time.time() - t0
            log.append(f"=== LLM 并发阶段完成，耗时 {elapsed:.1f} 秒 ===")
            yield _progress_emit(log, None)

            # 阶段 70-85%：插入注释
            sorted_items = sorted(to_process, key=lambda x: x["lineno"], reverse=True)
            for item in sorted_items:
                if cancel_token.is_canceled():
                    break
                if item["name"] not in results:
                    continue
                try:
                    doc = results[item["name"]]
                    item["docstring"] = doc
                    doc_entries.append(item)
                    annotated_code = insert_javadoc_into_code(annotated_code, item, doc)
                    log.append(f"↳ {item['name']} Javadoc 已插入")
                except SyntaxError as e:
                    log.append(f"✗ {item['name']} 插入失败: {e}")
                yield _progress_emit(log, None)

    if cancel_token.is_canceled():
        log.append("⚠️ 任务已取消")

    # 阶段 85-95%：构建 Markdown
    doc_entries.sort(key=lambda x: x["lineno"])
    try:
        new_items_map = {it["name"]: it for it in get_java_functions(annotated_code)}
        ann_lines = annotated_code.splitlines()
        for entry in doc_entries:
            it = new_items_map.get(entry["name"])
            if it is None:
                continue
            start = it["lineno"] - 1
            end = it.get("end_lineno", len(ann_lines))
            entry["code"] = "\n".join(ann_lines[start:end])
    except Exception:
        pass
    markdown_doc = build_java_markdown_docs(doc_entries)

    # v2.3.4：注释插入后语法二次校验（大括号 + 可选 javac），并 yield 一次进度
    _verify_java_annotated_code(annotated_code, log)
    yield _progress_emit(log, None)

    # 阶段 95-100%：写临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        java_temp_path = f.name

    final = (annotated_code, markdown_doc, "\n".join(log), md_temp_path, java_temp_path)
    yield _progress_emit(log, final)


def process_code(source_code: str, incremental: bool = False, language: str = "Python",
                 comment_lang: str = "中文", python_style: Optional[str] = None, java_style: Optional[str] = None):
    """主处理函数，返回注释后的代码、文档、日志、.md 下载路径、源码下载路径

    Args:
        source_code: 源代码字符串
        incremental: 增量更新模式，True 时跳过已有注释的函数（节省 API 调用）
        language: 编程语言（"Python" 或 "Java"）
        comment_lang: 注释语言（"中文" / "English" / "日本語"）
        python_style: Python 注释风格（Google 风格 / NumPy 风格 / reStructuredText）
        java_style: Java 注释风格（标准 Javadoc / 极简行内注释）

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
        return _process_java(source_code, incremental, comment_lang, java_style)
    return _process_python(source_code, incremental, comment_lang, python_style)


def process_code_with_progress(
    source_code: str,
    incremental: bool = False,
    language: str = "Python",
    comment_lang: str = "中文",
    python_style: Optional[str] = None,
    java_style: Optional[str] = None,
    cancel_token: Optional[CancelToken] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> Iterator[tuple]:
    """主处理函数（生成器版，带实时进度 + gr.Progress）

    功能与 process_code 相同，但：
      1. 作为生成器多次 yield，每一步都会更新 output_log 内容；
      2. 支持 CancelToken 让 UI 端取消任务；
      3. 支持 progress_cb(ratio: 0~1, desc: str) 回调（可选），用于 gr.Progress 百分比更新。

    Yields:
        tuple: (annotated_code | None, markdown_doc | None, log_text, md_path | None, src_path | None)
               中间态前 2 项与后 2 项为 None，仅更新 log_text；最终 yield 完整 5 元组。
    """
    cancel_token = cancel_token or CancelToken()

    # 1. 边界：空代码 / 无效代码直接返回（快速路径，不 yield 中间态）
    if not source_code or not source_code.strip():
        yield "", "未输入代码", "日志：无处理对象。", None, None
        return

    if language == "Python" and not _is_valid_python(source_code):
        yield (
            source_code,
            "代码无效，无法生成注释。",
            "日志：代码无效（语法解析失败），请检查输入。",
            None, None,
        )
        return
    if language == "Java" and not _is_valid_java(source_code):
        yield (
            source_code,
            "代码无效，无法生成注释。",
            "日志：代码无效（非有效 Java 代码），请检查输入。",
            None, None,
        )
        return

    if progress_cb is not None:
        try:
            progress_cb(0.02, "解析代码结构")
        except Exception:
            pass

    # 2. 路由到对应语言的生成器，逐次透传 yield
    inner = (
        _process_java_with_progress(source_code, incremental, comment_lang, java_style, cancel_token)
        if language == "Java"
        else _process_python_with_progress(source_code, incremental, comment_lang, python_style, cancel_token)
    )

    final_5tuple: Optional[tuple] = None
    last_log: Optional[str] = None
    # 统计中间步骤数量（粗略估算进度比例）
    for idx, frame in enumerate(inner):
        if cancel_token.is_canceled() and progress_cb is not None:
            try:
                progress_cb(progress_cb if isinstance(progress_cb, float) else 1.0, "已取消")
            except Exception:
                pass
        # frame: (annotated, md_doc, log_text, md_path, src_path)
        ann, md, log_txt, md_p, src_p = frame
        last_log = log_txt
        if ann is not None and md_p is not None and src_p is not None:
            final_5tuple = frame
            if progress_cb is not None:
                try:
                    progress_cb(1.0, "完成")
                except Exception:
                    pass
            yield final_5tuple
            return
        # 中间态：通过 progress_cb 按索引估算 0.02 ~ 0.97 的比例
        if progress_cb is not None:
            # 粗略估算：每一步平均推进一点点
            try:
                step = idx
                est_ratio = min(0.97, 0.05 + 0.92 * (step / max(step + 8, 10)))
                desc = "处理中..."
                if "并发生成" in log_txt or "生成 docstring" in log_txt or "生成 Javadoc" in log_txt:
                    desc = "调用 LLM 生成注释..."
                elif "翻译" in log_txt:
                    desc = "翻译已有注释..."
                elif "插入" in log_txt:
                    desc = "插入注释到源码..."
                elif "Markdown" in log_txt or "构建" in log_txt:
                    desc = "构建 API 文档..."
                elif "检测" in log_txt:
                    desc = "解析代码结构..."
                progress_cb(est_ratio, desc)
            except Exception:
                pass
        # 只更新 log_text，其他保持 None
        yield None, None, log_txt, None, None

    # 兜底（正常情况不会到这里）
    if final_5tuple is not None:
        yield final_5tuple
    else:
        log_txt = last_log or "日志：处理未完成。"
        yield source_code, "", log_txt, None, None


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

    严格化校验（v2.3.4 修复测试报告潜在问题）：
      1. 必须有非空非注释行；
      2. 必须包含 Java 类型声明关键字（class/interface/enum/record）作为独立词；
      3. 大括号必须匹配（屏蔽字符串/注释后），调用 _validate_braces；
      4. 至少有 1 个大括号对（避免纯关键字文本误判）。

    Args:
        source_code: Java 源代码字符串

    Returns:
        bool: 是否可能为有效 Java 代码
    """
    if not source_code or not source_code.strip():
        return False
    lines = source_code.strip().split('\n')
    meaningful_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]
    if not meaningful_lines:
        return False

    # 1. 必须含类型声明关键字（词边界匹配，避免 "hello class world" 误判）
    type_decl_pattern = re.compile(r'\b(?:class|interface|enum|record)\b')
    if not type_decl_pattern.search(source_code):
        return False

    # 2. 至少有 1 对大括号
    if source_code.count('{') < 1 or source_code.count('}') < 1:
        return False

    # 3. 大括号匹配校验（屏蔽字符串/注释后），失败则视为无效
    try:
        _validate_braces(source_code)
    except SyntaxError:
        return False

    return True


def _verify_java_annotated_code(annotated_code: str, log: list[str]) -> None:
    """Java 注释插入后的语法二次校验（v2.3.4 修复测试报告潜在问题）

    校验两步（失败仅日志警告，不抛异常、不阻断下载）：
      1. _validate_braces 大括号匹配；
      2. 若 PATH 中存在 javac，调用 `javac -d <tmpdir> <tmpfile>` 做真实语法检查
         （超时 15s，stderr 截取首行错误信息）。

    Args:
        annotated_code: 注释插入后的 Java 源代码
        log: 日志列表，校验结果会追加到此列表
    """
    # 1. 大括号匹配校验
    try:
        _validate_braces(annotated_code)
        log.append("✓ 注释后大括号匹配校验通过")
    except SyntaxError as e:
        log.append(f"⚠️ 注释后大括号匹配失败: {e}（建议检查源码）")

    # 2. javac 可选语法验证（仅在系统 PATH 中存在 javac 时调用）
    try:
        if not shutil.which("javac"):
            return
    except Exception:
        return

    tmp_dir = tempfile.mkdtemp(prefix="javac_check_")
    tmp_java = os.path.join(tmp_dir, "_AnnotatedCheck.java")
    try:
        with open(tmp_java, "w", encoding="utf-8") as f:
            f.write(annotated_code)
        proc = subprocess.run(
            ["javac", "-Xlint:none", "-encoding", "UTF-8", tmp_java],
            capture_output=True,
            timeout=15,
        )
        if proc.returncode == 0:
            log.append("✓ javac 语法校验通过")
        else:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            first_err = err.splitlines()[0] if err else "未知错误"
            log.append(f"⚠️ javac 语法校验失败: {first_err}（建议检查源码）")
    except subprocess.TimeoutExpired:
        log.append("⚠️ javac 语法校验超时（15s），已跳过")
    except Exception as e:
        log.append(f"⚠️ javac 语法校验异常: {e}")
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


def _analyze_java(source_code: str, comment_lang: str = "中文"):
    """Java 代码分析：大括号校验 + 代码摘要

    Args:
        source_code: Java 源代码字符串
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

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
        summary = generate_java_summary(source_code, comment_lang)
        log.append("✓ 摘要生成完成")
    except Exception as e:
        summary = f"摘要生成失败: {e}"
        log.append(f"✗ 摘要生成失败: {e}")

    return quality_report, annotation_report, summary, "\n".join(log)


def analyze_code(source_code: str, language: str = "Python", comment_lang: str = "中文"):
    """主分析函数，返回质量报告、类型注解报告、摘要、日志

    Args:
        source_code: 源代码字符串
        language: 编程语言（"Python" 或 "Java"）
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

    Returns:
        tuple: (quality_report, annotation_report, summary, log_text)
    """
    if not source_code or not source_code.strip():
        return "未输入代码", "未输入代码", "未输入代码", "日志：无处理对象。"

    if language == "Java":
        return _analyze_java(source_code, comment_lang)

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
        summary = generate_code_summary(source_code, comment_lang)
        log.append("✓ 摘要生成完成")
    except Exception as e:
        summary = f"摘要生成失败: {e}"
        log.append(f"✗ 摘要生成失败: {e}")

    return quality_report, annotation_report, summary, "\n".join(log)


# ==================================================================
# 批量处理（多文件 / ZIP 压缩包）
# ==================================================================

def _resolve_upload_path(uploaded) -> Optional[str]:
    """兼容 Gradio 文件对象/字典/字符串，解析出可读取的本地路径

    Args:
        uploaded: Gradio 单文件或批量上传返回的单个元素

    Returns:
        str 或 None: 可 open 的本地文件路径
    """
    if uploaded is None:
        return None
    # 优先用对象的 name 属性
    if hasattr(uploaded, "name") and uploaded.name:
        return uploaded.name
    # Gradio 6.x dict 格式
    if isinstance(uploaded, dict):
        for key in ("path", "name", "orig_name"):
            v = uploaded.get(key)
            if v:
                return v
    # 兜底：直接字符串
    s = str(uploaded)
    return s if os.path.isfile(s) else None


def _collect_source_files(root_dir: str, base_rel: str = "") -> list[tuple[str, str]]:
    """在目录中递归收集所有允许的源代码文件

    Args:
        root_dir: 扫描根目录
        base_rel: 为结果 rel_path 附加的前缀（通常是 zip 名或上传名）

    Returns:
        list[(abs_path, rel_path)]: 绝对路径与归档用的相对路径
    """
    results: list[tuple[str, str]] = []
    for current, dirnames, filenames in os.walk(root_dir):
        # 忽略明显不需要的目录
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_SRC_EXTS:
                continue
            abs_path = os.path.join(current, filename)
            rel = os.path.relpath(abs_path, root_dir)
            rel_path = os.path.join(base_rel, rel) if base_rel else rel
            rel_path = rel_path.replace(os.sep, "/")
            results.append((abs_path, rel_path))
    results.sort(key=lambda x: x[1])
    return results


def _extract_zip_safe(zip_path: str, target_dir: str) -> str:
    """安全解压 zip，防止 zip slip，返回真实的公共根目录或 target_dir

    Args:
        zip_path: zip 文件路径
        target_dir: 临时解压目录

    Returns:
        实际用于文件收集的根目录（通常是 target_dir）
    """
    target_abs = os.path.abspath(target_dir)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # zip slip 防御：解析后路径必须在 target_abs 之下
            member_path = os.path.abspath(os.path.join(target_dir, member.filename))
            if not member_path.startswith(target_abs + os.sep) and member_path != target_abs:
                continue  # 跳过异常条目
            # 跳过纯目录条目创建（避免空目录报错）
            if member.is_dir():
                os.makedirs(member_path, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(member_path), exist_ok=True)
            # 按 UTF-8 解码失败时回退到 cp437（常见 Windows zip 文件名编码问题）
            try:
                extracted = zf.extract(member, target_dir)
            except UnicodeDecodeError:
                # 尝试重新编码原始文件名
                raw = member.filename.encode("cp437", errors="ignore")
                decoded = raw.decode("gbk", errors="replace")
                target_path = os.path.join(target_dir, decoded)
                if not (os.path.abspath(target_path).startswith(target_abs + os.sep)):
                    continue
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(member) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted = target_path
            else:
                _ = extracted  # 保留变量，避免 linter 警告
    return target_dir


def _apply_naming_strategy(rel_path: str, strategy: str) -> str:
    """按命名策略把输出相对路径转换为 ZIP 归档路径

    v2.3.5 新增：批量 ZIP 输出文件命名可配置。

    Args:
        rel_path: 原始输出路径（POSIX 斜杠分隔），如 "mylib/utils.py" / "Main.java"
        strategy: NAMING_SAME / NAMING_SUFFIX / NAMING_SUBDIR

    Returns:
        str: 应用策略后的新归档路径（POSIX 斜杠分隔）
    """
    strategy = strategy if strategy in NAMING_STRATEGIES else NAMING_SUFFIX
    posix = rel_path.replace("\\", "/")
    directory, basename = posix.rsplit("/", 1) if "/" in posix else ("", posix)
    stem, ext = basename.rsplit(".", 1) if "." in basename else (basename, "")
    ext = f".{ext}" if ext else ""

    if strategy == NAMING_SAME:
        return posix
    if strategy == NAMING_SUFFIX:
        new_name = f"{stem}_annotated{ext}"
        return f"{directory}/{new_name}" if directory else new_name
    # NAMING_SUBDIR: 所有源码放入 annotated/ 顶层子目录，原目录结构保留
    return f"annotated/{posix}"


def _build_batch_zip(
    output_dir: str,
    log_text: str,
    aggregate_md: Optional[str] = None,
    naming_strategy: str = NAMING_SUFFIX,
) -> str:
    """将 output_dir 内处理后的结果打包为 zip，外加日志和聚合文档

    v2.3.5 新增 naming_strategy：按策略重命名归档路径（默认 _annotated 后缀）。

    Args:
        output_dir: 包含 annotated 源代码文件的输出目录（结构完整）
        log_text: 处理日志文本
        aggregate_md: 聚合 Markdown 文档（可空）
        naming_strategy: 输出命名策略 NAMING_SAME / NAMING_SUFFIX / NAMING_SUBDIR

    Returns:
        str: 打包后的临时 zip 文件绝对路径
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_out = tempfile.NamedTemporaryFile(
        mode="wb", prefix="annotated_batch_", suffix=f"_{ts}.zip", delete=False
    )
    zip_out.close()
    with zipfile.ZipFile(zip_out.name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. 源码（保持相对路径，按 naming_strategy 重命名）
        for current, _, filenames in os.walk(output_dir):
            for fn in filenames:
                abs_p = os.path.join(current, fn)
                rel_p = os.path.relpath(abs_p, output_dir).replace(os.sep, "/")
                archive_p = _apply_naming_strategy(rel_p, naming_strategy)
                zf.write(abs_p, archive_p)
        # 2. 处理日志
        zf.writestr("processing.log", log_text.encode("utf-8"))
        # 3. 聚合文档
        if aggregate_md:
            zf.writestr("API_DOCS_ALL.md", aggregate_md.encode("utf-8"))
    return zip_out.name


def process_batch_files(
    uploaded_files: list,
    comment_lang: str = "中文",
    incremental: bool = True,
    python_style: Optional[str] = None,
    java_style: Optional[str] = None,
    naming_strategy: str = NAMING_SUFFIX,
) -> tuple[str, Optional[str]]:
    """批量处理上传的多个文件或 ZIP 压缩包

    处理流程：
      1. 展开上传列表（混合多文件 + zip）
      2. zip 自动解压到临时目录 → 递归扫描 .py/.java
      3. 单文件直接按文件列表加入
      4. 对每个源文件调用 process_code（保留相对路径）
      5. 写出注释后的代码 + 聚合 API 文档 → 打包 zip 返回

    Args:
        uploaded_files: Gradio Upload 的文件列表（file_count="multiple" / 或包含 zip）
        comment_lang: 注释目标语言（"中文" / "English" / "日本語"）
        incremental: 是否增量模式（默认 True，跳过匹配注释并翻译不匹配的）
        python_style: Python 注释风格（Google 风格 / NumPy 风格 / reStructuredText）
        java_style: Java 注释风格（标准 Javadoc / 极简行内注释）
        naming_strategy: ZIP 源码输出命名策略 NAMING_SAME / NAMING_SUFFIX（默认） / NAMING_SUBDIR

    Returns:
        (log_text, zip_path): 处理日志文本 + 打包 zip 的临时路径（可用于 gr.DownloadButton）
    """
    if naming_strategy not in NAMING_STRATEGIES:
        naming_strategy = NAMING_SUFFIX
    log: list[str] = []
    # 1. 展开上传，解析路径
    if not uploaded_files:
        return "[错误] 未上传任何文件。", None
    # 统一成列表：用户可能传单个（非列表）或列表
    raw_list = uploaded_files if isinstance(uploaded_files, (list, tuple)) else [uploaded_files]
    file_records: list[tuple[str, str]] = []  # (本地绝对路径, 归档用相对路径)
    # 对非 zip 单文件上传，用「原始源路径」记录 → 后续基于它们求公共父级，保留目录结构
    nonzip_sources: list[tuple[str, str]] = []  # (staged_path, original_src_abs_path)
    tmp_root = tempfile.mkdtemp(prefix="batch_annot_")
    try:
        extract_stage = os.path.join(tmp_root, "in")
        os.makedirs(extract_stage, exist_ok=True)
        idx = 0
        for item in raw_list:
            src_path = _resolve_upload_path(item)
            if not src_path or not os.path.isfile(src_path):
                log.append(f"[跳过] 无法解析文件路径: {item!r}")
                continue
            name = os.path.basename(src_path)
            ext = os.path.splitext(name)[1].lower()
            if ext in ALLOWED_ZIP_EXTS:
                idx += 1
                zip_out = os.path.join(extract_stage, f"zip_{idx:02d}_{name}")
                os.makedirs(zip_out, exist_ok=True)
                try:
                    _extract_zip_safe(src_path, zip_out)
                    base_rel = os.path.splitext(name)[0]
                    collected = _collect_source_files(zip_out, base_rel)
                    log.append(f"[ZIP] 解压 {name}: 发现 {len(collected)} 个源文件")
                    file_records.extend(collected)
                except zipfile.BadZipFile:
                    log.append(f"[错误] {name} 不是有效的 zip 文件")
                except Exception as e:
                    log.append(f"[错误] 解压 {name} 失败: {e}")
            elif ext in ALLOWED_SRC_EXTS:
                # 单文件：先复制到 stage，延迟决定 rel_path（放到 nonzip_sources，之后根据公共父级决定）
                staged = os.path.join(extract_stage, f"file_{idx:02d}_{name}")
                idx += 1
                shutil.copyfile(src_path, staged)
                nonzip_sources.append((staged, os.path.abspath(src_path)))
                log.append(f"[文件] 加入待处理: {name}")
            else:
                log.append(f"[跳过] 不支持的文件类型: {name} ({ext})")

        # 1b. 非 zip 单文件：按原始源路径计算公共父级，生成 rel_path（保留目录结构）
        if nonzip_sources:
            # 求所有原始源文件的最长公共父目录（按绝对路径分割后的公共前缀）
            parts_list = [Path(src_abs).parts for _, src_abs in nonzip_sources]
            common_len = 0
            min_len = min(len(p) for p in parts_list)
            for i in range(min_len):
                if len({p[i] for p in parts_list}) == 1:
                    common_len = i + 1
                else:
                    break
            # 如果 common_len 已把「文件名」也匹配了（多文件相同路径，几乎不会发生），
            # 退一格避免 relpath 为空。
            if common_len == min(len(p) for p in parts_list) and len(parts_list) > 1:
                common_len = max(0, common_len - 1)
            # 关键：公共父级再向上退一层，使 relpath 保留「源目录相对结构」。
            # 例：src/pkg/utils.py + src/pkg/Helper.java → 公共 parts 到 src/pkg；
            #     退一层到 src → relpath 为 pkg/utils.py / pkg/Helper.java。
            # common_len == 1 通常只剩盘符，不再退。
            if common_len > 1:
                common_len -= 1
            if common_len > 0:
                parent_parts = parts_list[0][:common_len]
                # 卷标如 (C:\\, ...) 在 Windows 下 os.path.join 会报错，用 Path 构造
                common_parent = str(Path(*parent_parts))
            else:
                common_parent = None
            # 生成 rel_path：保留从公共父级到文件的相对路径
            for staged, src_abs in nonzip_sources:
                if common_parent and src_abs.startswith(common_parent + os.sep):
                    rel_raw = os.path.relpath(src_abs, common_parent)
                elif common_parent and os.path.abspath(src_abs).startswith(os.path.abspath(common_parent) + os.sep):
                    rel_raw = os.path.relpath(src_abs, common_parent)
                else:
                    # 没有公共父级（跨盘）：退化为 basename（避免全部打平 + 避免引用越界变量）
                    rel_raw = os.path.basename(src_abs)
                rel_p = rel_raw.replace(os.sep, "/")
                file_records.append((staged, rel_p))

        if not file_records:
            log.append("[错误] 没有发现可处理的 .py/.java 源文件")
            return "\n".join(log), None

        # 2. 按顺序处理每个文件（process_code 内部已有并发，这里保持顺序便于读日志）
        output_stage = os.path.join(tmp_root, "out")
        os.makedirs(output_stage, exist_ok=True)
        total = len(file_records)
        success = 0
        fail = 0
        aggregate_docs: list[str] = []
        log.append("")
        log.append(
            f"=== 批量处理开始：共 {total} 个文件，注释语言: {comment_lang}，增量: {incremental}，"
            f"命名策略: {naming_strategy} ==="
        )
        for abs_path, rel_path in file_records:
            log.append("-" * 60)
            log.append(f"  [处理中] {rel_path}")
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except UnicodeDecodeError:
                try:
                    with open(abs_path, "r", encoding="gbk") as f:
                        code = f.read()
                except Exception as e:
                    log.append(f"  ✗ 读取失败: {e}")
                    fail += 1
                    continue
            language = "Java" if abs_path.lower().endswith(".java") else "Python"
            try:
                annotated, markdown_doc, per_log, _md_p, _src_p = process_code(
                    code, incremental=incremental, language=language, comment_lang=comment_lang,
                    python_style=python_style, java_style=java_style,
                )
            except Exception as e:
                log.append(f"  ✗ process_code 异常: {e}")
                fail += 1
                continue
            # 输出保持相对路径结构
            out_file = os.path.join(output_stage, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            try:
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(annotated)
            except Exception as e:
                log.append(f"  ✗ 写出失败: {e}")
                fail += 1
                continue
            # 聚合 Markdown（按文件分节）
            if markdown_doc and markdown_doc.strip():
                aggregate_docs.append(f"# {rel_path}\n\n{markdown_doc}\n")
            for ln in per_log.splitlines()[:6]:  # 每个文件最多展示 6 行日志
                if ln.strip():
                    log.append(f"      | {ln}")
            log.append(f"  ✓ 完成: {rel_path}")
            success += 1
        log.append("-" * 60)
        log.append(f"=== 批量处理完成: 成功 {success}, 失败 {fail}, 总计 {total} ===")

        if success == 0:
            log.append("[错误] 没有成功处理的文件，跳过打包")
            return "\n".join(log), None

        # 3. 聚合文档与打包
        aggregate_md = "\n\n".join(aggregate_docs) if aggregate_docs else None
        try:
            zip_path = _build_batch_zip(output_stage, "\n".join(log), aggregate_md, naming_strategy)
        except Exception as e:
            log.append(f"[错误] 打包 zip 失败: {e}")
            return "\n".join(log), None
        log.append(f"[完成] 结果已打包: {os.path.basename(zip_path)}")
        return "\n".join(log), zip_path
    finally:
        # 清理临时目录（注意：返回的 zip 文件在 tmp_root 之外的 tempfile 命名区，不会被删）
        try:
            shutil.rmtree(tmp_root, ignore_errors=True)
        except Exception:
            pass


def process_batch_with_progress(
    uploaded_files: list,
    comment_lang: str = "中文",
    incremental: bool = True,
    python_style: Optional[str] = None,
    java_style: Optional[str] = None,
    naming_strategy: str = NAMING_SUFFIX,
    cancel_token: Optional[CancelToken] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> Iterator[tuple[str, Optional[str]]]:
    """批量处理（生成器版，带实时进度 + 取消 + gr.Progress）

    与 process_batch_files 功能相同，但：
      1. 每处理完 1 个文件 yield 一次 (log_text, None) 让 UI 更新日志；
      2. 最终 yield 一次 (log_text, zip_path) 含打包结果路径；
      3. 支持 CancelToken 取消（取消后立即返回已处理成功的部分打包结果）。

    v2.3.5 新增 naming_strategy 参数：ZIP 源码输出命名策略 same / suffix（默认） / subdir。

    Yields:
        (log_text: str, zip_path: str | None)
    """
    if naming_strategy not in NAMING_STRATEGIES:
        naming_strategy = NAMING_SUFFIX
    cancel_token = cancel_token or CancelToken()

    log: list[str] = []
    if not uploaded_files:
        yield "[错误] 未上传任何文件。", None
        return

    raw_list = uploaded_files if isinstance(uploaded_files, (list, tuple)) else [uploaded_files]
    file_records: list[tuple[str, str]] = []
    nonzip_sources: list[tuple[str, str]] = []  # (staged_path, original_src_abs_path)
    tmp_root = tempfile.mkdtemp(prefix="batch_annot_")
    try:
        extract_stage = os.path.join(tmp_root, "in")
        os.makedirs(extract_stage, exist_ok=True)
        idx = 0
        if progress_cb is not None:
            try:
                progress_cb(0.0, "展开上传文件...")
            except Exception:
                pass
        for item in raw_list:
            src_path = _resolve_upload_path(item)
            if not src_path or not os.path.isfile(src_path):
                log.append(f"[跳过] 无法解析文件路径: {item!r}")
                continue
            name = os.path.basename(src_path)
            ext = os.path.splitext(name)[1].lower()
            if ext in ALLOWED_ZIP_EXTS:
                idx += 1
                zip_out = os.path.join(extract_stage, f"zip_{idx:02d}_{name}")
                os.makedirs(zip_out, exist_ok=True)
                try:
                    _extract_zip_safe(src_path, zip_out)
                    base_rel = os.path.splitext(name)[0]
                    collected = _collect_source_files(zip_out, base_rel)
                    log.append(f"[ZIP] 解压 {name}: 发现 {len(collected)} 个源文件")
                    file_records.extend(collected)
                except zipfile.BadZipFile:
                    log.append(f"[错误] {name} 不是有效的 zip 文件")
                except Exception as e:
                    log.append(f"[错误] 解压 {name} 失败: {e}")
            elif ext in ALLOWED_SRC_EXTS:
                staged = os.path.join(extract_stage, f"file_{idx:02d}_{name}")
                idx += 1
                shutil.copyfile(src_path, staged)
                nonzip_sources.append((staged, os.path.abspath(src_path)))
                log.append(f"[文件] 加入待处理: {name}")
            else:
                log.append(f"[跳过] 不支持的文件类型: {name} ({ext})")
            yield "\n".join(log), None
            if cancel_token.is_canceled():
                log.append("⚠️ 批量任务已取消（解压阶段）")
                yield "\n".join(log), None
                return

        # 1b. 非 zip 单文件：按原始源路径计算公共父级，生成 rel_path（保留目录结构）
        if nonzip_sources:
            parts_list = [Path(src_abs).parts for _, src_abs in nonzip_sources]
            common_len = 0
            min_len = min(len(p) for p in parts_list)
            for i in range(min_len):
                if len({p[i] for p in parts_list}) == 1:
                    common_len = i + 1
                else:
                    break
            if common_len == min(len(p) for p in parts_list) and len(parts_list) > 1:
                common_len = max(0, common_len - 1)
            # 关键：公共父级再向上退一层（保证 relpath 保留源目录相对结构）
            if common_len > 1:
                common_len -= 1
            if common_len > 0:
                parent_parts = parts_list[0][:common_len]
                common_parent = str(Path(*parent_parts))
            else:
                common_parent = None
            for staged, src_abs in nonzip_sources:
                if common_parent and src_abs.startswith(common_parent + os.sep):
                    rel_raw = os.path.relpath(src_abs, common_parent)
                elif common_parent and os.path.abspath(src_abs).startswith(os.path.abspath(common_parent) + os.sep):
                    rel_raw = os.path.relpath(src_abs, common_parent)
                else:
                    rel_raw = os.path.basename(src_abs)
                rel_p = rel_raw.replace(os.sep, "/")
                file_records.append((staged, rel_p))

        if not file_records:
            log.append("[错误] 没有发现可处理的 .py/.java 源文件")
            yield "\n".join(log), None
            return

        output_stage = os.path.join(tmp_root, "out")
        os.makedirs(output_stage, exist_ok=True)
        total = len(file_records)
        success = 0
        fail = 0
        aggregate_docs: list[str] = []
        log.append("")
        log.append(
            f"=== 批量处理开始：共 {total} 个文件，注释语言: {comment_lang}，增量: {incremental}，"
            f"命名策略: {naming_strategy} ==="
        )
        yield "\n".join(log), None

        for i, (abs_path, rel_path) in enumerate(file_records, 1):
            if cancel_token.is_canceled():
                log.append("⚠️ 批量任务已取消（处理阶段），已处理文件将保留并打包")
                break
            log.append("-" * 60)
            log.append(f"  [处理中 {i}/{total}] {rel_path}")
            if progress_cb is not None:
                try:
                    progress_cb(0.05 + 0.90 * ((i - 1) / max(total, 1)), f"处理 {rel_path}")
                except Exception:
                    pass
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except UnicodeDecodeError:
                try:
                    with open(abs_path, "r", encoding="gbk") as f:
                        code = f.read()
                except Exception as e:
                    log.append(f"  ✗ 读取失败: {e}")
                    fail += 1
                    yield "\n".join(log), None
                    continue
            except Exception as e:
                log.append(f"  ✗ 读取失败: {e}")
                fail += 1
                yield "\n".join(log), None
                continue
            language = "Java" if abs_path.lower().endswith(".java") else "Python"
            try:
                annotated, markdown_doc, per_log, _md_p, _src_p = process_code(
                    code, incremental=incremental, language=language, comment_lang=comment_lang,
                    python_style=python_style, java_style=java_style,
                )
            except Exception as e:
                log.append(f"  ✗ process_code 异常: {e}")
                fail += 1
                yield "\n".join(log), None
                continue
            out_file = os.path.join(output_stage, rel_path.replace("/", os.sep))
            try:
                os.makedirs(os.path.dirname(out_file), exist_ok=True)
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(annotated)
            except Exception as e:
                log.append(f"  ✗ 写出失败: {e}")
                fail += 1
                yield "\n".join(log), None
                continue
            if markdown_doc and markdown_doc.strip():
                aggregate_docs.append(f"# {rel_path}\n\n{markdown_doc}\n")
            for ln in per_log.splitlines()[:6]:
                if ln.strip():
                    log.append(f"      | {ln}")
            log.append(f"  ✓ 完成: {rel_path}")
            success += 1
            yield "\n".join(log), None

        log.append("-" * 60)
        log.append(f"=== 批量处理完成: 成功 {success}, 失败 {fail}, 总计 {total} ===")
        if cancel_token.is_canceled():
            log.append("⚠️ （用户主动取消，仅返回已处理成功的部分）")
        yield "\n".join(log), None

        if success == 0:
            log.append("[错误] 没有成功处理的文件，跳过打包")
            yield "\n".join(log), None
            return

        if progress_cb is not None:
            try:
                progress_cb(0.96, "打包 ZIP 结果...")
            except Exception:
                pass
        aggregate_md = "\n\n".join(aggregate_docs) if aggregate_docs else None
        try:
            zip_path = _build_batch_zip(output_stage, "\n".join(log), aggregate_md, naming_strategy)
        except Exception as e:
            log.append(f"[错误] 打包 zip 失败: {e}")
            yield "\n".join(log), None
            return
        log.append(f"[完成] 结果已打包: {os.path.basename(zip_path)}")
        if progress_cb is not None:
            try:
                progress_cb(1.0, "完成")
            except Exception:
                pass
        yield "\n".join(log), zip_path
    finally:
        try:
            shutil.rmtree(tmp_root, ignore_errors=True)
        except Exception:
            pass


# ==================== Diff 视图辅助函数 ====================
def _diff_lang_class(language: str) -> str:
    return "language-python" if language == "Python" else "language-java"


def build_split_diff_html(original_code: str, annotated_code: str, language: str = "Python") -> str:
    """生成并排 Split Diff（GitHub 风格）HTML：左 Before / 右 After，新增行绿底，删除行红底。

    Args:
        original_code: 注释前的原始代码
        annotated_code: 注释后的代码
        language: 编程语言（影响展示标签）

    Returns:
        str: 可直接交给 gr.HTML 渲染的完整 HTML 片段
    """
    if not original_code and not annotated_code:
        return '<div class="diff-empty">未输入代码，没有差异可展示。</div>'

    before_lines = original_code.splitlines(keepends=False) if original_code else []
    after_lines = annotated_code.splitlines(keepends=False) if annotated_code else []

    sm = difflib.SequenceMatcher(a=before_lines, b=after_lines)
    opcodes = sm.get_opcodes()

    # 统计
    insert_count = 0
    delete_count = 0
    equal_count = 0
    for tag, _i1, _i2, _j1, _j2 in opcodes:
        if tag == "equal":
            equal_count += (_i2 - _i1)
        elif tag == "insert":
            insert_count += (_j2 - _j1)
        elif tag == "delete":
            delete_count += (_i2 - _i1)
        elif tag == "replace":
            delete_count += (_i2 - _i1)
            insert_count += (_j2 - _j1)

    diff_stats = f"+{insert_count} 插入 / -{delete_count} 删除 / {equal_count} 未变"

    # 生成行
    before_no = 1
    after_no = 1
    rows_html_parts = []
    fmt_lang = _diff_lang_class(language)

    def _esc(s: str) -> str:
        if s is None:
            return "&nbsp;"
        return html.escape(s) if s != "" else "&nbsp;"

    def _cell(class_name: str, line_no: Optional[int], content: str) -> str:
        ln = "&nbsp;" if line_no is None else str(line_no)
        return (
            f'<td class="diff-ln {class_name}">{ln}</td>'
            f'<td class="diff-code {class_name}"><pre class="{fmt_lang}">{_esc(content)}</pre></td>'
        )

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for k in range(i2 - i1):
                b_line = before_lines[i1 + k]
                a_line = after_lines[j1 + k]
                rows_html_parts.append(
                    "<tr>"
                    + _cell("diff-eq", before_no, b_line)
                    + _cell("diff-eq", after_no, a_line)
                    + "</tr>"
                )
                before_no += 1
                after_no += 1
        elif tag == "insert":
            for k in range(j2 - j1):
                a_line = after_lines[j1 + k]
                rows_html_parts.append(
                    "<tr>"
                    + _cell("diff-empty", None, "")
                    + _cell("diff-add", after_no, a_line)
                    + "</tr>"
                )
                after_no += 1
        elif tag == "delete":
            for k in range(i2 - i1):
                b_line = before_lines[i1 + k]
                rows_html_parts.append(
                    "<tr>"
                    + _cell("diff-del", before_no, b_line)
                    + _cell("diff-empty", None, "")
                    + "</tr>"
                )
                before_no += 1
        elif tag == "replace":
            b_len = i2 - i1
            a_len = j2 - j1
            n = max(b_len, a_len)
            for k in range(n):
                b_class = "diff-del" if k < b_len else "diff-empty"
                b_line = before_lines[i1 + k] if k < b_len else ""
                b_no = before_no if k < b_len else None
                a_class = "diff-add" if k < a_len else "diff-empty"
                a_line = after_lines[j1 + k] if k < a_len else ""
                a_no = after_no if k < a_len else None
                rows_html_parts.append(
                    "<tr>"
                    + _cell(b_class, b_no, b_line)
                    + _cell(a_class, a_no, a_line)
                    + "</tr>"
                )
                if k < b_len:
                    before_no += 1
                if k < a_len:
                    after_no += 1

    if insert_count == 0 and delete_count == 0:
        diff_stats += "  ✅ 未检测到代码差异"

    rows_html = "\n".join(rows_html_parts)

    return f"""
<div class="diff-wrapper">
  <style>
    .diff-wrapper {{ font-family: -apple-system, "Segoe UI", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif; }}
    .diff-header {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 10px 16px; border: 1px solid #d0d7de; border-radius: 6px 6px 0 0;
      background: #f6f8fa; font-size: 13px; color: #24292f;
      font-weight: 600;
    }}
    .diff-stats {{ color: #1a7f37; font-weight: 600; }}
    .diff-stats span.del {{ color: #cf222e; margin-left: 6px; }}
    .diff-table-wrap {{
      border: 1px solid #d0d7de; border-top: none; border-radius: 0 0 6px 6px;
      overflow-x: auto; background: #fff;
    }}
    .diff-table {{
      width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 12.5px;
    }}
    .diff-table td {{ padding: 0; vertical-align: top; border: 0; font-family: Consolas, "Liberation Mono", Menlo, monospace; }}
    .diff-ln {{
      width: 50px; text-align: right; padding: 1px 8px 1px 6px !important;
      color: #8c959f; user-select: none; background: #f6f8fa;
      border-right: 1px solid #eaeef2; white-space: nowrap;
    }}
    .diff-code {{
      padding: 1px 8px !important; white-space: pre;
    }}
    .diff-code pre {{ margin: 0; padding: 0; background: transparent; border: 0; font-size: 12.5px; line-height: 20px; }}
    tr.diff-row td {{ border-top: 1px solid #f6f8fa; }}
    .diff-eq.diff-ln {{ background: #f6f8fa; }}
    .diff-eq.diff-code {{ background: #ffffff; }}
    .diff-add.diff-ln {{ background: #ccffd8; color: #0f7b00; }}
    .diff-add.diff-code {{ background: #e6ffec; }}
    .diff-del.diff-ln {{ background: #ffd7d5; color: #ad0a0a; }}
    .diff-del.diff-code {{ background: #ffebe9; }}
    .diff-empty.diff-ln {{ background: #fafbfc; border-right: 1px solid #eaeef2; }}
    .diff-empty.diff-code {{ background: #fafbfc; }}
    .diff-cols-head {{
      display: grid; grid-template-columns: 1fr 1fr;
      border: 1px solid #d0d7de; border-top: none;
      background: #f6f8fa;
    }}
    .diff-cols-head > div {{
      padding: 6px 16px; font-size: 12px; color: #57606a; font-weight: 600;
    }}
    .diff-cols-head > div.before {{ border-right: 1px solid #eaeef2; }}
    .diff-empty {{ padding: 20px; color: #57606a; text-align: center; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; }}
  </style>
  <div class="diff-header">
    <div>🔍 Diff 视图（Before / After）</div>
    <div class="diff-stats">{diff_stats}</div>
  </div>
  <div class="diff-cols-head">
    <div class="before">⬅ Before：注释前原始代码（{language}）</div>
    <div class="after">➡ After：注释后代码（{language}）</div>
  </div>
  <div class="diff-table-wrap">
    <table class="diff-table">
      <colgroup>
        <col style="width:50px"><col style="width:calc(50% - 50px)">
        <col style="width:50px"><col style="width:calc(50% - 50px)">
      </colgroup>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</div>
"""


def _slugify_name(name: str, prefix: str = "", used: Optional[set] = None) -> str:
    """将任意名称转成 URL 友好的 Markdown 锚点 id，并保证不重复（processor 内部版本，避免循环依赖）"""
    import re
    if not name:
        name = "item"
    base = prefix + re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-_").lower()
    if not base:
        base = (prefix or "item") + "-unknown"
    if used is None:
        return base
    final = base
    i = 2
    while final in used:
        final = f"{base}-{i}"
        i += 1
    used.add(final)
    return final


def build_outline_markdown(source_code: str, language: str = "Python", title: str = "📋 函数/类导航大纲", collapsible: bool = True) -> str:
    """根据源代码解析出的函数/类结构，生成可点击跳转的大纲 Markdown

    每个条目链接锚点与 build_markdown_docs / build_java_markdown_docs 中生成的 slug_id 完全一致，
    可在 tab_docs（API 文档 Tab）点击大纲链接一键滚动到对应章节。

    v2.3.6 新增 ``collapsible`` 参数：
      - ``True``（默认）：输出 ``<details>`` 折叠结构，class 的方法嵌套在 class 条目内，
        顶级函数/类各自折叠；默认展开（``open``），用户可点击 summary 折叠/展开。
      - ``False``：保持旧版平铺 Markdown 无序列表格式（向后兼容）。

    .. important::
        **slug 分配顺序**始终按 items 的原始顺序（lineno 排序），与 annotator 的
        ``build_markdown_docs`` / ``build_java_markdown_docs`` 完全一致，保证锚点跳转有效。

    Args:
        source_code: 源代码字符串
        language: "Python" 或 "Java"，默认 Python
        title: 大纲标题文本（可国际化）
        collapsible: 是否输出 ``<details>`` 折叠结构（默认 True）

    Returns:
        str: Markdown/HTML 混合格式的大纲（空时返回空字符串）
    """
    if not source_code:
        return ""
    try:
        if language == "Java":
            items = get_java_functions(source_code)
        else:
            items = get_defined_functions(source_code)
    except Exception:
        return ""
    if not items:
        return ""

    # 1. 先按 items 原始顺序分配 slug（与 annotator 一致，保证锚点跳转有效）
    used_ids: set[str] = set()
    slug_map: dict[int, str] = {}  # id(item) → slug
    for it in items:
        prefix = "cls-" if it.get("type") == "class" else ("fn-" if language == "Python" else "m-")
        slug_map[id(it)] = _slugify_name(it["name"], prefix=prefix, used=used_ids)

    def _icon(it):
        return "🧩" if it.get("type") == "class" else "🔧"

    def _t_label(it):
        if it.get("type") == "class":
            return "Class"
        return "Function" if language == "Python" else "Method"

    # ---- 旧版平铺格式（collapsible=False）----
    if not collapsible:
        outline_lines = [f"**{title}**\n"]
        for it in items:
            slug = slug_map[id(it)]
            line = it.get("lineno", "?")
            outline_lines.append(f"- {_icon(it)} [`{it['name']}` ({_t_label(it)})](#{slug}) — *L{line}*")
        outline_lines.append("\n> 💡 点击条目跳转至「API 文档」Tab 对应章节（锚点滚动定位）\n")
        return "\n".join(outline_lines)

    # ---- 新版折叠格式（collapsible=True，默认）----
    # 2. 推断 class → method 层级关系（基于 lineno/end_lineno 范围包含）
    classes = [it for it in items if it.get("type") == "class"]

    def _find_parent_cls(item):
        for cls in classes:
            cls_start = cls.get("lineno", 0)
            cls_end = cls.get("end_lineno", 0) or 0
            if cls_end and cls_start < item.get("lineno", 0) <= cls_end:
                return cls
        return None

    # 3. 构建顶级条目列表（class + 顶级 function/method），按 lineno 排序
    top_items = []
    for it in items:
        if it.get("type") == "class" or _find_parent_cls(it) is None:
            top_items.append(it)
    top_items.sort(key=lambda x: x.get("lineno", 0))

    # 4. 输出 <details> 折叠结构
    parts = [f"**{title}**\n"]
    for it in top_items:
        slug = slug_map[id(it)]
        line = it.get("lineno", "?")
        icon = _icon(it)
        t_lbl = _t_label(it)
        if it.get("type") == "class":
            # class：开启 details，内嵌子方法列表
            parts.append(f'<details open>')
            parts.append(
                f'<summary>{icon} <a href="#{slug}"><code>{it["name"]}</code></a>'
                f' <small>({t_lbl}) — L{line}</small></summary>'
            )
            # 找属于该 class 的子条目
            children = [
                sub for sub in items
                if sub is not it
                and _find_parent_cls(sub) is it
            ]
            if children:
                parts.append("<ul>")
                for child in children:
                    c_slug = slug_map[id(child)]
                    c_line = child.get("lineno", "?")
                    parts.append(
                        f'<li>{_icon(child)} <a href="#{c_slug}"><code>{child["name"]}</code></a>'
                        f' <small>({_t_label(child)}) — L{c_line}</small></li>'
                    )
                parts.append("</ul>")
            parts.append("</details>")
        else:
            # 顶级 function/method：独立折叠（默认折叠）
            parts.append(f"<details>")
            parts.append(
                f'<summary>{icon} <a href="#{slug}"><code>{it["name"]}</code></a>'
                f' <small>({t_lbl}) — L{line}</small></summary>'
            )
            parts.append("</details>")

    parts.append("\n> 💡 点击条目跳转至「API 文档」Tab 对应章节；点击 ▶/▼ 折叠/展开\n")
    return "\n".join(parts)


# ================== API Key 预检 + Token 成本估算 ==================

_I18N_PREFLIGHT = {
    "中文": {
        "ok": "✅ API Key 预检通过",
        "failed": "❌ API Key 预检失败",
        "no_code": "（暂无源代码）请先输入代码",
        "no_items": "🔍 解析结果：未检测到函数或类定义（无需调用 LLM）",
        "analysis": "🔍 代码分析结果",
        "n_funcs": "🔧 函数/方法数",
        "n_classes": "🧩 类数",
        "n_total": "📊 合计条目总数",
        "cost_title": "💰 Token 用量 & 成本估算（仅供参考）",
        "tokens_total": "Tokens 估算总量",
        "tokens_in": "输入 Tokens 估算",
        "tokens_out": "输出 Tokens 估算",
        "cost_rmb": "成本估算",
        "per_item": "每条目平均 Tokens",
        "cny_symbol": "元",
    },
    "English": {
        "ok": "✅ API Key preflight passed",
        "failed": "❌ API Key preflight failed",
        "no_code": "(Empty. Paste code first to get estimate)",
        "no_items": "🔍 No functions or classes detected (no LLM calls needed)",
        "analysis": "🔍 Code analysis",
        "n_funcs": "🔧 Functions / Methods",
        "n_classes": "🧩 Classes",
        "n_total": "📊 Total items",
        "cost_title": "💰 Token usage & cost estimate (reference only)",
        "tokens_total": "Total tokens (est.)",
        "tokens_in": "Input tokens (est.)",
        "tokens_out": "Output tokens (est.)",
        "cost_rmb": "Estimated cost",
        "per_item": "Avg tokens per item",
        "cny_symbol": "CNY",
    },
    "日本語": {
        "ok": "✅ API Key 事前検証 OK",
        "failed": "❌ API Key 事前検証 失敗",
        "no_code": "（コード未入力）まずソースコードを貼り付けてください",
        "no_items": "🔍 関数・クラス定義が見つかりません（LLM 呼び出し不要）",
        "analysis": "🔍 コード分析結果",
        "n_funcs": "🔧 関数・メソッド数",
        "n_classes": "🧩 クラス数",
        "n_total": "📊 合計エントリ数",
        "cost_title": "💰 トークン消費量・費用概算（参考値）",
        "tokens_total": "総トークン数（概算）",
        "tokens_in": "入力トークン（概算）",
        "tokens_out": "出力トークン（概算）",
        "cost_rmb": "推定費用",
        "per_item": "1エントリあたり平均トークン",
        "cny_symbol": "元",
    },
}


def estimate_markup_cost(num_items: int, lang: str, avg_per_item: int | None = None) -> tuple[int, int, int, float]:
    """processor 内封装：仅做 token 估算（不调用网络），供 UI 监听输入变化时实时估算使用。

    返回 (total_tokens, input_tokens_est, output_tokens_est, cost_rmb)
    """
    return estimate_tokens_cost(num_items, avg_per_item)


def preflight_check(
    source_code: str,
    language: str = "Python",
    ui_lang: str = "中文",
    do_ping: bool = False,
    avg_per_item: int | None = None,
) -> tuple[bool, str, str]:
    """启动期 / 生成按钮前预检入口。

    组合三件事：
      1) 解析 AST，统计 函数数 / 类数 / 条目总数（供估算与展示）
      2) 可选 do_ping=True → 发 1-token 心跳检测 API Key 是否有效
      3) 根据条目数估算总 tokens、输入/输出 tokens 拆分、成本（人民币）

    Args:
        source_code: 源代码
        language: "Python" / "Java"
        ui_lang: UI 语言（用于返回 Markdown 文案 i18n）
        do_ping: 是否真实执行 ping（网络调用，生成按钮前/主动预检时置 True；输入框 change 实时估算置 False）
        avg_per_item: 自定义每条目平均 tokens（默认 350，config 可配置）

    Returns:
        (ok: bool, preflight_md: str, estimate_md: str)
        - ok: 预检是否通过（do_ping=False 时视为 True）
        - preflight_md: 预检结果 Markdown（✅ / ❌ 错误详情）
        - estimate_md: 成本估算 + 分析结果 Markdown（空代码 / 0 条目时返回提示语）
    """
    ui_lang_key = ui_lang if ui_lang in _I18N_PREFLIGHT else "中文"
    tpl = _I18N_PREFLIGHT[ui_lang_key]

    # —— A. API Key 预检（do_ping=True 时才调用网络）——
    if do_ping:
        ok, msg = ping_api_key()
    else:
        ok, msg = True, ""
    if not msg:
        pf_md = f"**{tpl['ok']}**"
    else:
        if ok:
            pf_md = f"**{tpl['ok']}** — _{msg}_"
        else:
            pf_md = f"**{tpl['failed']}**\n\n> {msg}"

    # —— B. 代码分析 + 估算（无代码 / 语法异常 / 0 条目 → 快速返回）——
    if not source_code:
        est_md = f"> {tpl['no_code']}"
        return ok, pf_md, est_md
    try:
        if language == "Java":
            items = get_java_functions(source_code)
        else:
            items = get_defined_functions(source_code)
    except Exception:
        items = []
    n_items = len(items)
    if n_items <= 0:
        est_md = f"> {tpl['no_items']}"
        return ok, pf_md, est_md
    n_funcs = sum(1 for x in items if x.get("type") != "class")
    n_classes = sum(1 for x in items if x.get("type") == "class")
    total_tok, in_tok, out_tok, cost = estimate_tokens_cost(n_items, avg_per_item)
    per = (int(avg_per_item) if avg_per_item and avg_per_item > 0 else None) or 350
    est_md = (
        f"**{tpl['cost_title']}**\n\n"
        f"- **{tpl['analysis']}**：{tpl['n_funcs']} = {n_funcs}、{tpl['n_classes']} = {n_classes}、**{tpl['n_total']} = {n_items}**\n"
        f"- {tpl['tokens_total']}：**{total_tok:,}**（{tpl['per_item']} = {per}）\n"
        f"- {tpl['tokens_in']}：{in_tok:,}　/　{tpl['tokens_out']}：{out_tok:,}\n"
        f"- **{tpl['cost_rmb']}：≈ ¥ {cost:.4f} {tpl['cny_symbol']}**"
        f"（入力 ¥{_PI:.2f}/1M · {_IR:.0%}；出力 ¥{_PO:.2f}/1M · {_OR:.0%}）\n"
    )
    return ok, pf_md, est_md


