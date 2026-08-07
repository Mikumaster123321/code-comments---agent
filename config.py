# -*- coding: utf-8 -*-
"""配置模块：集中管理 API Key、模型参数等配置"""
import os
import openai
from dotenv import load_dotenv

# 从 .env 文件或环境变量中读取 API Key，避免硬编码泄露
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise EnvironmentError(
        "未检测到 DEEPSEEK_API_KEY 环境变量。"
        "请复制 .env.example 为 .env 并填入你的 DeepSeek API Key。"
    )

# OpenAI 兼容客户端（DeepSeek）
client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# 模型参数
MODEL = "deepseek-chat"
TEMPERATURE = 0.2
MAX_TOKENS = 1024

# LLM 调用重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# 并发配置
MAX_WORKERS = 5

# Token 成本估算配置（DeepSeek 官方价格，2026 年参考值；单位：人民币 / 每 1M tokens）
# 来源：deepseek.com/price 参考价
PRICE_INPUT_PER_M = 0.27   # 输入单价：0.27 元 / 1,000,000 input tokens
PRICE_OUTPUT_PER_M = 1.10  # 输出单价：1.10 元 / 1,000,000 output tokens
# 平均每个函数/方法注释消耗 tokens 估算（输入 + 输出合计）
# 实测经验值：prompt 约 150 tokens（含模板），产出 docstring 约 200 tokens → 合计 350 作为默认值
AVG_TOKENS_PER_ITEM = 350
# 输入占比 / 输出占比（用于更精准估算）
INPUT_RATIO = 0.43   # 150 / 350
OUTPUT_RATIO = 0.57  # 200 / 350

