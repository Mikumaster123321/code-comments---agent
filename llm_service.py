# -*- coding: utf-8 -*-
"""LLM 调用模块：生成 docstring 和代码摘要，内置重试机制"""
import re
import time
import openai
from config import client, MODEL, TEMPERATURE, MAX_TOKENS, MAX_RETRIES, RETRY_DELAY
from i18n import LANG_NAME, LANG_CODE

PROMPT_TEMPLATE = (
    "你是一位资深 Python 开发工程师。请为以下{func_type}生成{lang_name}文档字符串（docstring）的内容。\n"
    "\n"
    "⚠️ 极其重要的格式要求（不遵守会导致Python语法错误）：\n"
    "1. 不要在开头和结尾添加任何三引号（\u0022\u0022\u0022或\u0027\u0027\u0027），我会在生成后自动包裹。\n"
    "2. 不要使用任何Markdown代码块标记（不要 ``` ）。\n"
    "3. 只输出文档字符串的纯文本内容，不要包含任何代码。\n"
    "4. 内容内部如果需要出现引号，请使用单引号或转义，绝对不要出现连续三个双引号。\n"
    "5. 文档内容必须使用 {lang_name} 撰写。\n"
    "\n"
    "文档内容要求（Google 风格）：\n"
    "- 第一行：一句话功能描述（简洁明确）\n"
    "- Args：参数名 + 类型 + 说明\n"
    "- Returns：返回类型 + 说明\n"
    "- Raises：可能抛出的异常 + 触发条件\n"
    "- 重要逻辑或算法请简要说明\n"
    "\n"
    "{func_type}名：{name}\n"
    "源代码：\n"
    "{code}\n"
)


def _call_llm_with_retry(prompt: str, temperature: float, max_tokens: int) -> str:
    """带重试机制的 LLM 调用

    Args:
        prompt: 提示词
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        str: LLM 生成的文本

    Raises:
        Exception: 重试次数用尽后抛出最后一次异常
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except (openai.APIError, openai.APIConnectionError,
                openai.APITimeoutError, openai.RateLimitError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    raise last_error


def _clean_docstring(docstring: str) -> str:
    """彻底清理 LLM 输出：去除三引号包裹和 Markdown 代码块标记

    Args:
        docstring: LLM 原始输出

    Returns:
        str: 清理后的纯文本 docstring
    """
    triple_double = chr(34) * 3   # """
    triple_single = chr(39) * 3   # '''
    M = re.MULTILINE
    # 按行清理开头/结尾的三引号（MULTILINE 让 ^/$ 匹配行边界）
    docstring = re.sub(r'^' + triple_double, '', docstring, flags=M)
    docstring = re.sub(triple_double + r'$', '', docstring, flags=M)
    docstring = re.sub(r'^' + triple_single, '', docstring, flags=M)
    docstring = re.sub(triple_single + r'$', '', docstring, flags=M)
    # 按行清理 Markdown 代码块标记
    docstring = re.sub(r'^```.*?\n', '', docstring, flags=M)
    docstring = re.sub(r'\n```$', '', docstring, flags=M)
    docstring = re.sub(r'^```', '', docstring, flags=M)
    docstring = re.sub(r'```$', '', docstring, flags=M)

    # 清理内容中残留的独立三引号行（整行就是三引号）
    cleaned_lines = []
    bad_markers = (triple_double, triple_single)
    for line in docstring.split('\n'):
        stripped = line.strip()
        if stripped in bad_markers:
            continue
        cleaned_lines.append(line)
    docstring = "\n".join(cleaned_lines)

    return docstring.strip()


def generate_docstring(item: dict, comment_lang: str = "中文") -> str:
    """调用 LLM 生成文档字符串

    Args:
        item: 函数/类信息字典，需包含 type/name/code
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

    Returns:
        str: 清理后的 docstring 文本
    """
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    prompt = PROMPT_TEMPLATE.format(
        func_type="类" if item["type"] == "class" else "函数",
        name=item["name"],
        code=item["code"],
        lang_name=lang_name,
    )
    docstring = _call_llm_with_retry(prompt, TEMPERATURE, MAX_TOKENS)
    return _clean_docstring(docstring)


def generate_code_summary(source: str, comment_lang: str = "中文") -> str:
    """调用 LLM 生成代码摘要：模块功能、核心类、依赖关系

    Args:
        source: Python 源代码字符串
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

    Returns:
        str: 代码摘要文本
    """
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    prompt = (
        f"请分析以下 Python 代码，生成一段简洁的{lang_name}摘要（200字以内）。\n"
        f"摘要应包含：\n"
        f"1. 模块整体功能\n"
        f"2. 核心类和函数\n"
        f"3. 主要依赖关系\n"
        f"\n"
        f"只输出{lang_name}摘要文本，不要使用 Markdown 标题或代码块。\n"
        f"\n"
        f"源代码：\n"
        f"{source}"
    )
    return _call_llm_with_retry(prompt, 0.3, 512)


def translate_docstring(docstring: str, comment_lang: str) -> str:
    """将已有 docstring 翻译为目标语言（若已是目标语言则原样返回）

    Args:
        docstring: 原始 docstring 文本
        comment_lang: 目标语言（"中文" / "English" / "日本語"）

    Returns:
        str: 翻译后的 docstring 文本
    """
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    prompt = (
        f"请将以下文档字符串翻译为{lang_name}。如果已经是{lang_name}，请原样返回不要修改。\n"
        f"\n"
        f"格式要求：\n"
        f"1. 不要添加三引号或 Markdown 标记\n"
        f"2. 保持原有的段落结构（如 Args/Returns 等）\n"
        f"3. 只输出翻译后的纯文本\n"
        f"\n"
        f"文档字符串：\n"
        f"{docstring}"
    )
    result = _call_llm_with_retry(prompt, 0.3, MAX_TOKENS)
    return _clean_docstring(result)


# ==================== Java Javadoc 生成 ====================

JAVA_PROMPT_TEMPLATE = (
    "你是一位资深 Java 开发工程师。请为以下{func_type}生成{lang_name} Javadoc 注释的内容。\n"
    "\n"
    "⚠️ 极其重要的格式要求（不遵守会导致 Java 语法错误）：\n"
    "1. 不要在开头和结尾添加 /** 或 */ 标记，我会在生成后自动包裹。\n"
    "2. 不要使用任何 Markdown 代码块标记（不要 ``` ）。\n"
    "3. 只输出 Javadoc 的纯文本内容，不要包含任何代码。\n"
    "4. 内容内部不要出现 */ 或 /** 字符串。\n"
    "5. 文档内容必须使用 {lang_name} 撰写。\n"
    "\n"
    "文档内容要求（Javadoc 风格）：\n"
    "- 第一行：一句话功能描述（简洁明确）\n"
    "- @param：参数名 + 说明（每个参数一行）\n"
    "- @return：返回值说明\n"
    "- @throws：可能抛出的异常 + 触发条件\n"
    "- 重要逻辑或算法请简要说明\n"
    "\n"
    "{func_type}名：{name}\n"
    "源代码：\n"
    "{code}\n"
)


def _clean_javadoc(text: str) -> str:
    """清理 LLM 输出的 Javadoc：去除 /** */ 包裹、行首 * 标记和 Markdown 代码块

    Args:
        text: LLM 原始输出

    Returns:
        str: 清理后的纯文本 Javadoc 内容
    """
    M = re.MULTILINE
    # 去除开头的 /**
    text = re.sub(r'^\s*/\*\*', '', text, flags=M)
    # 去除结尾的 */
    text = re.sub(r'\*/\s*$', '', text, flags=M)
    # 去除每行开头的 * 和可选空格
    lines = [re.sub(r'^\s*\*\s?', '', line) for line in text.split('\n')]
    text = '\n'.join(lines)
    # 去除 Markdown 代码块标记
    text = re.sub(r'^```[a-zA-Z]*\s*\n', '', text, flags=M)
    text = re.sub(r'\n```$', '', text, flags=M)
    text = re.sub(r'^```', '', text, flags=M)
    text = re.sub(r'```$', '', text, flags=M)
    return text.strip()


def generate_javadoc(item: dict, comment_lang: str = "中文") -> str:
    """调用 LLM 生成 Java Javadoc 注释

    Args:
        item: 方法/类信息字典，需包含 type/name/code
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

    Returns:
        str: 清理后的 Javadoc 文本
    """
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    prompt = JAVA_PROMPT_TEMPLATE.format(
        func_type="类" if item["type"] == "class" else "方法",
        name=item["name"],
        code=item["code"],
        lang_name=lang_name,
    )
    javadoc = _call_llm_with_retry(prompt, TEMPERATURE, MAX_TOKENS)
    return _clean_javadoc(javadoc)


def generate_java_summary(source: str, comment_lang: str = "中文") -> str:
    """调用 LLM 生成 Java 代码摘要：模块功能、核心类、依赖关系

    Args:
        source: Java 源代码字符串
        comment_lang: 注释语言（"中文" / "English" / "日本語"）

    Returns:
        str: 代码摘要文本
    """
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    prompt = (
        f"请分析以下 Java 代码，生成一段简洁的{lang_name}摘要（200字以内）。\n"
        f"摘要应包含：\n"
        f"1. 模块整体功能\n"
        f"2. 核心类和方法\n"
        f"3. 主要依赖关系\n"
        f"\n"
        f"只输出{lang_name}摘要文本，不要使用 Markdown 标题或代码块。\n"
        f"\n"
        f"源代码：\n"
        f"{source}"
    )
    return _call_llm_with_retry(prompt, 0.3, 512)


def translate_javadoc(javadoc: str, comment_lang: str) -> str:
    """将已有 Javadoc 翻译为目标语言（若已是目标语言则原样返回）

    Args:
        javadoc: 原始 Javadoc 文本
        comment_lang: 目标语言（"中文" / "English" / "日本語"）

    Returns:
        str: 翻译后的 Javadoc 文本
    """
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    prompt = (
        f"请将以下 Javadoc 注释翻译为{lang_name}。如果已经是{lang_name}，请原样返回不要修改。\n"
        f"\n"
        f"格式要求：\n"
        f"1. 不要添加 /** 或 */ 标记\n"
        f"2. 保持原有的 @param/@return/@throws 结构\n"
        f"3. 只输出翻译后的纯文本\n"
        f"\n"
        f"Javadoc 内容：\n"
        f"{javadoc}"
    )
    result = _call_llm_with_retry(prompt, 0.3, MAX_TOKENS)
    return _clean_javadoc(result)
