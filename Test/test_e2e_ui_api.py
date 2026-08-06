# -*- coding: utf-8 -*-
"""通过Gradio HTTP API进行端到端UI测试（等同于UI操作）"""
import sys
import os
import time
import ast
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gradio_client import Client
except ImportError:
    print("[FAIL] gradio_client 未安装，请运行: pip install gradio_client")
    sys.exit(1)


SERVER_URL = "http://127.0.0.1:7860"


def print_separator(title=""):
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def wait_for_server(timeout=30):
    """等待服务器就绪"""
    import urllib.request
    for i in range(timeout):
        try:
            r = urllib.request.urlopen(SERVER_URL, timeout=2)
            if r.status == 200:
                print(f"[INFO] 服务器就绪 (等待 {i+1}s)")
                return True
        except Exception:
            time.sleep(1)
    print(f"[FAIL] 服务器在 {timeout}s 内未就绪")
    return False


# ============================================================
# 测试1：Python文件上传及代码读取（通过Gradio API）
# ============================================================
def test_python_upload_via_api(client):
    print_separator("测试1：Python文件上传及代码读取（Gradio API）")
    try:
        test_file = os.path.join(os.path.dirname(__file__), "TestPythonFile.py")
        if not os.path.exists(test_file):
            print(f"[FAIL] 测试文件不存在: {test_file}")
            return False
        # 调用 handle_file_upload（api_name可以通过/predict?或查看config获取）
        # Gradio文件上传组件的change事件
        result = client.predict(
            handle_file(test_file),
            api_name="/handle_file_upload"
        )
        print(f"[INFO] API返回: {result}")
        # handle_file_upload 返回 (code, language)
        if isinstance(result, (list, tuple)) and len(result) == 2:
            code, lang = result
            print(f"[INFO] 识别语言: {lang}")
            print(f"[INFO] 代码行数: {len(code.splitlines())}")
            if lang == "Python" and "class UserManager" in code:
                print("[PASS] Python文件上传及代码读取成功")
                return True
        print(f"[FAIL] 返回格式不符预期: {result}")
        return False
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        return False


# ============================================================
# 测试2：Java文件上传及代码读取（通过Gradio API）
# ============================================================
def test_java_upload_via_api(client):
    print_separator("测试2：Java文件上传及代码读取（Gradio API）")
    try:
        test_file = os.path.join(os.path.dirname(__file__), "TestJavaFile.java")
        if not os.path.exists(test_file):
            print(f"[FAIL] 测试文件不存在: {test_file}")
            return False
        result = client.predict(
            handle_file(test_file),
            api_name="/handle_file_upload"
        )
        print(f"[INFO] API返回长度: {len(result) if isinstance(result, (list, tuple)) else 'N/A'}")
        if isinstance(result, (list, tuple)) and len(result) == 2:
            code, lang = result
            print(f"[INFO] 识别语言: {lang}")
            print(f"[INFO] 代码行数: {len(code.splitlines())}")
            if lang == "Java" and "public class UserService" in code:
                print("[PASS] Java文件上传及代码读取成功，语言自动识别正确")
                return True
        print(f"[FAIL] 返回格式不符预期")
        return False
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        return False


# ============================================================
# 测试3：Python代码分析（通过Gradio API）
# ============================================================
def test_python_analysis_via_api(client):
    print_separator("测试3：Python代码分析（Gradio API）")
    py_code = """from typing import List, Optional

class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    def greet(self) -> str:
        return f"Hello, {self.name}"

def filter_adults(users: List[User], min_age: int = 18) -> List[User]:
    return [u for u in users if u.age >= min_age]
"""
    try:
        # analyze_code: inputs=[input_box, language], outputs=[quality, annotation, summary, log]
        result = client.predict(
            py_code,
            "Python",
            api_name="/analyze_code"
        )
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            quality, annotation, summary = result[0], result[1], result[2]
            print(f"[INFO] 质量报告长度: {len(quality)}")
            print(f"[INFO] 注解报告长度: {len(annotation)}")
            print(f"[INFO] 摘要长度: {len(summary)}")
            print(f"[INFO] 摘要预览: {summary[:200]}")
            combined = quality + annotation + summary
            if "无效" in combined:
                print("[FAIL] 有效Python代码被误判为无效")
                return False
            if "User" in combined or "函数" in combined or "类" in combined:
                print("[PASS] Python代码分析成功")
                return True
        print(f"[FAIL] 返回格式不符预期")
        return False
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        return False


# ============================================================
# 测试4：Java代码分析（通过Gradio API）
# ============================================================
def test_java_analysis_via_api(client):
    print_separator("测试4：Java代码分析（Gradio API）")
    java_code = """package com.test;
public class Calculator {
    private int result;
    public Calculator() { this.result = 0; }
    public int add(int a, int b) { return a + b; }
    public int multiply(int a, int b) { return a * b; }
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println(calc.add(3, 5));
    }
}
"""
    try:
        result = client.predict(
            java_code,
            "Java",
            api_name="/analyze_code"
        )
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            quality, annotation, summary = result[0], result[1], result[2]
            print(f"[INFO] 质量报告长度: {len(quality)}")
            print(f"[INFO] 摘要预览: {summary[:200]}")
            combined = quality + annotation + summary
            if "无效" in combined:
                print("[FAIL] 有效Java代码被误判为无效")
                return False
            if "Calculator" in combined or "类" in combined or "方法" in combined:
                print("[PASS] Java代码分析成功")
                return True
        print(f"[FAIL] 返回格式不符预期")
        return False
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        return False


# ============================================================
# 测试5：Python注释生成+下载+AST验证（通过Gradio API）
# ============================================================
def test_python_annotate_via_api(client):
    print_separator("测试5：Python注释生成+下载+AST验证（Gradio API）")
    py_code = """from typing import List

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
"""
    try:
        # process_code: inputs=[input_box, incremental, language]
        # outputs=[output_code, output_docs, output_log, state_md_path, state_src_path]
        result = client.predict(
            py_code,
            False,  # incremental
            "Python",
            api_name="/process_code"
        )
        if isinstance(result, (list, tuple)) and len(result) >= 5:
            annotated, doc, log, md_path, src_path = result[:5]
            print(f"[INFO] 注释代码长度: {len(annotated) if annotated else 0}")
            print(f"[INFO] 文档长度: {len(doc) if doc else 0}")
            print(f"[INFO] 源码下载路径: {src_path}")
            if not annotated or '"""' not in annotated:
                print("[FAIL] 未生成docstring注释")
                return False
            print("[INFO] Docstring已生成")
            # 验证下载文件
            if src_path and os.path.exists(src_path):
                print(f"[INFO] 下载文件存在，大小: {os.path.getsize(src_path)} bytes")
                try:
                    with open(src_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                    print("[PASS] Python注释生成+下载+AST语法验证通过")
                    return True
                except SyntaxError as se:
                    print(f"[FAIL] 下载文件AST解析失败: {se}")
                    return False
            else:
                # 直接验证annotated
                try:
                    ast.parse(annotated)
                    print("[PASS] Python注释生成+AST语法验证通过（直接验证）")
                    return True
                except SyntaxError as se:
                    print(f"[FAIL] 注释代码AST解析失败: {se}")
                    return False
        print(f"[FAIL] 返回格式不符预期")
        return False
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        return False


# ============================================================
# 测试6：Java注释生成+下载+结构验证（通过Gradio API）
# ============================================================
def test_java_annotate_via_api(client):
    print_separator("测试6：Java注释生成+下载+结构验证（Gradio API）")
    java_code = """package com.test;
public class Calculator {
    private int result;
    public Calculator() { this.result = 0; }
    public int add(int a, int b) { return a + b; }
    public int multiply(int a, int b) { return a * b; }
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println(calc.add(3, 5));
    }
}
"""
    try:
        result = client.predict(
            java_code,
            False,
            "Java",
            api_name="/process_code"
        )
        if isinstance(result, (list, tuple)) and len(result) >= 5:
            annotated, doc, log, md_path, src_path = result[:5]
            print(f"[INFO] 注释代码长度: {len(annotated) if annotated else 0}")
            print(f"[INFO] 文档长度: {len(doc) if doc else 0}")
            print(f"[INFO] 源码下载路径: {src_path}")
            if not annotated or "/**" not in annotated:
                print("[FAIL] 未生成Javadoc注释")
                return False
            print("[INFO] Javadoc已生成")
            # 验证下载文件
            if src_path and os.path.exists(src_path):
                print(f"[INFO] 下载文件存在，大小: {os.path.getsize(src_path)} bytes")
                with open(src_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 结构检查
                checks = ["class Calculator", "public int add", "public int multiply", "public static void main"]
                for check in checks:
                    if check not in content:
                        print(f"[FAIL] 下载文件缺失关键结构: {check}")
                        return False
                print("[PASS] Java注释生成+下载+结构验证通过")
                return True
            else:
                # 直接验证annotated
                checks = ["class Calculator", "public int add", "public int multiply"]
                for check in checks:
                    if check not in annotated:
                        print(f"[FAIL] 注释代码缺失关键结构: {check}")
                        return False
                print("[PASS] Java注释生成+结构验证通过（直接验证）")
                return True
        print(f"[FAIL] 返回格式不符预期")
        return False
    except Exception as e:
        print(f"[FAIL] 异常: {e}")
        return False


# ============================================================
# 测试7：无效代码验证（通过Gradio API）
# ============================================================
def test_invalid_code_via_api(client):
    print_separator("测试7：无效代码验证（Gradio API）")
    all_pass = True
    cases = [
        ("psvm", "Python", "纯无意义字符串"),
        ("hello world", "Python", "普通英文句子"),
        ("psvm", "Java", "Java无意义输入"),
        ("hello world test", "Java", "Java普通句子"),
    ]
    for code, lang, desc in cases:
        try:
            result = client.predict(code, lang, api_name="/analyze_code")
            if isinstance(result, (list, tuple)) and len(result) >= 3:
                combined = result[0] + result[1] + result[2]
                print(f"\n[INFO] [{lang}/{desc}] input='{code}'")
                print(f"[INFO] 输出预览: {combined[:150]}")
                if "无效" in combined or "语法" in combined or "错误" in combined:
                    print(f"[PASS] 正确返回无效代码提示")
                else:
                    hallucination_keywords = ["SVM", "支持向量机", "向量机", "分类器", "机器学习"]
                    if any(kw.lower() in combined.lower() for kw in hallucination_keywords):
                        print(f"[FAIL] 返回了LLM幻觉内容")
                        all_pass = False
                    else:
                        print(f"[WARN] 未返回明显'无效'提示，但也未出现幻觉")
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
    from gradio_client import handle_file

    print("\n" + "#" * 70)
    print("#     代码注释 Agent 端到端 UI 测试（通过 Gradio HTTP API）")
    print("#" * 70)

    if not wait_for_server():
        sys.exit(1)

    try:
        client = Client(SERVER_URL, verbose=False)
        print(f"[INFO] Gradio 客户端连接成功")
    except Exception as e:
        print(f"[FAIL] 无法连接Gradio客户端: {e}")
        sys.exit(1)

    # 列出可用API
    try:
        info = client.view_api(return_format="dict")
        api_names = list(info.get("named_endpoints", {}).keys()) if isinstance(info, dict) else []
        print(f"[INFO] 可用API: {api_names}")
    except Exception:
        pass

    tests = [
        ("Python文件上传+语言识别", lambda: test_python_upload_via_api(client)),
        ("Java文件上传+语言识别", lambda: test_java_upload_via_api(client)),
        ("Python代码分析", lambda: test_python_analysis_via_api(client)),
        ("Java代码分析", lambda: test_java_analysis_via_api(client)),
        ("Python注释生成+下载+AST", lambda: test_python_annotate_via_api(client)),
        ("Java注释生成+下载+结构", lambda: test_java_annotate_via_api(client)),
        ("无效代码验证", lambda: test_invalid_code_via_api(client)),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"[FAIL] {name} 异常: {e}")
            results[name] = False

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
        print("\n  🎉 所有UI端到端测试通过！")
    else:
        print(f"\n  ⚠️  有 {total - passed} 个测试失败")
    sys.exit(0 if passed == total else 1)
