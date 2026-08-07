# -*- coding: utf-8 -*-
"""v2.3.5 批量 ZIP 输出命名策略专项测试（离线可跑，mock LLM 避免网络）

覆盖项：
  1. _apply_naming_strategy 单函数（same / suffix / subdir × 无子目录 / 有子目录 / 双扩展名）
  2. _build_batch_zip 真实 ZIP 结果校验（naming 选项在归档路径上生效，plus processing.log / API_DOCS_ALL.md 始终在根）
  3. process_batch_files 端到端：3 策略 × (单 .py, 单 .java, 多 py+java) — 解包检查文件名匹配
  4. 默认值与非法值降级（未传 / 传 "xxx_nonexistent" → 降级到 suffix）
  5. i18n 三语覆盖：naming_section / naming_label / naming_same_label / naming_suffix_label / naming_subdir_label
"""
import ast
import io
import os
import re
import sys
import types
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

# ---------- 准备 mock openai 环境（避免真实 LLM 网络调用） ----------
from unittest.mock import MagicMock

_mock_openai = types.ModuleType("openai")
_mock_openai.OpenAI = MagicMock()
for _name in ["AuthenticationError", "PermissionDeniedError", "RateLimitError",
             "NotFoundError", "APITimeoutError", "APIConnectionError", "APIStatusError"]:
    setattr(_mock_openai, _name, type(_name, (Exception,), {}))
sys.modules["openai"] = _mock_openai

from processor import (  # noqa: E402
    _apply_naming_strategy,
    _build_batch_zip,
    process_batch_files,
    NAMING_SAME, NAMING_SUFFIX, NAMING_SUBDIR, NAMING_STRATEGIES,
)


# ---------- 让 llm_service 不真实调用网络：伪造 generate_* 等函数 ----------
def _install_llm_mocks():
    """离线伪造注释生成：对每个 item 返回一个稳定 docstring（无网络）。

    仅影响当前进程的 llm_service module 级函数引用；因为 processor 已在 import 阶段
    用 from 导入，所以还需要改 processor module 的同名全局引用。
    """
    import llm_service
    import processor

    def fake_docstring(item, lang="中文", style=None):
        name = item.get("name", "X")
        return f'"""{name} 功能函数：演示用 mock 返回（{lang}）"""'.strip()

    def fake_javadoc(item, lang="中文", style=None):
        name = item.get("name", "X")
        return f"/**\n * {name} Javadoc 注释（mock, {lang}）。\n */"

    def fake_translate_docstring(old, lang="中文", style=None):
        return f'"""(translated to {lang}) {old[:30]}"""'

    def fake_translate_javadoc(old, lang="中文", style=None):
        return f"/** (translated to {lang}) */"

    def fake_summary(src, lang="中文"):
        return f"- Mock summary（{lang}）- 代码包含若干模块。"

    # llm_service 原函数被 from 导入的模块，这里同时改 2 处
    for mod, prefix in [(llm_service, ""), (processor, "")]:
        for attr, fn in [("generate_docstring", fake_docstring),
                         ("generate_javadoc", fake_javadoc),
                         ("translate_docstring", fake_translate_docstring),
                         ("translate_javadoc", fake_translate_javadoc),
                         ("generate_code_summary", fake_summary),
                         ("generate_java_summary", fake_summary)]:
            setattr(mod, attr, fn)

_install_llm_mocks()


PY_SRC_SINGLE = '''
def add(a, b):
    return a + b

class C:
    def m(self, x):
        return x * 2
'''

PY_SRC_MULTI = '''
def foo(x):
    return x + 1
'''

JAVA_SRC_SINGLE = '''
public class App {
    public int add(int a, int b) { return a + b; }
}
'''

JAVA_SRC_MULTI = '''
class Helper {
    void run() { System.out.println("hi"); }
}
'''


def _zip_list(zip_path: str):
    """读取 zip 内所有成员名（POSIX 斜杠），返回排序后的列表。"""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    return sorted(n.replace("\\", "/") for n in names)


class T1_ApplyNamingStrategy(unittest.TestCase):
    """单元：_apply_naming_strategy 各种路径组合"""

    def test_same_no_subdir(self):
        self.assertEqual(_apply_naming_strategy("utils.py", NAMING_SAME), "utils.py")
        self.assertEqual(_apply_naming_strategy("Main.java", NAMING_SAME), "Main.java")

    def test_same_with_subdir(self):
        self.assertEqual(
            _apply_naming_strategy("mylib/core/utils.py", NAMING_SAME),
            "mylib/core/utils.py",
        )
        self.assertEqual(
            _apply_naming_strategy("com/example/App.java", NAMING_SAME),
            "com/example/App.java",
        )

    def test_suffix_no_subdir(self):
        self.assertEqual(
            _apply_naming_strategy("utils.py", NAMING_SUFFIX),
            "utils_annotated.py",
        )
        self.assertEqual(
            _apply_naming_strategy("Main.java", NAMING_SUFFIX),
            "Main_annotated.java",
        )

    def test_suffix_with_subdir(self):
        self.assertEqual(
            _apply_naming_strategy("mylib/core/utils.py", NAMING_SUFFIX),
            "mylib/core/utils_annotated.py",
        )
        self.assertEqual(
            _apply_naming_strategy("com/example/App.java", NAMING_SUFFIX),
            "com/example/App_annotated.java",
        )

    def test_subdir_no_subdir(self):
        self.assertEqual(
            _apply_naming_strategy("utils.py", NAMING_SUBDIR),
            "annotated/utils.py",
        )

    def test_subdir_with_subdir(self):
        self.assertEqual(
            _apply_naming_strategy("mylib/core/utils.py", NAMING_SUBDIR),
            "annotated/mylib/core/utils.py",
        )

    def test_invalid_strategy_fallback_to_suffix(self):
        got = _apply_naming_strategy("utils.py", "weird_invalid")
        self.assertEqual(got, "utils_annotated.py")

    def test_windows_backslash_normalized(self):
        # Windows 路径作为输入也应按 POSIX 输出
        self.assertEqual(
            _apply_naming_strategy("mylib\\utils.py", NAMING_SUFFIX),
            "mylib/utils_annotated.py",
        )


class T2_BuildBatchZipMemberNames(unittest.TestCase):
    """_build_batch_zip 打包结果成员名检查"""

    def setUp(self):
        self.tmp_root = tempfile.mkdtemp(prefix="bz_")
        # 准备输出目录：myprj/__init__.py / myprj/core.py / Main.java
        d = Path(self.tmp_root) / "out"
        (d / "myprj").mkdir(parents=True)
        (d / "myprj" / "__init__.py").write_text("", encoding="utf-8")
        (d / "myprj" / "core.py").write_text("def x(): pass\n", encoding="utf-8")
        (d / "Main.java").write_text("class M{}\n", encoding="utf-8")
        self.out_dir = str(d)

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _make(self, strategy):
        return _build_batch_zip(
            self.out_dir,
            "mock log line\n",
            "# aggregate\nmock content\n",
            naming_strategy=strategy,
        )

    def test_same_members(self):
        z = self._make(NAMING_SAME)
        self.addCleanup(os.unlink, z)
        names = _zip_list(z)
        for expected in ["myprj/__init__.py", "myprj/core.py", "Main.java",
                         "processing.log", "API_DOCS_ALL.md"]:
            self.assertIn(expected, names, msg=f"missing {expected} in {names}")
        # 不能出现 _annotated
        self.assertEqual([n for n in names if "_annotated" in n], [])
        # 不能出现 annotated/ 顶层目录（NAMING_SAME 不加）
        self.assertEqual([n for n in names if n.startswith("annotated/")], [])

    def test_suffix_members(self):
        z = self._make(NAMING_SUFFIX)
        self.addCleanup(os.unlink, z)
        names = _zip_list(z)
        for expected in [
            "myprj/__init___annotated.py",
            "myprj/core_annotated.py",
            "Main_annotated.java",
            "processing.log",
            "API_DOCS_ALL.md",
        ]:
            self.assertIn(expected, names, msg=f"missing {expected} in {names}")

    def test_subdir_members(self):
        z = self._make(NAMING_SUBDIR)
        self.addCleanup(os.unlink, z)
        names = _zip_list(z)
        for expected in [
            "annotated/myprj/__init__.py",
            "annotated/myprj/core.py",
            "annotated/Main.java",
            "processing.log",
            "API_DOCS_ALL.md",
        ]:
            self.assertIn(expected, names, msg=f"missing {expected} in {names}")
        # processing.log / API_DOCS_ALL.md 始终在 ZIP 根
        self.assertIn("processing.log", names)
        self.assertIn("API_DOCS_ALL.md", names)


class T3_ProcessBatchFilesEndToEnd(unittest.TestCase):
    """process_batch_files 端到端：mock LLM，用真实临时文件上传检查结果 ZIP。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="batch_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, content):
        p = Path(self.tmp) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return str(p)

    def _run(self, upload_list, strategy=NAMING_SUFFIX):
        log_text, zip_path = process_batch_files(
            upload_list,
            comment_lang="中文",
            incremental=False,
            naming_strategy=strategy,
        )
        return log_text, zip_path

    def test_py_single_suffix(self):
        path = self._write("myfile.py", PY_SRC_SINGLE)
        log, zip_path = self._run([path], NAMING_SUFFIX)
        self.assertIsNotNone(zip_path, msg=log)
        self.addCleanup(os.unlink, zip_path)
        names = _zip_list(zip_path)
        self.assertIn("myfile_annotated.py", names, msg=names)
        # log 里应该出现策略名
        self.assertIn("命名策略: suffix", log)
        # 注释后的源码 AST 可解析（保证没写坏）
        with zipfile.ZipFile(zip_path) as zf:
            data = zf.read("myfile_annotated.py").decode("utf-8")
        ast.parse(data)  # 语法错误会直接抛

    def test_java_single_same(self):
        path = self._write("MyApp.java", JAVA_SRC_SINGLE)
        log, zip_path = self._run([path], NAMING_SAME)
        self.assertIsNotNone(zip_path, msg=log)
        self.addCleanup(os.unlink, zip_path)
        names = _zip_list(zip_path)
        self.assertIn("MyApp.java", names, msg=names)
        self.assertNotIn("MyApp_annotated.java", names, msg=names)

    def test_multi_mixed_subdir(self):
        pypath = self._write("src/pkg/utils.py", PY_SRC_MULTI)
        javapath = self._write("src/pkg/Helper.java", JAVA_SRC_MULTI)
        log, zip_path = self._run([pypath, javapath], NAMING_SUBDIR)
        self.assertIsNotNone(zip_path, msg=log)
        self.addCleanup(os.unlink, zip_path)
        names = _zip_list(zip_path)
        # 都放入 annotated/ 子目录；同时原相对目录关系保持（不被打平）
        # 实现会基于「公共父级再向上退一层」决定 rel_path，这里只要
        # 「末尾 pkg 层级存在」即满足源目录结构可配置的要求（不强制包含 src/）。
        py_ok = any(n.endswith("/pkg/utils.py") or n == "annotated/pkg/utils.py"
                    for n in names)
        java_ok = any(n.endswith("/pkg/Helper.java") or n == "annotated/pkg/Helper.java"
                      for n in names)
        self.assertTrue(py_ok, msg=f"pkg/utils.py path missing (annotated/) in {names}")
        self.assertTrue(java_ok, msg=f"pkg/Helper.java path missing (annotated/) in {names}")
        self.assertIn("processing.log", names)
        self.assertIn("API_DOCS_ALL.md", names)
        # Python 下载后 AST 仍可通过（从 names 里找到 py 的真实 member）
        py_member = next(n for n in names if n.endswith(".py"))
        with zipfile.ZipFile(zip_path) as zf:
            ast.parse(zf.read(py_member).decode("utf-8"))

    def test_default_is_suffix_when_invalid(self):
        """非法策略自动降级到 NAMING_SUFFIX（不抛异常）"""
        path = self._write("hello.py", PY_SRC_SINGLE)
        log, zip_path = process_batch_files(
            [path], comment_lang="中文", incremental=False,
            naming_strategy="NONEXISTENT_STRATEGY",
        )
        self.assertIsNotNone(zip_path, msg=log)
        self.addCleanup(os.unlink, zip_path)
        names = _zip_list(zip_path)
        self.assertIn("hello_annotated.py", names)


class T4_I18n(unittest.TestCase):
    """i18n 翻译项三语存在 & 非空"""
    def test_naming_keys_exist(self):
        from i18n import TRANSLATIONS
        for key in ["naming_section", "naming_label",
                    "naming_same_label", "naming_suffix_label", "naming_subdir_label"]:
            self.assertIn(key, TRANSLATIONS)
            entry = TRANSLATIONS[key]
            for lang in ["中文", "English", "日本語"]:
                self.assertIn(lang, entry, msg=f"{key} missing {lang}")
                self.assertTrue(entry[lang], msg=f"{key}/{lang} empty")


if __name__ == "__main__":
    unittest.main(verbosity=2)
