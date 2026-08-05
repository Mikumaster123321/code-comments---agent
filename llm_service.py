# -*- coding: utf-8 -*-
"""LLM 调用模块：生成 docstring 和代码摘要，内置重试机制"""
import re
import time
import openai
from config import client, MODEL, TEMPERATURE, MAX_TOKENS, MAX_RETRIES, RETRY_DELAY

PROMPT_TEMPLATE = (
    "你是一位资深 Python 开发工程师。请为以下{func_type}生成中文文档字符串（docstring）的内容。\n"
    "\n"
    "⚠️ 极其重要的格式要求（不遵守会导致Python语法错误）：\n"
    "1. 不要在开头和结尾添加任何三引号（\u0022\u0022\u0022或\u0027\u0027\u0027），我会在生成后自动包裹。\n"
    "2. 不要使用任何Markdown代码块标记（不要 ``` ）。\n"
    "3. 只输出文档字符串的纯文本内容，不要包含任何代码。\n"
    "4. 内容内部如果需要出现引号，请使用单引号或转义，绝对不要出现连续三个双引号。\n"
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


def generate_docstring(item: dict) -> str:
    """调用 LLM 生成文档字符串

    Args:
        item: 函数/类信息字典，需包含 type/name/code

    Returns:
        str: 清理后的 docstring 文本
    """
    prompt = PROMPT_TEMPLATE.format(
        func_type="类" if item["type"] == "class" else "函数",
        name=item["name"],
        code=item["code"]
    )
    docstring = _call_llm_with_retry(prompt, TEMPERATURE, MAX_TOKENS)
    return _clean_docstring(docstring)


def generate_code_summary(source: str) -> str:
    """调用 LLM 生成代码摘要：模块功能、核心类、依赖关系

    Args:
        source: Python 源代码字符串

    Returns:
        str: 代码摘要文本
    """
    prompt = (
        "请分析以下 Python 代码，生成一段简洁的中文摘要（200字以内）。\n"
        "摘要应包含：\n"
        "1. 模块整体功能\n"
        "2. 核心类和函数\n"
        "3. 主要依赖关系\n"
        "\n"
        "只输出摘要文本，不要使用 Markdown 标题或代码块。\n"
        "\n"
        "源代码：\n"
        f"{source}"
    )
    return _call_llm_with_retry(prompt, 0.3, 512)
