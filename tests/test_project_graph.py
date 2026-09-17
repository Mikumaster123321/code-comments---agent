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


def test_duplicate_class_names_use_source_ranges_for_method_containment(tmp_path):
    (tmp_path / "duplicate.py").write_text(
        "class A:\n"
        "    def run(self):\n"
        "        return 1\n\n"
        "class A:\n"
        "    def run(self):\n"
        "        return 2\n",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    symbol_contains = {
        (str(edge.source.identity), str(edge.target.identity))
        for edge in graph.edges_of_kind(GraphRelationKind.CONTAINS)
        if edge.source.kind == edge.target.kind == GraphNodeKind.SYMBOL
    }

    assert symbol_contains == {
        (
            "python:duplicate.py:A:class:line:1",
            "python:duplicate.py:A.run:method:line:2",
        ),
        (
            "python:duplicate.py:A:class:line:5",
            "python:duplicate.py:A.run:method:line:6",
        ),
    }


def test_cross_file_same_class_names_keep_containment_isolated(tmp_path):
    for filename in ("one.py", "two.py"):
        (tmp_path / filename).write_text(
            "class A:\n    def run(self):\n        pass\n", encoding="utf-8"
        )

    graph = build_graph(tmp_path)
    symbol_contains = {
        (str(edge.source.identity), str(edge.target.identity))
        for edge in graph.edges_of_kind(GraphRelationKind.CONTAINS)
        if edge.source.kind == edge.target.kind == GraphNodeKind.SYMBOL
    }

    assert symbol_contains == {
        ("python:one.py:A:class", "python:one.py:A.run:method"),
        ("python:two.py:A:class", "python:two.py:A.run:method"),
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
    (tmp_path / "package" / "feature").mkdir()
    (tmp_path / "package" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "package" / "local.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "package" / "feature" / "consumer.py").write_text(
        "import os\n"
        "import third.party as third\n"
        "from package import local\n"
        "from package.sub import name as alias\n"
        "from .. import local\n"
        "from ..shared import util\n",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    imports = {
        target
        for source, target in edge_pairs(graph, GraphRelationKind.IMPORTS)
        if source == "package/feature/consumer.py"
    }
    external_targets = {
        node.identity for node in graph.nodes_of_kind(GraphNodeKind.EXTERNAL_MODULE)
    }

    assert "package/local.py" in imports
    assert {"os", "third.party", "package.sub.name", "package.shared.util"} <= imports
    assert "..local" not in imports
    assert {
        "os",
        "third.party",
        "package.sub.name",
        "package.shared.util",
    } <= external_targets


def test_relative_unresolved_import_uses_canonical_module_identity(tmp_path):
    module_dir = tmp_path / "package" / "feature"
    module_dir.mkdir(parents=True)
    (module_dir / "consumer.py").write_text(
        "from ..services import user\n"
        "from .local import other\n",
        encoding="utf-8",
    )
    (tmp_path / "root.py").write_text("from . import local\n", encoding="utf-8")

    graph = build_graph(tmp_path)
    external_targets = {
        node.identity for node in graph.nodes_of_kind(GraphNodeKind.EXTERNAL_MODULE)
    }

    assert external_targets == {
        "package.feature.local.other",
        "package.services.user",
        "unresolved-relative:<root>:1:local",
    }
    assert "..services.user" not in external_targets
    assert ".local.other" not in external_targets


def test_self_import_and_star_import_behaviors_remain_explicit(tmp_path):
    (tmp_path / "selfmod.py").write_text(
        "import selfmod\nfrom external import *\n", encoding="utf-8"
    )

    graph = build_graph(tmp_path)
    imports = edge_pairs(graph, GraphRelationKind.IMPORTS)

    assert ("selfmod.py", "selfmod.py") in imports
    assert ("selfmod.py", "external.*") in imports


def test_unicode_path_and_duplicate_alias_import_are_deterministic(tmp_path):
    unicode_dir = tmp_path / "模块"
    unicode_dir.mkdir()
    (unicode_dir / "入口.py").write_text(
        "import os\nimport os as operating_system\n", encoding="utf-8"
    )

    graph = build_graph(tmp_path)
    imports = [
        edge
        for edge in graph.edges_of_kind(GraphRelationKind.IMPORTS)
        if edge.source.identity == "模块/入口.py" and edge.target.identity == "os"
    ]

    assert len(imports) == 1


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
