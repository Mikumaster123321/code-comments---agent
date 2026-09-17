# -*- coding: utf-8 -*-
"""配置模块 v2.4.0（大更新）：多 Provider / 多模型动态切换
集中管理 API Key、模型参数、Provider 元数据。

通过 ``PROVIDERS`` 字典集中定义所有 OpenAI 兼容协议提供商：
  - DeepSeek（默认）
  - OpenAI 官方
  - Azure OpenAI Service
  - 阿里百炼（DashScope / Alibaba Bailian）
  - 月之暗面（Moonshot AI / Kimi）
  - Custom（自定义 base_url / 模型名，兼容任意 OpenAI gateway）

对外公开 API（UI 与 llm_service 只调这些，避免直接改模块全局）：
    - :func:`get_providers`              → Provider 列表 [(label, key)]
    - :func:`get_models_for_provider`    → 指定 Provider 的模型列表 [(label, key)]
    - :func:`switch_provider`            → 切换 Provider + Model，重连 client
    - :func:`set_api_key`                → 运行时更新 API Key
    - :func:`get_active_provider`        → 当前 Provider key
    - :func:`get_active_model`           → 当前 Model key
    - :func:`get_active_client`          → 当前 openai.OpenAI client（供 llm_service 调用）
    - :func:`get_active_base_url`        → 当前 base_url（调试显示）
    - :func:`get_price_input_per_m`      → 当前 Provider 输入单价
    - :func:`get_price_output_per_m`     → 当前 Provider 输出单价
"""
import os
import threading
from typing import Optional
import openai
from dotenv import load_dotenv
from llm_provider import (
    ModelConfig,
    ProviderRegistry,
    RuntimeCredential,
    TaskScopedLLMProvider,
)

load_dotenv()


# ==========================================================================
# 1. PROVIDERS 字典：集中定义所有 OpenAI 兼容协议的 Provider
# ==========================================================================
PROVIDERS: dict[str, dict] = {
    "deepseek": {
        "label_zh": "DeepSeek",
        "label_en": "DeepSeek",
        "label_ja": "DeepSeek",
        "api_key_env": ["DEEPSEEK_API_KEY", "OPENAI_API_KEY"],
        "base_url": "https://api.deepseek.com",
        "models": {
            "deepseek-chat": "DeepSeek-V3 Chat (推荐)",
            "deepseek-reasoner": "DeepSeek-R1 推理模型",
        },
        # 官方参考价（元 / 每 1M tokens）
        "price_input_per_m": 0.27,
        "price_output_per_m": 1.10,
        "customizable_base_url": False,
    },
    "openai": {
        "label_zh": "OpenAI 官方",
        "label_en": "OpenAI Official",
        "label_ja": "OpenAI 公式",
        "api_key_env": ["OPENAI_API_KEY"],
        "base_url": "https://api.openai.com/v1",
        "models": {
            "gpt-4o-mini": "GPT-4o mini（性价比高）",
            "gpt-4o": "GPT-4o（通用）",
            "gpt-4.1": "GPT-4.1（最新）",
            "gpt-3.5-turbo": "GPT-3.5 Turbo（经典）",
        },
        "price_input_per_m": 0.75,   # ≈ 0.15 USD / 1M（粗略换算 RMB）
        "price_output_per_m": 2.50,  # ≈ 0.60 USD / 1M
        "customizable_base_url": False,
    },
    "azure": {
        "label_zh": "Azure OpenAI",
        "label_en": "Azure OpenAI Service",
        "label_ja": "Azure OpenAI",
        "api_key_env": ["AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"],
        # Azure 的 base_url 需要用户在 Portal 填 resource 名，这里仅占位，可自定义
        "base_url": "https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOYMENT",
        "models": {
            "gpt-4o-mini": "GPT-4o mini",
            "gpt-4o": "GPT-4o",
            "gpt-35-turbo": "GPT-3.5 Turbo",
        },
        "price_input_per_m": 0.85,
        "price_output_per_m": 2.80,
        "customizable_base_url": True,   # Azure 必须自定义
    },
    "dashscope": {
        "label_zh": "阿里百炼（Qwen）",
        "label_en": "Alibaba Bailian (Qwen)",
        "label_ja": "阿里百錬（Qwen）",
        "api_key_env": ["DASHSCOPE_API_KEY", "ALIBABA_API_KEY", "OPENAI_API_KEY"],
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            "qwen-plus": "Qwen-Plus（推荐）",
            "qwen-turbo": "Qwen-Turbo（便宜）",
            "qwen-max": "Qwen-Max（能力强）",
        },
        "price_input_per_m": 0.12,
        "price_output_per_m": 0.24,
        "customizable_base_url": False,
    },
    "moonshot": {
        "label_zh": "月之暗面（Kimi）",
        "label_en": "Moonshot AI (Kimi)",
        "label_ja": "月の暗面（Kimi）",
        "api_key_env": ["MOONSHOT_API_KEY", "KIMI_API_KEY", "OPENAI_API_KEY"],
        "base_url": "https://api.moonshot.cn/v1",
        "models": {
            "moonshot-v1-8k": "Moonshot-v1-8k",
            "moonshot-v1-32k": "Moonshot-v1-32k",
            "moonshot-v1-128k": "Moonshot-v1-128k（长上下文）",
        },
        "price_input_per_m": 0.12,
        "price_output_per_m": 0.12,
        "customizable_base_url": False,
    },
    "custom": {
        "label_zh": "Custom（自定义 OpenAI 兼容）",
        "label_en": "Custom (OpenAI-compatible)",
        "label_ja": "カスタム（OpenAI 互換）",
        "api_key_env": ["OPENAI_API_KEY"],
        "base_url": "http://localhost:8000/v1",   # 典型：Ollama / vLLM / OneAPI
        "models": {
            "custom-model": "自定义模型名（请在下栏修改）",
        },
        "price_input_per_m": 0.0,   # 本地/未知网关按 0 估算
        "price_output_per_m": 0.0,
        "customizable_base_url": True,
    },
}

PROVIDER_REGISTRY = ProviderRegistry(PROVIDERS)


# ==========================================================================
# 2. Provider 标签本地化
# ==========================================================================
def _provider_label(provider_key: str, lang: str) -> str:
    p = PROVIDERS.get(provider_key)
    if not p:
        return provider_key
    if lang == "English":
        return p["label_en"]
    if lang == "日本語":
        return p["label_ja"]
    return p["label_zh"]


# ==========================================================================
# 3. 运行时活动 Provider / Model / Client 状态（线程安全）
# ==========================================================================
_lock = threading.RLock()
_active_provider: str = "deepseek"
_active_model: str = "deepseek-chat"
_active_api_key: Optional[str] = None
_active_base_url: Optional[str] = None   # None = 使用 PROVIDERS 定义的默认
_active_client: Optional[openai.OpenAI] = None
_active_llm_provider: Optional[TaskScopedLLMProvider] = None
_custom_model_name: Optional[str] = None  # custom provider 下用户自定义的模型名


def _env_first(provider_key: str) -> Optional[str]:
    """从环境变量按优先级查找第一个非空 API Key"""
    p = PROVIDERS[provider_key]
    for key in p["api_key_env"]:
        v = os.getenv(key)
        if v:
            return v
    return None


def _rebuild_client() -> None:
    """按当前 _active_* 状态重建 _active_client"""
    global _active_client, _active_llm_provider
    p = PROVIDERS[_active_provider]
    base_url = _active_base_url if _active_base_url else p["base_url"]
    api_key = _active_api_key or _env_first(_active_provider) or "EMPTY_API_KEY"
    model_config = PROVIDER_REGISTRY.create_model_config(
        _active_provider,
        _active_model,
        base_url,
    )
    _active_llm_provider = PROVIDER_REGISTRY.create_provider(
        model_config,
        RuntimeCredential(api_key),
        openai.OpenAI,
    )
    _active_client = _active_llm_provider.client


# ---------- 初始化：按 .env 的 PROVIDER / MODEL 变量默认启动 ----------
_env_provider = os.getenv("PROVIDER", "deepseek").lower()
if _env_provider not in PROVIDERS:
    # 非法值 → 回退到 deepseek，不抛异常（启动时不能炸）
    _env_provider = "deepseek"
_active_provider = _env_provider
_default_models = list(PROVIDERS[_active_provider]["models"].keys())
_env_model = os.getenv("MODEL", _default_models[0])
_active_model = _env_model if _env_model in _default_models else _default_models[0]
# 如果 .env 设置了 BASE_URL（仅对 customizable 的 provider 生效）
if PROVIDERS[_active_provider]["customizable_base_url"]:
    _env_base_url = os.getenv("BASE_URL")
    if _env_base_url:
        _active_base_url = _env_base_url
_env_custom_model = os.getenv("CUSTOM_MODEL_NAME")
if _env_custom_model and _active_provider == "custom":
    _custom_model_name = _env_custom_model
_rebuild_client()


# ==========================================================================
# 4. 公开 API（UI 与 llm_service 只调用这里）
# ==========================================================================
def get_providers(lang: str = "中文") -> list[tuple[str, str]]:
    """返回 [(label, key)] 下拉框数据，按 lang 本地化 label"""
    return [
        (f"{_provider_label(k, lang)} ({k})", k)
        for k in PROVIDERS.keys()
    ]


def get_models_for_provider(provider_key: str, lang: str = "中文") -> list[tuple[str, str]]:
    """指定 Provider 的模型列表 [(label, key)]

    ``custom`` Provider 下如果用户通过 :func:`switch_provider` 设置了自定义模型名，
    会作为列表首项追加，保证 UI 下拉框显示用户值。
    """
    p = PROVIDERS.get(provider_key)
    if not p:
        return []
    items = []
    # custom provider 的用户自定义模型（首项）
    if provider_key == "custom" and _custom_model_name:
        items.append((f"✏️ {_custom_model_name}（自定义）", _custom_model_name))
    for k, v in p["models"].items():
        items.append((v, k))
    return items


def _validate_params(provider_key: str, model_key: str) -> None:
    if provider_key not in PROVIDERS:
        raise ValueError(f"未知 Provider: {provider_key}，允许: {list(PROVIDERS.keys())}")


def switch_provider(
    provider_key: str,
    model_key: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    custom_model_name: Optional[str] = None,
) -> tuple[bool, str]:
    """切换 Provider / Model / API Key / Base URL，线程安全

    Args:
        provider_key: 必须是 PROVIDERS 的 key 之一
        model_key: 模型名；None → 保持原 model（跨 Provider 切换时取第一个默认）
        api_key: None → 保持现有运行时 key；空串 '' → 重置为环境变量读取
        base_url: None → 使用 PROVIDERS 定义的默认；'' 无效；仅对 customizable=True 的 Provider 生效
        custom_model_name: 仅 custom Provider 下用，模型名的自由文本

    Returns:
        (success, message) 成功 True/False + 可读消息
    """
    global _active_provider, _active_model, _active_api_key, _active_base_url, _custom_model_name
    with _lock:
        try:
            _validate_params(provider_key, model_key or "")
        except ValueError as e:
            return False, f"❌ {e}"

        prev_provider = _active_provider
        _active_provider = provider_key

        # 切换 Provider 且未传模型时：新 Provider 的第一个默认
        if model_key is None and provider_key != prev_provider:
            model_key = list(PROVIDERS[provider_key]["models"].keys())[0]
        # 传了 model_key 则用；空串忽略
        if model_key:
            _active_model = model_key
        # custom provider 的自由模型名
        if provider_key == "custom":
            if custom_model_name:
                _custom_model_name = custom_model_name
                _active_model = custom_model_name

        # API Key 更新策略：None = 不变；'' = 重置环境变量；其他 = 覆盖
        if api_key is None:
            pass  # 保持当前
        elif api_key == "":
            _active_api_key = None  # 下次 _rebuild_client 自动读 env
        else:
            _active_api_key = api_key.strip() or None

        # Base URL 更新策略
        if PROVIDERS[provider_key]["customizable_base_url"]:
            if base_url is None:
                # 无显式参数：保持当前 _active_base_url（若无则取默认）
                pass
            elif base_url == "":
                _active_base_url = None  # 用 PROVIDERS 定义的默认
            else:
                _active_base_url = base_url.strip().rstrip("/")
        else:
            # 非 customizable：强制走 PROVIDERS 定义，忽略用户自定义
            _active_base_url = None

        try:
            _rebuild_client()
        except Exception as e:
            return False, f"❌ 连接 client 失败：{type(e).__name__}"

        p_label = _provider_label(provider_key, "中文")
        return True, f"✅ 已切换到 {p_label} → 模型 `{_active_model}`"


def set_api_key(api_key: str) -> tuple[bool, str]:
    """仅更新当前活动 Provider 的 API Key（不切 Provider）"""
    global _active_api_key
    if not api_key:
        # 空串 → 重置为环境变量读取
        with _lock:
            _active_api_key = None
            try:
                _rebuild_client()
            except Exception as e:
                return False, f"❌ {type(e).__name__}"
            return True, "✅ API Key 已重置为环境变量值"
    with _lock:
        _active_api_key = api_key.strip()
        try:
            _rebuild_client()
        except Exception as e:
            return False, f"❌ {type(e).__name__}"
        return True, "✅ API Key 已更新（仅运行时有效，不会写入 .env）"


def set_custom_base_url(base_url: Optional[str]) -> tuple[bool, str]:
    """仅当当前 Provider 是 customizable 时允许更新 base_url"""
    global _active_base_url
    with _lock:
        p = PROVIDERS[_active_provider]
        if not p["customizable_base_url"]:
            return False, f"❌ Provider `{_active_provider}` 不允许自定义 Base URL"
        _active_base_url = base_url.strip().rstrip("/") if base_url else None
        try:
            _rebuild_client()
        except Exception as e:
            return False, f"❌ {type(e).__name__}"
        url = _active_base_url or p["base_url"]
        return True, f"✅ Base URL 已更新为 `{url}`"


def get_active_provider() -> str:
    """当前 Provider key（deepseek / openai / …）"""
    with _lock:
        return _active_provider


def get_active_model() -> str:
    """当前 Model name（用于 client.chat.completions.create 的 model= 参数）"""
    with _lock:
        return _active_model


def get_active_client() -> openai.OpenAI:
    """获取当前 client（llm_service 每次请求都调用一次，确保切换后立即生效）"""
    with _lock:
        if _active_client is None:
            _rebuild_client()
        return _active_client


def get_active_model_config() -> ModelConfig:
    """Capture the active credential-free model configuration atomically."""
    with _lock:
        if _active_llm_provider is None:
            _rebuild_client()
        return _active_llm_provider.config


def get_active_llm_provider() -> TaskScopedLLMProvider:
    """Capture the current model/client pair for one task or request."""
    with _lock:
        if _active_llm_provider is None:
            _rebuild_client()
        return _active_llm_provider


def create_llm_provider(
    model_config: ModelConfig,
    credential: RuntimeCredential,
    client_factory=openai.OpenAI,
) -> TaskScopedLLMProvider:
    """Build an independent task-scoped provider without changing legacy state."""
    return PROVIDER_REGISTRY.create_provider(
        model_config,
        credential,
        client_factory,
    )


def get_provider_registry() -> ProviderRegistry:
    return PROVIDER_REGISTRY


def get_active_base_url() -> str:
    """当前 base_url（调试 / UI 显示用）"""
    with _lock:
        p = PROVIDERS[_active_provider]
        return _active_base_url or p["base_url"]


def is_active_provider_customizable() -> bool:
    """当前 Provider 是否允许自定义 base_url（Azure / Custom）"""
    with _lock:
        return PROVIDERS[_active_provider]["customizable_base_url"]


def get_price_input_per_m() -> float:
    """当前 Provider 输入单价（元 / 1M tokens）"""
    with _lock:
        return PROVIDERS[_active_provider]["price_input_per_m"]


def get_price_output_per_m() -> float:
    """当前 Provider 输出单价（元 / 1M tokens）"""
    with _lock:
        return PROVIDERS[_active_provider]["price_output_per_m"]


# ==========================================================================
# 5. 兼容旧代码：仍然暴露 client / MODEL 等顶层名字（读属性时动态计算）
# ==========================================================================
class _CompatModuleGlobals:
    """仅用于 docstring，未实际使用"""


def __getattr__(name):
    """模块级 getattr：保证 `from config import client, MODEL` 仍然生效"""
    if name == "client":
        return get_active_client()
    if name == "MODEL":
        return get_active_model()
    if name == "PRICE_INPUT_PER_M":
        return get_price_input_per_m()
    if name == "PRICE_OUTPUT_PER_M":
        return get_price_output_per_m()
    raise AttributeError(f"module 'config' has no attribute {name!r}")


# 其它参数与之前保持一致，与 Provider 无关
TEMPERATURE = 0.2
MAX_TOKENS = 1024
MAX_RETRIES = 3
RETRY_DELAY = 1.0
MAX_WORKERS = 5
AVG_TOKENS_PER_ITEM = 350
INPUT_RATIO = 0.43
OUTPUT_RATIO = 0.57
