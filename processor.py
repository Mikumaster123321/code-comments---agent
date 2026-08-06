# -*- coding: utf-8 -*-
"""主处理模块：协调解析、LLM 调用、注释插入，提供 process_code / analyze_code / 批量处理"""
import ast
import os
import io
import time
import shutil
import zipfile
import datetime
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from Py.parser import get_defined_functions
from llm_service import (
    generate_docstring, generate_code_summary,
    generate_javadoc, generate_java_summary,
    translate_docstring, translate_javadoc,
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


def _process_python(source_code: str, incremental: bool, comment_lang: str = "中文"):
    """Python 代码处理流程：解析 → 并发生成 docstring → 串行插入

    Args:
        source_code: Python 源代码字符串
        incremental: 增量更新模式
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

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
                translated = translate_docstring(existing, comment_lang)
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
                doc = generate_docstring(item, comment_lang)
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


def _process_java(source_code: str, incremental: bool, comment_lang: str = "中文"):
    """Java 代码处理流程：解析 → 并发生成 Javadoc → 串行插入

    Args:
        source_code: Java 源代码字符串
        incremental: 增量更新模式
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

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
                translated = translate_javadoc(existing_text, comment_lang)
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
                doc = generate_javadoc(item, comment_lang)
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

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(markdown_doc)
        md_temp_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
        f.write(annotated_code)
        java_temp_path = f.name

    return annotated_code, markdown_doc, "\n".join(log), md_temp_path, java_temp_path


def process_code(source_code: str, incremental: bool = False, language: str = "Python", comment_lang: str = "中文"):
    """主处理函数，返回注释后的代码、文档、日志、.md 下载路径、源码下载路径

    Args:
        source_code: 源代码字符串
        incremental: 增量更新模式，True 时跳过已有注释的函数（节省 API 调用）
        language: 编程语言（"Python" 或 "Java"）
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

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
        return _process_java(source_code, incremental, comment_lang)
    return _process_python(source_code, incremental, comment_lang)


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

def _resolve_upload_path(uploaded) -> str | None:
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


def _build_batch_zip(output_dir: str, log_text: str, aggregate_md: str | None = None) -> str:
    """将 output_dir 内处理后的结果打包为 zip，外加日志和聚合文档

    Args:
        output_dir: 包含 annotated 源代码文件的输出目录（结构完整）
        log_text: 处理日志文本
        aggregate_md: 聚合 Markdown 文档（可空）

    Returns:
        str: 打包后的临时 zip 文件绝对路径
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_out = tempfile.NamedTemporaryFile(
        mode="wb", prefix="annotated_batch_", suffix=f"_{ts}.zip", delete=False
    )
    zip_out.close()
    with zipfile.ZipFile(zip_out.name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. 源码（保持相对路径）
        for current, _, filenames in os.walk(output_dir):
            for fn in filenames:
                abs_p = os.path.join(current, fn)
                rel_p = os.path.relpath(abs_p, output_dir).replace(os.sep, "/")
                zf.write(abs_p, rel_p)
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
) -> tuple[str, str | None]:
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

    Returns:
        (log_text, zip_path): 处理日志文本 + 打包 zip 的临时路径（可用于 gr.DownloadButton）
    """
    log: list[str] = []
    # 1. 展开上传，解析路径
    if not uploaded_files:
        return "[错误] 未上传任何文件。", None
    # 统一成列表：用户可能传单个（非列表）或列表
    raw_list = uploaded_files if isinstance(uploaded_files, (list, tuple)) else [uploaded_files]
    file_records: list[tuple[str, str]] = []  # (本地绝对路径, 归档用相对路径)
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
                # 单文件：直接复制到 extract_stage/<原文件名>，保留原名
                staged = os.path.join(extract_stage, f"file_{idx:02d}_{name}")
                idx += 1
                shutil.copyfile(src_path, staged)
                rel_p = name.replace(os.sep, "/")
                file_records.append((staged, rel_p))
                log.append(f"[文件] 加入待处理: {name}")
            else:
                log.append(f"[跳过] 不支持的文件类型: {name} ({ext})")

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
        log.append(f"=== 批量处理开始：共 {total} 个文件，注释语言: {comment_lang}，增量: {incremental} ===")
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
                    code, incremental=incremental, language=language, comment_lang=comment_lang
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
            zip_path = _build_batch_zip(output_stage, "\n".join(log), aggregate_md)
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
