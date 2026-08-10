# -*- coding: utf-8 -*-
from __future__ import annotations
"""LLM 调用模块：生成 docstring/Javadoc（支持 Google/NumPy/reST/Javadoc/极简 多种风格），内置重试机制
v2.4.0 大更新：client/MODEL/PRICE_* 不再是 config 常量导入，而是通过 getter 每次动态获取，
保证 UI 切换 Provider/Model 后下一次请求立即生效。
"""
import re
import time
from typing import Optional
import openai
# v2.4.0 不再 import 常量 client, MODEL, PRICE_*；改为运行时 getter
import config as _cfg
# 无 Provider 无关的常量仍可直接 import
from config import TEMPERATURE, MAX_TOKENS, MAX_RETRIES, RETRY_DELAY
from config import AVG_TOKENS_PER_ITEM, INPUT_RATIO, OUTPUT_RATIO
from i18n import LANG_NAME, LANG_CODE

# ================== 注释风格定义 ==================

PYTHON_STYLE_GOOGLE = "Google 风格"
PYTHON_STYLE_NUMPY = "NumPy 风格"
PYTHON_STYLE_RST = "reStructuredText"
JAVA_STYLE_JAVADOC = "标准 Javadoc"
JAVA_STYLE_MINIMAL = "极简行内注释"

PYTHON_STYLES = [PYTHON_STYLE_GOOGLE, PYTHON_STYLE_NUMPY, PYTHON_STYLE_RST]
JAVA_STYLES = [JAVA_STYLE_JAVADOC, JAVA_STYLE_MINIMAL]

# 通用基础 prompt（Python），最后拼接 {style_rules}
PYTHON_PROMPT_BASE = (
    "你是一位资深 Python 开发工程师。请为以下{func_type}生成{lang_name}文档字符串（docstring）的内容。\n"
    "\n"
    "⚠️ 极其重要的格式要求（不遵守会导致Python语法错误）：\n"
    "1. 不要在开头和结尾添加任何三引号（\"\"\"或'''），我会在生成后自动包裹。\n"
    "2. 不要使用任何Markdown代码块标记（不要 ``` ）。\n"
    "3. 只输出文档字符串的纯文本内容，不要包含任何代码。\n"
    "4. 内容内部如果需要出现引号，请使用单引号或转义，绝对不要出现连续三个双引号。\n"
    "5. 文档内容必须使用 {lang_name} 撰写。\n"
    "\n"
    "{style_rules}\n"
    "\n"
    "{func_type}名：{name}\n"
    "源代码：\n"
    "{code}\n"
)

# Python 各风格的详细格式规则
PYTHON_STYLE_RULES = {
    PYTHON_STYLE_GOOGLE: (
        "文档内容要求（Google 风格）：\n"
        "- 第一行：一句话功能描述（简洁明确）\n"
        "- 空一行后写参数/返回/异常（若有）\n"
        "- Args:\n"
        "    参数名: 参数类型或说明\n"
        "    （每个参数一行，注意缩进为 4 空格）\n"
        "- Returns:\n"
        "    返回类型或说明\n"
        "- Raises:\n"
        "    异常类型: 触发条件\n"
        "- 重要逻辑或算法请简要说明"
    ),
    PYTHON_STYLE_NUMPY: (
        "文档内容要求（NumPy / Napoleon 风格）：\n"
        "- 第一行：一句话功能描述（简洁明确）\n"
        "- 空一行后写详细描述（可选），再写参数/返回等小节\n"
        "- Parameters\n"
        "----------\n"
        "name : type\n"
        "    每个参数说明（缩进 4 空格）\n"
        "- Returns\n"
        "-------\n"
        "type\n"
        "    返回值说明（缩进 4 空格）\n"
        "- Raises\n"
        "------\n"
        "ExceptionType\n"
        "    触发条件说明\n"
        "- 小节分隔线长度必须与标题完全一致（例如 \"Parameters\" 下面 10 个 \"-\"）"
    ),
    PYTHON_STYLE_RST: (
        "文档内容要求（reStructuredText / Sphinx 风格）：\n"
        "- 第一行：一句话功能描述（简洁明确）\n"
        "- 空一行后写参数/返回/异常（若有）\n"
        "- :param name: 参数说明\n"
        "  :type name: 参数类型\n"
        "  （每个参数一对 :param/:type）\n"
        "- :return: 返回值说明\n"
        "  :rtype: 返回类型\n"
        "- :raises ExceptionType: 触发条件说明"
    ),
}

# 翻译时的风格重写规则（Python）：翻译后需按目标风格重新组织格式
PYTHON_TRANSLATE_STYLE_RULES = {
    PYTHON_STYLE_GOOGLE: (
        "翻译完成后，请严格按 Google 风格重新组织文档结构（Args / Returns / Raises 小节）。\n"
        "第一行一句话功能描述，空一行后参数/返回/异常小节，Args 内部每行 4 空格缩进。"
    ),
    PYTHON_STYLE_NUMPY: (
        "翻译完成后，请严格按 NumPy Napoleon 风格重新组织文档结构。\n"
        "使用 Parameters / Returns / Raises 作为小节标题，并在标题下方用等长的 \"-\" 作为分隔线，\n"
        "参数格式为 \"name : type\"，下一行缩进 4 空格写说明。"
    ),
    PYTHON_STYLE_RST: (
        "翻译完成后，请严格按 reStructuredText Sphinx 风格重新组织文档结构。\n"
        "使用 :param name: / :type name: 描述参数，:return: / :rtype: 描述返回值，\n"
        ":raises ExceptionType: 描述异常。"
    ),
}

# ==================== Java 部分 ====================

JAVA_PROMPT_BASE = (
    "你是一位资深 Java 开发工程师。请为以下{func_type}生成{lang_name} Javadoc 注释的内容。\n"
    "\n"
    "⚠️ 极其重要的格式要求（不遵守会导致 Java 语法错误）：\n"
    "1. 不要在开头和结尾添加 /** 或 */ 标记，我会在生成后自动包裹。\n"
    "2. 不要使用任何 Markdown 代码块标记（不要 ``` ）。\n"
    "3. 只输出 Javadoc 的纯文本内容，不要包含任何代码。\n"
    "4. 内容内部不要出现 */ 或 /** 字符串。\n"
    "5. 文档内容必须使用 {lang_name} 撰写。\n"
    "\n"
    "{style_rules}\n"
    "\n"
    "{func_type}名：{name}\n"
    "源代码：\n"
    "{code}\n"
)

JAVA_STYLE_RULES = {
    JAVA_STYLE_JAVADOC: (
        "文档内容要求（标准 Javadoc 风格）：\n"
        "- 第一行：一句话功能描述（简洁明确）\n"
        "- 空一行后写详细描述（可选）\n"
        "- @param 参数名 参数说明（每个参数一行）\n"
        "- @return 返回值说明（无返回值则不写）\n"
        "- @throws 异常类型 触发条件说明"
    ),
    JAVA_STYLE_MINIMAL: (
        "文档内容要求（极简行内注释风格）：\n"
        "- 仅用 1~3 行描述**核心功能**，保持非常简短\n"
        "- **严禁使用任何 @param / @return / @throws 标签**，不要罗列参数细节\n"
        "- 适合快速阅读场景，仅表达此方法/类的作用"
    ),
}

JAVA_TRANSLATE_STYLE_RULES = {
    JAVA_STYLE_JAVADOC: (
        "翻译完成后，请严格按标准 Javadoc 风格重组：保留 @param/@return/@throws 标签，\n"
        "第一行一句话功能描述 + 空行 + 标签列表。"
    ),
    JAVA_STYLE_MINIMAL: (
        "翻译完成后，请按**极简风格重写**：只保留 1~3 行核心功能描述，\n"
        "删除所有 @param/@return/@throws 标签，严禁罗列参数细节。"
    ),
}


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
            response = _cfg.get_active_client().chat.completions.create(
                model=_cfg.get_active_model(),
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


def generate_docstring(item: dict, comment_lang: str = "中文", style: Optional[str] = None) -> str:
    """调用 LLM 生成文档字符串

    Args:
        item: 函数/类信息字典，需包含 type/name/code
        comment_lang: 注释语言（"中文" / "English" / "日本語"）
        style: 注释风格，Google 风格 / NumPy 风格 / reStructuredText

    Returns:
        str: 清理后的 docstring 文本
    """
    if style is None or style not in PYTHON_STYLE_RULES:
        style = PYTHON_STYLE_GOOGLE
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    style_rules = PYTHON_STYLE_RULES[style]
    prompt = PYTHON_PROMPT_BASE.format(
        func_type="类" if item["type"] == "class" else "函数",
        name=item["name"],
        code=item["code"],
        lang_name=lang_name,
        style_rules=style_rules,
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


def translate_docstring(docstring: str, comment_lang: str, style: Optional[str] = None) -> str:
    """将已有 docstring 翻译为目标语言，并按目标风格重组格式

    Args:
        docstring: 原始 docstring 文本
        comment_lang: 目标语言（"中文" / "English" / "日本語"）
        style: 目标注释风格，Google 风格 / NumPy 风格 / reStructuredText

    Returns:
        str: 翻译后的 docstring 文本
    """
    if style is None or style not in PYTHON_TRANSLATE_STYLE_RULES:
        style = PYTHON_STYLE_GOOGLE
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    style_rule = PYTHON_TRANSLATE_STYLE_RULES[style]
    prompt = (
        f"请将以下文档字符串翻译为{lang_name}。如果已经是{lang_name}，请按风格规则重排格式。\n"
        f"\n"
        f"格式要求：\n"
        f"1. 不要添加三引号或 Markdown 标记\n"
        f"2. {style_rule}\n"
        f"3. 只输出翻译后的纯文本\n"
        f"\n"
        f"文档字符串：\n"
        f"{docstring}"
    )
    result = _call_llm_with_retry(prompt, 0.3, MAX_TOKENS)
    return _clean_docstring(result)


# ==================== Java Javadoc 生成 ====================


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


def generate_javadoc(item: dict, comment_lang: str = "中文", style: Optional[str] = None) -> str:
    """调用 LLM 生成 Java Javadoc 注释

    Args:
        item: 方法/类信息字典，需包含 type/name/code
        comment_lang: 注释语言（"中文" / "English" / "日本語"）
        style: 注释风格，标准 Javadoc / 极简行内注释

    Returns:
        str: 清理后的 Javadoc 文本
    """
    if style is None or style not in JAVA_STYLE_RULES:
        style = JAVA_STYLE_JAVADOC
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    style_rules = JAVA_STYLE_RULES[style]
    prompt = JAVA_PROMPT_BASE.format(
        func_type="类" if item["type"] == "class" else "方法",
        name=item["name"],
        code=item["code"],
        lang_name=lang_name,
        style_rules=style_rules,
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


def translate_javadoc(javadoc: str, comment_lang: str, style: Optional[str] = None) -> str:
    """将已有 Javadoc 翻译为目标语言，并按目标风格重组格式

    Args:
        javadoc: 原始 Javadoc 文本
        comment_lang: 目标语言（"中文" / "English" / "日本語"）
        style: 目标注释风格，标准 Javadoc / 极简行内注释

    Returns:
        str: 翻译后的 Javadoc 文本
    """
    if style is None or style not in JAVA_TRANSLATE_STYLE_RULES:
        style = JAVA_STYLE_JAVADOC
    lang_name = LANG_NAME.get(comment_lang, "Chinese (Simplified)")
    style_rule = JAVA_TRANSLATE_STYLE_RULES[style]
    prompt = (
        f"请将以下 Javadoc 注释翻译为{lang_name}。如果已经是{lang_name}，请按风格规则重排格式。\n"
        f"\n"
        f"格式要求：\n"
        f"1. 不要添加 /** 或 */ 标记\n"
        f"2. {style_rule}\n"
        f"3. 只输出翻译后的纯文本\n"
        f"\n"
        f"Javadoc 内容：\n"
        f"{javadoc}"
    )
    result = _call_llm_with_retry(prompt, 0.3, MAX_TOKENS)
    return _clean_javadoc(result)


# ================== API Key 预检 + Token 成本估算 ==================

def ping_api_key(timeout: float = 6.0) -> tuple[bool, str]:
    """1-token 心跳测试：检查 API Key 是否有效、模型是否可用（v2.4.0 动态获取 client/model）。

    注意：不会重试（因为要快速反馈），超时 6s 判定失败。

    Returns:
        (ok: bool, message: str)
        ok=True, message="OK" / "OK (model=<model>)" 表示通过
        ok=False, message 为友好错误描述（HTTP 401 Key 无效 / 网络异常 / 超时 / 其他）
    """
    cur_model = _cfg.get_active_model()
    try:
        resp = _cfg.get_active_client().chat.completions.create(
            model=cur_model,
            messages=[{"role": "user", "content": "ping"}],
            temperature=0.0,
            max_tokens=1,
            timeout=timeout,
        )
        if resp and hasattr(resp, "choices") and resp.choices:
            return True, f"OK (model={cur_model})"
        return True, f"OK (model={cur_model}, empty choices)"
    except openai.AuthenticationError:
        return False, "AuthenticationError: API Key 无效或已过期，请检查对应 Provider 的 API Key 环境变量"
    except openai.PermissionDeniedError:
        return False, "PermissionDeniedError: API Key 无权限访问该模型或该接口"
    except openai.RateLimitError:
        return False, "RateLimitError: 请求频率超限或账户余额不足，请稍后重试/检查账户余额"
    except openai.NotFoundError:
        return False, f"NotFoundError: 模型 {cur_model} 不存在或 base_url 配置错误"
    except openai.APITimeoutError:
        return False, f"APITimeoutError: 请求超时（{timeout}s），请检查网络或稍后重试"
    except Exception as e:
        name = type(e).__name__
        msg = str(e).strip().splitlines()[0] if str(e).strip() else name
        return False, f"{name}: {msg}"


def estimate_tokens_cost(
    num_items: int,
    avg_tokens_per_item: int | None = None,
) -> tuple[int, int, int, float]:
    """根据函数/方法数量估算 Token 用量与成本（人民币）。

    Args:
        num_items: AST 解析出的函数/类/方法总数量（来自 Py/get_defined_functions 或 Java/get_java_functions）
        avg_tokens_per_item: 可选自定义，默认取 config.AVG_TOKENS_PER_ITEM（350）

    Returns:
        (total_tokens, input_tokens_est, output_tokens_est, cost_rmb)
        - total_tokens: 总 tokens 估算（整数）
        - input_tokens_est: 输入 tokens 估算
        - output_tokens_est: 输出 tokens 估算
        - cost_rmb: 人民币元（2 位小数）
    """
    if num_items <= 0:
        return 0, 0, 0, 0.0
    per = int(avg_tokens_per_item) if avg_tokens_per_item and avg_tokens_per_item > 0 else AVG_TOKENS_PER_ITEM
    total = num_items * per
    inp = int(total * INPUT_RATIO)
    out = int(total * OUTPUT_RATIO)
    # 成本 = 输入 tokens/1e6 * 输入单价 + 输出 tokens/1e6 * 输出单价（v2.4.0 按当前 Provider 动态计算）
    cost = (inp / 1_000_000.0) * _cfg.get_price_input_per_m() + (out / 1_000_000.0) * _cfg.get_price_output_per_m()
    return total, inp, out, round(cost, 4)
