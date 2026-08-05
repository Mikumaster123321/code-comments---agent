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
