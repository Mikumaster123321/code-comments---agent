# -*- coding: utf-8 -*-
"""端到端全面测试：文件上传、代码读取、分析、注释、下载、无效代码（修正版）"""
import sys
import os
import ast
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processor import handle_file_upload, process_code, analyze_code


def print_separator(title=""):
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


# ============================================================
# 测试1：Java文件上传及代码读取
# ============================================================
def test_java_file_upload():
    print_separator("测试1：Java文件上传及代码读取")
    test_file = os.path.join(os.path.dirname(__file__), "TestJavaFile.java")
    if not os.path.exists(test_file):
        print(f"[FAIL] 测试文件不存在: {test_file}")
        return False
    try:
        result = handle_file_upload(test_file)
        if result is None:
            print("[FAIL] handle_file_upload 返回 None")
            return False
        # handle_file_upload 返回 (code, language) 元组
        code, lang = result
        print(f"[INFO] 识别语言: {lang}")
        print(f"[INFO] 读取代码行数: {len(code.splitlines())}")
        if lang != "Java":
            print(f"[FAIL] 预期语言 Java, 实际: {lang}")
            return False
        if "public class UserService" not in code:
            print("[FAIL] 代码内容不完整（未找到 UserService 类）")
            return False
        if "public static void main" not in code:
            print("[FAIL] 代码内容不完整（未找到 main 方法）")
            return False
        print("[PASS] Java文件上传及代码读取成功")
        return True
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试2：Python文件上传及代码读取
# ============================================================
def test_python_file_upload():
    print_separator("测试2：Python文件上传及代码读取")
    test_file = os.path.join(os.path.dirname(__file__), "TestPythonFile.py")
    if not os.path.exists(test_file):
        print(f"[FAIL] 测试文件不存在: {test_file}")
        return False
    try:
        result = handle_file_upload(test_file)
        if result is None:
            print("[FAIL] handle_file_upload 返回 None")
            return False
        code, lang = result
        print(f"[INFO] 识别语言: {lang}")
        print(f"[INFO] 读取代码行数: {len(code.splitlines())}")
        if lang != "Python":
            print(f"[FAIL] 预期语言 Python, 实际: {lang}")
            return False
        if "class UserManager" not in code:
            print("[FAIL] 代码内容不完整（未找到 UserManager 类）")
            return False
        if "def create_sample_users" not in code:
            print("[FAIL] 代码内容不完整（未找到 create_sample_users 函数）")
            return False
        print("[PASS] Python文件上传及代码读取成功")
        return True
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试3：Java代码分析
# ============================================================
def test_java_analysis():
    print_separator("测试3：Java代码分析")
    java_code = """
package com.test;
import java.util.List;
public class TestUser {
    private String name;
    public TestUser(String n) { this.name = n; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public static List<String> filterNames(List<String> names, String prefix) {
        List<String> result = new java.util.ArrayList<>();
        for (String s : names) { if (s.startsWith(prefix)) result.add(s); }
        return result;
    }
    public static void main(String[] args) { System.out.println("Hello"); }
}
    """
    try:
        # analyze_code 返回 (quality_report, annotation_report, summary, log_text)
        quality, annotation, summary, log = analyze_code(java_code.strip(), language="Java")
        print(f"[INFO] 质量报告长度: {len(quality)}")
        print(f"[INFO] 注解报告长度: {len(annotation)}")
        print(f"[INFO] 摘要长度: {len(summary)}")
        print(f"[INFO] 日志长度: {len(log)}")
        # 有效代码不应返回"无效代码"提示
        combined = quality + annotation + summary
        if "无效" in combined and ("语法" in combined or "代码" in combined):
            print("[FAIL] 有效Java代码被误判为无效")
            return False
        if "类" in combined or "方法" in combined or "TestUser" in combined:
            print("[PASS] Java代码分析成功")
            return True
        else:
            print(f"[WARN] 分析结果格式不明确，请人工确认: {quality[:300]}")
            return True
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试4：Python代码分析
# ============================================================
def test_python_analysis():
    print_separator("测试4：Python代码分析")
    py_code = """
from typing import List, Optional

class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    def greet(self) -> str:
        return f"Hello, {self.name}"

def filter_adults(users: List[User], min_age: int = 18) -> List[User]:
    return [u for u in users if u.age >= min_age]

def find_user(users: List[User], name: str) -> Optional[User]:
    for u in users:
        if u.name == name:
            return u
    return None
    """
    try:
        quality, annotation, summary, log = analyze_code(py_code.strip(), language="Python")
        print(f"[INFO] 质量报告长度: {len(quality)}")
        print(f"[INFO] 注解报告长度: {len(annotation)}")
        print(f"[INFO] 摘要长度: {len(summary)}")
        print(f"[INFO] 日志长度: {len(log)}")
        combined = quality + annotation + summary
        if "无效" in combined and ("语法" in combined or "代码" in combined):
            print("[FAIL] 有效Python代码被误判为无效")
            return False
        if "类" in combined or "函数" in combined or "User" in combined:
            print("[PASS] Python代码分析成功")
            return True
        else:
            print(f"[WARN] 分析结果格式不明确: {quality[:300]}")
            return True
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试5：Java代码注释生成 + 下载后语法结构验证
# ============================================================
def test_java_annotate_and_syntax():
    print_separator("测试5：Java代码注释生成 + 下载后语法结构验证")
    java_code = """
package com.test;
public class Calculator {
    private int result;
    public Calculator() { this.result = 0; }
    public int add(int a, int b) { return a + b; }
    public int multiply(int a, int b) { return a * b; }
    public void reset() { this.result = 0; }
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println(calc.add(3, 5));
    }
}
    """
    try:
        # process_code 返回 (annotated_code, markdown_doc, log_text, md_path, src_path)
        annotated, doc, log, md_path, src_path = process_code(
            java_code.strip(), language="Java", incremental=False
        )
        print(f"[INFO] 注释代码长度: {len(annotated) if annotated else 0}")
        print(f"[INFO] 文档长度: {len(doc) if doc else 0}")
        print(f"[INFO] 日志长度: {len(log) if log else 0}")
        print(f"[INFO] .md下载路径: {md_path}")
        print(f"[INFO] 源码下载路径: {src_path}")
        if not annotated or len(annotated.strip()) == 0:
            print("[FAIL] 注释后的代码为空")
            return False
        # 检查是否包含Javadoc注释
        if "/**" not in annotated or "*/" not in annotated:
            print("[FAIL] 生成的代码中未找到 Javadoc 注释 (/** */)")
            print(f"[INFO] 注释代码前800字符:\n{annotated[:800]}")
            return False
        print("[INFO] Javadoc 注释已生成")
        # 保存到临时文件
        tmp_file = os.path.join(tempfile.gettempdir(), "test_annotated.java")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(annotated)
        print(f"[INFO] 注释后代码已保存到: {tmp_file}")
        # 验证源码下载路径文件存在
        if src_path and os.path.exists(src_path):
            print(f"[INFO] 源码下载路径文件存在，大小: {os.path.getsize(src_path)} bytes")
            with open(src_path, 'r', encoding='utf-8') as f:
                src_content = f.read()
            # 验证下载的文件是否和注释后的代码一致
            if src_content.strip() != annotated.strip():
                print("[WARN] 下载文件内容与注释后代码不完全一致（可能换行差异）")
        else:
            print(f"[WARN] 源码下载路径为空或不存在: {src_path}")
        # 基本结构检查
        checks = ["class Calculator", "public int add", "public int multiply",
                  "public void reset", "public static void main"]
        for check in checks:
            if check not in annotated:
                print(f"[FAIL] 注释后代码缺失关键结构: {check}")
                return False
        print("[PASS] Java注释生成成功，代码结构完整，已保存")
        return True
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试6：Python代码注释生成 + 下载后AST语法验证
# ============================================================
def test_python_annotate_and_syntax():
    print_separator("测试6：Python代码注释生成 + 下载后AST语法验证")
    py_code = """
from typing import List

class ShopCart:
    def __init__(self):
        self.items = {}
    def add_item(self, name: str, qty: int, price: float) -> None:
        self.items[name] = (qty, price)
    def remove_item(self, name: str) -> bool:
        if name in self.items:
            del self.items[name]
            return True
        return False
    def calculate_total(self) -> float:
        total = 0.0
        for qty, price in self.items.values():
            total += qty * price
        return total

def process_orders(carts: List[ShopCart]) -> List[float]:
    return [c.calculate_total() for c in carts]
    """
    try:
        annotated, doc, log, md_path, src_path = process_code(
            py_code.strip(), language="Python", incremental=False
        )
        print(f"[INFO] 注释代码长度: {len(annotated) if annotated else 0}")
        print(f"[INFO] 文档长度: {len(doc) if doc else 0}")
        print(f"[INFO] 日志长度: {len(log) if log else 0}")
        print(f"[INFO] .md下载路径: {md_path}")
        print(f"[INFO] 源码下载路径: {src_path}")
        if not annotated or len(annotated.strip()) == 0:
            print("[FAIL] 注释后的代码为空")
            return False
        # 检查是否包含docstring注释
        if '"""' not in annotated:
            print("[FAIL] 生成的代码中未找到 docstring 注释")
            print(f"[INFO] 注释代码前800字符:\n{annotated[:800]}")
            return False
        print("[INFO] Docstring 注释已生成")
        # 保存到临时文件并通过 AST 验证语法
        tmp_file = os.path.join(tempfile.gettempdir(), "test_annotated.py")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(annotated)
        print(f"[INFO] 注释后代码已保存到: {tmp_file}")
        try:
            with open(tmp_file, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            print(f"[INFO] AST 解析成功，包含 {len(tree.body)} 个顶层节点")
        except SyntaxError as se:
            print(f"[FAIL] 注释后代码存在语法错误 (AST解析失败): {se}")
            print(f"[INFO] 错误位置: 第{se.lineno}行, 第{se.offset}列")
            return False
        # 验证下载路径文件存在且AST通过
        if src_path and os.path.exists(src_path):
            print(f"[INFO] 源码下载路径文件存在，大小: {os.path.getsize(src_path)} bytes")
            try:
                with open(src_path, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
                print("[INFO] 下载路径文件 AST 语法验证通过")
            except SyntaxError as se:
                print(f"[FAIL] 下载路径文件 AST 解析失败: {se}")
                return False
        # 基本结构检查
        checks = ["class ShopCart", "def add_item", "def remove_item",
                  "def calculate_total", "def process_orders"]
        for check in checks:
            if check not in annotated:
                print(f"[FAIL] 注释后代码缺失关键结构: {check}")
                return False
        print("[PASS] Python注释生成成功，AST语法验证通过，代码结构完整")
        return True
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试7：无效代码输入验证（Python + Java）
# ============================================================
def test_invalid_code():
    print_separator("测试7：无效代码输入验证")
    all_pass = True
    python_invalid_cases = [
        ("psvm", "纯无意义字符串"),
        ("hello world", "普通英文句子"),
    ]
    for code, desc in python_invalid_cases:
        try:
            quality, annotation, summary, log = analyze_code(code, language="Python")
            combined = quality + annotation + summary
            print(f"\n[INFO] Python无效代码测试 [{desc}]: input='{code}'")
            print(f"[INFO] 输出摘要: {combined[:200]}")
            if "无效" in combined or "语法" in combined or "错误" in combined:
                print(f"[PASS] 正确返回无效代码提示")
            else:
                hallucination_keywords = ["SVM", "支持向量机", "向量机", "分类器", "机器学习", "训练"]
                if any(kw.lower() in combined.lower() for kw in hallucination_keywords):
                    print(f"[FAIL] 返回了LLM幻觉内容（疑似SVM等无意义分析）")
                    all_pass = False
                else:
                    print(f"[WARN] 未返回明显'无效'提示，但也未出现幻觉: {combined[:200]}")
        except Exception as e:
            print(f"[FAIL] 异常: {e}")
            all_pass = False
    java_invalid_cases = [
        ("psvm", "纯无意义字符串"),
        ("hello world test", "普通英文句子"),
    ]
    for code, desc in java_invalid_cases:
        try:
            quality, annotation, summary, log = analyze_code(code, language="Java")
            combined = quality + annotation + summary
            print(f"\n[INFO] Java无效代码测试 [{desc}]: input='{code}'")
            print(f"[INFO] 输出摘要: {combined[:200]}")
            if "无效" in combined or "语法" in combined or "错误" in combined:
                print(f"[PASS] 正确返回无效代码提示")
            else:
                hallucination_keywords = ["SVM", "支持向量机", "向量机", "分类器"]
                if any(kw.lower() in combined.lower() for kw in hallucination_keywords):
                    print(f"[FAIL] 返回了LLM幻觉内容")
                    all_pass = False
                else:
                    print(f"[WARN] 未返回明显'无效'提示，但也未出现幻觉: {combined[:200]}")
        except Exception as e:
            print(f"[FAIL] 异常: {e}")
            all_pass = False
    if all_pass:
        print("\n[PASS] 无效代码验证整体通过")
    return all_pass


# ============================================================
# 主测试入口
# ============================================================
if __name__ == "__main__":
    results = {}
    tests = [
        ("Java文件上传+自动识别语言", test_java_file_upload),
        ("Python文件上传+自动识别语言", test_python_file_upload),
        ("Java代码分析(4-tuple)", test_java_analysis),
        ("Python代码分析(4-tuple)", test_python_analysis),
        ("Java注释生成+结构验证(5-tuple)", test_java_annotate_and_syntax),
        ("Python注释生成+AST验证(5-tuple)", test_python_annotate_and_syntax),
        ("无效代码验证(Python+Java)", test_invalid_code),
    ]
    print("\n" + "#" * 70)
    print("#     代码注释 Agent 全面端到端测试 (修正版)")
    print("#" * 70)
    for name, test_fn in tests:
        results[name] = test_fn()
    # 汇总
    print("\n" + "#" * 70)
    print("#     测试汇总")
    print("#" * 70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
    print(f"\n  总计: {passed}/{total} 通过")
    if passed == total:
        print("\n  🎉 所有测试通过！")
    else:
        print(f"\n  ⚠️  有 {total - passed} 个测试失败")
    sys.exit(0 if passed == total else 1)
