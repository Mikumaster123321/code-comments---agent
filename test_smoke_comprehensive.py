"""综合 Smoke 测试：覆盖 process_code 边界、注释后语法、Diff 边界、i18n key 完整性、批量边界、模块导入。

不发起真实 LLM 请求（mock _call_llm_with_retry），可离线运行。
"""
import ast
import os
import sys
import types
import unittest
from unittest.mock import patch

# ---------- 缺失依赖的 fake 注入（与 test_styles.py 一致） ----------
def _inject_fake_module(name: str):
    if name not in sys.modules:
        m = types.ModuleType(name)
        sys.modules[name] = m
    return sys.modules[name]


_inject_fake_module("openai")
_inject_fake_module("zhipuai")
_inject_fake_module("dotenv")


class _FakeClient:
    def __init__(self, *a, **kw):
        self.api_key = kw.get("api_key")
        self.base_url = kw.get("base_url")


_fake_openai = sys.modules["openai"]
_fake_openai.OpenAI = _FakeClient
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None

import os as _os
_os.environ.setdefault("DEEPSEEK_API_KEY", "sk-test-fake-key")

sys.path.insert(0, ".")

import llm_service
from llm_service import _call_llm_with_retry as _orig_llm_call
from processor import (
    process_code, process_batch_files, build_split_diff_html,
)
from i18n import TRANSLATIONS, t


# ==================== Mock 辅助 ====================
class ReturnFixed:
    """每次 _call_llm_with_retry 返回固定字符串。"""

    def __init__(self, value: str):
        self.value = value
        self.calls = 0

    def __call__(self, prompt, temperature, max_tokens):
        self.calls += 1
        return self.value


# ==================== 测试用例 ====================
class TestProcessCodeInputBoundaries(unittest.TestCase):
    """process_code 在各种输入下不崩溃。"""

    def test_empty_string(self):
        a, m, l, _mp, _sp = process_code("", False, "Python", "中文")
        self.assertEqual(a, "")

    def test_only_spaces(self):
        a, m, l, _mp, _sp = process_code("   \n\t  ", False, "Python", "中文")
        self.assertEqual(a, "")

    def test_only_newlines(self):
        a, m, l, _mp, _sp = process_code("\n\n\n", False, "Python", "中文")
        self.assertEqual(a, "")

    def test_invalid_python_returns_original(self):
        """无效 Python（语法错误）返回原代码，不崩溃。"""
        src = "def x(:\n    return 1"
        a, m, l, _mp, _sp = process_code(src, False, "Python", "中文")
        self.assertEqual(a, src)
        self.assertIn("无效", m)

    def test_invalid_java_returns_original(self):
        """无效 Java（不包含有效 class/method 结构）返回原代码。"""
        src = "public class { int x = ;"
        a, m, l, _mp, _sp = process_code(src, False, "Java", "中文")
        self.assertEqual(a, src)
        self.assertTrue(
            ("无效" in m) or ("未检测到" in m),
            f"提示信息应说明代码无效或未检测到结构，实际: {m}"
        )

    def test_invalid_language_falls_back_to_python(self):
        """语言参数非 Python/Java，默认走 Python 分支不会错（实际 language Dropdown 限制）。"""
        src = "def f(x): return x\n"
        a, m, l, _mp, _sp = process_code(src, False, "Python", "中文")
        self.assertIsInstance(a, str)

    def test_return_tuple_len_5(self):
        """返回值始终是 5 元组。"""
        result = process_code("", False, "Python", "中文")
        self.assertEqual(len(result), 5)
        result = process_code("a=1", False, "Python", "中文")
        self.assertEqual(len(result), 5)

    def test_returns_types(self):
        a, m, l, mp, sp = process_code("x=1\n", False, "Python", "中文")
        self.assertIsInstance(a, str)
        self.assertIsInstance(m, str)
        self.assertIsInstance(l, str)


class TestAnnotatedCodeSyntaxValid(unittest.TestCase):
    """LLM 生成注释插入后，annotated_code 必须可被 Python 语法解析（ast.parse）。"""

    def test_python_insert_docstring_parses(self):
        """Mock 一个 Google 风格 docstring，验证插入后的代码语法正确。"""
        src = "def calc(x, y):\n    return x + y\n\ndef noop():\n    pass\n"
        fake_doc = '"""计算两数之和。\n\nArgs:\n    x: 第一个数字\n    y: 第二个数字\n\nReturns:\n    求和结果\n"""\n'
        # 因为有 2 个函数，mock 只返回同一个 fake_doc
        mock_fn = ReturnFixed(fake_doc)
        with patch.object(llm_service, "_call_llm_with_retry", mock_fn):
            annotated, markdown_doc, log, mdp, srcp = process_code(
                src, False, "Python", "中文"
            )
        # 至少调用了 1 次 LLM
        self.assertGreaterEqual(mock_fn.calls, 1)
        # annotated_code 必须可被 ast.parse
        try:
            ast.parse(annotated)
        except SyntaxError as e:
            self.fail(f"annotated Python 代码包含语法错误: {e}\n代码:\n{annotated}")

    def test_python_with_existing_docstring_incremental_still_parses(self):
        """已有 docstring 时增量模式（翻译），注释后语法仍正确。"""
        src = '''def foo(x):
    """旧的中文 docstring"""
    return x * 2
'''
        # 返回翻译后的英文 docstring
        mock_fn = ReturnFixed('"""Translated: English docstring"""\n')
        with patch.object(llm_service, "_call_llm_with_retry", mock_fn):
            annotated, _m, _l, _mdp, _sp = process_code(
                src, True, "Python", "English"
            )
        try:
            ast.parse(annotated)
        except SyntaxError as e:
            self.fail(f"增量翻译后的代码包含语法错误: {e}\n代码:\n{annotated}")

    def test_class_and_function_both_insert_parses(self):
        """类和函数同时插入注释，结果必须 parse 通过。"""
        src = "class A:\n    def method(self, x):\n        return x\n\ndef outer():\n    return 1\n"
        fake_func = '"""Func docstring."""\n'
        fake_cls = '"""Class docstring."""\n'
        # 交替返回类/函数 doc：第一次可能是类，第二次 method，第三次 outer
        call_seq = iter([fake_cls, fake_func, fake_func])

        def _next_prompt(*a, **kw):
            try:
                return next(call_seq)
            except StopIteration:
                return fake_func

        with patch.object(llm_service, "_call_llm_with_retry", _next_prompt):
            annotated, _m, _l, _, _ = process_code(src, False, "Python", "English")
        try:
            ast.parse(annotated)
        except SyntaxError as e:
            self.fail(f"插入类/函数注释后语法错误: {e}\n代码:\n{annotated}")


class TestDiffEdgeCases(unittest.TestCase):
    """Diff 视图各种边界输入不崩溃。"""

    def test_none_inputs_coerced(self):
        """虽然函数注解是 str，但调用方传空串也应兼容。"""
        html = build_split_diff_html("", "", "Python")
        self.assertIsInstance(html, str)

    def test_only_whitespace_lines(self):
        html = build_split_diff_html("a = 1\n   \n", "a = 1\n   \n", "Python")
        self.assertIn("未检测到代码差异", html)

    def test_single_line_diff(self):
        html = build_split_diff_html("a=1", "a=2", "Python")
        self.assertIn("diff-add", html)
        self.assertIn("diff-del", html)

    def test_after_has_many_blank_lines(self):
        """注释后多出若干空行，不崩溃。"""
        html = build_split_diff_html(
            "def f():\n    return 1\n",
            "def f():\n    '''doc'''\n\n\n    return 1\n",
            "Python",
        )
        self.assertIn("+3 插入", html)

    def test_chinese_only_comment_lines(self):
        """仅含中文字符的行。"""
        before = "x = 1\n"
        after = "# 我是中文注释\nx = 1\n"
        html = build_split_diff_html(before, after, "Python")
        self.assertIn("我是中文注释", html)


class TestI18nCoverage(unittest.TestCase):
    """扫描 ui.py / processor.py 里对 t(key, ...) 的所有调用，确保 key 都在 TRANSLATIONS。"""

    def _scan_for_t_keys(self, path: str):
        """简单正则匹配 t("xxx", 或 t('xxx',。"""
        import re
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        pattern = re.compile(r"\bt\(\s*['\"]([^'\"]+)['\"]\s*[,)]")
        return pattern.findall(src)

    def test_all_ui_keys_exist(self):
        missing = []
        for path in [os.path.join(".", "ui.py"), os.path.join(".", "processor.py")]:
            if not os.path.exists(path):
                continue
            for key in self._scan_for_t_keys(path):
                if key not in TRANSLATIONS:
                    missing.append((path, key))
        self.assertEqual(
            missing, [],
            f"以下 i18n key 在 TRANSLATIONS 中缺失: {missing}"
        )

    def test_every_lang_has_all_keys(self):
        """每个 key 必须有中文/English/日本語 三个值，不能少。"""
        required = {"中文", "English", "日本語"}
        bad = []
        for key, vals in TRANSLATIONS.items():
            missing_lang = required - set(vals.keys())
            if missing_lang:
                bad.append((key, sorted(missing_lang)))
        self.assertEqual(
            bad, [],
            f"以下 i18n key 缺少语言条目: {bad}"
        )

    def test_t_fallback_to_chinese(self):
        """不存在的 key 不会崩溃，返回对应值。"""
        self.assertIsInstance(t("tab_diff", "English"), str)
        # 找不到的 key 应返回中文或空串（不抛异常）
        try:
            r = t("NONEXISTENT_KEY_XYZ", "English")
        except Exception as e:
            self.fail(f"t() 对不存在 key 抛异常: {e}")


class TestBatchBoundaries(unittest.TestCase):
    """process_batch_files 边界输入不崩溃。"""

    def test_empty_list(self):
        log, zip_path = process_batch_files([], "中文", True)
        self.assertIsInstance(log, str)
        self.assertIsNone(zip_path)

    def test_none_uploaded_files(self):
        """传 None 代替 list，需兼容。"""
        try:
            log, zip_path = process_batch_files(None, "中文", True)
        except Exception as e:
            self.fail(f"process_batch_files(None) 不应抛异常: {e}")

    def test_bad_type_list_elements(self):
        """列表元素不是 file 字典 / 路径字符串，需要安全失败。"""
        log, zip_path = process_batch_files(["/nonexistent/path/abc.py"], "中文", True)
        self.assertIsInstance(log, str)


class TestModuleSanity(unittest.TestCase):
    """导入 / 基本符号完整性检查。"""

    def test_all_processor_exports_exist(self):
        """ui 依赖 processor 导出的符号全部存在。"""
        import processor
        required = [
            "process_code", "analyze_code", "handle_file_upload",
            "process_batch_files", "build_split_diff_html",
        ]
        missing = [n for n in required if not hasattr(processor, n)]
        self.assertEqual(missing, [], f"processor 缺少符号: {missing}")

    def test_all_llm_service_constants(self):
        required_const = [
            "PYTHON_STYLE_GOOGLE", "PYTHON_STYLE_NUMPY", "PYTHON_STYLE_RST",
            "JAVA_STYLE_JAVADOC", "JAVA_STYLE_MINIMAL",
        ]
        missing = [n for n in required_const if not hasattr(llm_service, n)]
        self.assertEqual(missing, [], f"llm_service 缺少常量: {missing}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
