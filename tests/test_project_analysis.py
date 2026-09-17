from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import pytest

from code_maintenance import (
    AnalysisEngine,
    AnalysisFinding,
    ComplexityTool,
    DependencyTool,
    FileState,
    GraphEdge,
    GraphNode,
    GraphNodeKind,
    GraphRelationKind,
    ProjectGraph,
    ProjectSnapshot,
    SnapshotMetadata,
    StructureTool,
    SymbolId,
    SymbolKind,
    SymbolState,
)


def make_snapshot(
    file_names=(),
    symbol_ids=(),
    imports=(),
    symbol_contains=(),
):
    project_node = GraphNode(GraphNodeKind.PROJECT, "project-1", "project")
    file_nodes = {
        path: GraphNode(GraphNodeKind.FILE, path, path) for path in file_names
    }
    symbol_nodes = {
        symbol_id: GraphNode(
            GraphNodeKind.SYMBOL, symbol_id, symbol_id.qualified_name
        )
        for symbol_id in symbol_ids
    }
    external_nodes = {}
    nodes = [project_node, *file_nodes.values(), *symbol_nodes.values()]
    edges = [
        GraphEdge(project_node, node, GraphRelationKind.CONTAINS)
        for node in file_nodes.values()
    ]
    edges.extend(
        GraphEdge(
            file_nodes[symbol_id.relative_path],
            symbol_node,
            GraphRelationKind.CONTAINS,
        )
        for symbol_id, symbol_node in symbol_nodes.items()
    )
    edges.extend(
        GraphEdge(
            symbol_nodes[parent],
            symbol_nodes[child],
            GraphRelationKind.CONTAINS,
        )
        for parent, child in symbol_contains
    )
    for source, target in imports:
        target_node = file_nodes.get(target)
        if target_node is None:
            target_node = external_nodes.setdefault(
                target,
                GraphNode(GraphNodeKind.EXTERNAL_MODULE, target, target),
            )
        edges.append(
            GraphEdge(file_nodes[source], target_node, GraphRelationKind.IMPORTS)
        )
    nodes.extend(external_nodes.values())
    graph = ProjectGraph(nodes=tuple(nodes), edges=tuple(edges))
    files = tuple(FileState(path, "python", f"hash:{path}") for path in file_names)
    symbols = tuple(
        SymbolState(symbol_id, f"hash:{symbol_id}") for symbol_id in symbol_ids
    )
    return ProjectSnapshot(
        project_id="project-1",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        files=files,
        symbols=symbols,
        graph=graph,
        content_hash="snapshot-hash",
        metadata=SnapshotMetadata(
            file_count=len(files),
            symbol_count=len(symbols),
            graph_node_count=len(nodes),
            graph_edge_count=len(edges),
        ),
    )


class FixedTool:
    def __init__(self, tool_id, findings):
        self.tool_id = tool_id
        self.findings = findings

    def analyze(self, snapshot):
        return list(self.findings)


class FailingTool:
    tool_id = "broken"

    def analyze(self, snapshot):
        raise RuntimeError("unstable details must not leak into ordering")


def file_finding(rule_id, path="main.py"):
    return AnalysisFinding(rule_id, rule_id, "warning", path, 0)


def class_fixture(method_count=2):
    class_id = SymbolId("python", "model.py", "Model", SymbolKind.CLASS)
    methods = tuple(
        SymbolId("python", "model.py", f"Model.method_{index}", SymbolKind.METHOD)
        for index in range(method_count)
    )
    return make_snapshot(
        ("model.py",),
        (class_id, *methods),
        symbol_contains=tuple((class_id, method) for method in methods),
    )


def test_engine_with_zero_tools_returns_no_findings():
    assert AnalysisEngine(tools=()).analyze(make_snapshot()) == []


def test_engine_runs_one_tool():
    expected = file_finding("structure.fixture")

    assert AnalysisEngine([FixedTool("fixed", [expected])]).analyze(
        make_snapshot(("main.py",))
    ) == [expected]


def test_engine_orders_tools_and_findings_deterministically():
    later = FixedTool("z-tool", [file_finding("z.rule", "z.py")])
    earlier = FixedTool(
        "a-tool",
        [file_finding("a.rule", "b.py"), file_finding("a.rule", "a.py")],
    )

    findings = AnalysisEngine([later, earlier]).analyze(make_snapshot())

    assert [(finding.rule_id, finding.relative_path) for finding in findings] == [
        ("a.rule", "a.py"),
        ("a.rule", "b.py"),
        ("z.rule", "z.py"),
    ]


def test_one_tool_failure_is_reported_without_destroying_other_results():
    healthy = file_finding("structure.healthy")

    findings = AnalysisEngine(
        [FailingTool(), FixedTool("healthy", [healthy])]
    ).analyze(make_snapshot())

    assert healthy in findings
    failure = next(item for item in findings if item.rule_id == "analysis.tool_failure")
    assert failure.severity == "error"
    assert failure.relative_path == ""
    assert failure.line == 0
    assert failure.symbol_id is None
    assert failure.message == (
        "Analysis tool 'broken' failed with RuntimeError; other tools continued."
    )


@pytest.mark.parametrize(
    ("tool_id", "malformed"),
    [
        (
            "bad-symbol",
            AnalysisFinding(
                "malformed.symbol", "bad symbol", "warning", "main.py", 0, "bad"
            ),
        ),
        (
            "bad-line",
            AnalysisFinding("malformed.line", "bad line", "warning", "main.py", "0"),
        ),
        (
            "bad-severity",
            AnalysisFinding("malformed.severity", "bad severity", 5, "main.py", 0),
        ),
    ],
)
def test_malformed_finding_isolated_per_tool(tool_id, malformed):
    healthy = file_finding("structure.healthy")
    engine = AnalysisEngine(
        [FixedTool(tool_id, [malformed]), FixedTool("healthy", [healthy])]
    )

    findings = engine.analyze(make_snapshot(("main.py",)))

    assert healthy in findings
    failures = [item for item in findings if item.rule_id == "analysis.tool_failure"]
    assert len(failures) == 1
    assert failures[0].message == (
        f"Analysis tool '{tool_id}' failed with TypeError; other tools continued."
    )


def test_multiple_malformed_and_failing_tools_are_ordered_deterministically():
    healthy = file_finding("structure.healthy")
    tools = [
        FixedTool(
            "bad-symbol",
            [AnalysisFinding("bad.symbol", "bad", "warning", "", 0, "bad")],
        ),
        FixedTool(
            "bad-line",
            [AnalysisFinding("bad.line", "bad", "warning", "", "0")],
        ),
        FixedTool(
            "bad-severity",
            [AnalysisFinding("bad.severity", "bad", 5, "", 0)],
        ),
        FailingTool(),
        FixedTool("healthy", [healthy]),
    ]
    engine = AnalysisEngine(tools)

    first = engine.analyze(make_snapshot())
    second = engine.analyze(make_snapshot())

    assert first == second
    assert healthy in first
    failures = [item for item in first if item.rule_id == "analysis.tool_failure"]
    assert len(failures) == 4
    assert [item.message for item in failures] == sorted(
        item.message for item in failures
    )


def test_finding_scope_conventions_remain_expressible():
    symbol_id = SymbolId("python", "main.py", "run", SymbolKind.FUNCTION)
    project = AnalysisFinding("scope.project", "project", "warning", "", 0)
    file = AnalysisFinding("scope.file", "file", "warning", "main.py", 4)
    symbol = AnalysisFinding(
        "scope.symbol", "symbol", "warning", "main.py", 7, symbol_id
    )

    assert (project.relative_path, project.line, project.symbol_id) == ("", 0, None)
    assert (file.relative_path, file.line, file.symbol_id) == ("main.py", 4, None)
    assert (symbol.relative_path, symbol.line, symbol.symbol_id) == (
        symbol_id.relative_path,
        7,
        symbol_id,
    )


@pytest.mark.parametrize(
    ("limit", "expected_count"),
    [(3, 0), (2, 0), (1, 1)],
    ids=("below", "boundary", "above"),
)
def test_complexity_class_method_threshold(limit, expected_count):
    findings = ComplexityTool(max_methods_per_class=limit).analyze(class_fixture())

    assert len(findings) == expected_count
    if findings:
        assert findings[0].rule_id == "complexity.class_method_count"
        assert findings[0].relative_path == "model.py"


@pytest.mark.parametrize(
    ("limit", "expected_count"),
    [(4, 0), (3, 0), (2, 1)],
    ids=("below", "boundary", "above"),
)
def test_structure_symbol_density_threshold(limit, expected_count):
    findings = StructureTool(max_symbols_per_file=limit).analyze(class_fixture())

    assert len(findings) == expected_count
    if findings:
        assert findings[0].rule_id == "structure.symbol_density"


def test_dependency_tool_accepts_acyclic_graph():
    snapshot = make_snapshot(
        ("a.py", "b.py", "c.py"), imports=(("a.py", "b.py"), ("b.py", "c.py"))
    )

    assert DependencyTool(max_fan_out=10).analyze(snapshot) == []


def test_dependency_tool_reports_simple_cycle_once():
    snapshot = make_snapshot(
        ("a.py", "b.py"), imports=(("a.py", "b.py"), ("b.py", "a.py"))
    )

    findings = DependencyTool(max_fan_out=10).analyze(snapshot)

    assert len(findings) == 1
    assert findings[0].rule_id == "dependency.cycle"
    assert findings[0].relative_path == "a.py"
    assert findings[0].message == "Import cycle includes 2 files: a.py, b.py."


def test_dependency_tool_reports_multi_file_cycle_canonically():
    snapshot = make_snapshot(
        ("c.py", "a.py", "b.py"),
        imports=(("c.py", "a.py"), ("a.py", "b.py"), ("b.py", "c.py")),
    )

    findings = DependencyTool(max_fan_out=10).analyze(snapshot)

    assert [(item.relative_path, item.message) for item in findings] == [
        ("a.py", "Import cycle includes 3 files: a.py, b.py, c.py.")
    ]


def test_dependency_tool_handles_deep_acyclic_chain_without_failure():
    files = tuple(f"node_{index:04d}.py" for index in range(1601))
    imports = tuple(zip(files, files[1:]))
    snapshot = make_snapshot(files, imports=imports)

    findings = AnalysisEngine([DependencyTool(max_fan_out=10)]).analyze(snapshot)

    assert findings == []


def test_dependency_tool_finds_cycle_at_end_of_deep_chain():
    files = tuple(f"node_{index:04d}.py" for index in range(1601))
    imports = (*tuple(zip(files, files[1:])), (files[-1], files[1500]))
    snapshot = make_snapshot(files, imports=imports)

    findings = AnalysisEngine([DependencyTool(max_fan_out=10)]).analyze(snapshot)

    cycles = [item for item in findings if item.rule_id == "dependency.cycle"]
    assert len(cycles) == 1
    assert cycles[0].relative_path == files[1500]
    assert files[-1] in cycles[0].message
    assert not any(item.rule_id == "analysis.tool_failure" for item in findings)


def test_dependency_tool_reports_self_cycle():
    snapshot = make_snapshot(("self.py",), imports=(("self.py", "self.py"),))

    findings = DependencyTool(max_fan_out=10).analyze(snapshot)

    assert [(item.rule_id, item.relative_path, item.message) for item in findings] == [
        ("dependency.cycle", "self.py", "Import cycle includes 1 file: self.py.")
    ]


def test_dependency_tool_reports_two_disjoint_cycles_in_stable_order():
    snapshot = make_snapshot(
        ("d.py", "b.py", "a.py", "c.py"),
        imports=(
            ("a.py", "b.py"),
            ("b.py", "a.py"),
            ("c.py", "d.py"),
            ("d.py", "c.py"),
        ),
    )

    findings = DependencyTool(max_fan_out=10).analyze(snapshot)

    assert [(item.rule_id, item.relative_path) for item in findings] == [
        ("dependency.cycle", "a.py"),
        ("dependency.cycle", "c.py"),
    ]


def test_dependency_fan_out_counts_duplicate_import_edges_once():
    snapshot = make_snapshot(
        ("main.py",),
        imports=(
            ("main.py", "external"),
            ("main.py", "external"),
            ("main.py", "external"),
        ),
    )

    assert DependencyTool(max_fan_out=1).analyze(snapshot) == []


@pytest.mark.parametrize(
    ("limit", "expected_count"),
    [(3, 0), (2, 0), (1, 1)],
    ids=("below", "boundary", "above"),
)
def test_dependency_fan_out_threshold(limit, expected_count):
    snapshot = make_snapshot(
        ("main.py",), imports=(("main.py", "one"), ("main.py", "two"))
    )

    findings = DependencyTool(max_fan_out=limit).analyze(snapshot)

    assert len(findings) == expected_count
    if findings:
        assert findings[0].rule_id == "dependency.concentration"


def test_empty_project_is_valid_for_default_engine():
    assert AnalysisEngine().analyze(make_snapshot()) == []


def test_repeated_runs_return_exactly_equal_findings():
    snapshot = make_snapshot(
        ("b.py", "a.py"), imports=(("b.py", "a.py"), ("a.py", "b.py"))
    )
    engine = AnalysisEngine(
        [DependencyTool(max_fan_out=0), StructureTool(max_symbols_per_file=0)]
    )

    assert engine.analyze(snapshot) == engine.analyze(snapshot)


def test_analysis_uses_snapshot_without_filesystem_reads(monkeypatch):
    snapshot = class_fixture()

    def reject_read(*args, **kwargs):
        raise AssertionError("analysis must not read source files")

    monkeypatch.setattr(Path, "read_text", reject_read)

    AnalysisEngine().analyze(snapshot)


def test_rule_ids_are_stable_machine_readable_values():
    class_id = SymbolId("python", "a.py", "A", SymbolKind.CLASS)
    method_ids = tuple(
        SymbolId("python", "a.py", f"A.m{index}", SymbolKind.METHOD)
        for index in range(2)
    )
    snapshot = make_snapshot(
        ("a.py", "b.py"),
        (class_id, *method_ids),
        imports=(("a.py", "b.py"), ("a.py", "external"), ("b.py", "a.py")),
        symbol_contains=tuple((class_id, method) for method in method_ids),
    )

    findings = AnalysisEngine(
        [
            ComplexityTool(max_methods_per_class=1),
            StructureTool(max_symbols_per_file=2),
            DependencyTool(max_fan_out=1),
        ]
    ).analyze(snapshot)

    assert {finding.rule_id for finding in findings} == {
        "complexity.class_method_count",
        "structure.symbol_density",
        "dependency.cycle",
        "dependency.concentration",
    }
    assert all(
        rule_id.replace(".", "").replace("_", "").islower()
        for rule_id in {finding.rule_id for finding in findings}
    )


def test_phase_4_fixture_metrics_baseline():
    snapshot = make_snapshot(
        ("a.py", "b.py"), imports=(("a.py", "b.py"), ("b.py", "a.py"))
    )
    engine = AnalysisEngine([DependencyTool(max_fan_out=10)])

    started = perf_counter()
    findings = engine.analyze(snapshot)
    elapsed = perf_counter() - started

    assert snapshot.metadata.file_count == 2
    assert snapshot.metadata.symbol_count == 0
    assert snapshot.metadata.graph_node_count == 3
    assert snapshot.metadata.graph_edge_count == 4
    assert Counter(item.rule_id for item in findings) == Counter(
        {"dependency.cycle": 1}
    )
    assert elapsed < 1.0


def test_iterative_dependency_analysis_synthetic_graph_smoke():
    files = tuple(f"file_{index:04d}.py" for index in range(3000))
    chain = tuple(zip(files, files[1:]))
    extra_edges = tuple((files[index], files[index + 2]) for index in range(2001))
    imports = (*chain, *extra_edges)
    snapshot = make_snapshot(files, imports=imports)
    engine = AnalysisEngine([DependencyTool(max_fan_out=10)])

    first = engine.analyze(snapshot)
    second = engine.analyze(snapshot)

    assert len(imports) == 5000
    assert first == second == []
