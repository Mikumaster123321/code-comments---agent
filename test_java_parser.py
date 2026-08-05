# -*- coding: utf-8 -*-
"""Java 解析器和注释器的单元测试（不依赖 LLM）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from java_parser import get_defined_functions
from java_annotator import (
    insert_javadoc_into_code, _format_javadoc, _validate_braces,
    extract_existing_javadoc, build_java_markdown_docs,
)


JAVA_SAMPLE = """package com.example;

import java.util.List;
import java.util.ArrayList;

/**
 * 用户管理服务类
 * 负责用户的增删改查
 */
public class UserService {
    private List<String> users = new ArrayList<>();

    public UserService() {
        this.users = new ArrayList<>();
    }

    /**
     * 添加新用户
     * @param name 用户名
     */
    public void addUser(String name) {
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("用户名不能为空");
        }
        users.add(name);
    }

    @Override
    public String toString() {
        return "UserService{users=" + users.size() + "}";
    }

    public List<String> getUsers() {
        return users;
    }

    private int binarySearch(int[] arr, int target) {
        int left = 0;
        int right = arr.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) {
                return mid;
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return -1;
    }
}
"""


def test_parser():
    """测试 Java 解析器"""
    print("=" * 60)
    print("测试 1: Java 解析器")
    print("=" * 60)
    items = get_defined_functions(JAVA_SAMPLE)

    assert len(items) >= 5, f"期望至少 5 个节点，实际 {len(items)}"
    print(f"✓ 提取到 {len(items)} 个节点:")

    for item in items:
        print(f"  - {item['type']:7s} {item['name']:20s} 行 {item['lineno']}-{item['end_lineno']}  has_javadoc={item['has_docstring']}")

    # 验证类
    class_item = next(i for i in items if i["type"] == "class")
    assert class_item["name"] == "UserService", f"类名应为 UserService，实际 {class_item['name']}"
    assert class_item["has_docstring"] is True, "UserService 应有 Javadoc"
    print("✓ 类 UserService 检测正确（含已有 Javadoc）")

    # 验证构造器
    ctor = next(i for i in items if i["name"] == "UserService" and i["type"] == "method")
    assert ctor["lineno"] > class_item["lineno"], "构造器应在类之后"
    print("✓ 构造器 UserService() 检测正确")

    # 验证已有 Javadoc 的方法
    add_user = next(i for i in items if i["name"] == "addUser")
    assert add_user["has_docstring"] is True, "addUser 应有 Javadoc"
    assert add_user["existing_javadoc"] is not None, "addUser 的 existing_javadoc 应非 None"
    print("✓ addUser 检测正确（含已有 Javadoc）")

    # 验证无 Javadoc 的方法
    to_string = next(i for i in items if i["name"] == "toString")
    assert to_string["has_docstring"] is False, "toString 不应有 Javadoc"
    print("✓ toString 检测正确（无 Javadoc，有 @Override 注解）")

    binary = next(i for i in items if i["name"] == "binarySearch")
    assert binary["has_docstring"] is False, "binarySearch 不应有 Javadoc"
    print("✓ binarySearch 检测正确（无 Javadoc）")

    # 验证注解不会被误认为方法
    override_items = [i for i in items if i["name"] == "Override"]
    assert len(override_items) == 0, "@Override 不应被识别为方法"
    print("✓ @Override 注解未被误识别为方法")

    print()
    return items


def test_javadoc_format():
    """测试 Javadoc 格式化"""
    print("=" * 60)
    print("测试 2: Javadoc 格式化")
    print("=" * 60)

    doc = "计算两个数的和\n@param a 第一个数\n@param b 第二个数\n@return 两数之和"
    formatted = _format_javadoc(doc, "    ")
    expected_lines = [
        "    /**",
        "     * 计算两个数的和",
        "     * @param a 第一个数",
        "     * @param b 第二个数",
        "     * @return 两数之和",
        "     */",
    ]
    actual_lines = formatted.split('\n')
    assert actual_lines == expected_lines, f"格式化结果不符:\n期望: {expected_lines}\n实际: {actual_lines}"
    print("✓ Javadoc 格式化正确:")
    for line in formatted.split('\n'):
        print(f"  {line}")
    print()


def test_insert_javadoc():
    """测试 Javadoc 插入"""
    print("=" * 60)
    print("测试 3: Javadoc 插入")
    print("=" * 60)

    items = get_defined_functions(JAVA_SAMPLE)

    # 找到无 Javadoc 的 binarySearch 方法
    binary = next(i for i in items if i["name"] == "binarySearch")
    doc = "二分查找算法\n@param arr 已排序的整数数组\n@param target 目标值\n@return 目标索引，未找到返回 -1"

    result = insert_javadoc_into_code(JAVA_SAMPLE, binary, doc)

    # 验证 Javadoc 已插入
    result_lines = result.splitlines()
    # 找到 binarySearch 的行
    bs_idx = None
    for i, line in enumerate(result_lines):
        if "private int binarySearch" in line:
            bs_idx = i
            break
    assert bs_idx is not None, "未找到 binarySearch"
    assert "/**" in result_lines[bs_idx - 6], "应插入 Javadoc 开头"
    assert "二分查找算法" in result_lines[bs_idx - 5], "应包含描述"
    assert "*/" in result_lines[bs_idx - 1], "应插入 Javadoc 结尾"
    print("✓ Javadoc 已正确插入到 binarySearch 上方")

    # 验证大括号仍匹配
    _validate_braces(result)
    print("✓ 插入后大括号匹配正常")
    print()


def test_replace_javadoc():
    """测试替换已有 Javadoc"""
    print("=" * 60)
    print("测试 4: 替换已有 Javadoc")
    print("=" * 60)

    items = get_defined_functions(JAVA_SAMPLE)

    # 找到已有 Javadoc 的 addUser 方法
    add_user = next(i for i in items if i["name"] == "addUser")
    old_range = add_user["existing_javadoc"]
    assert old_range is not None

    new_doc = "添加新用户到列表中（更新版）\n@param name 用户名，不能为空\n@throws IllegalArgumentException 用户名为空时抛出"
    result = insert_javadoc_into_code(JAVA_SAMPLE, add_user, new_doc)

    result_lines = result.splitlines()
    # 验证旧 Javadoc 被替换
    assert "添加新用户到列表中（更新版）" in result, "应包含新 Javadoc"
    assert "更新版" in result, "新 Javadoc 内容应存在"

    # 统计 Javadoc 数量（addUser 附近应只有 1 个）
    add_user_idx = None
    for i, line in enumerate(result_lines):
        if "public void addUser" in line:
            add_user_idx = i
            break
    assert add_user_idx is not None

    # 向上查找 Javadoc
    javadoc_count = 0
    for j in range(add_user_idx - 1, max(add_user_idx - 10, 0), -1):
        if "*/" in result_lines[j]:
            javadoc_count += 1
            break
    assert javadoc_count == 1, f"addUser 上方应有 1 个 Javadoc，实际 {javadoc_count}"
    print("✓ 已有 Javadoc 被正确替换")

    _validate_braces(result)
    print("✓ 替换后大括号匹配正常")
    print()


def test_extract_existing_javadoc():
    """测试提取已有 Javadoc 文本"""
    print("=" * 60)
    print("测试 5: 提取已有 Javadoc 文本")
    print("=" * 60)

    lines = JAVA_SAMPLE.splitlines()
    items = get_defined_functions(JAVA_SAMPLE)
    add_user = next(i for i in items if i["name"] == "addUser")
    js, je = add_user["existing_javadoc"]

    text = extract_existing_javadoc(lines, js, je)
    assert "添加新用户" in text, f"应包含'添加新用户'，实际: {text}"
    assert "@param name 用户名" in text, f"应包含 @param，实际: {text}"
    assert "/**" not in text, "不应包含 /** 标记"
    assert "*/" not in text, "不应包含 */ 标记"
    assert " *" not in text, "不应包含行首 * 标记"
    print(f"✓ 提取的 Javadoc 文本: {text!r}")
    print()


def test_multiple_insertions():
    """测试多个 Javadoc 串行插入（从下到上）"""
    print("=" * 60)
    print("测试 6: 多个 Javadoc 串行插入")
    print("=" * 60)

    items = get_defined_functions(JAVA_SAMPLE)
    # 找出所有无 Javadoc 的方法
    no_doc = [i for i in items if not i["has_docstring"]]
    print(f"  无 Javadoc 的节点: {[i['name'] for i in no_doc]}")
    assert len(no_doc) >= 3, f"期望至少 3 个无 Javadoc 节点，实际 {len(no_doc)}"

    result = JAVA_SAMPLE
    # 从下到上插入
    sorted_items = sorted(no_doc, key=lambda x: x["lineno"], reverse=True)
    for item in sorted_items:
        doc = f"{item['name']} 方法的 Javadoc 注释\n@return 返回值说明"
        result = insert_javadoc_into_code(result, item, doc)

    _validate_braces(result)
    print("✓ 多个 Javadoc 插入后大括号匹配正常")

    # 验证所有方法都有 Javadoc
    new_items = get_defined_functions(result)
    for item in new_items:
        if item["type"] == "method":
            assert item["has_docstring"], f"{item['name']} 应有 Javadoc"
    print("✓ 所有方法现在都有 Javadoc")
    print()


def test_markdown_docs():
    """测试 Markdown 文档生成"""
    print("=" * 60)
    print("测试 7: Markdown 文档生成")
    print("=" * 60)

    items = get_defined_functions(JAVA_SAMPLE)
    for item in items:
        item["docstring"] = f"{item['name']} 的说明文档"
    md = build_java_markdown_docs(items)

    assert "# Java API 文档" in md, "应包含标题"
    assert "```java" in md, "应包含 java 代码块"
    assert "UserService" in md, "应包含类名"
    assert "addUser" in md, "应包含方法名"
    print("✓ Markdown 文档生成正确")
    print()


def test_brace_validation():
    """测试大括号校验"""
    print("=" * 60)
    print("测试 8: 大括号校验")
    print("=" * 60)

    # 正常代码
    _validate_braces(JAVA_SAMPLE)
    print("✓ 正常代码大括号匹配通过")

    # 缺少闭括号
    bad_code = "public class Foo {\n    public void bar() {\n"
    try:
        _validate_braces(bad_code)
        assert False, "应抛出异常"
    except SyntaxError:
        print("✓ 缺少闭括号时正确抛出异常")

    # 多余闭括号
    bad_code2 = "public class Foo {\n}}\n"
    try:
        _validate_braces(bad_code2)
        assert False, "应抛出异常"
    except SyntaxError:
        print("✓ 多余闭括号时正确抛出异常")

    # 字符串中的大括号不应影响校验
    tricky_code = 'public class Foo {\n    String s = "{}}{}";\n}\n'
    _validate_braces(tricky_code)
    print("✓ 字符串中的大括号被正确屏蔽")
    print()


if __name__ == "__main__":
    test_parser()
    test_javadoc_format()
    test_insert_javadoc()
    test_replace_javadoc()
    test_extract_existing_javadoc()
    test_multiple_insertions()
    test_markdown_docs()
    test_brace_validation()
    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
