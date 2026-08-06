# -*- coding: utf-8 -*-
"""代码注释与文档生成 Agent — 入口文件

启动 Gradio Web 界面。
架构拆分：
  main.py           — 入口文件（本文件）
  ui.py             — Gradio 界面构建
  processor.py      — 主处理逻辑（多语言调度、并发生成 + 串行插入）
  llm_service.py    — LLM 调用（docstring/Javadoc 生成、代码摘要，含重试）
  config.py         — 配置（API Key、模型参数）
  Py/               — Python 专用模块
    parser.py         — AST 解析（提取函数/类定义）
    annotator.py      — 注释插入与 Markdown 文档生成
    analyzer.py       — 代码质量分析与类型注解检查
  Java/             — Java 专用模块
    java_parser.py    — 正则解析（提取类/方法定义）
    java_annotator.py — Javadoc 插入与 Markdown 文档生成
  Test/             — 测试用例
    test_java_parser.py       — Java 解析器单元测试
    test_java_integration.py  — Java 集成测试（调用 LLM）
    test_complex_java.py      — 复杂嵌套端到端测试
    ComplexExample.java       — Java 测试样例文件
"""
from ui import create_ui, CUSTOM_CSS

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(css=CUSTOM_CSS)
