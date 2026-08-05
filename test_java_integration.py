# -*- coding: utf-8 -*-
"""Java 完整流程集成测试（调用 LLM）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor import process_code, analyze_code
from java_annotator import _validate_braces


JAVA_CODE = """package com.example;

public class Calculator {

    public int add(int a, int b) {
        return a + b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }

    public int factorial(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }
}
"""


def test_full_process():
    """测试完整流程：解析 -> LLM 生成 Javadoc -> 插入"""
    print("=" * 60)
    print("Java 完整流程集成测试")
    print("=" * 60)

    annotated, markdown, log, md_path, java_path = process_code(
        JAVA_CODE, incremental=False, language="Java"
    )

    print("\n--- 处理日志 ---")
    print(log)

    print("\n--- 注释后的代码 ---")
    print(annotated)

    print("\n--- Markdown 文档 ---")
    print(markdown[:500] + "..." if len(markdown) > 500 else markdown)

    # 验证大括号匹配
    _validate_braces(annotated)
    print("\n--- 大括号校验通过 ---")

    # 验证 Javadoc 已插入
    assert "/**" in annotated, "应包含 Javadoc 开头"
    assert "*/" in annotated, "应包含 Javadoc 结尾"
    assert annotated.count("/**") >= 4, f"应至少 4 个 Javadoc，实际 {annotated.count('/**')}"

    # 验证下载文件
    assert md_path is not None, "md 文件路径不应为 None"
    assert java_path is not None, "java 文件路径不应为 None"
    assert java_path.endswith(".java"), f"文件应以 .java 结尾: {java_path}"

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    assert "Calculator" in md_content, "Markdown 应包含 Calculator"

    with open(java_path, 'r', encoding='utf-8') as f:
        java_content = f.read()
    assert "Calculator" in java_content, "Java 文件应包含 Calculator"

    print("\n--- 文件下载验证通过 ---")
    print(f"  Markdown: {md_path}")
    print(f"  Java:     {java_path}")

    print("\n" + "=" * 60)
    print("集成测试通过！")
    print("=" * 60)


def test_analyze():
    """测试 Java 代码分析"""
    print("\n" + "=" * 60)
    print("Java 代码分析测试")
    print("=" * 60)

    quality, annotation, summary, log = analyze_code(JAVA_CODE, language="Java")

    print("\n--- 质量分析 ---")
    print(quality)
    print("\n--- 类型注解 ---")
    print(annotation)
    print("\n--- 代码摘要 ---")
    print(summary)
    print("\n--- 分析日志 ---")
    print(log)

    assert "大括号" in quality, "质量分析应包含大括号校验"
    assert "静态类型" in annotation, "类型注解报告应说明 Java 是静态类型"

    print("\n" + "=" * 60)
    print("分析测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_full_process()
    test_analyze()
