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


def _write_required_documents(root: Path, state: dict) -> None:
    for relative_path in state["required_documents"]:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative_path == "README.md":
            content = f"### V{state['version']}\n"
        elif relative_path == state.get("final_qa_evidence"):
            content = "# Independent Final Release QA\n\nVerdict: PASS\n"
        else:
            content = f"# Required V{state['version']} document\n"
        path.write_text(content, encoding="utf-8")


def _release_repository(
    tmp_path: Path,
    *,
    lifecycle: str = "RELEASE_CANDIDATE",
    schema_version: str = "v2",
) -> tuple[Path, dict, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "maintenance")
    _git(root, "config", "user.name", "Workflow Test")
    _git(root, "config", "user.email", "workflow@example.invalid")
    (root / "code_maintenance").mkdir()
    version = "3.1.3" if schema_version == "v2" else "3.1.2"
    (root / "code_maintenance/__init__.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )
    (root / "README.md").write_text(f"### V{version}\n", encoding="utf-8")
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    _git(root, "add", "README.md", "baseline.txt", "code_maintenance/__init__.py")
    _git(root, "commit", "-m", "baseline")
    baseline = _git(root, "rev-parse", "HEAD")
    baseline_version = "3.1.2" if schema_version == "v2" else "3.1.1"
    baseline_tag = f"v{baseline_version}"
    _git(root, "tag", baseline_tag, baseline)
    if schema_version == "v1":
        sentinel = "V3.1.2 RELEASE_CANDIDATE"
        state = {
            "schema_version": "v1",
            "version": version,
            "state": lifecycle,
            "expected_branch": "maintenance",
            "release_commit": None,
            "tag": None,
            "baseline": {
                "version": baseline_version,
                "commit": baseline,
                "tag": baseline_tag,
            },
            "document_sentinel": sentinel,
            "required_documents": ["README.md"],
        }
        (root / "README.md").write_text(
            f"{sentinel}\n### V{version}\n", encoding="utf-8"
        )
    else:
        state = {
            "schema_version": "v2",
            "version": version,
            "state": lifecycle,
            "expected_development_branch": "maintenance",
            "expected_main_branch": "main",
            "release_commit": None,
            "tag": None,
            "baseline": {
                "version": baseline_version,
                "commit": baseline,
                "tag": baseline_tag,
            },
            "required_documents": [
                "README.md",
                "docs/qa/V3_1_3_Final_Release_QA.md",
            ],
            "final_qa_evidence": "docs/qa/V3_1_3_Final_Release_QA.md",
        }
    _write_state(root, state)
    _git(root, "add", ".")
    _git(root, "commit", "-m", "release candidate")
    return root, state, baseline


def _configure_release_constants(monkeypatch, baseline: str, *, legacy: bool = False) -> None:
    monkeypatch.setattr(dev, "BASELINE_RELEASE_COMMIT", baseline)
    monkeypatch.setattr(dev, "BASELINE_VERSION", "3.1.1" if legacy else "3.1.2")
    monkeypatch.setattr(dev, "BASELINE_TAG", "v3.1.1" if legacy else "v3.1.2")
    monkeypatch.setattr(dev, "validate_archive_v310", lambda **kwargs: 0)


@pytest.mark.parametrize("lifecycle", ("PREPARING", "RELEASE_CANDIDATE", "RELEASED"))
def test_release_state_lifecycle_values(tmp_path, lifecycle):
    root, state, _ = _release_repository(tmp_path, lifecycle=lifecycle)
    if lifecycle == "RELEASED":
        state["tag"] = "v3.1.3"
        state["release_commit"] = _git(root, "rev-parse", "HEAD")
        _write_state(root, state)
    assert dev._load_release_state(root)["state"] == lifecycle


def test_legacy_v1_release_state_remains_readable(tmp_path):
    root, state, _ = _release_repository(tmp_path, schema_version="v1")
    assert dev._load_release_state(root) == state


def test_release_check_rejects_version_mismatch(tmp_path, monkeypatch):
    root, _, baseline = _release_repository(tmp_path)
    _configure_release_constants(monkeypatch, baseline)
    with pytest.raises(dev.WorkflowError, match="requested release version"):
        dev.release_check("3.1.4", remote=False, root=root)


def test_release_check_rejects_wrong_local_branch_intent(tmp_path, monkeypatch):
    root, _, baseline = _release_repository(tmp_path)
    _configure_release_constants(monkeypatch, baseline)
    _git(root, "switch", "-c", "wrong-branch")
    with pytest.raises(dev.WorkflowError, match="release branch"):
        dev.release_check("3.1.3", remote=False, root=root)


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
    _git(root, "tag", "v3.1.3")
    state.update({"state": "RELEASED", "tag": "v3.1.3", "release_commit": "0" * 40})
    with pytest.raises(dev.WorkflowError, match="released tag target"):
        dev._verify_tag_state("3.1.3", state, root)


def test_release_commit_may_be_ancestor_of_later_head(tmp_path):
    root, state, _ = _release_repository(tmp_path)
    release_commit = _git(root, "rev-parse", "HEAD")
    _git(root, "tag", "-a", "v3.1.3", "-m", "release", release_commit)
    (root / "later.txt").write_text("release record\n", encoding="utf-8")
    _git(root, "add", "later.txt")
    _git(root, "commit", "-m", "record release identity")
    state.update(
        {"state": "RELEASED", "tag": "v3.1.3", "release_commit": release_commit}
    )
    dev._verify_tag_state("3.1.3", state, root)
    assert _git(root, "rev-parse", "HEAD") != release_commit


def test_release_commit_must_be_ancestor_of_runtime_head(tmp_path, monkeypatch):
    root, state, _ = _release_repository(tmp_path)
    current_head = _git(root, "rev-parse", "HEAD")
    monkeypatch.setattr(
        dev,
        "_git_output",
        lambda arguments, *, root: (
            "f" * 40 if arguments == ["rev-parse", "v3.1.3^{}"] else current_head
        ),
    )
    monkeypatch.setattr(
        dev,
        "_git",
        lambda arguments, *, root, capture=True: subprocess.CompletedProcess(
            arguments,
            1 if arguments[:2] == ["merge-base", "--is-ancestor"] else 0,
            "",
            "",
        ),
    )
    state.update({"state": "RELEASED", "tag": "v3.1.3", "release_commit": "f" * 40})
    with pytest.raises(dev.WorkflowError, match="release commit ancestry"):
        dev._verify_tag_state("3.1.3", state, root)


def test_v2_release_requires_final_qa_evidence(tmp_path, monkeypatch):
    root, _, baseline = _release_repository(tmp_path)
    _configure_release_constants(monkeypatch, baseline)
    with pytest.raises(dev.WorkflowError, match="Final QA evidence"):
        dev.release_check("3.1.3", remote=False, root=root)


def test_release_check_is_offline_by_default(tmp_path, monkeypatch, capsys):
    root, state, baseline = _release_repository(tmp_path)
    _write_required_documents(root, state)
    _git(root, "add", ".")
    _git(root, "commit", "-m", "final qa evidence")
    _configure_release_constants(monkeypatch, baseline)
    monkeypatch.setattr(
        dev,
        "_remote_release_check",
        lambda *args, **kwargs: pytest.fail("remote check must remain opt-in"),
    )
    assert dev.release_check("3.1.3", remote=False, root=root) == 0
    assert "remote_check=disabled" in capsys.readouterr().out


def _remote_result(state: dict, head: str, *, mismatch: str | None = None):
    main_head = "a" * 40 if mismatch == "main" else head
    development_head = "b" * 40 if mismatch == "development" else head
    tag_target = "c" * 40 if mismatch == "tag" else state["release_commit"]
    lines = [
        f"{main_head}\trefs/heads/{state['expected_main_branch']}",
        f"{development_head}\trefs/heads/{state['expected_development_branch']}",
        f"{'d' * 40}\trefs/tags/{state['tag']}",
        f"{tag_target}\trefs/tags/{state['tag']}^{{}}",
    ]
    return subprocess.CompletedProcess([], 0, "\n".join(lines) + "\n", "")


@pytest.mark.parametrize(
    ("mismatch", "message"),
    (
        ("main", "remote main branch target"),
        ("development", "remote development branch target"),
        ("tag", "remote released tag target"),
    ),
)
def test_remote_release_identity_mismatches_fail(tmp_path, monkeypatch, mismatch, message):
    root, state, _ = _release_repository(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    state.update({"state": "RELEASED", "tag": "v3.1.3", "release_commit": "e" * 40})
    monkeypatch.setattr(dev, "_git_output", lambda arguments, *, root: "github\ngitee")
    monkeypatch.setattr(
        dev,
        "_git",
        lambda arguments, *, root, capture=True: _remote_result(
            state, head, mismatch=mismatch
        ),
    )
    with pytest.raises(dev.WorkflowError, match=message):
        dev._remote_release_check("3.1.3", state, root, head)


def test_remote_release_identity_accepts_both_remotes(tmp_path, monkeypatch):
    root, state, _ = _release_repository(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    state.update({"state": "RELEASED", "tag": "v3.1.3", "release_commit": "e" * 40})
    calls = []
    monkeypatch.setattr(dev, "_git_output", lambda arguments, *, root: "github\ngitee")
    monkeypatch.setattr(
        dev,
        "_git",
        lambda arguments, *, root, capture=True: (
            calls.append(arguments[1]) or _remote_result(state, head)
        ),
    )
    dev._remote_release_check("3.1.3", state, root, head)
    assert calls == ["github", "gitee"]
