# -*- coding: utf-8 -*-
"""v2.3.7 会话持久化专项测试（离线）

T1_SaveLoadRoundTrip    — 保存→加载往返完整性（单字段 / 全字段 / 多轮覆盖）
T2_WhitelistSecurity    — API Key 等非白名单字段绝不被写入 / 读取 + None 字段剔除
T3_FileFormatTolerance  — 空文件 / 非法 JSON / 非 dict 顶层 / data 缺失 / 脏数据注入
T4_ClearAndNonexistent  — clear_workspace 删除 / 无文件时不报错
T5_DefaultPathStable    — _default_workspace_path 输出稳定含 tempdir，多次调用一致
T6_I18nKeys             — workspace_* 5 个 key 三语存在非空
T7_UiComponents          — ui.py 定义 ws_save_btn / ws_restore_btn / ws_clear_btn + 事件绑定引用
"""
import ast
import json
import os
import sys
import types
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# ---------- mock openai ----------
_mock_openai = types.ModuleType("openai")
_mock_openai.OpenAI = MagicMock()
for _n in ["AuthenticationError", "PermissionDeniedError", "RateLimitError",
           "NotFoundError", "APITimeoutError", "APIConnectionError", "APIStatusError"]:
    setattr(_mock_openai, _n, type(_n, (Exception,), {}))
sys.modules["openai"] = _mock_openai

from processor import (  # noqa: E402
    save_workspace, load_workspace, clear_workspace,
    _default_workspace_path, WS_ALLOWED_FIELDS,
)


SAMPLE_DATA = {
    "source_code": "def foo(): pass\n",
    "language": "Java",
    "ui_lang": "English",
    "python_style": "简约",
    "java_style": "详细",
    "naming_strategy": "subdir",
}


class T1_SaveLoadRoundTrip(unittest.TestCase):
    """保存→加载往返数据完整性"""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="ws_")
        self._path = os.path.join(self._tmpdir, "ws.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_all_fields_roundtrip(self):
        ok, msg = save_workspace(SAMPLE_DATA, path=self._path)
        self.assertTrue(ok, msg)
        ok, msg2, loaded = load_workspace(path=self._path)
        self.assertTrue(ok, msg2)
        self.assertEqual(loaded, SAMPLE_DATA)
        self.assertIn("已恢复", msg2)

    def test_partial_fields(self):
        partial = {"source_code": "x = 1", "ui_lang": "日本語"}
        ok, _ = save_workspace(partial, path=self._path)
        self.assertTrue(ok)
        ok, _, loaded = load_workspace(path=self._path)
        self.assertTrue(ok)
        self.assertEqual(loaded, partial)

    def test_overwrite_multiple_rounds(self):
        for i in range(3):
            data = {"source_code": f"v{i}", "ui_lang": "中文"}
            save_workspace(data, path=self._path)
        ok, _, loaded = load_workspace(path=self._path)
        self.assertTrue(ok)
        self.assertEqual(loaded["source_code"], "v2")

    def test_contains_saved_at_meta(self):
        save_workspace(SAMPLE_DATA, path=self._path)
        with open(self._path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIn("_saved_at", payload)
        self.assertIn("_version", payload)
        self.assertEqual(payload["_version"], 1)
        self.assertEqual(payload["data"], SAMPLE_DATA)


class T2_WhitelistSecurity(unittest.TestCase):
    """白名单安全：API Key 等非白名单字段绝不会被持久化"""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="wssec_")
        self._path = os.path.join(self._tmpdir, "ws.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_api_key_filtered_out_on_save(self):
        leaky = {
            "source_code": "hello",
            "api_key": "sk-THIS_IS_A_SECRET_123456",
            "api_base_url": "https://evil.com",
            "language": "Python",
            "password": "qwerty",
        }
        save_workspace(leaky, path=self._path)
        with open(self._path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIn("source_code", payload["data"])
        self.assertNotIn("api_key", payload["data"])
        self.assertNotIn("api_base_url", payload["data"])
        self.assertNotIn("password", payload["data"])
        self.assertNotIn("sk-THIS", json.dumps(payload))

    def test_none_fields_skipped(self):
        with_none = {
            "source_code": None,
            "language": "Python",
            "python_style": None,
            "ui_lang": "中文",
            "naming_strategy": None,
        }
        save_workspace(with_none, path=self._path)
        _, _, loaded = load_workspace(path=self._path)
        self.assertNotIn("source_code", loaded)
        self.assertNotIn("python_style", loaded)
        self.assertNotIn("naming_strategy", loaded)
        self.assertIn("language", loaded)
        self.assertIn("ui_lang", loaded)

    def test_injected_fields_filtered_on_load(self):
        """即使磁盘上的文件被注入，加载时仍按白名单过滤"""
        evil = {
            "_version": 999,
            "data": {
                "source_code": "x",
                "api_key": "INJECTED_FROM_DISK",
                "language": "Java",
                "arbitrary": 42,
            }
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(evil, f)
        _, _, loaded = load_workspace(path=self._path)
        self.assertNotIn("api_key", loaded)
        self.assertNotIn("arbitrary", loaded)
        self.assertEqual(loaded, {"source_code": "x", "language": "Java"})

    def test_whitelist_frozen_cannot_be_changed_runtime(self):
        self.assertIsInstance(WS_ALLOWED_FIELDS, frozenset)
        # frozenset 是不可变的
        with self.assertRaises(AttributeError):
            WS_ALLOWED_FIELDS.add("api_key")


class T3_FileFormatTolerance(unittest.TestCase):
    """文件格式容错：各种异常输入绝不抛 Exception"""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="wstol_")
        self._path = os.path.join(self._tmpdir, "ws.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_nonexistent_returns_false(self):
        ok, msg, data = load_workspace(path=self._path + "_nope")
        self.assertFalse(ok)
        self.assertEqual(data, {})

    def test_empty_file(self):
        Path(self._path).write_text("", encoding="utf-8")
        ok, msg, data = load_workspace(path=self._path)
        self.assertFalse(ok)
        self.assertEqual(data, {})

    def test_malformed_json(self):
        Path(self._path).write_text("{not valid {{ json", encoding="utf-8")
        ok, msg, data = load_workspace(path=self._path)
        self.assertFalse(ok)
        self.assertIn("JSON", msg)
        self.assertEqual(data, {})

    def test_top_level_list(self):
        Path(self._path).write_text("[1,2,3]", encoding="utf-8")
        ok, _, data = load_workspace(path=self._path)
        self.assertFalse(ok)
        self.assertEqual(data, {})

    def test_missing_data_key(self):
        Path(self._path).write_text('{"_version":1}', encoding="utf-8")
        ok, _, data = load_workspace(path=self._path)
        self.assertFalse(ok)
        self.assertEqual(data, {})

    def test_non_utf8_file(self):
        with open(self._path, "wb") as f:
            f.write(b"\xff\xfe\x00\x00")  # 非法 UTF-8 开头
        ok, msg, data = load_workspace(path=self._path)
        self.assertFalse(ok)
        self.assertEqual(data, {})

    def test_save_with_data_none_no_crash(self):
        ok, _ = save_workspace(None, path=self._path)
        self.assertTrue(ok)
        ok2, _, loaded = load_workspace(path=self._path)
        self.assertTrue(ok2)
        self.assertEqual(loaded, {})


class T4_ClearAndNonexistent(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="wsclear_")
        self._path = os.path.join(self._tmpdir, "ws.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_clear_existing(self):
        save_workspace(SAMPLE_DATA, path=self._path)
        self.assertTrue(os.path.isfile(self._path))
        ok, msg = clear_workspace(path=self._path)
        self.assertTrue(ok)
        self.assertFalse(os.path.isfile(self._path))

    def test_clear_nonexistent_no_crash(self):
        ok, msg = clear_workspace(path=os.path.join(self._tmpdir, "nope.json"))
        self.assertTrue(ok)
        self.assertIn("不存在", msg)

    def test_load_after_clear_returns_false(self):
        save_workspace(SAMPLE_DATA, path=self._path)
        clear_workspace(path=self._path)
        ok, _, data = load_workspace(path=self._path)
        self.assertFalse(ok)
        self.assertEqual(data, {})


class T5_DefaultPathStable(unittest.TestCase):
    def test_path_in_tempdir(self):
        p = _default_workspace_path()
        self.assertIn(tempfile.gettempdir(), p)
        self.assertTrue(p.endswith("_code_comments_agent_workspace.json"))

    def test_multiple_calls_consistent(self):
        a = _default_workspace_path()
        b = _default_workspace_path()
        self.assertEqual(a, b)

    def test_path_contains_short_hash(self):
        p = _default_workspace_path()
        # 文件名部分形如 xxxxxxxx_code_comments_agent_workspace.json (8 hex)
        base = os.path.basename(p)
        prefix = base.split("_code_comments_")[0]
        self.assertEqual(len(prefix), 8)
        self.assertRegex(prefix, r"^[0-9a-f]{8}$")


class T6_I18nKeys(unittest.TestCase):
    def test_all_workspace_keys_3langs(self):
        from i18n import TRANSLATIONS
        keys = ["workspace_title", "workspace_save_btn", "workspace_restore_btn",
                "workspace_clear_btn", "workspace_tip"]
        for k in keys:
            self.assertIn(k, TRANSLATIONS, msg=f"missing i18n key {k}")
            for lang in ["中文", "English", "日本語"]:
                self.assertIn(lang, TRANSLATIONS[k], msg=f"{k} missing {lang}")
                self.assertTrue(TRANSLATIONS[k][lang], msg=f"{k}/{lang} empty")


class T7_UiComponents(unittest.TestCase):
    """ui.py 源码中定义并引用了 workspace 三大按钮"""

    def _read_ui(self):
        with open(os.path.join(os.path.dirname(__file__), "ui.py"),
                  "r", encoding="utf-8") as f:
            return f.read()

    def test_components_declared(self):
        src = self._read_ui()
        for name in ["ws_save_btn", "ws_restore_btn", "ws_clear_btn",
                     "workspace_title_md", "ws_tip_md"]:
            self.assertIn(f"{name} = gr.", src, msg=f"missing {name} declaration")

    def test_events_bound(self):
        src = self._read_ui()
        for name in ["ws_save_btn.click", "ws_restore_btn.click", "ws_clear_btn.click"]:
            self.assertIn(name, src, msg=f"missing event binding {name}")

    def test_callbacks_use_processor_functions(self):
        src = self._read_ui()
        for fn in ["save_workspace", "load_workspace", "clear_workspace"]:
            self.assertIn(fn, src, msg=f"ui.py 未引用 processor.{fn}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
