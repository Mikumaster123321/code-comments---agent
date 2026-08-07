"""注释风格模板单元测试：验证 5 种风格 prompt 注入、翻译规则、参数链路。

测试策略：mock _call_llm_with_retry，捕获实际传入的 prompt，断言关键词。
不发起真实 LLM 请求，可离线运行。缺少 openai / zhipuai 时会自动注入 fake 模块。
"""
import sys
import types
import unittest
from unittest.mock import patch


# 提前注入缺失的第三方模块 fake，避免 import 阶段报错
def _inject_fake_module(name: str):
    if name not in sys.modules:
        m = types.ModuleType(name)
        sys.modules[name] = m
    return sys.modules[name]


_inject_fake_module("openai")
_inject_fake_module("zhipuai")
_inject_fake_module("dotenv")


class _FakeClient:
    """fake openai client，仅用于让 config.py import 通过"""
    def __init__(self, *a, **kw):
        self.api_key = kw.get("api_key")
        self.base_url = kw.get("base_url")


fake_openai = sys.modules["openai"]
fake_openai.OpenAI = _FakeClient

fake_dotenv = sys.modules["dotenv"]
fake_dotenv.load_dotenv = lambda *a, **kw: None

# 防止 config.py 在 import 阶段报缺少 API key
import os
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-test-fake-key")

sys.path.insert(0, ".")

import llm_service
from llm_service import (
    generate_docstring, translate_docstring,
    generate_javadoc, translate_javadoc,
    PYTHON_STYLE_GOOGLE, PYTHON_STYLE_NUMPY, PYTHON_STYLE_RST,
    JAVA_STYLE_JAVADOC, JAVA_STYLE_MINIMAL,
)
from processor import process_code, build_split_diff_html


# ==================== mock 工具 ====================
class PromptCapture:
    """捕获传入 _call_llm_with_retry 的 prompt。"""

    def __init__(self, return_value: str = "MOCKED_OUTPUT\n"):
        self.prompts = []
        self.return_value = return_value

    def __call__(self, prompt, temperature, max_tokens):
        self.prompts.append(prompt)
        return self.return_value


# ==================== 测试样本 ====================
PYTHON_ITEM = {
    "name": "calc_total",
    "type": "function",
    "code": "def calc_total(a: int, b: int) -> int:\n    return a + b",
    "params": ["a", "b"],
    "returns": "int",
    "decorator": [],
}

JAVA_ITEM = {
    "name": "UserService",
    "type": "class",
    "code": "public class UserService { public String greet(String name){ return \"hi \\+ name; } }",
    "params": ["name"],
    "returns": "String",
}


# ==================== Python 生成风格测试 ====================
class TestPythonGenerateStyles(unittest.TestCase):

    def setUp(self):
        self.capture = PromptCapture('"""功能说明\n\nArgs:\n    x: int\n\nReturns:\n    int\n"""')

    def test_google_style_prompt(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_docstring(PYTHON_ITEM, "中文", PYTHON_STYLE_GOOGLE)
        prompt = self.capture.prompts[0]
        self.assertIn("Google", prompt)
        self.assertIn("Args:", prompt)

    def test_numpy_style_prompt(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_docstring(PYTHON_ITEM, "中文", PYTHON_STYLE_NUMPY)
        prompt = self.capture.prompts[0]
        self.assertIn("NumPy", prompt)
        self.assertIn("Parameters", prompt)
        self.assertIn("-------", prompt)

    def test_rst_style_prompt(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_docstring(PYTHON_ITEM, "中文", PYTHON_STYLE_RST)
        prompt = self.capture.prompts[0]
        self.assertIn("reStructuredText", prompt)
        self.assertIn(":param", prompt)
        self.assertIn(":return:", prompt)

    def test_default_is_google(self):
        """不传 style 时应默认为 Google 风格。"""
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_docstring(PYTHON_ITEM, "中文")
        prompt = self.capture.prompts[0]
        self.assertIn("Google", prompt)


# ==================== Python 翻译风格测试 ====================
class TestPythonTranslateStyles(unittest.TestCase):

    def setUp(self):
        self.capture = PromptCapture('"""翻译结果"""')

    def test_google_translate_rule(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            translate_docstring('"""Old docstring"""', "English", PYTHON_STYLE_GOOGLE)
        prompt = self.capture.prompts[0]
        self.assertIn("Google", prompt)

    def test_numpy_translate_rule(self):
        self.capture.prompts.clear()
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            translate_docstring('"""Old docstring"""', "English", PYTHON_STYLE_NUMPY)
        prompt = self.capture.prompts[0]
        self.assertIn("NumPy", prompt)

    def test_rst_translate_rule(self):
        self.capture.prompts.clear()
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            translate_docstring('"""Old docstring"""', "English", PYTHON_STYLE_RST)
        prompt = self.capture.prompts[0]
        self.assertIn("reStructuredText", prompt)


# ==================== Java 生成风格测试 ====================
class TestJavaGenerateStyles(unittest.TestCase):

    def setUp(self):
        self.capture = PromptCapture("/** Javadoc */")

    def test_javadoc_style_prompt(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_javadoc(JAVA_ITEM, "中文", JAVA_STYLE_JAVADOC)
        prompt = self.capture.prompts[0]
        self.assertIn("Javadoc", prompt)
        self.assertIn("@param", prompt)

    def test_minimal_style_prompt(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_javadoc(JAVA_ITEM, "中文", JAVA_STYLE_MINIMAL)
        prompt = self.capture.prompts[0]
        self.assertIn("极简", prompt)

    def test_default_is_javadoc(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            generate_javadoc(JAVA_ITEM, "中文")
        prompt = self.capture.prompts[0]
        self.assertIn("Javadoc", prompt)


# ==================== Java 翻译风格测试 ====================
class TestJavaTranslateStyles(unittest.TestCase):

    def setUp(self):
        self.capture = PromptCapture("/** Translated */")

    def test_javadoc_translate(self):
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            translate_javadoc("/** Old */", "English", JAVA_STYLE_JAVADOC)
        prompt = self.capture.prompts[0]
        self.assertIn("Javadoc", prompt)

    def test_minimal_translate(self):
        self.capture.prompts.clear()
        with patch.object(llm_service, "_call_llm_with_retry", self.capture):
            translate_javadoc("/** Old */", "English", JAVA_STYLE_MINIMAL)
        prompt = self.capture.prompts[0]
        self.assertIn("极简", prompt)


# ==================== processor 参数链路测试 ====================
class TestProcessorStyleArgPass(unittest.TestCase):
    """确保 process_code 能正确把风格透传到 LLM 层（不调用真实 API）。"""

    def test_process_python_with_style_no_crash(self):
        capture = PromptCapture('"""MOCK"""')
        code = "def foo(x):\n    return x + 1\n"
        with patch.object(llm_service, "_call_llm_with_retry", capture):
            annotated, md, log, _mdp, _srcp = process_code(
                code, False, "Python", "中文",
                python_style=PYTHON_STYLE_NUMPY,
            )
        self.assertIsInstance(annotated, str)
        self.assertGreater(len(capture.prompts), 0)
        prompt = capture.prompts[0]
        # 必须注入 NumPy 风格关键词
        self.assertIn("NumPy", prompt)

    def test_process_java_with_style_no_crash(self):
        capture = PromptCapture("/** Mock */")
        code = "public class A { public int b(int x){return x;} }"
        with patch.object(llm_service, "_call_llm_with_retry", capture):
            annotated, md, log, _mdp, _srcp = process_code(
                code, False, "Java", "中文",
                java_style=JAVA_STYLE_MINIMAL,
            )
        self.assertIsInstance(annotated, str)
        self.assertGreater(len(capture.prompts), 0)
        prompt = capture.prompts[0]
        # 必须注入极简关键词
        self.assertIn("极简", prompt)


# ==================== Diff 视图测试 ====================
class TestDiffView(unittest.TestCase):
    """验证 build_split_diff_html 输出结构、统计、样式关键词正确。"""

    def test_same_code_no_diff(self):
        """相同代码 → 统计 0/0/未变，提示 未检测到差异。"""
        html = build_split_diff_html("def f(x):\n    return x\n",
                                     "def f(x):\n    return x\n",
                                     "Python")
        self.assertIn("未检测到代码差异", html)
        self.assertIn("+0 插入 / -0 删除 / 2 未变", html)
        self.assertIn("Before", html)
        self.assertIn("After", html)
        self.assertIn("</table>", html)

    def test_insert_docstring_shows_add(self):
        """在函数上方插入三引号 docstring → after 新增行渲染为 diff-add，无删除行。"""
        before = "def foo():\n    return 42\n"
        after = '"""模块功能。"""\ndef foo():\n    """功能说明。"""\n    return 42\n'
        html = build_split_diff_html(before, after, "Python")
        # 新增行存在（具体 td cell class 片段）
        self.assertIn('<td class="diff-code diff-add">', html)
        # 删除行不存在（注意：CSS 样式表里总有 diff-del 字面量，因此必须匹配 td 的具体 class）
        self.assertNotIn('<td class="diff-code diff-del">', html)
        self.assertNotIn('<td class="diff-ln diff-del">', html)
        self.assertIn('+2 插入 / -0 删除 / 2 未变', html)
        # 包含模块 docstring 内容 HTML escape 后的片段
        self.assertIn("模块功能", html)

    def test_delete_line_shows_del(self):
        """删除行 → diff-del td cell 出现。"""
        before = "a = 1\nb = 2\nc = 3\n"
        after = "a = 1\nc = 3\n"
        html = build_split_diff_html(before, after, "Python")
        self.assertIn('<td class="diff-code diff-del">', html)
        self.assertIn("+0 插入 / -1 删除 / 2 未变", html)

    def test_replace_line_adds_and_deletes(self):
        """替换行 → 同时有 add 和 del。"""
        before = "x = 'old'\n"
        after = "x = 'new'\n"
        html = build_split_diff_html(before, after, "Java")
        self.assertIn("diff-add", html)
        self.assertIn("diff-del", html)
        self.assertIn("Java", html)

    def test_empty_input(self):
        """空输入不报错。"""
        html = build_split_diff_html("", "", "Python")
        self.assertIn("未输入代码，没有差异可展示。", html)

    def test_language_label_propagates(self):
        """语言标签正确显示在 Before/After 头部。"""
        html_py = build_split_diff_html("a=1\n", "a=1\n", "Python")
        self.assertIn("（Python）", html_py)
        html_java = build_split_diff_html("a=1;\n", "a=1;\n", "Java")
        self.assertIn("（Java）", html_java)

    def test_html_escape_special_chars(self):
        """HTML 特殊字符如 < > & 被 escape，避免 XSS / 样式错乱。"""
        before = "s = '<script>alert(1)</script>'\n"
        after = "s = '<script>alert(1)</script>'\n"
        html = build_split_diff_html(before, after, "Python")
        # < 应被转义为 &lt;，而不是直接出现在 DOM 里
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
