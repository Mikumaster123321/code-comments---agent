# -*- coding: utf-8 -*-
"""程序正常使用验证：模拟 UI 完整流程（不启动 Web 服务器）"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
sys.stdout = open(os.path.join(_ROOT, '_verify_result.txt'), 'w', encoding='utf-8')

from processor import process_code, analyze_code, handle_file_upload
from ui import create_ui, CUSTOM_CSS


# ==================== 测试数据 ====================

JAVA_CODE = """package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    public int multiply(int a, int b) {
        return a * b;
    }
}
"""

PYTHON_CODE = """def greet(name):
    return f"Hello, {name}!"

class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_info(self):
        return f"{self.name} is {self.age} years old"
"""


# ==================== 验证步骤 ====================

def verify_ui_creation():
    """验证 1: UI 创建"""
    print("=" * 60)
    print("验证 1: Gradio 界面创建")
    print("=" * 60)
    demo = create_ui()
    assert demo is not None, "UI 创建失败"
    assert CUSTOM_CSS, "CUSTOM_CSS 不应为空"
    print("  [OK] Gradio 界面创建成功")
    print(f"  [OK] CSS 长度: {len(CUSTOM_CSS)} 字符")
    print()


def verify_java_process():
    """验证 2: Java 代码注释流程"""
    print("=" * 60)
    print("验证 2: Java 代码注释生成（调用 LLM）")
    print("=" * 60)
    annotated, markdown, log, md_path, java_path = process_code(
        JAVA_CODE, incremental=False, language="Java"
    )
    print("  --- 处理日志 ---")
    for line in log.split('\n'):
        print(f"    {line}")

    assert "/**" in annotated, "Java 代码应包含 Javadoc"
    assert "*/" in annotated, "Java 代码应包含 Javadoc 结尾"
    assert md_path and md_path.endswith(".md"), "应有 .md 下载文件"
    assert java_path and java_path.endswith(".java"), "应有 .java 下载文件"
    print(f"\n  [OK] Javadoc 已生成 ({annotated.count('/**')} 个)")
    print(f"  [OK] Markdown 下载: {os.path.basename(md_path)}")
    print(f"  [OK] Java 下载: {os.path.basename(java_path)}")

    # 验证下载文件内容
    with open(java_path, 'r', encoding='utf-8') as f:
        java_content = f.read()
    assert "Calculator" in java_content, "下载的 Java 文件应包含 Calculator"
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    assert "# Java API" in md_content, "Markdown 应包含 Java API 标题"
    print("  [OK] 下载文件内容验证通过")
    print()


def verify_python_process():
    """验证 3: Python 代码注释流程"""
    print("=" * 60)
    print("验证 3: Python 代码注释生成（调用 LLM）")
    print("=" * 60)
    annotated, markdown, log, md_path, py_path = process_code(
        PYTHON_CODE, incremental=False, language="Python"
    )
    print("  --- 处理日志 ---")
    for line in log.split('\n'):
        print(f"    {line}")

    assert '"""' in annotated, "Python 代码应包含 docstring"
    assert md_path and md_path.endswith(".md"), "应有 .md 下载文件"
    assert py_path and py_path.endswith(".py"), "应有 .py 下载文件"
    print(f"\n  [OK] docstring 已生成 ({annotated.count(chr(34)*3)//2} 个)")
    print(f"  [OK] Markdown 下载: {os.path.basename(md_path)}")
    print(f"  [OK] Python 下载: {os.path.basename(py_path)}")

    # 验证编码声明
    assert annotated.startswith('# -*- coding: utf-8 -*-'), "Python 应有编码声明"
    print("  [OK] 编码声明存在")
    print()


def verify_java_analyze():
    """验证 4: Java 代码分析"""
    print("=" * 60)
    print("验证 4: Java 代码分析")
    print("=" * 60)
    quality, annotation, summary, log = analyze_code(JAVA_CODE, language="Java")
    assert "大括号" in quality, "质量分析应包含大括号校验"
    assert "静态类型" in annotation, "应说明 Java 是静态类型"
    assert summary, "摘要不应为空"
    print(f"  [OK] 质量分析: {quality[:50]}...")
    print(f"  [OK] 类型注解: {annotation[:50]}...")
    print(f"  [OK] 摘要长度: {len(summary)} 字符")
    print()


def verify_python_analyze():
    """验证 5: Python 代码分析"""
    print("=" * 60)
    print("验证 5: Python 代码分析")
    print("=" * 60)
    quality, annotation, summary, log = analyze_code(PYTHON_CODE, language="Python")
    assert quality, "质量分析不应为空"
    assert annotation, "类型注解检查不应为空"
    assert summary, "摘要不应为空"
    print(f"  [OK] 质量分析: {quality[:50]}...")
    print(f"  [OK] 类型注解: {annotation[:50]}...")
    print(f"  [OK] 摘要长度: {len(summary)} 字符")
    print()


def verify_file_upload():
    """验证 6: 文件上传功能"""
    print("=" * 60)
    print("验证 6: 文件上传（handle_file_upload）")
    print("=" * 60)

    class FakeUpload:
        def __init__(self, path):
            self.name = path

    java_file = os.path.join(_ROOT, "Test", "ComplexExample.java")
    content = handle_file_upload(FakeUpload(java_file))
    assert content, "上传内容不应为空"
    assert "public class Library" in content, "应包含 Library 类"
    print(f"  [OK] 上传 ComplexExample.java 成功 ({len(content)} 字符)")
    print()


def verify_incremental_mode():
    """验证 7: 增量更新模式"""
    print("=" * 60)
    print("验证 7: 增量更新模式（跳过已有注释）")
    print("=" * 60)
    # JAVA_CODE 无 Javadoc，增量模式应处理所有方法
    annotated, markdown, log, _, _ = process_code(
        JAVA_CODE, incremental=True, language="Java"
    )
    assert "/**" in annotated, "增量模式也应生成 Javadoc"
    # 再次处理，此时已有 Javadoc，应跳过
    annotated2, _, log2, _, _ = process_code(
        annotated, incremental=True, language="Java"
    )
    assert "跳过" in log2 or "无需调用" in log2, "增量模式应跳过已有注释"
    print(f"  [OK] 增量模式第一次: 生成 Javadoc")
    print(f"  [OK] 增量模式第二次: 跳过已有注释")
    print()


if __name__ == "__main__":
    verify_ui_creation()
    verify_file_upload()
    verify_java_process()
    verify_python_process()
    verify_java_analyze()
    verify_python_analyze()
    verify_incremental_mode()

    print("=" * 60)
    print("ALL VERIFICATIONS PASSED")
    print("=" * 60)
