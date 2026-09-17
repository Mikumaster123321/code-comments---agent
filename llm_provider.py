# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class ModelConfig:
    """Serializable, credential-free model selection for one task."""

    provider_id: str
    model: str
    base_url: str

    def __post_init__(self) -> None:
        for field_name in ("provider_id", "model", "base_url"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
            object.__setattr__(self, field_name, value.strip())
        object.__setattr__(self, "provider_id", self.provider_id.lower())
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))
        if not self.base_url:
            raise ValueError("base_url must contain more than slash characters")

    def to_dict(self) -> dict[str, str]:
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "base_url": self.base_url,
        }


class RuntimeCredential:
    """Non-serializable runtime secret passed only to provider construction."""

    __slots__ = ("__secret",)

    def __init__(self, secret: str) -> None:
        if not isinstance(secret, str) or not secret.strip():
            raise ValueError("credential must be a non-empty string")
        self.__secret = secret.strip()

    def get_secret_value(self) -> str:
        return self.__secret

    def __repr__(self) -> str:
        return "RuntimeCredential(<redacted>)"

    __str__ = __repr__

    def __reduce__(self):
        raise TypeError("RuntimeCredential cannot be serialized")


@dataclass(frozen=True)
class ProviderMetadata:
    provider_id: str
    labels: tuple[tuple[str, str], ...]
    models: tuple[tuple[str, str], ...]
    default_base_url: str
    credential_env_vars: tuple[str, ...]
    customizable_base_url: bool
    price_input_per_m: float
    price_output_per_m: float

    @property
    def default_model(self) -> str:
        return self.models[0][0]

    def label_for(self, language: str) -> str:
        labels = dict(self.labels)
        return labels.get(language, labels.get("中文", self.provider_id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "models": [model for model, _label in self.models],
            "default_model": self.default_model,
            "default_base_url": self.default_base_url,
            "customizable_base_url": self.customizable_base_url,
            "price_input_per_m": self.price_input_per_m,
            "price_output_per_m": self.price_output_per_m,
        }


@runtime_checkable
class LLMProvider(Protocol):
    @property
    def config(self) -> ModelConfig:
        ...

    def create_completion(self, **kwargs: Any) -> Any:
        ...


@dataclass(frozen=True, repr=False)
class TaskScopedLLMProvider:
    """A model/client pair captured once and reused for one request or task."""

    config: ModelConfig
    client: Any

    def create_completion(self, **kwargs: Any) -> Any:
        return self.client.chat.completions.create(model=self.config.model, **kwargs)

    def __repr__(self) -> str:
        return f"TaskScopedLLMProvider(config={self.config!r}, client=<redacted>)"


class ProviderRegistry:
    """Read-only provider metadata and explicit task-provider factory."""

    def __init__(self, providers: Mapping[str, Mapping[str, Any]]) -> None:
        metadata: dict[str, ProviderMetadata] = {}
        for provider_id, raw in providers.items():
            normalized_id = provider_id.strip().lower()
            models = tuple((str(key), str(label)) for key, label in raw["models"].items())
            if not models:
                raise ValueError(f"provider {normalized_id!r} must define at least one model")
            metadata[normalized_id] = ProviderMetadata(
                provider_id=normalized_id,
                labels=(
                    ("中文", str(raw["label_zh"])),
                    ("English", str(raw["label_en"])),
                    ("日本語", str(raw["label_ja"])),
                ),
                models=models,
                default_base_url=str(raw["base_url"]).rstrip("/"),
                credential_env_vars=tuple(str(name) for name in raw["api_key_env"]),
                customizable_base_url=bool(raw["customizable_base_url"]),
                price_input_per_m=float(raw["price_input_per_m"]),
                price_output_per_m=float(raw["price_output_per_m"]),
            )
        self._providers = MappingProxyType(metadata)

    def provider_ids(self) -> tuple[str, ...]:
        return tuple(self._providers)

    def get(self, provider_id: str) -> ProviderMetadata:
        try:
            return self._providers[provider_id.strip().lower()]
        except (AttributeError, KeyError) as exc:
            raise ValueError(f"unknown provider: {provider_id!r}") from exc

    def create_model_config(
        self,
        provider_id: str,
        model: str | None = None,
        base_url: str | None = None,
    ) -> ModelConfig:
        metadata = self.get(provider_id)
        selected_model = (
            model.strip()
            if isinstance(model, str) and model.strip()
            else metadata.default_model
        )
        if base_url is not None and base_url.strip() and not metadata.customizable_base_url:
            normalized = base_url.strip().rstrip("/")
            if normalized != metadata.default_base_url:
                raise ValueError(f"provider {metadata.provider_id!r} does not allow a custom base_url")
        selected_base_url = (
            base_url.strip().rstrip("/")
            if isinstance(base_url, str) and base_url.strip()
            else metadata.default_base_url
        )
        return ModelConfig(metadata.provider_id, selected_model, selected_base_url)

    def create_provider(
        self,
        config: ModelConfig,
        credential: RuntimeCredential,
        client_factory: Callable[..., Any],
    ) -> TaskScopedLLMProvider:
        metadata = self.get(config.provider_id)
        if not metadata.customizable_base_url and config.base_url != metadata.default_base_url:
            raise ValueError(f"provider {metadata.provider_id!r} does not allow a custom base_url")
        client = client_factory(
            api_key=credential.get_secret_value(),
            base_url=config.base_url,
        )
        return TaskScopedLLMProvider(config=config, client=client)
