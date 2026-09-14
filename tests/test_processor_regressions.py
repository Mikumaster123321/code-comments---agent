from pathlib import Path
import re

from code_maintenance import SymbolId
import processor


def _cleanup_result(result):
    annotated_code, markdown, log, markdown_path, source_path = result
    for path in (markdown_path, source_path):
        if path:
            Path(path).unlink(missing_ok=True)
    return annotated_code, markdown, log


def _markdown_sections(markdown, heading):
    pattern = rf"^{re.escape(heading)}.*?(?=^## |\Z)"
    return re.findall(pattern, markdown, flags=re.MULTILINE | re.DOTALL)


def test_same_named_methods_keep_their_own_generated_docstrings(monkeypatch):
    source = '''\
class First:
    def __init__(self):
        pass

class Second:
    def __init__(self):
        pass
'''
    monkeypatch.setattr(
        processor,
        "generate_docstring",
        lambda item, *_args: f"Generated for line {item['lineno']}",
    )

    annotated_code, _, _ = _cleanup_result(processor.process_code(source))

    assert "Generated for line 2" in annotated_code
    assert "Generated for line 6" in annotated_code


def test_processor_backfills_symbol_ids_and_builds_symbol_lookup():
    source = '''\
class First:
    def run(self):
        pass

class Second:
    def run(self):
        pass
'''

    items, lookup = processor._parse_items_with_symbols(
        source, "Python", "src\\example.py"
    )
    methods = [item for item in items if item["name"] == "run"]

    assert all(isinstance(item["symbol_id"], SymbolId) for item in items)
    assert [item["qualified_name"] for item in methods] == ["First.run", "Second.run"]
    assert set(lookup) == {item["symbol_id"] for item in items}
    assert all(symbol.relative_path == "src/example.py" for symbol in lookup.values())


def test_python_markdown_keeps_same_named_methods_associated(monkeypatch):
    source = '''\
class First:
    def run(self):
        return 1

class Second:
    def run(self):
        return 2
'''
    monkeypatch.setattr(
        processor,
        "generate_docstring",
        lambda item, *_args: f"Documentation for {item['qualified_name']}",
    )

    _, markdown, _ = _cleanup_result(processor.process_code(source))
    method_sections = _markdown_sections(markdown, "## 🔧 run (Function)")

    assert len(method_sections) == 2
    assert "return 1" in method_sections[0]
    assert "Documentation for First.run" in method_sections[0]
    assert "Documentation for Second.run" not in method_sections[0]
    assert "return 2" in method_sections[1]
    assert "Documentation for Second.run" in method_sections[1]
    assert "Documentation for First.run" not in method_sections[1]


def test_java_overloads_keep_results_and_markdown_associated(monkeypatch):
    source = '''\
class Example {
    int foo(int value) { return value; }
    String foo(String value) { return value; }
}
'''

    def generate(item, *_args):
        if item["type"] == "class":
            return "Documentation for Example"
        return f"Documentation for {item['symbol_id'].semantic_disambiguator}"

    monkeypatch.setattr(processor, "generate_javadoc", generate)

    annotated, markdown, _ = _cleanup_result(
        processor.process_code(source, language="Java")
    )
    method_sections = _markdown_sections(markdown, "## 🔧 foo (Method)")

    assert "Documentation for foo(int)" in annotated
    assert "Documentation for foo(String)" in annotated
    assert len(method_sections) == 2
    assert "int foo(int value)" in method_sections[0]
    assert "Documentation for foo(int)" in method_sections[0]
    assert "Documentation for foo(String)" not in method_sections[0]
    assert "String foo(String value)" in method_sections[1]
    assert "Documentation for foo(String)" in method_sections[1]
    assert "Documentation for foo(int)" not in method_sections[1]


def test_single_line_java_overload_results_do_not_collide(monkeypatch):
    source = "class A { int foo(int x){ return x; } String foo(String s){ return s; } }"
    monkeypatch.setattr(
        processor,
        "generate_javadoc",
        lambda item, *_args: f"Documentation for {item['symbol_id'].semantic_disambiguator}",
    )

    annotated, markdown, _ = _cleanup_result(
        processor.process_code(source, language="Java")
    )
    method_sections = _markdown_sections(markdown, "## 🔧 foo (Method)")

    assert "Documentation for foo(int)" in annotated
    assert "Documentation for foo(String)" in annotated
    assert "Documentation for foo(int)" in method_sections[0]
    assert "Documentation for foo(String)" not in method_sections[0]
    assert "Documentation for foo(String)" in method_sections[1]
    assert "Documentation for foo(int)" not in method_sections[1]


def test_diff_contains_both_same_named_method_results(monkeypatch):
    source = '''\
class First:
    def run(self):
        return 1

class Second:
    def run(self):
        return 2
'''
    monkeypatch.setattr(
        processor,
        "generate_docstring",
        lambda item, *_args: f"Documentation for {item['qualified_name']}",
    )
    annotated, _, _ = _cleanup_result(processor.process_code(source))

    diff = processor.build_split_diff_html(source, annotated)

    assert "Documentation for First.run" in diff
    assert "Documentation for Second.run" in diff


def test_navigation_anchors_match_markdown_for_same_named_methods(monkeypatch):
    source = '''\
class First:
    def run(self):
        return 1

class Second:
    def run(self):
        return 2
'''
    monkeypatch.setattr(
        processor,
        "generate_docstring",
        lambda item, *_args: f"Documentation for {item['qualified_name']}",
    )
    _, markdown, _ = _cleanup_result(processor.process_code(source))

    outline = processor.build_outline_markdown(source)
    outline_anchors = re.findall(r'href="#([^"]+)"><code>run</code>', outline)
    markdown_anchors = re.findall(r'<a id="([^"]+)"></a>', markdown)

    assert outline_anchors == ["fn-run", "fn-run-2"]
    assert all(anchor in markdown_anchors for anchor in outline_anchors)


def test_progress_processor_keeps_same_named_method_results(monkeypatch):
    source = '''\
class First:
    def run(self):
        return 1

class Second:
    def run(self):
        return 2
'''
    monkeypatch.setattr(
        processor,
        "generate_docstring",
        lambda item, *_args: f"Documentation for {item['qualified_name']}",
    )

    frames = list(processor.process_code_with_progress(source))
    annotated, _, _ = _cleanup_result(frames[-1])

    assert "Documentation for First.run" in annotated
    assert "Documentation for Second.run" in annotated
