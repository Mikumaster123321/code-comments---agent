import json
import pickle
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

import config
import llm_service
import processor
from llm_provider import ModelConfig, ProviderRegistry, RuntimeCredential


class StubClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.calls = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, model, **kwargs):
        self.calls.append((model, kwargs))
        content = f"{self.api_key}|{self.base_url}|{model}"
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class StubClientFactory:
    def __init__(self):
        self.clients = []

    def __call__(self, api_key, base_url):
        client = StubClient(api_key, base_url)
        self.clients.append(client)
        return client


@pytest.fixture
def restore_legacy_provider_state():
    names = (
        "_active_provider",
        "_active_model",
        "_active_api_key",
        "_active_base_url",
        "_active_client",
        "_active_llm_provider",
        "_custom_model_name",
    )
    original = {name: getattr(config, name) for name in names}
    yield
    with config._lock:
        for name, value in original.items():
            setattr(config, name, value)


def _provider(
    registry: ProviderRegistry,
    factory: StubClientFactory,
    provider_id: str,
    model: str,
    secret: str,
    base_url: str | None = None,
):
    model_config = registry.create_model_config(provider_id, model, base_url)
    return registry.create_provider(
        model_config,
        RuntimeCredential(secret),
        factory,
    )


def test_model_config_is_immutable_deterministic_and_credential_free():
    model_config = ModelConfig(
        " Custom ",
        " model-a ",
        "https://gateway.example/v1/",
    )

    assert model_config == ModelConfig(
        "custom", "model-a", "https://gateway.example/v1"
    )
    assert model_config.to_dict() == {
        "provider_id": "custom",
        "model": "model-a",
        "base_url": "https://gateway.example/v1",
    }
    assert json.loads(json.dumps(model_config.to_dict())) == model_config.to_dict()
    assert "api_key" not in model_config.to_dict()
    with pytest.raises(FrozenInstanceError):
        model_config.model = "model-b"


def test_runtime_credential_is_redacted_and_not_serializable():
    secret = "test-secret-A"
    credential = RuntimeCredential(secret)

    assert secret not in repr(credential)
    assert secret not in str(credential)
    assert not hasattr(credential, "to_dict")
    with pytest.raises(TypeError):
        json.dumps(credential)
    with pytest.raises(TypeError):
        pickle.dumps(credential)


def test_provider_registry_exposes_existing_metadata_without_credentials():
    registry = config.get_provider_registry()

    assert registry.provider_ids() == (
        "deepseek",
        "openai",
        "azure",
        "dashscope",
        "moonshot",
        "custom",
    )
    deepseek = registry.get("deepseek")
    assert deepseek.default_model == "deepseek-chat"
    assert deepseek.default_base_url == "https://api.deepseek.com"
    assert deepseek.label_for("English") == "DeepSeek"
    assert "credential" not in deepseek.to_dict()
    assert "api_key" not in deepseek.to_dict()


def test_registry_enforces_base_url_policy():
    registry = config.get_provider_registry()

    with pytest.raises(ValueError):
        registry.create_model_config(
            "deepseek", "deepseek-chat", "https://other.example/v1"
        )
    custom = registry.create_model_config(
        "custom", "model-a", "https://other.example/v1/"
    )
    assert custom.base_url == "https://other.example/v1"


def test_task_configs_clients_and_credentials_are_isolated():
    registry = config.get_provider_registry()
    factory = StubClientFactory()
    task_a = _provider(
        registry,
        factory,
        "deepseek",
        "deepseek-chat",
        "test-secret-A",
    )
    task_b = _provider(
        registry,
        factory,
        "custom",
        "model-b",
        "test-secret-B",
        "https://gateway-b.example/v1",
    )

    result_a = task_a.create_completion(messages=[]).choices[0].message.content
    result_b = task_b.create_completion(messages=[]).choices[0].message.content

    assert result_a == "test-secret-A|https://api.deepseek.com|deepseek-chat"
    assert result_b == "test-secret-B|https://gateway-b.example/v1|model-b"
    assert "test-secret-B" not in result_a
    assert "test-secret-A" not in result_b
    assert "test-secret-A" not in repr(task_a)
    assert "test-secret-B" not in repr(task_b)


def test_concurrent_task_provider_calls_remain_isolated():
    registry = config.get_provider_registry()
    factory = StubClientFactory()
    task_a = _provider(
        registry, factory, "deepseek", "deepseek-chat", "test-secret-A"
    )
    task_b = _provider(
        registry,
        factory,
        "custom",
        "model-b",
        "test-secret-B",
        "https://gateway-b.example/v1",
    )

    def call(provider):
        return provider.create_completion(messages=[]).choices[0].message.content

    providers = [task_a, task_b] * 20
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(call, providers))

    assert set(results[::2]) == {
        "test-secret-A|https://api.deepseek.com|deepseek-chat"
    }
    assert set(results[1::2]) == {
        "test-secret-B|https://gateway-b.example/v1|model-b"
    }


def test_legacy_switch_only_changes_future_task_context(
    monkeypatch,
    restore_legacy_provider_state,
):
    factory = StubClientFactory()
    monkeypatch.setattr(config.openai, "OpenAI", factory)

    ok_a, message_a = config.switch_provider(
        "deepseek", "deepseek-chat", api_key="test-secret-A"
    )
    captured_a = config.get_active_llm_provider()
    ok_b, message_b = config.switch_provider(
        "custom",
        "model-b",
        api_key="test-secret-B",
        base_url="https://gateway-b.example/v1",
        custom_model_name="model-b",
    )
    captured_b = config.get_active_llm_provider()

    assert ok_a and ok_b
    assert "test-secret-A" not in message_a
    assert "test-secret-B" not in message_b
    assert captured_a.config.provider_id == "deepseek"
    assert captured_a.config.model == "deepseek-chat"
    assert captured_b.config.provider_id == "custom"
    assert captured_b.config.model == "model-b"
    assert captured_a.client is not captured_b.client
    old_result = captured_a.create_completion(messages=[]).choices[0].message.content
    assert old_result == "test-secret-A|https://api.deepseek.com|deepseek-chat"


def test_llm_service_explicit_provider_never_reads_legacy_active_state(monkeypatch):
    registry = config.get_provider_registry()
    provider = _provider(
        registry,
        StubClientFactory(),
        "custom",
        "model-a",
        "test-secret-A",
        "https://gateway-a.example/v1",
    )
    monkeypatch.setattr(
        llm_service._cfg,
        "get_active_llm_provider",
        lambda: pytest.fail("explicit provider path read legacy global state"),
    )
    monkeypatch.setattr(
        llm_service._cfg,
        "get_price_input_per_m",
        lambda: pytest.fail("explicit pricing path read legacy global state"),
    )
    monkeypatch.setattr(
        llm_service._cfg,
        "get_price_output_per_m",
        lambda: pytest.fail("explicit pricing path read legacy global state"),
    )

    result = llm_service.generate_code_summary("x = 1", provider=provider)
    cost = llm_service.estimate_tokens_cost(2, provider=provider)

    assert result == "test-secret-A|https://gateway-a.example/v1|model-a"
    assert cost == (700, 301, 398, 0.0)


def test_retry_reuses_same_explicit_task_provider(monkeypatch):
    class RetryableError(Exception):
        pass

    class RetryProvider:
        config = ModelConfig("custom", "model-a", "https://gateway.example/v1")

        def __init__(self):
            self.calls = 0

        def create_completion(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RetryableError("transient")
            message = SimpleNamespace(content="recovered")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    provider = RetryProvider()
    monkeypatch.setattr(llm_service.openai, "APIConnectionError", RetryableError)
    monkeypatch.setattr(llm_service, "RETRY_DELAY", 0)
    monkeypatch.setattr(
        llm_service._cfg,
        "get_active_llm_provider",
        lambda: pytest.fail("retry read legacy global state"),
    )

    result = llm_service._call_llm_with_retry("prompt", 0.0, 1, provider)

    assert result == "recovered"
    assert provider.calls == 2


def test_llm_error_message_does_not_include_credential(monkeypatch):
    class FailingProvider:
        config = ModelConfig("custom", "model-a", "https://gateway.example/v1")

        def create_completion(self, **kwargs):
            raise RuntimeError("provider echoed test-secret-A")

    with pytest.raises(llm_service.LLMRequestError) as exc_info:
        llm_service._call_llm_with_retry("prompt", 0.0, 1, FailingProvider())

    assert "test-secret-A" not in str(exc_info.value)
    assert "RuntimeError" in str(exc_info.value)


def test_processor_captures_one_provider_for_whole_task(monkeypatch):
    registry = config.get_provider_registry()
    provider = _provider(
        registry,
        StubClientFactory(),
        "custom",
        "model-a",
        "test-secret-A",
        "https://gateway-a.example/v1",
    )
    captures = []

    def capture():
        captures.append(provider)
        return provider

    def generate(item, _lang, _style, task_provider):
        assert task_provider is provider
        return f"generated by {task_provider.config.model}"

    monkeypatch.setattr(processor, "get_active_llm_provider", capture)
    monkeypatch.setattr(processor, "generate_docstring", generate)
    monkeypatch.setattr(processor, "MAX_WORKERS", 1)

    result = processor.process_code(
        "def a():\n    pass\n\ndef b():\n    pass\n"
    )
    for output_path in result[3:]:
        if output_path:
            Path(output_path).unlink(missing_ok=True)

    assert len(captures) == 1
    assert result[0].count("generated by model-a") == 2


def test_workspace_persistence_drops_credentials_and_provider_objects(tmp_path):
    workspace_path = tmp_path / "workspace.json"
    secret = "test-secret-A"

    ok, _message = processor.save_workspace(
        {
            "source_code": "x = 1",
            "language": "Python",
            "api_key": secret,
            "credential": RuntimeCredential(secret),
            "model_config": ModelConfig(
                "custom", "model-a", "https://gateway.example/v1"
            ),
        },
        str(workspace_path),
    )
    persisted = workspace_path.read_text(encoding="utf-8")

    assert ok
    assert secret not in persisted
    assert "api_key" not in persisted
    assert "credential" not in persisted
    assert "model_config" not in persisted


def test_code_maintenance_has_no_provider_or_sdk_dependency():
    package_root = Path(__file__).parents[1] / "code_maintenance"

    for path in package_root.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "llm_provider" not in source
        assert "import openai" not in source
        assert "import config" not in source
