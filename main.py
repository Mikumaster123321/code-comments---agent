# -*- coding: utf-8 -*-
"""LLM-assisted Software Maintenance Platform — Gradio 入口。

V3.0.0 RC1 保留 legacy-compatible Processor，并提供项目级维护核心：
  main.py           — 入口文件（本文件）
  ui.py             — Gradio 界面构建
  processor.py      — 主处理逻辑（多语言调度、并发生成 + 串行插入）
  llm_service.py    — LLM 调用（docstring/Javadoc 生成、代码摘要，含重试）
  config.py         — legacy Provider 配置与任务级 Provider 捕获
  llm_provider.py   — BYOK 模型配置、运行时凭据与 Provider Registry
  Py/               — Python 专用模块
    parser.py         — AST 解析（提取函数/类定义）
    annotator.py      — 注释插入与 Markdown 文档生成
    analyzer.py       — 代码质量分析与类型注解检查
  Java/             — Java 专用模块
    java_parser.py    — 正则解析（提取类/方法定义）
    java_annotator.py — Javadoc 插入与 Markdown 文档生成
  code_maintenance/ — Domain、Scanner、Graph、Snapshot、Analysis Engine
  tests/            — 离线自动化测试
"""
from ui import create_ui, CUSTOM_CSS

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(css=CUSTOM_CSS)
