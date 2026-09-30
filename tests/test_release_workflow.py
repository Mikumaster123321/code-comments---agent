from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.dev as dev


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_state(root: Path, state: dict) -> None:
    path = root / dev.RELEASE_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _release_repository(tmp_path: Path, *, lifecycle: str = "RELEASE_CANDIDATE"):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "maintenance")
    _git(root, "config", "user.name", "Workflow Test")
    _git(root, "config", "user.email", "workflow@example.invalid")
    (root / "code_maintenance").mkdir()
    (root / "code_maintenance/__init__.py").write_text('__version__ = "3.1.1"\n')
    sentinel = "<!-- release-state: V3.1.1 RELEASE_CANDIDATE -->"
    (root / "README.md").write_text(f"{sentinel}\n### V3.1.1\n", encoding="utf-8")
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    _git(root, "add", "README.md", "baseline.txt", "code_maintenance/__init__.py")
    _git(root, "commit", "-m", "baseline")
    baseline = _git(root, "rev-parse", "HEAD")
    _git(root, "tag", "v3.1.0", baseline)
    state = {
        "schema_version": "v1",
        "version": "3.1.1",
        "state": lifecycle,
        "expected_branch": "maintenance",
        "release_commit": None,
        "tag": None,
        "baseline": {"version": "3.1.0", "commit": baseline, "tag": "v3.1.0"},
        "document_sentinel": sentinel,
        "required_documents": ["README.md"],
    }
    _write_state(root, state)
    _git(root, "add", dev.RELEASE_STATE_PATH)
    _git(root, "commit", "-m", "release candidate")
    return root, state, baseline


@pytest.mark.parametrize("lifecycle", ("PREPARING", "RELEASE_CANDIDATE", "RELEASED"))
def test_release_state_lifecycle_values(tmp_path, lifecycle):
    root, state, _ = _release_repository(tmp_path, lifecycle=lifecycle)
    if lifecycle == "RELEASED":
        state["tag"] = "v3.1.1"
        state["release_commit"] = _git(root, "rev-parse", "HEAD")
        _write_state(root, state)
    assert dev._load_release_state(root)["state"] == lifecycle


def test_release_check_rejects_version_mismatch(tmp_path, monkeypatch):
    root, state, baseline = _release_repository(tmp_path)
    monkeypatch.setattr(dev, "BASELINE_RELEASE_COMMIT", baseline)
    with pytest.raises(dev.WorkflowError, match="requested release version"):
        dev.release_check("3.1.2", remote=False, root=root)


def test_release_check_rejects_protected_staged_path(tmp_path):
    root, _, _ = _release_repository(tmp_path)
    protected = root / "docs/thesis/private.txt"
    protected.parent.mkdir(parents=True)
    protected.write_text("private\n", encoding="utf-8")
    _git(root, "add", "docs/thesis/private.txt")
    with pytest.raises(dev.WorkflowError, match="protected path staging"):
        dev._release_worktree_check(root)


def test_released_tag_target_must_match_metadata(tmp_path):
    root, state, _ = _release_repository(tmp_path)
    _git(root, "tag", "v3.1.1")
    state.update({"state": "RELEASED", "tag": "v3.1.1", "release_commit": "0" * 40})
    with pytest.raises(dev.WorkflowError, match="released tag target"):
        dev._verify_tag_state("3.1.1", state, root)


def test_release_check_is_offline_by_default(tmp_path, monkeypatch, capsys):
    root, _, baseline = _release_repository(tmp_path)
    monkeypatch.setattr(dev, "BASELINE_RELEASE_COMMIT", baseline)
    monkeypatch.setattr(dev, "validate_archive_v310", lambda **kwargs: 0)
    monkeypatch.setattr(
        dev,
        "_remote_tag_check",
        lambda *args, **kwargs: pytest.fail("remote check must remain opt-in"),
    )
    assert dev.release_check("3.1.1", remote=False, root=root) == 0
    assert "remote_check=disabled" in capsys.readouterr().out


def test_remote_check_runs_only_when_requested(tmp_path, monkeypatch):
    root, _, baseline = _release_repository(tmp_path)
    calls = []
    monkeypatch.setattr(dev, "_remote_tag_check", lambda version, metadata, repo: calls.append(version))
    monkeypatch.setattr(dev, "BASELINE_RELEASE_COMMIT", baseline)
    monkeypatch.setattr(dev, "validate_archive_v310", lambda **kwargs: 0)
    assert dev.release_check("3.1.1", remote=True, root=root) == 0
    assert calls == ["3.1.1"]
