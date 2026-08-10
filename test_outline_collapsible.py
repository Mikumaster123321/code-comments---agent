# -*- coding: utf-8 -*-
"""v2.3.6 大纲折叠 + 搜索面板 CSS 注入专项测试（离线，不依赖 LLM）

覆盖项：
  T1 — build_outline_markdown(collapsible=True) 折叠结构
       - Python class+method+顶级函数：details/summary 结构正确
       - Java class+method：details/summary 结构正确
       - 只有顶级函数（无 class）：每个函数一个 details
       - 空源码 / 语法错误 / 无定义：返回空字符串
  T2 — build_outline_markdown(collapsible=False) 向后兼容
       - 输出旧版平铺 Markdown 无序列表格式
       - 锚点链接 #slug 仍然存在
  T3 — slug 一致性：collapsible=True 和 False 的锚点链接完全一致
       - 与 annotator build_markdown_docs 的 slug_id 完全一致
  T4 — i18n：search_hint key 三语存在非空
  T5 — CSS 注入验证：ui.py 的 custom_css 包含搜索面板 + 折叠样式关键选择器
"""
import ast
import os
import sys
import types
import unittest
from unittest.mock import MagicMock

# ---------- mock openai（避免真实网络） ----------
_mock_openai = types.ModuleType("openai")
_mock_openai.OpenAI = MagicMock()
for _name in ["AuthenticationError", "PermissionDeniedError", "RateLimitError",
             "NotFoundError", "APITimeoutError", "APIConnectionError", "APIStatusError"]:
    setattr(_mock_openai, _name, type(_name, (Exception,), {}))
sys.modules["openai"] = _mock_openai

from processor import build_outline_markdown  # noqa: E402
from Py.annotator import build_markdown_docs  # noqa: E402
from Java.java_annotator import build_java_markdown_docs  # noqa: E402


PY_SRC = '''
def top_func(x):
    return x + 1

class MyClass:
    def method_a(self):
        pass

    def method_b(self, y):
        return y * 2

def another_top(z):
    return z
'''

JAVA_SRC = '''
public class App {
    public int add(int a, int b) {
        return a + b;
    }

    public void run() {
        System.out.println("hi");
    }
}
'''

PY_NO_CLASS = '''
def foo():
    pass

def bar():
    pass
'''


class T1_CollapsibleStructure(unittest.TestCase):
    """collapsible=True 折叠结构验证"""

    def test_py_class_with_methods(self):
        md = build_outline_markdown(PY_SRC, language="Python", collapsible=True)
        # 标题存在
        self.assertIn("函数/类导航大纲", md)
        # details/summary 标签存在
        self.assertIn("<details", md)
        self.assertIn("<summary", md)
        self.assertIn("</details>", md)
        # class 默认展开
        self.assertIn("<details open>", md)
        # 子方法在 <ul><li> 中
        self.assertIn("<ul>", md)
        self.assertIn("<li>", md)
        self.assertIn("method_a", md)
        self.assertIn("method_b", md)
        # 顶级函数也存在
        self.assertIn("top_func", md)
        self.assertIn("another_top", md)
        # class 条目内有 code 标签
        self.assertIn("<code>MyClass</code>", md)

    def test_java_class_with_methods(self):
        md = build_outline_markdown(JAVA_SRC, language="Java", collapsible=True)
        self.assertIn("<details", md)
        self.assertIn("<summary", md)
        self.assertIn("App", md)
        self.assertIn("add", md)
        self.assertIn("run", md)
        # Java 方法标签应为 "Method"
        self.assertIn("Method", md)

    def test_py_no_class_only_functions(self):
        md = build_outline_markdown(PY_NO_CLASS, language="Python", collapsible=True)
        # 顶级函数各自一个 details（无 open 属性）
        self.assertEqual(md.count("<details>"), 2)  # foo + bar
        self.assertNotIn("<details open>", md)
        self.assertIn("foo", md)
        self.assertIn("bar", md)

    def test_empty_source(self):
        self.assertEqual(build_outline_markdown("", collapsible=True), "")

    def test_syntax_error(self):
        self.assertEqual(build_outline_markdown("def broken(:", collapsible=True), "")

    def test_no_definitions(self):
        self.assertEqual(build_outline_markdown("x = 1\nprint(x)", collapsible=True), "")

    def test_class_children_nested_in_details(self):
        """class 的方法必须嵌套在 class 的 <details> 内，不是平级"""
        md = build_outline_markdown(PY_SRC, language="Python", collapsible=True)
        # 找到 MyClass 的 details 块
        details_start = md.find("<details open>")
        details_end = md.find("</details>", details_start)
        self.assertGreater(details_start, -1)
        self.assertGreater(details_end, details_start)
        class_block = md[details_start:details_end + len("</details>")]
        # method_a 和 method_b 必须在 class 的 details 块内
        self.assertIn("method_a", class_block)
        self.assertIn("method_b", class_block)
        # top_func 不在 class 块内（在另一个 details 中）
        self.assertNotIn("top_func", class_block)


class T2_BackwardCompatFlatFormat(unittest.TestCase):
    """collapsible=False 向后兼容：旧版平铺 Markdown 无序列表格式"""

    def test_flat_format_python(self):
        md = build_outline_markdown(PY_SRC, language="Python", collapsible=False)
        # 不含 details/summary
        self.assertNotIn("<details", md)
        self.assertNotIn("<summary", md)
        # 含旧版无序列表
        self.assertIn("- 🧩", md)
        self.assertIn("- 🔧", md)
        # 含锚点链接
        self.assertIn("](#", md)
        # 含行号
        self.assertIn("*L", md)

    def test_flat_format_java(self):
        md = build_outline_markdown(JAVA_SRC, language="Java", collapsible=False)
        self.assertNotIn("<details", md)
        self.assertIn("App", md)
        self.assertIn("Method", md)


class T3_SlugConsistency(unittest.TestCase):
    """collapsible=True / False / annotator 三方 slug 一致性"""

    def test_python_slugs_match_annotator(self):
        """collapsible 版锚点与 annotator build_markdown_docs 的 slug_id 完全一致"""
        from Py.parser import get_defined_functions
        items = get_defined_functions(PY_SRC)
        # annotator slug 分配
        entries = [{"name": it["name"], "type": it["type"]} for it in items]
        used = set()
        from Py.annotator import _slugify
        annotator_slugs = []
        for e in entries:
            prefix = "cls-" if e["type"] == "class" else "fn-"
            annotator_slugs.append(_slugify(e["name"], prefix=prefix, used=used))

        # outline collapsible=True 的锚点链接
        md_collapsible = build_outline_markdown(PY_SRC, language="Python", collapsible=True)
        # outline collapsible=False 的锚点链接
        md_flat = build_outline_markdown(PY_SRC, language="Python", collapsible=False)

        for slug in annotator_slugs:
            href = f"#{slug}"
            self.assertIn(href, md_collapsible, msg=f"collapsible 缺少锚点 {href}")
            self.assertIn(href, md_flat, msg=f"flat 缺少锚点 {href}")

    def test_java_slugs_match_annotator(self):
        from Java.java_parser import get_defined_functions as get_java
        items = get_java(JAVA_SRC)
        entries = [{"name": it["name"], "type": it["type"]} for it in items]
        used = set()
        from Java.java_annotator import _slugify
        annotator_slugs = []
        for e in entries:
            prefix = "cls-" if e["type"] == "class" else "m-"
            annotator_slugs.append(_slugify(e["name"], prefix=prefix, used=used))

        md_collapsible = build_outline_markdown(JAVA_SRC, language="Java", collapsible=True)
        md_flat = build_outline_markdown(JAVA_SRC, language="Java", collapsible=False)

        for slug in annotator_slugs:
            href = f"#{slug}"
            self.assertIn(href, md_collapsible, msg=f"collapsible 缺少锚点 {href}")
            self.assertIn(href, md_flat, msg=f"flat 缺少锚点 {href}")

    def test_collapsible_and_flat_slugs_identical(self):
        """同一源码 collapsible=True 和 False 产出的锚点集合完全相同"""
        for src, lang in [(PY_SRC, "Python"), (JAVA_SRC, "Java"), (PY_NO_CLASS, "Python")]:
            md_c = build_outline_markdown(src, language=lang, collapsible=True)
            md_f = build_outline_markdown(src, language=lang, collapsible=False)
            # 提取所有 #slug 链接
            import re
            slugs_c = set(re.findall(r'href="#([^"]+)"', md_c)) | set(re.findall(r'\]\(#([^)]+)\)', md_c))
            slugs_f = set(re.findall(r'href="#([^"]+)"', md_f)) | set(re.findall(r'\]\(#([^)]+)\)', md_f))
            self.assertEqual(slugs_c, slugs_f, msg=f"slug 集合不一致 ({lang})")


class T4_I18nSearchHint(unittest.TestCase):
    """i18n search_hint key 三语存在非空"""

    def test_search_hint_exists(self):
        from i18n import TRANSLATIONS
        self.assertIn("search_hint", TRANSLATIONS)
        entry = TRANSLATIONS["search_hint"]
        for lang in ["中文", "English", "日本語"]:
            self.assertIn(lang, entry, msg=f"search_hint missing {lang}")
            self.assertTrue(entry[lang], msg=f"search_hint/{lang} empty")
            # 必须包含 Ctrl+F
            self.assertIn("Ctrl+F", entry[lang], msg=f"search_hint/{lang} missing Ctrl+F")


class T5_CSSInjection(unittest.TestCase):
    """ui.py custom_css 包含搜索面板 + 折叠样式关键选择器"""

    def test_css_contains_search_panel_selectors(self):
        # 读取 ui.py 源码检查 CSS 字符串
        ui_path = os.path.join(os.path.dirname(__file__), "ui.py")
        with open(ui_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 搜索面板关键选择器
        for selector in [".cm-panels", ".cm-textfield", ".cm-button",
                         ".cm-searchMatch", ".cm-searchMatch-selected"]:
            self.assertIn(selector, src, msg=f"CSS 缺少搜索面板选择器 {selector}")

    def test_css_contains_outline_fold_selectors(self):
        ui_path = os.path.join(os.path.dirname(__file__), "ui.py")
        with open(ui_path, "r", encoding="utf-8") as f:
            src = f.read()
        # 大纲折叠关键选择器
        for selector in [".outline-sidebar details", ".outline-sidebar summary",
                         ".outline-sidebar details[open]",
                         ".outline-sidebar summary::before",
                         ".outline-sidebar details > ul"]:
            self.assertIn(selector, src, msg=f"CSS 缺少折叠选择器 {selector}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
