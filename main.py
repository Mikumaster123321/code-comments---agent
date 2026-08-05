# -*- coding: utf-8 -*-
"""代码注释与文档生成 Agent — 入口文件

启动 Gradio Web 界面。
架构拆分：
  config.py      — 配置（API Key、模型参数）
  parser.py      — AST 解析（提取函数/类定义）
  llm_service.py — LLM 调用（docstring 生成、代码摘要，含重试）
  annotator.py   — 注释插入与 Markdown 文档生成
  analyzer.py    — 代码质量分析与类型注解检查
  processor.py   — 主处理逻辑（并发生成 + 串行插入）
  ui.py          — Gradio 界面构建
  main.py        — 入口文件（本文件）
"""
from ui import create_ui, CUSTOM_CSS

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(css=CUSTOM_CSS)
