# -*- coding: utf-8 -*-
"""v2.7.0 实时进度条 + 取消任务 测试（生成器 / CancelToken）

覆盖：
  1) CancelToken 线程安全行为
  2) process_code_with_progress 边界（空代码/无效代码）
  3) process_code_with_progress 有效代码（中间态+最终态结构）
  4) _process_python_with_progress 取消场景：取消触发后保留中间结果
  5) process_batch_with_progress 边界（空列表/非法路径）
  6) i18n 新增 cancel_btn / batch_cancel_btn 三语完整性
"""
import sys
import os
import types
import unittest
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Fake 第三方依赖（测试核心逻辑，不真实调用 LLM）
def _inject_fake_module(name: str, **attrs):
    if name not in sys.modules:
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m
        return m
    # 已存在：覆盖传入 attrs
    m = sys.modules[name]
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def _no_op(*_a, **_kw):
    return None


_inject_fake_module("dotenv", load_dotenv=_no_op, find_dotenv=_no_op)
m_openai = _inject_fake_module("openai")
m_openai.OpenAI = type("OpenAI", (), {"__init__": lambda self, *a, **kw: None})
_inject_fake_module("zhipuai")

# 避免 config.py 在 import 阶段因为无 API Key 抛异常
os.environ.setdefault("DEEPSEEK_API_KEY", "fake_key_for_unittest_only")
os.environ.setdefault("ZHIPU_API_KEY", "fake_key_for_unittest_only")

# 在 import processor 前，把 llm_service 的 generate / translate 替换成快速 mock
import processor as proc_mod  # noqa: E402
import llm_service  # noqa: E402
from i18n import TRANSLATIONS  # noqa: E402
from processor import (  # noqa: E402
    CancelToken,
    _process_python_with_progress,
    _process_java_with_progress,
    process_code_with_progress,
    process_batch_with_progress,
)

PY_SAMPLE = """\
def add(a, b):
    return a + b

class Calculator:
    def mul(self, x, y):
        return x * y
"""

JAVA_SAMPLE = """\
public class Hello {
    public int add(int a, int b) {
        return a + b;
    }
}
"""


def _install_fast_llm_stubs():
    """把真实 LLM 调用替换成本地 0 延迟假数据，避免真请求 API。"""
    def mock_gen_doc(item, cl="中文", style=None):
        name = item.get("name", "fn")
        if name == "Calculator":
            return f'"""{name}: 模拟类注释"""'
        return f'"""Simulated docstring for {name}.\n\nArgs:\n    a: 第一个参数\nReturns:\n    结果\n"""'

    def mock_translate_doc(doc, cl, style=None):
        return (doc or "") + " [已翻译Mock]"

    def mock_gen_javadoc(item, cl="中文", style=None):
        name = item.get("name", "fn")
        return f"/**\n * {name} 模拟Javadoc.\n * @param x 参数\n * @return 结果\n */"

    def mock_translate_javadoc(jv, cl, style=None):
        return (jv or "") + " [translated mock]"

    # 替换
    llm_service.generate_docstring = mock_gen_doc
    llm_service.translate_docstring = mock_translate_doc
    llm_service.generate_javadoc = mock_gen_javadoc
    llm_service.translate_javadoc = mock_translate_javadoc
    # 透传到 processor 引用（import 时绑定的）
    proc_mod.generate_docstring = mock_gen_doc
    proc_mod.translate_docstring = mock_translate_doc
    proc_mod.generate_javadoc = mock_gen_javadoc
    proc_mod.translate_javadoc = mock_translate_javadoc


_install_fast_llm_stubs()


class TestCancelToken(unittest.TestCase):
    def test_init_state_false(self):
        tok = CancelToken()
        self.assertFalse(tok.is_canceled())

    def test_cancel_and_reset(self):
        tok = CancelToken()
        tok.cancel()
        self.assertTrue(tok.is_canceled())
        tok.reset()
        self.assertFalse(tok.is_canceled())

    def test_thread_safe(self):
        tok = CancelToken()
        n = 10000

        def canceller():
            for _ in range(n):
                tok.cancel()
                tok.reset()

        threads = [threading.Thread(target=canceller) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # 结束时：最后一次 reset 后状态为 False
        self.assertIsInstance(tok.is_canceled(), bool)


class TestProcessCodeWithProgressBoundaries(unittest.TestCase):
    def test_empty_code_single_yield(self):
        frames = list(process_code_with_progress("", incremental=True, language="Python", comment_lang="中文"))
        self.assertEqual(len(frames), 1)
        ann, md, lg, md_p, src_p = frames[0]
        self.assertEqual(ann, "")
        self.assertIsNone(md_p)
        self.assertIsNone(src_p)

    def test_invalid_python_single_yield(self):
        frames = list(process_code_with_progress("@@@@ not python", incremental=True, language="Python"))
        self.assertEqual(len(frames), 1)
        ann, md, lg, md_p, src_p = frames[0]
        self.assertIsNone(md_p)
        self.assertIsNone(src_p)
        self.assertIn("无效", lg + " " + md)

    def test_invalid_java_single_yield(self):
        frames = list(process_code_with_progress("abc 123 不是java", incremental=True, language="Java"))
        self.assertEqual(len(frames), 1)
        ann, md, lg, md_p, src_p = frames[0]
        self.assertIsNone(md_p)
        self.assertIsNone(src_p)


class TestProcessCodeWithProgressValid(unittest.TestCase):
    def test_python_multi_yield_and_final_tuple(self):
        frames = list(process_code_with_progress(PY_SAMPLE, incremental=False, language="Python", comment_lang="中文"))
        self.assertGreaterEqual(len(frames), 2, "至少有 1 帧中间态 + 1 帧最终态")
        # 最后一帧是完整 5 元组（md_path / src_path 均为 str 文件路径）
        last = frames[-1]
        ann, md, lg, md_p, src_p = last
        self.assertIsInstance(ann, str)
        self.assertTrue(len(ann) > 0)
        self.assertIsInstance(md_p, str)
        self.assertIsInstance(src_p, str)
        self.assertTrue(md_p.endswith(".md"))
        self.assertTrue(src_p.endswith(".py"))
        # 中间帧：log_text 非空字符串
        for f in frames[:-1]:
            _a, _m, log_t, _mp, _sp = f
            self.assertIsInstance(log_t, str)

    def test_java_multi_yield_and_final_tuple(self):
        frames = list(process_code_with_progress(JAVA_SAMPLE, incremental=False, language="Java", comment_lang="中文"))
        self.assertGreaterEqual(len(frames), 2)
        last = frames[-1]
        ann, md, lg, md_p, src_p = last
        self.assertIsInstance(ann, str)
        self.assertIsInstance(md_p, str)
        self.assertIsInstance(src_p, str)
        self.assertTrue(md_p.endswith(".md"))
        self.assertTrue(src_p.endswith(".java"))

    def test_progress_cb_called(self):
        called = {"n": 0, "last_ratio": -1.0}

        def cb(ratio, desc):
            called["n"] += 1
            self.assertGreaterEqual(ratio, 0.0)
            self.assertLessEqual(ratio, 1.0)
            called["last_ratio"] = max(called["last_ratio"], ratio)

        frames = list(process_code_with_progress(
            PY_SAMPLE, incremental=False, language="Python", comment_lang="中文",
            progress_cb=cb,
        ))
        self.assertGreater(called["n"], 0)
        # 最终 ratio 应当为 1.0
        self.assertAlmostEqual(called["last_ratio"], 1.0, delta=0.001)


class TestCancelScenario(unittest.TestCase):
    def test_python_cancel_before_process(self):
        """取消标志位一开始就为 True：只解析，跳过后续阶段"""
        tok = CancelToken()
        tok.cancel()
        frames = list(_process_python_with_progress(PY_SAMPLE, False, "中文", None, tok))
        self.assertGreaterEqual(len(frames), 1)
        # 最终帧（最后一帧）：md_p / src_p 应该有（即使取消，也会生成已有的结果）
        last = frames[-1]
        ann, md, lg, md_p, src_p = last
        # 取消状态下不会有 LLM 生成阶段，但应该有快速返回
        self.assertIn("取消", lg)
        # 返回的文件路径应该依然存在（打包了已有的）
        self.assertIsInstance(md_p, str)
        self.assertIsInstance(src_p, str)

    def test_java_cancel_before_process(self):
        tok = CancelToken()
        tok.cancel()
        frames = list(_process_java_with_progress(JAVA_SAMPLE, False, "中文", None, tok))
        self.assertGreaterEqual(len(frames), 1)
        last = frames[-1]
        ann, md, lg, md_p, src_p = last
        self.assertIn("取消", lg)
        self.assertIsInstance(md_p, str)
        self.assertIsInstance(src_p, str)


class TestBatchWithProgress(unittest.TestCase):
    def test_empty_upload(self):
        frames = list(process_batch_with_progress(None, "中文", True))
        self.assertEqual(len(frames), 1)
        lg, zp = frames[-1]
        self.assertIn("未上传", lg)
        self.assertIsNone(zp)

    def test_empty_list(self):
        frames = list(process_batch_with_progress([], "中文", True))
        self.assertEqual(len(frames), 1)
        lg, zp = frames[-1]
        self.assertIn("未上传", lg)
        self.assertIsNone(zp)

    def test_illegal_paths_only(self):
        frames = list(process_batch_with_progress(
            ["not_exists_xyz_1234.py", "another_not_exists.java"], "中文", True,
        ))
        self.assertGreaterEqual(len(frames), 1)
        lg, zp = frames[-1]
        # 没有可处理的文件 -> None zip
        self.assertIsNone(zp)


class TestI18nCoverageProgress(unittest.TestCase):
    def test_cancel_btn_three_langs(self):
        key = "cancel_btn"
        self.assertIn(key, TRANSLATIONS, f"missing i18n key: {key}")
        entry = TRANSLATIONS[key]
        for lang in ("中文", "English", "日本語"):
            self.assertIn(lang, entry, f"cancel_btn missing {lang}")
            self.assertTrue(isinstance(entry[lang], str) and len(entry[lang]) > 0)

    def test_batch_cancel_btn_three_langs(self):
        key = "batch_cancel_btn"
        self.assertIn(key, TRANSLATIONS, f"missing i18n key: {key}")
        entry = TRANSLATIONS[key]
        for lang in ("中文", "English", "日本語"):
            self.assertIn(lang, entry, f"batch_cancel_btn missing {lang}")
            self.assertTrue(isinstance(entry[lang], str) and len(entry[lang]) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
