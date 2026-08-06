# -*- coding: utf-8 -*-
"""测试注释语言切换功能：中文 / English / 日本語"""
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processor import process_code, analyze_code

SAMPLE_PY = '''def greet(name):
    return f"Hello, {name}!"


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_info(self):
        return f"{self.name} is {self.age} years old"
'''


def test_comment_languages():
    print("=" * 70)
    print("测试注释语言切换功能")
    print("=" * 70)

    for lang in ["中文", "English", "日本語"]:
        print(f"\n--- 语言: {lang} ---")
        result = process_code(SAMPLE_PY, incremental=False, language="Python", comment_language=lang)
        annotated_code, markdown_doc, log_text, md_path, py_path = result

        # 检查是否成功生成
        if "日志：无处理对象" in log_text or "代码无效" in log_text:
            print(f"❌ {lang} 处理失败: {log_text}")
            continue

        print(f"✓ 处理成功")
        print(f"  日志摘要: {log_text[:120]}...")
        print(f"  注释代码前 15 行:")
        for i, line in enumerate(annotated_code.split('\n')[:15], 1):
            print(f"    {i:2d}| {line}")

        # 测试 analyze_code 也支持
        analyze_result = analyze_code(SAMPLE_PY, language="Python", comment_language=lang)
        quality, annotation, summary, alog = analyze_result
        print(f"  分析摘要前 80 字: {summary[:80]}...")
        print()

    print("=" * 70)
    print("✅ 所有语言测试完成")
    print("=" * 70)


if __name__ == "__main__":
    test_comment_languages()
