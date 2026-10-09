import logging
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

import config
import llm_service
import processor
from code_comments_agent.reliability import (
    APPLICATION_GENERATION_ATTEMPTS,
    RUNTIME_LIMITS,
    SDK_MAX_RETRIES,
    TRANSPORT_ATTEMPTS_PER_APPLICATION_ATTEMPT,
    RuntimeLimits,
    log_diagnostic,
    new_operation_id,
)
from code_comments_agent.workspace import load_workspace, save_workspace
from llm_provider import ModelConfig, RuntimeCredential


class CountingProvider:
    config = ModelConfig("custom", "test-model", "https://example.test/v1")

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def create_completion(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def _completion(content="ok"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _write_zip(path: Path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content, external_attr in entries:
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            if external_attr is not None:
                info.external_attr = external_attr
            archive.writestr(info, content)


def test_runtime_attempt_contract_is_explicit_and_single_owner():
    assert SDK_MAX_RETRIES == 0
    assert APPLICATION_GENERATION_ATTEMPTS == 1
    assert TRANSPORT_ATTEMPTS_PER_APPLICATION_ATTEMPT == 1
    assert config.MAX_RETRIES == 1


def test_default_client_factory_disables_sdk_retries_and_sets_generation_timeout(monkeypatch):
    captured = {}

    def factory(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(config.openai, "OpenAI", factory)
    provider = config.create_llm_provider(
        ModelConfig("custom", "test-model", "https://example.test/v1"),
        RuntimeCredential("test-secret"),
    )

    assert provider.client is not None
    assert captured["max_retries"] == 0
    assert captured["timeout"] == RUNTIME_LIMITS.generation_timeout_seconds


@pytest.mark.parametrize(
    ("exception_name", "category"),
    (
        ("AuthenticationError", "authentication"),
        ("PermissionDeniedError", "permission"),
        ("BadRequestError", "invalid_request"),
        ("NotFoundError", "invalid_request"),
        ("RateLimitError", "rate_limit"),
        ("APITimeoutError", "ambiguous_timeout"),
        ("APIConnectionError", "connection"),
    ),
)
def test_generation_exception_matrix_never_retries(monkeypatch, exception_name, category):
    error_type = type(f"Stub{exception_name}", (Exception,), {})
    monkeypatch.setattr(llm_service.openai, exception_name, error_type)
    provider = CountingProvider(error=error_type("sensitive provider text"))

    with pytest.raises(llm_service.LLMRequestError) as exc_info:
        llm_service._call_llm_with_retry("secret prompt", 0.0, 1, provider)

    assert len(provider.calls) == 1
    assert "sensitive provider text" not in str(exc_info.value)
    assert llm_service._request_error_category(error_type()) == category


def test_ping_is_one_low_cost_bounded_request():
    provider = CountingProvider(result=_completion("pong"))

    ok, message = llm_service.ping_api_key(timeout=2.5, provider=provider)

    assert ok and "test-model" in message
    assert len(provider.calls) == 1
    assert provider.calls[0]["max_tokens"] == 1
    assert provider.calls[0]["timeout"] == 2.5


def test_structured_diagnostic_allowlist_redacts_unapproved_fields(caplog):
    logger = logging.getLogger("v314-diagnostic-test")
    operation_id = new_operation_id()
    with caplog.at_level(logging.INFO, logger=logger.name):
        log_diagnostic(
            logger,
            "request_failed",
            operation_id=operation_id,
            stage="generation",
            error_category="authentication",
            credential="secret-key",
            prompt="private source",
            path="/Users/private/work.py",
        )

    text = caplog.text
    assert operation_id in text
    assert "stage=generation" in text
    assert "error_category=authentication" in text
    assert "secret-key" not in text
    assert "private source" not in text
    assert "/Users/private" not in text
    assert new_operation_id() != operation_id


def test_pending_futures_are_cancelled_while_running_work_finishes():
    class Pending:
        cancelled = False

        def done(self):
            return False

        def cancel(self):
            self.cancelled = True

    pending = Pending()

    class Executor:
        def shutdown(self, **kwargs):
            self.kwargs = kwargs

    executor = Executor()
    processor._shutdown_executor_safe(executor, {pending: object()})

    assert pending.cancelled
    assert executor.kwargs == {"wait": True, "cancel_futures": True}


def test_single_source_limit_rejects_before_provider_lookup(monkeypatch):
    monkeypatch.setattr(
        processor,
        "RUNTIME_LIMITS",
        RuntimeLimits(single_source_bytes=4),
    )
    monkeypatch.setattr(
        processor,
        "get_active_llm_provider",
        lambda: pytest.fail("oversized source reached provider construction"),
    )

    result = processor.process_code("def too_large():\n    pass\n")

    assert result[0] == ""
    assert "处理上限" in result[1]


@pytest.mark.parametrize(
    ("entries", "limits", "code"),
    (
        (
            [("../escape.py", b"x", None)],
            RuntimeLimits(),
            "ZIP_PATH_UNSAFE",
        ),
        (
            [("link.py", b"target", (stat.S_IFLNK | 0o777) << 16)],
            RuntimeLimits(),
            "ZIP_SYMLINK_UNSUPPORTED",
        ),
        (
            [("a.py", b"x", None), ("b.py", b"x", None)],
            RuntimeLimits(zip_member_count=1),
            "ZIP_MEMBER_LIMIT_EXCEEDED",
        ),
        (
            [("large.py", b"x" * 20, None)],
            RuntimeLimits(zip_uncompressed_bytes=10),
            "ZIP_UNCOMPRESSED_LIMIT_EXCEEDED",
        ),
        (
            [("ratio.py", b"A" * 10_000, None)],
            RuntimeLimits(zip_compression_ratio=2.0),
            "ZIP_COMPRESSION_RATIO_EXCEEDED",
        ),
    ),
)
def test_zip_guards_reject_with_stable_reason(tmp_path, monkeypatch, entries, limits, code):
    archive = tmp_path / "input.zip"
    target = tmp_path / "out"
    target.mkdir()
    _write_zip(archive, entries)
    monkeypatch.setattr(processor, "RUNTIME_LIMITS", limits)

    with pytest.raises(processor.ResourceLimitError, match=code):
        processor._extract_zip_safe(str(archive), str(target))


def test_batch_all_failed_is_not_counted_or_packaged(tmp_path, monkeypatch):
    source = tmp_path / "failed.py"
    source.write_text("def failed():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(
        processor,
        "process_code",
        lambda *args, **kwargs: ("", "failure", "✗ failed [PROVIDER_FAILURE]", None, None),
    )

    log, zip_path = processor.process_batch_files([str(source)], llm_provider=object())

    assert zip_path is None
    assert "成功 0, 失败 1" in log
    assert "ALL_SYMBOLS_FAILED" in log


@pytest.mark.parametrize(
    ("per_log", "expected_label"),
    (
        ("✓ one", "✓ 完成"),
        ("✓ one\n✗ two [PROVIDER_FAILURE]", "PARTIAL_SYMBOL_FAILURES"),
    ),
)
def test_batch_success_and_partial_outcomes_cleanup_intermediates(
    tmp_path, monkeypatch, per_log, expected_label
):
    source = tmp_path / "sample.py"
    source.write_text("def sample():\n    pass\n", encoding="utf-8")
    md_temp = tmp_path / "ignored.md"
    src_temp = tmp_path / "ignored.py"
    md_temp.write_text("docs", encoding="utf-8")
    src_temp.write_text("annotated", encoding="utf-8")
    monkeypatch.setattr(
        processor,
        "process_code",
        lambda *args, **kwargs: (
            "def sample():\n    pass\n",
            "docs",
            per_log,
            str(md_temp),
            str(src_temp),
        ),
    )

    log, zip_path = processor.process_batch_files([str(source)], llm_provider=object())

    try:
        assert zip_path and Path(zip_path).is_file()
        assert expected_label in log
        assert not md_temp.exists()
        assert not src_temp.exists()
    finally:
        if zip_path:
            Path(zip_path).unlink(missing_ok=True)


def test_batch_cancelled_with_results_is_packaged_and_stops_new_work(tmp_path, monkeypatch):
    source = tmp_path / "sample.py"
    source.write_text("def sample():\n    pass\n", encoding="utf-8")
    token = processor.CancelToken()

    def result(*args, **kwargs):
        token.cancel()
        return "def sample():\n    pass\n", "docs", "✓ sample", None, None

    monkeypatch.setattr(processor, "process_code", result)
    frames = list(
        processor.process_batch_with_progress(
            [str(source)], cancel_token=token, llm_provider=object()
        )
    )
    zip_path = next((path for _log, path in frames if path), None)

    try:
        assert zip_path and Path(zip_path).is_file()
        assert any("CANCELLED_WITH_RESULTS" in log for log, _path in frames)
    finally:
        if zip_path:
            Path(zip_path).unlink(missing_ok=True)


def test_partial_zip_is_removed_when_packaging_fails(tmp_path, monkeypatch):
    output = tmp_path / "out"
    output.mkdir()
    (output / "a.py").write_text("x = 1\n", encoding="utf-8")
    partial = tmp_path / "partial.zip"

    class Temporary:
        name = str(partial)

        def close(self):
            partial.touch()

    monkeypatch.setattr(processor.tempfile, "NamedTemporaryFile", lambda **kwargs: Temporary())

    class BrokenZip:
        def __init__(self, *args, **kwargs):
            raise OSError("package failure")

    monkeypatch.setattr(processor.zipfile, "ZipFile", BrokenZip)

    with pytest.raises(OSError):
        processor._build_batch_zip(str(output), "log")
    assert not partial.exists()


def test_workspace_round_trip_version_and_failure_cleanup(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace.json"
    data = {
        "source_code": "x = 1",
        "output_lang": "English",
        "rewrite_existing": False,
        "api_key": "must-not-persist",
    }
    assert save_workspace(data, str(workspace))[0]
    ok, _message, loaded = load_workspace(str(workspace))
    assert ok
    assert loaded["output_lang"] == "English"
    assert loaded["rewrite_existing"] is False
    assert "api_key" not in loaded

    workspace.write_text('{"_version": 999, "data": {}}', encoding="utf-8")
    ok, message, loaded = load_workspace(str(workspace))
    assert not ok and loaded == {}
    assert "WORKSPACE_VERSION_UNSUPPORTED" in message

    monkeypatch.setattr(os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("fail")))
    assert not save_workspace(data, str(workspace))[0]
    assert not Path(str(workspace) + ".tmp").exists()


def test_javac_user_log_redacts_temporary_absolute_path(tmp_path, monkeypatch):
    javac_dir = tmp_path / "private-javac-path"
    monkeypatch.setattr(processor.shutil, "which", lambda _name: "/usr/bin/javac")

    def make_temp(**kwargs):
        javac_dir.mkdir()
        return str(javac_dir)

    monkeypatch.setattr(processor.tempfile, "mkdtemp", make_temp)

    def run(command, **kwargs):
        return SimpleNamespace(
            returncode=1,
            stderr=f"{command[-1]}:1: error: invalid syntax".encode(),
        )

    monkeypatch.setattr(processor.subprocess, "run", run)
    log = []
    processor._verify_java_annotated_code("class A {}", log)

    visible = "\n".join(log)
    assert str(tmp_path) not in visible
    assert "<temporary-java-file>" in visible


def test_imports_are_lazy_and_do_not_load_ui_or_e5():
    code = (
        "import sys; import config; "
        "assert config._active_client is None; "
        "import project_intelligence, processor; "
        "assert 'gradio' not in sys.modules; "
        "assert 'transformers' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_pre_v32_compatibility_surfaces_remain_available():
    import code_maintenance
    import project_intelligence
    from code_comments_agent.ui_styles import CUSTOM_CSS

    for name in ("ModelConfig", "RuntimeCredential", "TaskScopedLLMProvider"):
        assert hasattr(__import__("llm_provider"), name)
    for name in ("process_code", "process_code_with_progress", "process_batch_files", "CancelToken"):
        assert hasattr(processor, name)
    for name in ("RetrievalService", "RetrievalQuery", "ContextPackage"):
        assert hasattr(project_intelligence, name)
    ui_source = (Path(__file__).resolve().parents[1] / "ui.py").read_text(encoding="utf-8")
    assert "from code_comments_agent.ui_styles import CUSTOM_CSS" in ui_source
    assert isinstance(CUSTOM_CSS, str)
    assert hasattr(code_maintenance, "SourceFile")


def test_ci_contract_contains_python310_import_ui_and_full_smokes():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/pytest.yml").read_text(
        encoding="utf-8"
    )
    assert 'python-version: "3.10"' in workflow
    assert "Import and lazy-startup smoke" in workflow
    assert "Build Gradio UI without a Provider request" in workflow
    assert "python scripts/dev.py test full" in workflow
