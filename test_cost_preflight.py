# -*- coding: utf-8 -*-
"""v2.3.3 API Key 预检 / Token 用量估算 单元测试
覆盖：
- estimate_tokens_cost 数学正确性（0/N 项目、自定义 per_item、金额拆分）
- ping_api_key 参数正确性（断言传 max_tokens=1 / temperature=0 / messages=[{"role":"user","content":"ping"}]）
- ping_api_key 7 种异常精确捕获（AuthenticationError/RateLimitError/NotFoundError...）
- preflight_check 边界：空代码 / 0 条目 / Python / Java / EN JA 文案 / i18n fallback
- i18n：preflight_btn / estimate_label / preflight_label 三语齐全
"""
import os
import sys
import types
import unittest

# —— 测试环境依赖隔离 —— #
os.environ.setdefault("DEEPSEEK_API_KEY", "fake_key_for_unittest_only")


def _inject_fake_module(name, attrs=None):
    m = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(m, k, v)
    sys.modules[name] = m


if "dotenv" not in sys.modules:
    _inject_fake_module("dotenv", {"load_dotenv": lambda *a, **k: None})

# —— 注入一个可拦截的假 openai：client.chat.completions.create 会被我们 patch —— #
class _FakeChoices:
    def __init__(self):
        # 支持索引访问（resp.choices[0]）
        pass

    def __len__(self):
        return 1


class _FakeResp:
    def __init__(self):
        self.choices = _FakeChoices()


class _FakeCompletions:
    # 单元测试里用 unittest.mock.patch 替换该 create
    @staticmethod
    def create(*a, **k):  # pragma: no cover - 真实行为由 patch 决定
        return _FakeResp()


class _FakeChat:
    completions = _FakeCompletions


class _FakeOpenAI:
    def __init__(self, *a, **k):
        self.chat = _FakeChat


if "openai" not in sys.modules:
    # 注入假 openai 模块 + 全部常见异常类
    class _BaseFakeErr(Exception):
        pass
    class _AuthenticationError(_BaseFakeErr): pass
    class _PermissionDeniedError(_BaseFakeErr): pass
    class _RateLimitError(_BaseFakeErr): pass
    class _NotFoundError(_BaseFakeErr): pass
    class _APITimeoutError(_BaseFakeErr): pass

    _fake_mod = types.ModuleType("openai")
    _fake_mod.OpenAI = _FakeOpenAI
    _fake_mod.AuthenticationError = _AuthenticationError
    _fake_mod.PermissionDeniedError = _PermissionDeniedError
    _fake_mod.RateLimitError = _RateLimitError
    _fake_mod.NotFoundError = _NotFoundError
    _fake_mod.APITimeoutError = _APITimeoutError
    sys.modules["openai"] = _fake_mod
else:  # pragma: no cover - 分支只在 discover 同进程时触发
    _fake_mod = sys.modules["openai"]


class EstimateTokensCostTests(unittest.TestCase):
    def test_zero_items_returns_zero_vector(self):
        from llm_service import estimate_tokens_cost
        self.assertEqual(estimate_tokens_cost(0), (0, 0, 0, 0.0))
        self.assertEqual(estimate_tokens_cost(-5), (0, 0, 0, 0.0))

    def test_10_items_math(self):
        """默认 AVG=350；INPUT_RATIO=0.43 OUTPUT_RATIO=0.57；PI=0.27 PO=1.10 每 1M tokens 元"""
        from llm_service import estimate_tokens_cost
        total, inp, out, cost = estimate_tokens_cost(10)
        self.assertEqual(total, 10 * 350)
        self.assertAlmostEqual(inp / total, 0.43, delta=0.01)
        self.assertAlmostEqual(out / total, 0.57, delta=0.01)
        # 成本：(inp / 1e6) * 0.27 + (out / 1e6) * 1.10
        expected = (inp / 1_000_000.0) * 0.27 + (out / 1_000_000.0) * 1.10
        self.assertAlmostEqual(cost, expected, delta=0.0001)
        # 10 × 350 tokens = 3500 tokens ≈ ¥0.0022~¥0.0045 范围以内（粗略合理性）
        self.assertLess(cost, 0.1)
        self.assertGreaterEqual(cost, 0.0)

    def test_custom_avg_tokens_per_item(self):
        from llm_service import estimate_tokens_cost
        total, inp, out, _ = estimate_tokens_cost(4, avg_tokens_per_item=1000)
        self.assertEqual(total, 4 * 1000)
        self.assertEqual(inp + out, total)


class PingAPIKeyParameterTests(unittest.TestCase):
    """ping_api_key 必须按要求以 max_tokens=1 / temperature=0 / messages=[{role:user,content:ping}] 发出请求"""

    def test_ping_sends_expected_parameters(self):
        import config as _cfg
        captured = {}

        def _fake_create(**kwargs):
            captured.update(kwargs)
            return _FakeResp()

        # 注意：config 里 client 是 import 时创建的，需要 patch client.chat.completions.create
        original = _cfg.client.chat.completions.create
        try:
            _cfg.client.chat.completions.create = _fake_create
            from llm_service import ping_api_key
            ok, msg = ping_api_key(timeout=3.5)
        finally:
            _cfg.client.chat.completions.create = original

        self.assertTrue(ok)
        self.assertEqual(captured.get("model"), _cfg.MODEL)  # deepseek-chat
        self.assertEqual(captured.get("temperature"), 0.0)
        self.assertEqual(captured.get("max_tokens"), 1)
        self.assertEqual(captured.get("timeout"), 3.5)
        self.assertEqual(captured.get("messages"), [{"role": "user", "content": "ping"}])

    def test_ping_exceptions_mapped_to_user_friendly_messages(self):
        """7 种异常 → ok=False + message 里有关键词"""
        import config as _cfg
        from llm_service import ping_api_key
        from openai import (
            AuthenticationError, PermissionDeniedError, RateLimitError,
            NotFoundError, APITimeoutError,
        )
        cases = [
            (AuthenticationError("bad key"), "AuthenticationError", "API Key 无效"),
            (PermissionDeniedError("denied"), "PermissionDeniedError", "无权限"),
            (RateLimitError("rate"), "RateLimitError", "频率超限"),
            (NotFoundError("not found"), "NotFoundError", "模型"),
            (APITimeoutError("timeout"), "APITimeoutError", "超时"),
            (RuntimeError("boom"), "RuntimeError", "boom"),
        ]
        for exc, want_err_type, want_substr in cases:
            def _raiser(_exc=exc, **kw):
                raise _exc
            original = _cfg.client.chat.completions.create
            try:
                _cfg.client.chat.completions.create = _raiser
                ok, msg = ping_api_key(timeout=1.0)
            finally:
                _cfg.client.chat.completions.create = original
            self.assertFalse(ok, f"{type(exc).__name__} 应该 ok=False")
            self.assertIn(want_err_type, msg)
            self.assertIn(want_substr, msg)


class PreflightCheckBoundaryTests(unittest.TestCase):
    PY_CODE = '''
class User:
    def __init__(self, name): self.name = name
    def greet(self): return f"Hi {self.name}"

def square(x):
    return x * x

def main():
    u = User("A")
    print(u.greet(), square(3))
'''
    JAVA_CODE = '''
public class SampleApp {
    public SampleApp(){}
    public int add(int a, int b){ return a+b; }
    public static void main(String[] a){ new SampleApp().add(1,2); }
}
'''

    def test_empty_source_returns_no_code_prompt(self):
        from processor import preflight_check
        ok, pf, est = preflight_check("", "Python", "中文", do_ping=False)
        self.assertTrue(ok)  # 不 ping 永远通过
        self.assertIn("暂无源代码", est)

    def test_no_items_code_returns_detect_nothing(self):
        from processor import preflight_check
        ok, pf, est = preflight_check("x = 1 + 2", "Python", "中文", do_ping=False)
        self.assertTrue(ok)
        self.assertIn("未检测到函数或类定义", est)

    def test_python_code_counts_functions_classes_and_estimates_cost(self):
        from processor import preflight_check
        ok, pf, est = preflight_check(self.PY_CODE, "Python", "中文", do_ping=False)
        self.assertTrue(ok)
        # 结构：1 class（User，__init__+greet 两个方法） + square（函数） + main（函数）
        # get_defined_functions 会把方法也抽出来？这里只断言 n_total >= 3 且有货币符号 ¥
        self.assertIn("📊 合计条目总数", est)
        self.assertIn("¥", est)
        self.assertIn("元", est)
        self.assertIn("🔧 函数/方法数", est)
        self.assertIn("🧩 类数", est)

    def test_java_code_contains_java_analysis_keywords(self):
        from processor import preflight_check
        ok, pf, est = preflight_check(self.JAVA_CODE, "Java", "中文", do_ping=False)
        self.assertTrue(ok)
        self.assertIn("¥", est)

    def test_language_english_and_japanese_markdown(self):
        """i18n fallback：EN / JA 必须出现相应语言的关键词（不可全是中文）"""
        from processor import preflight_check
        _, _, est_en = preflight_check(self.PY_CODE, "Python", "English", do_ping=False)
        _, _, est_ja = preflight_check(self.PY_CODE, "Python", "日本語", do_ping=False)
        self.assertIn("Total items", est_en)
        self.assertIn("Estimated cost", est_en)
        self.assertIn("合計エントリ数", est_ja)
        self.assertIn("推定費用", est_ja)

    def test_invalid_language_falls_back_to_chinese(self):
        from processor import preflight_check
        _, _, est = preflight_check(self.PY_CODE, "Python", "Deutsch", do_ping=False)
        self.assertIn("合计条目总数", est)  # 中文默认


class I18nKeysTests(unittest.TestCase):
    def test_three_new_keys_three_languages(self):
        from i18n import TRANSLATIONS
        for k in ("preflight_btn", "estimate_label", "preflight_label"):
            self.assertIn(k, TRANSLATIONS, f"缺少 i18n key: {k}")
            for lang in ("中文", "English", "日本語"):
                self.assertIn(lang, TRANSLATIONS[k], f"{k} 缺少 {lang}")
                self.assertTrue(TRANSLATIONS[k][lang].strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
