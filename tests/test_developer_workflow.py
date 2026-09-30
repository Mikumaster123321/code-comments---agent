from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.dev as dev
import scripts.export_formal_thesis_tables as formal_export


ROOT = Path(__file__).resolve().parents[1]
DEV_SCRIPT = ROOT / "scripts/dev.py"


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def _snapshot(tmp_path: Path, *, revision: str = dev.E5_REVISION) -> Path:
    snapshot = tmp_path / "models--intfloat--multilingual-e5-base" / "snapshots" / revision
    snapshot.mkdir(parents=True)
    for name in dev.E5_REQUIRED_FILES:
        content = "{}"
        if name == "config.json":
            content = json.dumps({"_name_or_path": dev.E5_REPOSITORY, "hidden_size": 768})
        (snapshot / name).write_text(content, encoding="utf-8")
    return snapshot


def test_command_help_from_repository_and_external_cwd(tmp_path):
    for cwd in (ROOT, tmp_path):
        result = subprocess.run(
            [sys.executable, str(DEV_SCRIPT), "--help"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "project-smoke" in result.stdout
        assert "release-check" in result.stdout


def test_main_dispatch_and_structured_failure(monkeypatch, capsys):
    monkeypatch.setattr(dev, "project_smoke", lambda: 17)
    assert dev.main(["project-smoke"]) == 17
    monkeypatch.setattr(
        dev,
        "project_smoke",
        lambda: dev._fail("probe", "pass", "fail", "repair it"),
    )
    assert dev.main(["project-smoke"]) == 1
    stderr = capsys.readouterr().err
    assert "What failed: probe" in stderr
    assert "Expected: pass" in stderr
    assert "Actual: fail" in stderr
    assert "Safe recovery: repair it" in stderr


def test_project_smoke_is_offline_and_minimal(capsys):
    assert dev.project_smoke() == 0
    output = capsys.readouterr().out
    assert "project_smoke=PASS" in output
    assert "files=1" in output
    assert "hits=1" in output


def test_doctor_redacts_secret_values_and_reports_probe(monkeypatch, capsys):
    secret = "never-print-this-secret"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setattr(dev, "_dependency_version", lambda name: "1.0")
    monkeypatch.setattr(dev, "_pytest_probe", lambda root=dev.REPOSITORY_ROOT: _completed(-11))
    monkeypatch.setattr(dev, "_git_output", lambda args, root=dev.REPOSITORY_ROOT: "main")
    monkeypatch.setattr(dev, "_run_process", lambda *args, **kwargs: _completed(0, "git version 2"))
    assert dev.doctor(root=ROOT) == 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "OPENAI_API_KEY=set" in combined
    assert secret not in combined
    assert "pytest_plugin_probe=FAIL" in combined
    assert "environment workaround" in combined
    assert "historical_formal_runtime=" in combined


def test_pytest_probe_uses_subprocess_without_shell(monkeypatch):
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return _completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    dev._pytest_probe(ROOT)
    assert observed["command"][:3] == [sys.executable, "-m", "pytest"]
    assert observed["kwargs"]["cwd"] == ROOT
    assert "shell" not in observed["kwargs"]


@pytest.mark.parametrize("profile", tuple(dev.TEST_PROFILES))
def test_stable_test_profiles_preserve_passthrough(monkeypatch, profile):
    monkeypatch.setattr(dev, "_pytest_probe", lambda root=dev.REPOSITORY_ROOT: _completed())
    command = dev._pytest_command(profile, ("--collect-only", "-x"))
    assert command[:3] == [sys.executable, "-m", "pytest"]
    assert command[-2:] == ["--collect-only", "-x"]
    for test_path in dev.TEST_PROFILES[profile]:
        assert test_path in command


def test_test_profile_preserves_pytest_exit_code(monkeypatch):
    monkeypatch.setattr(dev, "_pytest_command", lambda *args, **kwargs: ["pytest"])
    monkeypatch.setattr(dev, "_run_process", lambda *args, **kwargs: _completed(5))
    assert dev.run_test_profile("llm", ()) == 5


def test_model_check_rejects_missing_dependencies(monkeypatch):
    monkeypatch.setattr(dev, "_dependency_version", lambda name: None)
    with pytest.raises(dev.WorkflowError, match="optional E5 dependencies"):
        dev.model_check(cache_dir=None, model_path=None, smoke=False)


def test_model_snapshot_rejects_wrong_revision(tmp_path):
    snapshot = _snapshot(tmp_path, revision="wrong-revision")
    with pytest.raises(dev.WorkflowError, match="resolved revision"):
        dev._validate_model_snapshot(snapshot, root=tmp_path / "repository")


def test_model_snapshot_rejects_missing_files(tmp_path):
    snapshot = _snapshot(tmp_path)
    (snapshot / "tokenizer.json").unlink()
    with pytest.raises(dev.WorkflowError, match="snapshot files"):
        dev._validate_model_snapshot(snapshot, root=tmp_path / "repository")


def test_model_snapshot_rejects_dangling_symlink(tmp_path):
    snapshot = _snapshot(tmp_path)
    (snapshot / "dangling").symlink_to(snapshot / "missing-blob")
    with pytest.raises(dev.WorkflowError, match="snapshot symlinks"):
        dev._validate_model_snapshot(snapshot, root=tmp_path / "repository")


def test_model_snapshot_rejects_repository_internal_cache(tmp_path):
    root = tmp_path / "repository"
    snapshot = _snapshot(root)
    with pytest.raises(dev.WorkflowError, match="cache location"):
        dev._validate_model_snapshot(snapshot, root=root)


def test_resource_metrics_are_optional(monkeypatch):
    path = ROOT / "scripts/validate_phase32_real_model.py"
    spec = importlib.util.spec_from_file_location("phase32_portability", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "resource", None)
    assert module._rss_mb() is None
    assert module._rss_text(None) == "unavailable"


def test_archive_validator_accepts_released_v310():
    assert dev.validate_archive_v310(root=ROOT) == 0


def test_archive_validator_rejects_wrong_identity(monkeypatch):
    monkeypatch.setattr(dev, "FORMAL_ARTIFACT_IDENTITY", "0" * 64)
    with pytest.raises(dev.WorkflowError, match="canonical identity"):
        dev.validate_archive_v310(root=ROOT)


def test_archive_validator_rejects_wrong_ancestry(monkeypatch):
    monkeypatch.setattr(dev, "FORMAL_ARCHIVE_COMMIT", "0" * 40)
    with pytest.raises(dev.WorkflowError, match="archive ancestry"):
        dev.validate_archive_v310(root=ROOT)


def test_python_optimized_mode_keeps_critical_checks(tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{}", encoding="utf-8")
    snapshot = _snapshot(tmp_path / "cache")
    config = snapshot / "config.json"
    config.write_text(json.dumps({"_name_or_path": dev.E5_REPOSITORY, "hidden_size": 1}))
    code = f"""
from pathlib import Path
import scripts.dev as dev
import scripts.export_formal_thesis_tables as export
failures = 0
export.ROOT = Path({str(tmp_path)!r})
for callback in (
    lambda: export.verified_json(Path('bad.json'), '0' * 64),
    lambda: export._verify_equal('wrong', export.EXPECTED_IDENTITY, 'artifact identity'),
    lambda: export._verify_equal('wrong', 'expected', 'committed CSV'),
    lambda: dev._validate_model_snapshot(Path({str(snapshot)!r}), root=Path({str(tmp_path / 'repo')!r})),
):
    try:
        callback()
    except (export.ExportValidationError, dev.WorkflowError):
        failures += 1
raise SystemExit(0 if failures == 4 else 1)
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_export_checker_has_no_optimization_sensitive_assertions():
    source = (ROOT / "scripts/export_formal_thesis_tables.py").read_text(encoding="utf-8")
    assert "assert " not in source
    source = (ROOT / "scripts/validate_phase32_real_model.py").read_text(encoding="utf-8")
    assert "assert " not in source
