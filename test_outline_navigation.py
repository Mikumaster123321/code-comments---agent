# -*- coding: utf-8 -*-
"""v2.6.2 函数/类导航大纲 + TOC + 锚点 单元测试
覆盖：build_outline_markdown、Py/annotator build_markdown_docs(含TOC+slug)、
Java/java_annotator build_java_markdown_docs(含TOC+slug)、i18n outline_title 三语齐全。
"""
import os
import sys
import types
import unittest

# —— 测试环境依赖隔离：注入假 dotenv + 假 openai + 假 DEEPSEEK_API_KEY —— #
os.environ.setdefault("DEEPSEEK_API_KEY", "fake_key_for_unittest_only")
def _inject_fake_module(name, attrs=None):
    m = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(m, k, v)
    sys.modules[name] = m
if "dotenv" not in sys.modules:
    _inject_fake_module("dotenv", {"load_dotenv": lambda *a, **k: None})
if "openai" not in sys.modules:
    # 仅当 openai 模块未加载时注入一个兼容桩，避免 discover 同进程下其它测试的 prompt capture 失效
    class _FakeChatCompletions:
        @staticmethod
        def create(*a, **k):
            raise RuntimeError("fake openai.create — 此测试不应触发真实 LLM 调用")
    class _FakeChat:
        completions = _FakeChatCompletions
    class _FakeOpenAI:
        def __init__(self, *a, **k):
            self.chat = _FakeChat
    _inject_fake_module("openai", {"OpenAI": _FakeOpenAI})


class SlugifyTests(unittest.TestCase):
    def test_slugify_basic_python_class(self):
        from Py.annotator import _slugify
        self.assertEqual(_slugify("Calculator", prefix="cls-"), "cls-calculator")
        self.assertEqual(_slugify("addTwoNumbers", prefix="fn-"), "fn-addtwonumbers")
        self.assertEqual(_slugify("foo bar", prefix="fn-"), "fn-foo-bar")

    def test_slugify_deduplicate(self):
        from Py.annotator import _slugify
        used = set()
        a = _slugify("foo", prefix="fn-", used=used)
        b = _slugify("foo", prefix="fn-", used=used)
        c = _slugify("foo", prefix="fn-", used=used)
        self.assertEqual(a, "fn-foo")
        self.assertEqual(b, "fn-foo-2")
        self.assertEqual(c, "fn-foo-3")


class BuildOutlineMarkdownTests(unittest.TestCase):
    PY_CODE = '''# sample
class Calculator:
    """A simple calculator"""
    def add(self, a, b):
        return a + b
    def subtract(self, a, b):
        return a - b

def helper(x):
    return x * 2

def main():
    c = Calculator()
    print(c.add(1, 2))
'''

    JAVA_CODE = '''public class HelloApp {
    public HelloApp() {}
    public int add(int a, int b) { return a + b; }
    public static void main(String[] args) {
        System.out.println("hi");
    }
}
'''

    def test_outline_non_empty_python(self):
        from processor import build_outline_markdown
        md = build_outline_markdown(self.PY_CODE, "Python")
        self.assertIn("fn-helper", md)
        self.assertIn("fn-main", md)
        self.assertIn("cls-calculator", md)
        # 行号信息：Calculator 大约在 L2
        self.assertIn("L2", md)
        # 大纲标题
        self.assertIn("📋 函数/类导航大纲", md)
        # 提示语：说明点跳转去 API 文档 Tab
        self.assertIn("API 文档", md)

    def test_outline_empty_code_returns_empty(self):
        from processor import build_outline_markdown
        self.assertEqual(build_outline_markdown("", "Python"), "")
        self.assertEqual(build_outline_markdown(None, "Python"), "")

    def test_outline_invalid_python_returns_empty(self):
        from processor import build_outline_markdown
        # 非法语法：直接返回空字符串（不抛异常）
        self.assertEqual(build_outline_markdown("def foo(:\n  pass", "Python"), "")

    def test_outline_slugs_match_annotator_slugs_python(self):
        """build_outline_markdown 的 slug 必须与 build_markdown_docs 生成的 slug_id 完全一致，
        否则大纲点击跳转会定位不到目标章节。"""
        from processor import build_outline_markdown
        from Py.annotator import build_markdown_docs
        from Py.parser import get_defined_functions

        items = get_defined_functions(self.PY_CODE)
        entries = []
        for it in items:
            entries.append({
                "name": it["name"], "type": it["type"], "lineno": it["lineno"],
                "code": it["code"], "docstring": "_doc_"
            })
        md_docs = build_markdown_docs(entries)
        outline = build_outline_markdown(self.PY_CODE, "Python")

        # 注释 doc_entries 里写入的 slug_id 必须出现在 build_markdown_docs 产出的锚点 id=... 里
        for e in entries:
            self.assertIn(f'id="{e["slug_id"]}"', md_docs)
            # 大纲必须包含同样的 #slug_id 链接
            self.assertIn(f"#{e['slug_id']}", outline)


class BuildMarkdownDocsTOCTests(unittest.TestCase):
    def test_python_docs_has_toc_section_and_anchor_heading(self):
        from Py.annotator import build_markdown_docs
        entries = [
            {"name": "Foo", "type": "class", "lineno": 1, "code": "class Foo: pass", "docstring": "Cls doc"},
            {"name": "bar", "type": "function", "lineno": 5, "code": "def bar(): pass", "docstring": "Fn doc"},
        ]
        md = build_markdown_docs(entries)
        # 顶部 TOC 章节出现
        self.assertIn("Table of Contents", md)
        # TOC 中必须有 Markdown 链接（](#xxx) 形式）
        self.assertIn("](#cls-foo)", md)
        self.assertIn("](#fn-bar)", md)
        # 详情 heading 有锚点 <a id="cls-foo"></a>
        self.assertIn('<a id="cls-foo"></a>', md)
        self.assertIn('<a id="fn-bar"></a>', md)
        # 行号展示
        self.assertIn("L1", md)
        self.assertIn("L5", md)

    def test_java_docs_has_toc_section_and_anchor_heading(self):
        from Java.java_annotator import build_java_markdown_docs
        entries = [
            {"name": "UserService", "type": "class", "lineno": 3, "code": "class UserService {}", "docstring": "svc"},
            {"name": "findById", "type": "method", "lineno": 7, "code": "int findById(long id)", "docstring": "find"},
        ]
        md = build_java_markdown_docs(entries)
        self.assertIn("Table of Contents", md)
        self.assertIn("](#cls-userservice)", md)
        # Java 方法前缀是 m- 不是 fn-
        self.assertIn("](#m-findbyid)", md)
        self.assertIn('<a id="cls-userservice"></a>', md)
        self.assertIn('<a id="m-findbyid"></a>', md)


class I18nOutlineTitleTests(unittest.TestCase):
    def test_outline_title_three_languages_present(self):
        from i18n import TRANSLATIONS
        key = "outline_title"
        self.assertIn(key, TRANSLATIONS)
        for lang in ("中文", "English", "日本語"):
            self.assertIn(lang, TRANSLATIONS[key], f"outline_title 缺少 {lang} 翻译")
            self.assertTrue(TRANSLATIONS[key][lang].strip(), f"outline_title {lang} 为空")
        self.assertIn("大纲", TRANSLATIONS["outline_title"]["中文"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
