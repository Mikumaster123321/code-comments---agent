from code_maintenance import (
    GraphNodeKind,
    GraphRelationKind,
    ProjectGraphBuilder,
    ProjectScanner,
    SymbolId,
)


def build_graph(root):
    return ProjectGraphBuilder().build(ProjectScanner().scan(root))


def edge_pairs(graph, relation):
    return {
        (str(edge.source.identity), str(edge.target.identity))
        for edge in graph.edges_of_kind(relation)
    }


def test_graph_contains_project_files_and_file_symbols(tmp_path):
    (tmp_path / "first.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (tmp_path / "Second.java").write_text(
        "class Second { void run() {} }", encoding="utf-8"
    )

    graph = build_graph(tmp_path)
    project = graph.nodes_of_kind(GraphNodeKind.PROJECT)[0]
    files = graph.nodes_of_kind(GraphNodeKind.FILE)
    symbols = graph.nodes_of_kind(GraphNodeKind.SYMBOL)
    contains = edge_pairs(graph, GraphRelationKind.CONTAINS)

    assert [node.identity for node in files] == ["Second.java", "first.py"]
    assert len(symbols) == 3
    assert (str(project.identity), "first.py") in contains
    assert ("first.py", "python:first.py:run:function") in contains
    assert all(isinstance(node.identity, SymbolId) for node in symbols)


def test_same_named_python_symbols_in_files_and_classes_remain_distinct(tmp_path):
    (tmp_path / "one.py").write_text(
        "class First:\n    def run(self):\n        pass\n\n"
        "class Second:\n    def run(self):\n        pass\n",
        encoding="utf-8",
    )
    (tmp_path / "two.py").write_text(
        "class First:\n    def run(self):\n        pass\n", encoding="utf-8"
    )

    graph = build_graph(tmp_path)
    run_ids = {
        node.identity
        for node in graph.nodes_of_kind(GraphNodeKind.SYMBOL)
        if node.label.endswith(".run")
    }

    assert len(run_ids) == 3
    assert {symbol_id.relative_path for symbol_id in run_ids} == {"one.py", "two.py"}
    assert {symbol_id.qualified_name for symbol_id in run_ids} == {
        "First.run",
        "Second.run",
    }


def test_nested_classes_and_methods_use_existing_qualified_names(tmp_path):
    (tmp_path / "nested.py").write_text(
        "class Outer:\n"
        "    class Inner:\n"
        "        def work(self):\n"
        "            pass\n",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    contains = edge_pairs(graph, GraphRelationKind.CONTAINS)

    assert (
        "python:nested.py:Outer:class",
        "python:nested.py:Outer.Inner:class",
    ) in contains
    assert (
        "python:nested.py:Outer.Inner:class",
        "python:nested.py:Outer.Inner.work:method",
    ) in contains


def test_java_overloads_keep_symbol_identity_in_graph(tmp_path):
    (tmp_path / "Example.java").write_text(
        "class Example { int find(int x) { return x; } "
        "String find(String x) { return x; } }",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    overloads = [
        node.identity
        for node in graph.nodes_of_kind(GraphNodeKind.SYMBOL)
        if node.label == "Example.find"
    ]

    assert len(overloads) == 2
    assert {symbol_id.semantic_disambiguator for symbol_id in overloads} == {
        "find(int)",
        "find(String)",
    }


def test_python_imports_cover_aliases_from_and_relative_forms(tmp_path):
    (tmp_path / "package").mkdir()
    (tmp_path / "package" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "package" / "local.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "package" / "consumer.py").write_text(
        "import os\n"
        "import third.party as third\n"
        "from package import local\n"
        "from package.sub import name as alias\n"
        "from . import local\n"
        "from ..shared import util\n",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    imports = {
        target
        for source, target in edge_pairs(graph, GraphRelationKind.IMPORTS)
        if source == "package/consumer.py"
    }
    external_targets = {
        node.identity for node in graph.nodes_of_kind(GraphNodeKind.EXTERNAL_MODULE)
    }

    assert "package/local.py" in imports
    assert {"os", "third.party", "package.sub.name", "..shared.util"} <= imports
    assert ".local" not in imports
    assert {"os", "third.party", "package.sub.name", "..shared.util"} <= external_targets


def test_java_imports_cover_multiple_normal_imports_and_internal_resolution(tmp_path):
    service_dir = tmp_path / "com" / "example"
    service_dir.mkdir(parents=True)
    (service_dir / "Service.java").write_text(
        "package com.example; public class Service {}", encoding="utf-8"
    )
    (tmp_path / "App.java").write_text(
        "import java.util.List;\n"
        "import com.example.Service;\n"
        "class App { List<String> values; Service service; }\n",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    imports = {
        target
        for source, target in edge_pairs(graph, GraphRelationKind.IMPORTS)
        if source == "App.java"
    }
    external_targets = {
        node.identity for node in graph.nodes_of_kind(GraphNodeKind.EXTERNAL_MODULE)
    }

    assert imports == {"java.util.List", "com/example/Service.java"}
    assert external_targets == {"java.util.List"}


def test_repeated_builds_have_identical_nodes_edges_and_order(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\n\nclass App:\n    def run(self):\n        pass\n",
        encoding="utf-8",
    )
    scan = ProjectScanner().scan(tmp_path)
    builder = ProjectGraphBuilder()

    first = builder.build(scan)
    second = builder.build(scan)

    assert first == second
    assert first.nodes == second.nodes
    assert first.edges == second.edges


def test_empty_project_produces_a_valid_project_only_graph(tmp_path):
    graph = build_graph(tmp_path)

    assert len(graph.nodes) == 1
    assert graph.nodes[0].kind == GraphNodeKind.PROJECT
    assert graph.edges == ()
