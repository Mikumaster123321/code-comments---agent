# -*- coding: utf-8 -*-
"""v2.4.0 专项测试：多 Provider / 多模型切换（config + llm_service）
覆盖范围：PROVIDERS 字典完整性 / switch_provider / set_api_key /
         set_custom_base_url / __getattr__ 兼容旧代码 / llm_service 动态获取等
"""
import sys
import os
import unittest
import importlib

# 确保能导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestProvidersDict(unittest.TestCase):
    """PROVIDERS 字典完整性测试"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg

    def test_001_providers_has_all_6_keys(self):
        """必须包含 6 个 Provider：deepseek/openai/azure/dashscope/moonshot/custom"""
        expected = {"deepseek", "openai", "azure", "dashscope", "moonshot", "custom"}
        self.assertEqual(set(self.cfg.PROVIDERS.keys()), expected)

    def test_002_each_provider_has_required_fields(self):
        """每个 Provider 必须包含 label_zh/label_en/label_ja/api_key_env/
           base_url/models/price_input_per_m/price_output_per_m/customizable_base_url
        """
        required = {
            "label_zh", "label_en", "label_ja", "api_key_env",
            "base_url", "models",
            "price_input_per_m", "price_output_per_m",
            "customizable_base_url",
        }
        for key, p in self.cfg.PROVIDERS.items():
            missing = required - set(p.keys())
            self.assertFalse(missing, f"Provider {key} 缺少字段: {missing}")

    def test_003_price_is_non_negative(self):
        """输入/输出单价必须 >= 0"""
        for key, p in self.cfg.PROVIDERS.items():
            self.assertGreaterEqual(p["price_input_per_m"], 0, f"{key} input price < 0")
            self.assertGreaterEqual(p["price_output_per_m"], 0, f"{key} output price < 0")

    def test_004_models_not_empty(self):
        """每个 Provider 的 models 不能为空"""
        for key, p in self.cfg.PROVIDERS.items():
            self.assertTrue(len(p["models"]) >= 1, f"Provider {key} 模型列表为空")

    def test_005_azure_and_custom_are_customizable(self):
        """只有 azure 和 custom 允许自定义 base_url"""
        for key, p in self.cfg.PROVIDERS.items():
            if key in ("azure", "custom"):
                self.assertTrue(p["customizable_base_url"], f"{key} 应为 customizable")
            else:
                self.assertFalse(p["customizable_base_url"], f"{key} 不应为 customizable")

    def test_006_api_key_env_is_list(self):
        """api_key_env 必须是非空 list"""
        for key, p in self.cfg.PROVIDERS.items():
            self.assertIsInstance(p["api_key_env"], list, f"{key} api_key_env 不是 list")
            self.assertGreaterEqual(len(p["api_key_env"]), 1, f"{key} api_key_env 为空")


class TestProviderLabelLocalization(unittest.TestCase):
    """Provider 标签三语本地化"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg

    def test_010_provider_label_zh(self):
        lbl = self.cfg._provider_label("deepseek", "中文")
        self.assertEqual(lbl, "DeepSeek")

    def test_011_provider_label_en(self):
        lbl = self.cfg._provider_label("openai", "English")
        self.assertEqual(lbl, "OpenAI Official")

    def test_012_provider_label_ja(self):
        lbl = self.cfg._provider_label("dashscope", "日本語")
        self.assertEqual(lbl, "阿里百錬（Qwen）")

    def test_013_provider_label_unknown_fallback(self):
        """未知 Provider 回退 key 本身"""
        lbl = self.cfg._provider_label("nonexistent", "中文")
        self.assertEqual(lbl, "nonexistent")


class TestPublicGetters(unittest.TestCase):
    """公开 getter 函数：get_providers / get_models_for_provider /
       get_active_provider / get_active_model / get_active_base_url /
       is_active_provider_customizable / get_price_input_per_m / get_price_output_per_m
    """

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg
        # 先确保回到 deepseek，避免被其他测试改动
        cls.cfg.switch_provider("deepseek")

    def setUp(self):
        # 每个测试回到 deepseek 默认
        self.cfg.switch_provider("deepseek")

    def test_020_get_providers_returns_list_of_tuples(self):
        items = self.cfg.get_providers("中文")
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 6)
        for label, key in items:
            self.assertIsInstance(label, str)
            self.assertIsInstance(key, str)
            self.assertIn(key, self.cfg.PROVIDERS)

    def test_021_get_providers_en_has_english_labels(self):
        items = self.cfg.get_providers("English")
        openai_label = [lbl for lbl, k in items if k == "openai"][0]
        self.assertIn("OpenAI Official", openai_label)

    def test_022_get_models_for_deepseek(self):
        models = self.cfg.get_models_for_provider("deepseek")
        keys = [k for _, k in models]
        self.assertIn("deepseek-chat", keys)
        self.assertIn("deepseek-reasoner", keys)

    def test_023_get_models_for_openai(self):
        models = self.cfg.get_models_for_provider("openai")
        keys = [k for _, k in models]
        self.assertIn("gpt-4o-mini", keys)
        self.assertIn("gpt-4o", keys)

    def test_024_get_models_for_unknown_returns_empty(self):
        models = self.cfg.get_models_for_provider("nonexistent")
        self.assertEqual(models, [])

    def test_025_get_active_provider_default_is_deepseek(self):
        self.assertEqual(self.cfg.get_active_provider(), "deepseek")

    def test_026_get_active_model_default_is_deepseek_chat(self):
        # 允许 .env 覆盖，但至少属于 deepseek 模型列表
        active = self.cfg.get_active_model()
        self.assertIn(active, list(self.cfg.PROVIDERS["deepseek"]["models"].keys()))

    def test_027_get_active_base_url_default(self):
        self.assertEqual(self.cfg.get_active_base_url(), "https://api.deepseek.com")

    def test_028_is_active_provider_customizable_default_false(self):
        self.assertFalse(self.cfg.is_active_provider_customizable())

    def test_029_get_price_per_m_deepseek_values(self):
        self.assertAlmostEqual(self.cfg.get_price_input_per_m(), 0.27)
        self.assertAlmostEqual(self.cfg.get_price_output_per_m(), 1.10)


class TestSwitchProvider(unittest.TestCase):
    """switch_provider 各种场景"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg

    def setUp(self):
        self.cfg.switch_provider("deepseek")

    def test_030_switch_to_openai_success(self):
        ok, msg = self.cfg.switch_provider("openai")
        self.assertTrue(ok, msg)
        self.assertIn("✅", msg)
        self.assertEqual(self.cfg.get_active_provider(), "openai")
        # 跨 Provider 切换：model 自动取第一个默认
        self.assertEqual(
            self.cfg.get_active_model(),
            list(self.cfg.PROVIDERS["openai"]["models"].keys())[0],
        )

    def test_031_switch_with_explicit_model(self):
        ok, _ = self.cfg.switch_provider("openai", model_key="gpt-4o")
        self.assertTrue(ok)
        self.assertEqual(self.cfg.get_active_model(), "gpt-4o")

    def test_032_switch_unknown_provider_fails(self):
        ok, msg = self.cfg.switch_provider("unknown-xxx")
        self.assertFalse(ok)
        self.assertIn("❌", msg)
        self.assertIn("未知 Provider", msg)
        # 失败不影响当前状态
        self.assertEqual(self.cfg.get_active_provider(), "deepseek")

    def test_033_switch_to_azure_updates_base_url_default(self):
        ok, _ = self.cfg.switch_provider("azure")
        self.assertTrue(ok)
        self.assertTrue(self.cfg.is_active_provider_customizable())
        # Azure 默认为占位模板字符串
        self.assertIn("YOUR-RESOURCE", self.cfg.get_active_base_url())

    def test_034_switch_to_custom_with_custom_model(self):
        ok, msg = self.cfg.switch_provider(
            "custom",
            custom_model_name="my-local-model-v2",
            base_url="http://localhost:1234/v1",
        )
        self.assertTrue(ok, msg)
        self.assertEqual(self.cfg.get_active_model(), "my-local-model-v2")
        self.assertEqual(self.cfg.get_active_base_url(), "http://localhost:1234/v1")

    def test_035_switch_with_api_key_empty_string_resets_env(self):
        # 先手动设一个假 key
        ok1, _ = self.cfg.set_api_key("sk-fake-123")
        self.assertTrue(ok1)
        # api_key='' 重置为环境变量
        ok2, _ = self.cfg.switch_provider("deepseek", api_key="")
        self.assertTrue(ok2)

    def test_036_switch_non_customizable_provider_base_url_ignored(self):
        """deepseek 不可自定义 base_url，传参数也会被忽略"""
        ok, _ = self.cfg.switch_provider(
            "deepseek", base_url="http://should-be-ignored.com"
        )
        self.assertTrue(ok)
        self.assertEqual(self.cfg.get_active_base_url(), "https://api.deepseek.com")

    def test_037_switch_to_moonshot_price_matches(self):
        self.cfg.switch_provider("moonshot")
        self.assertAlmostEqual(self.cfg.get_price_input_per_m(), 0.12)
        self.assertAlmostEqual(self.cfg.get_price_output_per_m(), 0.12)

    def test_038_switch_to_dashscope_price_matches(self):
        self.cfg.switch_provider("dashscope")
        self.assertAlmostEqual(self.cfg.get_price_input_per_m(), 0.12)
        self.assertAlmostEqual(self.cfg.get_price_output_per_m(), 0.24)


class TestSetApiKeyAndBaseUrl(unittest.TestCase):
    """set_api_key / set_custom_base_url 独立接口"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg

    def setUp(self):
        self.cfg.switch_provider("deepseek")

    def test_040_set_api_key_valid_string(self):
        ok, msg = self.cfg.set_api_key("sk-new-key-12345")
        self.assertTrue(ok)
        self.assertIn("✅", msg)

    def test_041_set_api_key_empty_resets(self):
        ok, _ = self.cfg.set_api_key("sk-temp")
        self.assertTrue(ok)
        ok, msg = self.cfg.set_api_key("")
        self.assertTrue(ok)
        self.assertIn("重置为环境变量", msg)

    def test_042_set_custom_base_url_non_customizable_fails(self):
        """deepseek 不可自定义 base_url，直接拒绝"""
        ok, msg = self.cfg.set_custom_base_url("http://example.com")
        self.assertFalse(ok)
        self.assertIn("不允许自定义", msg)

    def test_043_set_custom_base_url_azure_allowed(self):
        self.cfg.switch_provider("azure")
        ok, msg = self.cfg.set_custom_base_url("https://my-res.openai.azure.com/openai/deployments/dep1")
        self.assertTrue(ok, msg)
        self.assertIn("my-res.openai.azure.com", self.cfg.get_active_base_url())

    def test_044_set_custom_base_url_none_uses_default(self):
        self.cfg.switch_provider("custom")
        self.cfg.set_custom_base_url("http://custom-url.com")
        self.assertEqual(self.cfg.get_active_base_url(), "http://custom-url.com")
        ok, _ = self.cfg.set_custom_base_url(None)
        self.assertTrue(ok)
        # None → 回退 PROVIDERS 默认
        self.assertEqual(
            self.cfg.get_active_base_url(),
            self.cfg.PROVIDERS["custom"]["base_url"],
        )

    def test_045_set_custom_base_url_trailing_slash_stripped(self):
        self.cfg.switch_provider("custom")
        ok, _ = self.cfg.set_custom_base_url("http://x.com/v1/")
        self.assertTrue(ok)
        self.assertEqual(self.cfg.get_active_base_url(), "http://x.com/v1")


class TestCompatGetAttr(unittest.TestCase):
    """模块级 __getattr__：兼容旧代码 from config import client / MODEL / PRICE_*"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg
        # 强制 reload 以触发 getattr 逻辑
        importlib.reload(cfg)
        cls.cfg = cfg

    def setUp(self):
        self.cfg.switch_provider("deepseek")

    def test_050_attr_client_returns_openai_instance(self):
        import openai
        c = self.cfg.client
        self.assertIsInstance(c, openai.OpenAI)

    def test_051_attr_MODEL_matches_getter(self):
        self.assertEqual(self.cfg.MODEL, self.cfg.get_active_model())

    def test_052_attr_MODEL_after_switch(self):
        self.cfg.switch_provider("openai", model_key="gpt-4o")
        self.assertEqual(self.cfg.MODEL, "gpt-4o")

    def test_053_attr_PRICE_INPUT_PER_M(self):
        self.assertAlmostEqual(self.cfg.PRICE_INPUT_PER_M, 0.27)

    def test_054_attr_PRICE_OUTPUT_PER_M(self):
        self.assertAlmostEqual(self.cfg.PRICE_OUTPUT_PER_M, 1.10)

    def test_055_attr_PRICE_after_switch_moonshot(self):
        self.cfg.switch_provider("moonshot")
        self.assertAlmostEqual(self.cfg.PRICE_INPUT_PER_M, 0.12)
        self.assertAlmostEqual(self.cfg.PRICE_OUTPUT_PER_M, 0.12)

    def test_056_unknown_attr_raises(self):
        with self.assertRaises(AttributeError):
            _ = self.cfg.NONEXISTENT_ATTR_XYZ


class TestLLMServiceDynamic(unittest.TestCase):
    """llm_service 通过 getter 动态获取 client/MODEL/PRICE_*"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        import llm_service as ls
        cls.cfg = cfg
        cls.ls = ls

    def setUp(self):
        self.cfg.switch_provider("deepseek")

    def test_060_estimate_cost_uses_deepseek_prices(self):
        """num_items=1000 → 足够大，成本 > 0；切换 Provider 后成本应改变"""
        t1, i1, o1, c1 = self.ls.estimate_tokens_cost(1000)
        self.assertGreater(t1, 0)
        # 切到 Moonshot（单价便宜），相同 items 下成本更低
        self.cfg.switch_provider("moonshot")
        t2, i2, o2, c2 = self.ls.estimate_tokens_cost(1000)
        # token 总量不变
        self.assertEqual(t1, t2)
        self.assertEqual(i1, i2)
        self.assertEqual(o1, o2)
        # Moonshot 成本 < DeepSeek
        self.assertLess(c2, c1)

    def test_061_estimate_cost_zero_items(self):
        t, i, o, c = self.ls.estimate_tokens_cost(0)
        self.assertEqual((t, i, o, c), (0, 0, 0, 0.0))

    def test_062_estimate_cost_negative_items(self):
        t, i, o, c = self.ls.estimate_tokens_cost(-10)
        self.assertEqual((t, i, o, c), (0, 0, 0, 0.0))

    def test_063_custom_provider_zero_price(self):
        self.cfg.switch_provider("custom")
        _, _, _, c = self.ls.estimate_tokens_cost(10000)
        self.assertEqual(c, 0.0)

    def test_064_estimate_with_custom_avg(self):
        t, _, _, _ = self.ls.estimate_tokens_cost(10, avg_tokens_per_item=100)
        self.assertEqual(t, 1000)


class TestCustomProviderModels(unittest.TestCase):
    """Custom Provider 下的自定义模型名处理"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg

    def setUp(self):
        self.cfg.switch_provider("deepseek")

    def test_070_models_for_custom_without_name_no_prefix_item(self):
        models = self.cfg.get_models_for_provider("custom")
        # 首项不是自定义的 ✏️ 项目
        self.assertNotIn("✏️", models[0][0])

    def test_071_models_for_custom_after_switch_has_prefix(self):
        self.cfg.switch_provider("custom", custom_model_name="my-model")
        models = self.cfg.get_models_for_provider("custom")
        self.assertIn("✏️", models[0][0])
        self.assertIn("my-model", models[0][1])


class TestProviderMeta(unittest.TestCase):
    """额外的元数据和边界检查"""

    @classmethod
    def setUpClass(cls):
        import config as cfg
        cls.cfg = cfg

    def test_080_get_active_client_is_reusable(self):
        """两次调用返回同一实例（缓存）"""
        c1 = self.cfg.get_active_client()
        c2 = self.cfg.get_active_client()
        self.assertIs(c1, c2)

    def test_081_threading_lock_exists(self):
        import threading
        self.assertIsInstance(self.cfg._lock, type(threading.RLock()))

    def test_082_get_active_client_after_switch_is_new(self):
        """切换后 client 被重建（不是同一个实例）"""
        c1 = self.cfg.get_active_client()
        self.cfg.switch_provider("openai")
        c2 = self.cfg.get_active_client()
        self.assertIsNot(c1, c2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
