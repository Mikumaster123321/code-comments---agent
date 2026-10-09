from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import code_comments_agent.ui_styles as ui_styles
import code_comments_agent.workspace as workspace
import processor
import scripts.dev as dev


ROOT = Path(__file__).resolve().parents[1]


def test_root_entrypoint_and_developer_command_hub_remain_available():
    assert (ROOT / "main.py").is_file()
    assert (ROOT / "scripts/dev.py").is_file()
    assert callable(dev.main)
    assert "release" in dev.TEST_PROFILES


def test_ui_custom_css_is_a_root_compatibility_reexport(monkeypatch):
    monkeypatch.setitem(sys.modules, "gradio", types.ModuleType("gradio"))
    spec = importlib.util.spec_from_file_location("_architecture_ui", ROOT / "ui.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.CUSTOM_CSS is ui_styles.CUSTOM_CSS
    assert module.CUSTOM_CSS.startswith("\n/* ===== 全局基础 ===== */")


def test_processor_workspace_api_is_a_compatibility_reexport():
    assert processor.save_workspace is workspace.save_workspace
    assert processor.load_workspace is workspace.load_workspace
    assert processor.clear_workspace is workspace.clear_workspace
    assert processor._default_workspace_path is workspace._default_workspace_path
    assert processor.WS_ALLOWED_FIELDS is workspace.WS_ALLOWED_FIELDS


def test_internal_support_package_stays_strictly_bounded():
    package_files = {
        path.name
        for path in (ROOT / "code_comments_agent").glob("*.py")
        if path.is_file()
    }
    assert package_files == {
        "__init__.py",
        "reliability.py",
        "ui_styles.py",
        "workspace.py",
    }


def test_documentation_navigation_paths_exist():
    required = (
        "docs/README.md",
        "docs/architecture/Repository_Architecture_Map_V3_1_3.md",
        "docs/architecture/V3_1_4_Pre_V3_2_Compatibility_Contract.md",
        "docs/architecture/V3_1_4_Runtime_Reliability_Contract.md",
        "docs/development/README.md",
        "docs/qa/README.md",
        "docs/release/README.md",
    )
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path


def test_v2_release_state_has_no_self_referential_final_head():
    state = json.loads((ROOT / dev.RELEASE_STATE_PATH).read_text(encoding="utf-8"))

    assert state["schema_version"] == "v2"
    assert state["version"] == "3.1.4"
    assert state["expected_development_branch"] == "v3.1.4-dev"
    assert state["expected_main_branch"] == "main"
    assert state["final_qa_evidence"] == "docs/qa/V3_1_4_Final_Release_QA.md"
    assert "final_head" not in state
    assert dev._load_release_state(ROOT) == state


def test_formal_identity_constants_remain_frozen():
    assert dev.FORMAL_EXECUTION_REVISION == "2749969cd3a2d4d6e1e8d81160eebd5fb360879b"
    assert dev.FORMAL_ARTIFACT_IDENTITY == (
        "acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3"
    )
    assert dev.FORMAL_ARTIFACT_SHA256 == (
        "2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41"
    )


def test_release_contract_describes_two_stage_identity():
    contract = (ROOT / "docs/release/Version_Documentation_Contract.md").read_text(
        encoding="utf-8"
    )
    for phrase in (
        "release_commit",
        "final_head",
        "runtime",
        "Final QA",
        "GitHub",
        "Gitee",
    ):
        assert phrase in contract
