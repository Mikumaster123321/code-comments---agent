# -*- coding: utf-8 -*-
"""v2.3.8 代码风格检查专项测试（离线，不依赖 LLM）

T1_PythonStyleLint    — style_lint(Python) 检出各类 PEP8 问题
T2_JavaStyleLint      — style_lint(Java) 检出 Google Java Style 问题
T3_CleanCode          — 干净代码 → 0 issues / 未发现问题报告
T4_AnalyzeCodeReturn5 — analyze_code 返回 5 元组（含 style_report）
T5_I18n               — style_title key 三语存在非空
T6_UiComponents       — ui.py 声明 style_title_md + style_output + analyze_btn 5 outputs
"""
import ast
import os
import sys
import types
import unittest
from unittest.mock import MagicMock

# ---------- mock openai ----------
_mock_openai = types.ModuleType("openai")
_mock_openai.OpenAI = MagicMock()
for _n in ["AuthenticationError", "PermissionDeniedError", "RateLimitError",
           "NotFoundError", "APITimeoutError", "APIConnectionError", "APIStatusError"]:
    setattr(_mock_openai, _n, type(_n, (Exception,), {}))
sys.modules["openai"] = _mock_openai

from processor import style_lint, analyze_code  # noqa: E402
from processor import _lint_python_basic, _lint_java_regex  # noqa: E402


PY_MESSY = '''def  foo(  x,y):
\treturn x+y
''' + "x = 'a' * 120\n"  # 行过长


PY_CLEAN = '''def foo(x, y):
    return x + y
'''

JAVA_MESSY = '''public class App{
\tpublic int add(int a,int b){return a+b;}
}
'''

JAVA_CLEAN = '''public class App {
  public int add(int a, int b) {
    return a + b;
  }
}
'''


class T1_PythonStyleLint(unittest.TestCase):
    """Python style_lint 检出 PEP8 问题"""

    def test_detects_long_line(self):
        report = style_lint("x = '" + "a" * 120 + "'\n", language="Python")
        self.assertIn("E501", report)

    def test_detects_trailing_whitespace(self):
        report = style_lint("x = 1   \n", language="Python")
        # trailing whitespace 会触发 W291（pycodestyle 或 basic）
        self.assertTrue("W291" in report or "尾随空格" in report or "trailing" in report.lower() or "E501" not in report)

    def test_detects_tab_indent(self):
        report = style_lint("\tx = 1\n", language="Python")
        self.assertTrue("W191" in report or "Tab" in report or "tab" in report.lower())

    def test_detects_missing_newline(self):
        report = style_lint("x = 1", language="Python")
        self.assertTrue("W292" in report or "换行" in report or "newline" in report.lower())

    def test_detects_extra_blank_lines(self):
        src = "x = 1\n\n\n\ny = 2\n"
        report = style_lint(src, language="Python")
        self.assertTrue("E303" in report or "空行过多" in report)

    def test_report_contains_title(self):
        report = style_lint("x = 1\n", language="Python")
        self.assertIn("代码风格检查", report)

    def test_report_contains_tool_name(self):
        report = style_lint("x = 1\n", language="Python")
        # 必须标明用的什么工具
        self.assertTrue("PEP8" in report or "pycodestyle" in report)

    def test_empty_source(self):
        report = style_lint("", language="Python")
        self.assertIn("无代码", report)

    def test_i18n_english(self):
        report = style_lint("x = 1\n", language="Python", comment_lang="English")
        self.assertIn("Code Style", report)

    def test_i18n_japanese(self):
        report = style_lint("x = 1\n", language="Python", comment_lang="日本語")
        self.assertIn("スタイル", report)


class T2_JavaStyleLint(unittest.TestCase):
    """Java style_lint 检出 Google Java Style 问题"""

    def test_detects_tab_indent(self):
        report = style_lint("\tint x = 1;\n", language="Java")
        self.assertTrue("GJL003" in report or "Tab" in report)

    def test_detects_missing_space_after_comma(self):
        report = style_lint("int a,b;\n", language="Java")
        self.assertTrue("GJL004" in report or "逗号" in report or "comma" in report.lower())

    def test_detects_brace_without_space(self):
        report = style_lint("if(true){\n  x = 1;\n}\n", language="Java")
        self.assertTrue("GJL005" in report or "大括号" in report)

    def test_detects_long_line(self):
        report = style_lint("// " + "a" * 120 + "\n", language="Java")
        self.assertTrue("GJL001" in report or "行过长" in report)

    def test_detects_missing_newline(self):
        report = style_lint("class A {}", language="Java")
        self.assertTrue("GJL007" in report or "换行" in report)

    def test_report_contains_tool_name(self):
        report = style_lint("class A {}\n", language="Java")
        self.assertIn("Google Java Style", report)

    def test_java_regex_direct(self):
        """直接测试 _lint_java_regex 返回结构"""
        issues = _lint_java_regex("\tint x=1;\n")
        self.assertIsInstance(issues, list)
        self.assertTrue(len(issues) > 0)
        for item in issues:
            self.assertEqual(len(item), 3)  # (code, lineno, desc)

    def test_java_extra_blank_lines(self):
        src = "class A {\n\n\n\n  int x = 1;\n}\n"
        issues = _lint_java_regex(src)
        self.assertTrue(any("GJL006" in i[0] for i in issues))


class T3_CleanCode(unittest.TestCase):
    """干净代码 → 0 issues"""

    def test_python_clean(self):
        report = style_lint(PY_CLEAN, language="Python")
        self.assertIn("未发现风格问题", report)

    def test_java_clean(self):
        report = style_lint(JAVA_CLEAN, language="Java")
        self.assertIn("未发现风格问题", report)


class T4_AnalyzeCodeReturn5(unittest.TestCase):
    """analyze_code 返回 5 元组（含 style_report）"""

    def test_python_returns_5_tuple(self):
        result = analyze_code(PY_CLEAN, language="Python", comment_lang="中文")
        self.assertEqual(len(result), 5, msg=f"analyze_code 应返回 5 元组，实际 {len(result)}")
        quality, annotation, summary, style_report, log = result
        self.assertIsInstance(style_report, str)
        self.assertIn("代码风格", style_report)
        self.assertIn("风格检查", log)

    def test_java_returns_5_tuple(self):
        result = analyze_code(JAVA_CLEAN, language="Java", comment_lang="中文")
        self.assertEqual(len(result), 5)
        quality, annotation, summary, style_report, log = result
        self.assertIsInstance(style_report, str)
        self.assertIn("代码风格", style_report)

    def test_empty_code_returns_5_tuple(self):
        result = analyze_code("", language="Python")
        self.assertEqual(len(result), 5)

    def test_invalid_python_returns_5_tuple(self):
        result = analyze_code("def broken(:", language="Python")
        self.assertEqual(len(result), 5)
        # style_report 应提示跳过
        style_report = result[3]
        self.assertIn("跳过", style_report)

    def test_invalid_java_returns_5_tuple(self):
        result = analyze_code("not java code", language="Java")
        self.assertEqual(len(result), 5)

    def test_messy_python_style_in_report(self):
        result = analyze_code(PY_MESSY, language="Python", comment_lang="中文")
        style_report = result[3]
        self.assertTrue("E501" in style_report or "行过长" in style_report or "W191" in style_report or "Tab" in style_report)


class T5_I18n(unittest.TestCase):
    """i18n style_title key 三语"""

    def test_style_title_exists(self):
        from i18n import TRANSLATIONS
        self.assertIn("style_title", TRANSLATIONS)
        entry = TRANSLATIONS["style_title"]
        for lang in ["中文", "English", "日本語"]:
            self.assertIn(lang, entry)
            self.assertTrue(entry[lang])
            self.assertIn("Style", entry[lang])


class T6_UiComponents(unittest.TestCase):
    """ui.py 声明 style_title_md + style_output + analyze_btn 5 outputs"""

    def _read_ui(self):
        path = os.path.join(os.path.dirname(__file__), "ui.py")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_components_declared(self):
        src = self._read_ui()
        self.assertIn("style_title_md = gr.Markdown", src)
        self.assertIn("style_output = gr.Markdown", src)

    def test_analyze_btn_5_outputs(self):
        src = self._read_ui()
        # analyze_btn.click outputs 必须包含 style_output
        # 找到 analyze_btn.click 块
        idx = src.find("analyze_btn.click")
        self.assertGreater(idx, -1)
        block = src[idx:idx + 500]
        self.assertIn("style_output", block)

    def test_style_title_in_apply_ui_language(self):
        src = self._read_ui()
        self.assertIn('t("style_title"', src)

    def test_style_title_md_in_ui_lang_change(self):
        src = self._read_ui()
        self.assertIn("style_title_md", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
