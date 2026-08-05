# -*- coding: utf-8 -*-
"""复杂嵌套 Java 代码端到端测试：上传 → 解析 → 注释 → 下载 → 语法验证"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 重定向输出到文件（避免终端 GBK 编码问题）
_RESULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_result.txt')
sys.stdout = open(_RESULT_FILE, 'w', encoding='utf-8')

from java_parser import get_defined_functions
from java_annotator import _validate_braces
from processor import process_code, handle_file_upload


JAVA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ComplexExample.java")


def step1_upload():
    """步骤 1：模拟文件上传"""
    print("=" * 70)
    print("步骤 1: 模拟文件上传（handle_file_upload）")
    print("=" * 70)

    class FakeUpload:
        """模拟 Gradio 文件对象"""
        def __init__(self, path):
            self.name = path

    source = handle_file_upload(FakeUpload(JAVA_FILE))
    assert source, "上传后内容不应为空"
    assert "public class Library" in source, "应包含 Library 类"
    print(f"  文件大小: {len(source)} 字符, {source.count(chr(10))} 行")
    print("  [OK] 文件上传成功\n")
    return source


def step2_parse(source):
    """步骤 2：解析器提取节点"""
    print("=" * 70)
    print("步骤 2: 解析器提取类/方法节点")
    print("=" * 70)

    items = get_defined_functions(source)
    print(f"  提取到 {len(items)} 个节点:")
    for item in items:
        print(f"    - {item['type']:7s} {item['name']:20s} 行 {item['lineno']:3d}-{item['end_lineno']:3d}  "
              f"has_javadoc={item['has_docstring']}")

    # 验证关键节点都被提取到
    names = [i["name"] for i in items]
    expected = ["Library", "BookStatus", "Book", "Member", "addBook",
                "registerMember", "findBookByTitle", "filterBooks",
                "runMaintenanceTask", "getAvailableBooks", "toString"]
    for name in expected:
        assert name in names, f"未提取到节点: {name}"

    # 验证已有 Javadoc 的节点
    with_doc = [i["name"] for i in items if i["has_docstring"]]
    assert "Library" in with_doc, "Library 应有 Javadoc"
    assert "BookStatus" in with_doc, "BookStatus 应有 Javadoc"
    assert "addBook" in with_doc, "addBook 应有 Javadoc"
    print(f"\n  已有 Javadoc 的节点: {with_doc}")

    # 验证匿名类未被误识别为方法
    assert "Runnable" not in names, "匿名类 Runnable 不应被识别为方法"
    # run 方法在匿名类内部，会被识别为方法（这是合理的，它确实是方法声明）
    run_items = [i for i in items if i["name"] == "run"]
    assert len(run_items) == 1, f"run 方法应被识别 1 次，实际 {len(run_items)} 次"
    print(f"\n  已有 Javadoc 的节点: {with_doc}")

    print("  [OK] 解析器验证通过\n")
    return items


def step3_annotate(source):
    """步骤 3：生成 Javadoc 注释"""
    print("=" * 70)
    print("步骤 3: 调用 process_code 生成 Javadoc（调用 LLM）")
    print("=" * 70)

    annotated, markdown, log, md_path, java_path = process_code(
        source, incremental=False, language="Java"
    )

    print("  --- 处理日志 ---")
    for line in log.split('\n'):
        print(f"    {line}")

    assert annotated, "注释后代码不应为空"
    assert markdown, "Markdown 文档不应为空"
    assert md_path and md_path.endswith(".md"), f"md 文件路径错误: {md_path}"
    assert java_path and java_path.endswith(".java"), f"java 文件路径错误: {java_path}"

    print(f"\n  [OK] 注释生成完成")
    print(f"  [OK] Markdown 文件: {md_path}")
    print(f"  [OK] Java 文件: {java_path}\n")
    return annotated, markdown, md_path, java_path


def step4_download_verify(md_path, java_path):
    """步骤 4：验证下载文件"""
    print("=" * 70)
    print("步骤 4: 验证下载文件内容")
    print("=" * 70)

    # 读取下载的 Java 文件
    with open(java_path, 'r', encoding='utf-8') as f:
        java_content = f.read()
    assert "public class Library" in java_content, "下载的 Java 文件应包含 Library"
    assert "/**" in java_content, "下载的 Java 文件应包含 Javadoc"
    print(f"  Java 文件大小: {len(java_content)} 字符")
    print(f"  Javadoc 数量: {java_content.count('/**')}")

    # 读取下载的 Markdown 文件
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    assert "# Java API 文档" in md_content, "Markdown 应包含标题"
    assert "```java" in md_content, "Markdown 应包含 java 代码块"
    print(f"  Markdown 文件大小: {len(md_content)} 字符")

    print("  [OK] 下载文件验证通过\n")
    return java_content


def step5_syntax_check(java_content):
    """步骤 5：语法验证（大括号匹配）"""
    print("=" * 70)
    print("步骤 5: 语法验证（大括号匹配检查）")
    print("=" * 70)

    try:
        _validate_braces(java_content)
        print("  [OK] 大括号匹配校验通过")
    except SyntaxError as e:
        print(f"  [FAIL] 大括号校验失败: {e}")
        raise

    # 重新解析注释后的代码，验证结构完整
    new_items = get_defined_functions(java_content)
    print(f"  重新解析注释后代码: {len(new_items)} 个节点")

    # 所有的类和方法现在都应该有 Javadoc
    no_doc = [i["name"] for i in new_items if not i["has_docstring"]]
    if no_doc:
        print(f"  [WARN] 以下节点无 Javadoc: {no_doc}")
    else:
        print(f"  [OK] 所有 {len(new_items)} 个节点均有 Javadoc")

    # 验证原始方法数量保持一致（注释不应破坏代码结构）
    original_items = get_defined_functions(open(JAVA_FILE, 'r', encoding='utf-8').read())
    assert len(new_items) == len(original_items), \
        f"节点数量变化: 原始 {len(original_items)} → 注释后 {len(new_items)}"
    print(f"  [OK] 节点数量一致（{len(original_items)} 个）")

    # 验证代码结构未被破坏：类名、方法名一致
    orig_names = sorted([(i["type"], i["name"]) for i in original_items])
    new_names = sorted([(i["type"], i["name"]) for i in new_items])
    assert orig_names == new_names, f"节点不一致:\n原始: {orig_names}\n注释后: {new_names}"
    print(f"  [OK] 所有类名/方法名一致\n")
    return new_items


def step6_show_result(java_content):
    """步骤 6：展示注释后的代码"""
    print("=" * 70)
    print("步骤 6: 注释后的 Java 代码")
    print("=" * 70)
    print(java_content)


if __name__ == "__main__":
    source = step1_upload()
    items = step2_parse(source)
    annotated, markdown, md_path, java_path = step3_annotate(source)
    java_content = step4_download_verify(md_path, java_path)
    new_items = step5_syntax_check(java_content)
    step6_show_result(java_content)

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
