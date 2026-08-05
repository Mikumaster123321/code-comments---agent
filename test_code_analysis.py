# -*- coding: utf-8 -*-
"""单元测试：代码质量分析、类型注解检查、代码摘要生成三个新功能

测试覆盖：
- _calc_complexity / _calc_max_depth 辅助函数
- analyze_code_quality 代码质量分析
- check_type_annotations 类型注解检查
- generate_code_summary 代码摘要生成（通过 monkeypatch mock LLM 调用）
- analyze_code 主分析函数（含异常处理与空输入处理）
"""
import os
import ast

# 在导入 main 之前设置测试用 API Key，避免 EnvironmentError
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key-for-unit-test")

import pytest
import main


# ==================== 测试夹具 ====================

@pytest.fixture
def sample_high_complexity():
    """高圈复杂度代码（复杂度 = 6，触发 ⚡ 警告）"""
    return '''def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return 3
            return 2
        return 1
    elif x < -10:
        for i in range(10):
            if i == x:
                return i
    return 0
'''


@pytest.fixture
def sample_deep_nesting():
    """深嵌套代码（最大深度 = 5，触发 ⚠️ 警告）"""
    return '''def deep_func(data):
    if data:
        for item in data:
            if item:
                while item > 0:
                    if item % 2 == 0:
                        item //= 2
                    else:
                        item -= 1
'''


@pytest.fixture
def sample_long_function():
    """过长函数（行数 > 50，触发 ⚠️ 警告）"""
    lines = ['def long_func():']
    for i in range(60):
        lines.append(f'    x{i} = {i}')
    lines.append('    return sum(locals().values())')
    return '\n'.join(lines)


@pytest.fixture
def sample_too_many_params():
    """参数过多的函数（参数数 = 7 > 5，触发 ⚠️ 警告）"""
    return '''def many_params(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g
'''


@pytest.fixture
def sample_class_code():
    """包含类的代码"""
    return '''class Foo:
    def __init__(self):
        self.x = 0
    def method(self, y: int) -> int:
        return self.x + y
'''


# ==================== _calc_complexity 测试 ====================

class TestCalcComplexity:
    """测试圈复杂度计算"""

    def test_simple_function_complexity_is_one(self):
        """无分支的简单函数复杂度应为 1"""
        tree = ast.parse("def f():\n    return 1\n")
        func = tree.body[0]
        assert main._calc_complexity(func) == 1

    def test_if_increases_complexity(self):
        """每个 if 应使复杂度 +1"""
        tree = ast.parse("def f(x):\n    if x:\n        return 1\n    return 0\n")
        func = tree.body[0]
        assert main._calc_complexity(func) == 2

    def test_for_loop_increases_complexity(self):
        """for 循环应使复杂度 +1"""
        tree = ast.parse("def f(xs):\n    for x in xs:\n        print(x)\n")
        func = tree.body[0]
        assert main._calc_complexity(func) == 2

    def test_while_increases_complexity(self):
        """while 循环应使复杂度 +1"""
        tree = ast.parse("def f():\n    while True:\n        break\n")
        func = tree.body[0]
        assert main._calc_complexity(func) == 2

    def test_try_except_increases_complexity(self):
        """try/except 应使复杂度 +2（Try +1，ExceptHandler +1）"""
        tree = ast.parse("def f():\n    try:\n        pass\n    except Exception:\n        pass\n")
        func = tree.body[0]
        assert main._calc_complexity(func) == 3

    def test_bool_op_and_increases_complexity(self):
        """and 操作数每多一个 +1（3 个操作数 -> +2）"""
        tree = ast.parse("def f(a, b, c):\n    return a and b and c\n")
        func = tree.body[0]
        assert main._calc_complexity(func) == 3

    def test_multiple_branches(self):
        """多分支综合计算"""
        code = '''def f(x):
    if x > 0:
        for i in range(x):
            if i == 5:
                while i > 0:
                    i -= 1
    return 0
'''
        tree = ast.parse(code)
        func = tree.body[0]
        # 1(基) + if + for + if + while = 5
        assert main._calc_complexity(func) == 5

    def test_match_case_increases_complexity(self):
        """match/case 语句应使复杂度 +1（Python 3.10+）"""
        code = '''def handle(x):
    match x:
        case 1:
            return "one"
        case _:
            return "other"
'''
        tree = ast.parse(code)
        func = tree.body[0]
        # 1(基) + match = 2
        assert main._calc_complexity(func) == 2


# ==================== _calc_max_depth 测试 ====================

class TestCalcMaxDepth:
    """测试最大嵌套深度计算"""

    def test_flat_function_depth_zero(self):
        """无嵌套的扁平函数深度应为 0"""
        tree = ast.parse("def f():\n    return 1\n")
        func = tree.body[0]
        assert main._calc_max_depth(func) == 0

    def test_single_if_depth_one(self):
        """单层 if 深度为 1"""
        tree = ast.parse("def f(x):\n    if x:\n        return 1\n")
        func = tree.body[0]
        assert main._calc_max_depth(func) == 1

    def test_nested_if_depth_two(self):
        """两层嵌套 if 深度为 2"""
        code = '''def f(x):
    if x:
        if x > 1:
            return 1
'''
        tree = ast.parse(code)
        func = tree.body[0]
        assert main._calc_max_depth(func) == 2

    def test_deep_nesting(self):
        """多层嵌套（if+for+if+while+if = 深度 5）"""
        code = '''def f(x):
    if x:
        for i in range(x):
            if i:
                while i > 0:
                    if i % 2:
                        i -= 1
'''
        tree = ast.parse(code)
        func = tree.body[0]
        assert main._calc_max_depth(func) == 5


# ==================== analyze_code_quality 测试 ====================

class TestAnalyzeCodeQuality:
    """测试代码质量分析主函数"""

    def test_empty_code_returns_report(self):
        """空代码应返回带表头的报告"""
        report = main.analyze_code_quality("")
        assert "代码质量分析报告" in report
        assert "(无函数/类)" in report

    def test_good_function_marked_well(self):
        """良好函数应标记为 ✅良好"""
        report = main.analyze_code_quality("def add(a: int, b: int) -> int:\n    return a + b\n")
        assert "✅良好" in report

    def test_report_contains_table_header(self):
        """报告应包含表格表头"""
        report = main.analyze_code_quality("def f():\n    pass\n")
        assert "| 函数/类 | 类型 | 行数 |" in report

    def test_no_issues_when_good(self):
        """无问题时应显示质量良好"""
        report = main.analyze_code_quality("def f():\n    return 1\n")
        assert "代码质量良好" in report

    def test_issues_section_when_problems(self, sample_deep_nesting):
        """有 ⚠️ 问题时应包含问题列表"""
        report = main.analyze_code_quality(sample_deep_nesting)
        assert "需要关注的问题" in report

    def test_high_complexity_medium_warning(self):
        """复杂度 > 5 且 <= 10 应有 ⚡ 警告"""
        branches = "\n".join(f"    if x == {i}: pass" for i in range(7))
        code = f"def f(x):\n{branches}\n"
        report = main.analyze_code_quality(code)
        assert "⚡复杂度较高" in report

    def test_very_high_complexity_warning(self):
        """复杂度 > 10 应有 ⚠️ 警告"""
        branches = "\n".join(f"    if x == {i}: pass" for i in range(15))
        code = f"def f(x):\n{branches}\n"
        report = main.analyze_code_quality(code)
        assert "⚠️复杂度过高" in report

    def test_long_function_marked(self, sample_long_function):
        """过长函数应被标记"""
        report = main.analyze_code_quality(sample_long_function)
        assert "⚠️函数过长" in report

    def test_too_many_params_marked(self, sample_too_many_params):
        """参数过多的函数应被标记"""
        report = main.analyze_code_quality(sample_too_many_params)
        assert "⚠️参数过多" in report

    def test_deep_nesting_marked(self, sample_deep_nesting):
        """深嵌套应被标记"""
        report = main.analyze_code_quality(sample_deep_nesting)
        assert "⚠️嵌套过深" in report

    def test_class_analyzed(self, sample_class_code):
        """类应被分析"""
        report = main.analyze_code_quality(sample_class_code)
        assert "Foo" in report
        assert "类" in report

    def test_invalid_syntax_raises(self):
        """语法错误应抛出 SyntaxError"""
        with pytest.raises(SyntaxError):
            main.analyze_code_quality("def f(:\n")


# ==================== check_type_annotations 测试 ====================

class TestCheckTypeAnnotations:
    """测试类型注解检查"""

    def test_complete_annotations_no_issues(self):
        """完整注解应返回 ✅"""
        report = main.check_type_annotations("def add(a: int, b: int) -> int:\n    return a + b\n")
        assert "✅" in report
        assert "完整" in report
        assert "缺失" not in report

    def test_missing_param_annotation(self):
        """缺失参数注解应报告"""
        report = main.check_type_annotations("def greet(name):\n    return name\n")
        assert "参数 `name` 缺少类型注解" in report
        assert "1" in report  # 共发现 1 处

    def test_missing_return_annotation(self):
        """缺失返回值注解应报告"""
        report = main.check_type_annotations("def f(a: int):\n    return a\n")
        assert "返回值缺少类型注解" in report

    def test_self_parameter_excluded(self):
        """self 参数不应报告（用带返回注解的方法隔离测试）"""
        report = main.check_type_annotations(
            "class A:\n    def method(self) -> None:\n        pass\n"
        )
        assert "✅" in report

    def test_cls_parameter_excluded(self):
        """cls 参数不应报告（用带返回注解的方法隔离测试）"""
        report = main.check_type_annotations(
            "class A:\n    @classmethod\n    def f(cls) -> int:\n        return 1\n"
        )
        assert "✅" in report

    def test_init_return_annotation_not_required(self):
        """__init__ 方法不需要返回值注解（约定返回 None），不应误报"""
        report = main.check_type_annotations(
            "class A:\n    def __init__(self, x: int):\n        self.x = x\n"
        )
        assert "✅" in report
        assert "返回值缺少类型注解" not in report

    def test_multiple_missing_counted(self):
        """多处缺失应正确计数（3 参数 + 1 返回值 = 4）"""
        code = '''def f(a, b, c):
    return a + b + c
'''
        report = main.check_type_annotations(code)
        assert "4" in report

    def test_empty_code_no_issues(self):
        """空代码应返回无问题"""
        report = main.check_type_annotations("")
        assert "✅" in report

    def test_report_contains_function_name(self):
        """报告应包含函数名"""
        report = main.check_type_annotations("def my_func(x):\n    return x\n")
        assert "my_func" in report

    def test_report_contains_line_number(self):
        """报告应包含行号"""
        report = main.check_type_annotations("def my_func(x):\n    return x\n")
        assert "行 1" in report

    def test_invalid_syntax_raises(self):
        """语法错误应抛出 SyntaxError"""
        with pytest.raises(SyntaxError):
            main.check_type_annotations("def f(:")


# ==================== generate_code_summary 测试 ====================

def _make_fake_response(content: str):
    """构造一个假的 LLM 响应对象"""
    class FakeMessage:
        pass
    class FakeChoice:
        pass
    class FakeResponse:
        pass
    msg = FakeMessage()
    msg.content = content
    choice = FakeChoice()
    choice.message = msg
    resp = FakeResponse()
    resp.choices = [choice]
    return resp


class TestGenerateCodeSummary:
    """测试代码摘要生成（通过 monkeypatch mock LLM 调用）"""

    def test_summary_returns_llm_content(self, monkeypatch):
        """摘要应返回 LLM 响应内容"""
        monkeypatch.setattr(
            main.client.chat.completions, "create",
            lambda *a, **k: _make_fake_response("这是一个示例模块，包含核心功能。")
        )
        result = main.generate_code_summary("def f():\n    pass\n")
        assert result == "这是一个示例模块，包含核心功能。"

    def test_summary_strips_whitespace(self, monkeypatch):
        """摘要应去除两端空白"""
        monkeypatch.setattr(
            main.client.chat.completions, "create",
            lambda *a, **k: _make_fake_response("  摘要内容  \n")
        )
        result = main.generate_code_summary("x = 1\n")
        assert result == "摘要内容"

    def test_summary_llm_error_propagates(self, monkeypatch):
        """LLM 异常应向上传播"""
        def fake_create(*args, **kwargs):
            raise RuntimeError("API 不可用")
        monkeypatch.setattr(main.client.chat.completions, "create", fake_create)
        with pytest.raises(RuntimeError):
            main.generate_code_summary("x = 1\n")

    def test_summary_uses_model_config(self, monkeypatch):
        """应使用模块配置的 model/temperature/max_tokens"""
        captured = {}

        def fake_create(*args, **kwargs):
            captured.update(kwargs)
            return _make_fake_response("摘要")

        monkeypatch.setattr(main.client.chat.completions, "create", fake_create)
        main.generate_code_summary("x = 1\n")
        assert captured["model"] == main.MODEL
        assert captured["temperature"] == 0.3
        assert captured["max_tokens"] == 512

    def test_summary_prompt_contains_source(self, monkeypatch):
        """prompt 应包含源代码"""
        captured = {}

        def fake_create(*args, **kwargs):
            captured.update(kwargs)
            return _make_fake_response("摘要")

        monkeypatch.setattr(main.client.chat.completions, "create", fake_create)
        source = "def unique_name():\n    pass\n"
        main.generate_code_summary(source)
        assert "unique_name" in captured["messages"][0]["content"]


# ==================== analyze_code 主函数测试 ====================

class TestAnalyzeCode:
    """测试主分析函数（整合三个功能，含异常处理）"""

    def test_empty_input_returns_placeholder(self):
        """空输入应返回占位文本"""
        q, a, s, log = main.analyze_code("")
        assert q == "未输入代码"
        assert a == "未输入代码"
        assert s == "未输入代码"
        assert "无处理对象" in log

    def test_whitespace_only_returns_placeholder(self):
        """纯空白输入应返回占位文本"""
        q, a, s, log = main.analyze_code("   \n  \t  ")
        assert q == "未输入代码"

    def test_quality_report_generated(self):
        """应生成质量报告"""
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert "代码质量分析报告" in q

    def test_annotation_report_generated(self):
        """应生成类型注解报告"""
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert "类型注解检查报告" in a

    def test_summary_generated_via_llm(self, monkeypatch):
        """应通过 LLM 生成摘要"""
        monkeypatch.setattr(
            main.client.chat.completions, "create",
            lambda *a, **k: _make_fake_response("测试摘要")
        )
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert s == "测试摘要"
        assert "✓ 摘要生成完成" in log

    def test_quality_failure_handled(self, monkeypatch):
        """质量分析失败应被捕获并记录日志"""
        def boom(src):
            raise ValueError("boom")
        monkeypatch.setattr(main, "analyze_code_quality", boom)
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert "分析失败" in q
        assert "✗ 质量分析失败" in log

    def test_annotation_failure_handled(self, monkeypatch):
        """类型注解检查失败应被捕获并记录日志"""
        def boom(src):
            raise ValueError("boom")
        monkeypatch.setattr(main, "check_type_annotations", boom)
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert "检查失败" in a
        assert "✗ 类型注解检查失败" in log

    def test_summary_failure_handled(self, monkeypatch):
        """摘要生成失败应被捕获并记录日志"""
        def fake_create(*args, **kwargs):
            raise RuntimeError("API 错误")
        monkeypatch.setattr(main.client.chat.completions, "create", fake_create)
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert "摘要生成失败" in s
        assert "✗ 摘要生成失败" in log

    def test_log_contains_all_sections(self):
        """日志应包含三个分析阶段"""
        q, a, s, log = main.analyze_code("def f():\n    return 1\n")
        assert "代码质量分析" in log
        assert "类型注解检查" in log
        assert "代码摘要生成" in log
