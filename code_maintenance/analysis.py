from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar, Iterable, Protocol

from .domain import AnalysisFinding, SymbolId, SymbolKind
from .graph import GraphNodeKind, GraphRelationKind
from .snapshot import ProjectSnapshot


class AnalysisTool(Protocol):
    """Deterministic, read-only analysis over an existing project snapshot."""

    tool_id: str

    def analyze(self, snapshot: ProjectSnapshot) -> list[AnalysisFinding]: ...


def _symbol_id_key(symbol_id: SymbolId | None) -> tuple[str, str, str, str, str, int]:
    if symbol_id is None:
        return ("", "", "", "", "", -1)
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        symbol_id.semantic_disambiguator or "",
        symbol_id.fallback_line if symbol_id.fallback_line is not None else -1,
    )


def _finding_key(finding: AnalysisFinding) -> tuple:
    return (
        finding.rule_id,
        finding.relative_path,
        finding.line,
        _symbol_id_key(finding.symbol_id),
        finding.severity,
        finding.message,
    )


def _validate_finding(finding: AnalysisFinding) -> None:
    if not isinstance(finding, AnalysisFinding):
        raise TypeError("analysis tools must return AnalysisFinding values")
    for value in (
        finding.rule_id,
        finding.message,
        finding.severity,
        finding.relative_path,
    ):
        if not isinstance(value, str):
            raise TypeError("finding text fields must be strings")
    if type(finding.line) is not int:
        raise TypeError("finding line must be an integer")
    if finding.symbol_id is None:
        return
    if not isinstance(finding.symbol_id, SymbolId):
        raise TypeError("finding symbol_id must be a SymbolId or None")
    symbol_id = finding.symbol_id
    for value in (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
    ):
        if not isinstance(value, str):
            raise TypeError("SymbolId text fields must be strings")
    if not isinstance(symbol_id.kind, SymbolKind):
        raise TypeError("SymbolId kind must be a SymbolKind")
    if (
        symbol_id.semantic_disambiguator is not None
        and not isinstance(symbol_id.semantic_disambiguator, str)
    ):
        raise TypeError("SymbolId semantic_disambiguator must be a string or None")
    if symbol_id.fallback_line is not None and type(symbol_id.fallback_line) is not int:
        raise TypeError("SymbolId fallback_line must be an integer or None")


@dataclass(frozen=True)
class ComplexityTool:
    """Report classes with excessive direct method concentration."""

    max_methods_per_class: int = 10
    tool_id: ClassVar[str] = "complexity"

    def __post_init__(self) -> None:
        if self.max_methods_per_class < 0:
            raise ValueError("max_methods_per_class must be non-negative")

    def analyze(self, snapshot: ProjectSnapshot) -> list[AnalysisFinding]:
        class_names: dict[SymbolId, str] = {}
        for node in snapshot.graph.nodes:
            if (
                node.kind == GraphNodeKind.SYMBOL
                and isinstance(node.identity, SymbolId)
                and node.identity.kind == SymbolKind.CLASS
            ):
                class_names[node.identity] = node.label

        methods_by_class: dict[SymbolId, set[SymbolId]] = defaultdict(set)
        for edge in snapshot.graph.edges:
            if (
                edge.relation == GraphRelationKind.CONTAINS
                and edge.source.kind == GraphNodeKind.SYMBOL
                and edge.target.kind == GraphNodeKind.SYMBOL
                and isinstance(edge.source.identity, SymbolId)
                and isinstance(edge.target.identity, SymbolId)
                and edge.source.identity.kind == SymbolKind.CLASS
                and edge.target.identity.kind == SymbolKind.METHOD
            ):
                methods_by_class[edge.source.identity].add(edge.target.identity)

        findings = []
        for class_id in sorted(class_names, key=_symbol_id_key):
            count = len(methods_by_class[class_id])
            if count <= self.max_methods_per_class:
                continue
            findings.append(
                AnalysisFinding(
                    rule_id="complexity.class_method_count",
                    message=(
                        f"Class '{class_names[class_id]}' defines {count} direct methods, "
                        f"exceeding the limit of {self.max_methods_per_class}."
                    ),
                    severity="warning",
                    relative_path=class_id.relative_path,
                    line=0,
                    symbol_id=None,
                )
            )
        return findings


@dataclass(frozen=True)
class StructureTool:
    """Report files whose symbol count exceeds a deterministic limit."""

    max_symbols_per_file: int = 50
    tool_id: ClassVar[str] = "structure"

    def __post_init__(self) -> None:
        if self.max_symbols_per_file < 0:
            raise ValueError("max_symbols_per_file must be non-negative")

    def analyze(self, snapshot: ProjectSnapshot) -> list[AnalysisFinding]:
        symbol_counts: dict[str, int] = defaultdict(int)
        for symbol in snapshot.symbols:
            symbol_counts[symbol.id.relative_path] += 1

        findings = []
        for file_state in sorted(snapshot.files, key=lambda item: item.relative_path):
            count = symbol_counts[file_state.relative_path]
            if count <= self.max_symbols_per_file:
                continue
            findings.append(
                AnalysisFinding(
                    rule_id="structure.symbol_density",
                    message=(
                        f"File defines {count} symbols, exceeding the limit of "
                        f"{self.max_symbols_per_file}."
                    ),
                    severity="warning",
                    relative_path=file_state.relative_path,
                    line=0,
                    symbol_id=None,
                )
            )
        return findings


@dataclass(frozen=True)
class DependencyTool:
    """Report import cycles and files with concentrated outgoing dependencies."""

    max_fan_out: int = 10
    tool_id: ClassVar[str] = "dependency"

    def __post_init__(self) -> None:
        if self.max_fan_out < 0:
            raise ValueError("max_fan_out must be non-negative")

    def analyze(self, snapshot: ProjectSnapshot) -> list[AnalysisFinding]:
        file_paths = {
            node.identity
            for node in snapshot.graph.nodes
            if node.kind == GraphNodeKind.FILE and isinstance(node.identity, str)
        }
        import_targets: dict[str, set[str]] = {
            path: set() for path in file_paths
        }
        internal_adjacency: dict[str, set[str]] = {
            path: set() for path in file_paths
        }
        for edge in snapshot.graph.edges:
            if (
                edge.relation != GraphRelationKind.IMPORTS
                or edge.source.kind != GraphNodeKind.FILE
                or not isinstance(edge.source.identity, str)
                or edge.source.identity not in file_paths
            ):
                continue
            target = str(edge.target.identity)
            import_targets[edge.source.identity].add(target)
            if (
                edge.target.kind == GraphNodeKind.FILE
                and isinstance(edge.target.identity, str)
                and edge.target.identity in file_paths
            ):
                internal_adjacency[edge.source.identity].add(edge.target.identity)

        findings = []
        for component in _strongly_connected_components(internal_adjacency):
            is_cycle = len(component) > 1 or component[0] in internal_adjacency[
                component[0]
            ]
            if not is_cycle:
                continue
            members = ", ".join(component)
            noun = "file" if len(component) == 1 else "files"
            findings.append(
                AnalysisFinding(
                    rule_id="dependency.cycle",
                    message=(
                        f"Import cycle includes {len(component)} {noun}: {members}."
                    ),
                    severity="warning",
                    relative_path=component[0],
                    line=0,
                    symbol_id=None,
                )
            )

        for path in sorted(import_targets):
            count = len(import_targets[path])
            if count <= self.max_fan_out:
                continue
            findings.append(
                AnalysisFinding(
                    rule_id="dependency.concentration",
                    message=(
                        f"File imports {count} distinct targets, exceeding the limit "
                        f"of {self.max_fan_out}."
                    ),
                    severity="warning",
                    relative_path=path,
                    line=0,
                    symbol_id=None,
                )
            )
        return findings


def _strongly_connected_components(
    adjacency: dict[str, set[str]],
) -> tuple[tuple[str, ...], ...]:
    neighbors = {
        vertex: tuple(sorted(targets)) for vertex, targets in adjacency.items()
    }
    reverse_neighbors: dict[str, list[str]] = {vertex: [] for vertex in adjacency}
    for vertex in sorted(neighbors):
        for target in neighbors[vertex]:
            reverse_neighbors[target].append(vertex)

    visited: set[str] = set()
    finish_order: list[str] = []
    for start in sorted(neighbors):
        if start in visited:
            continue
        visited.add(start)
        stack: list[tuple[str, int]] = [(start, 0)]
        while stack:
            vertex, next_index = stack[-1]
            if next_index < len(neighbors[vertex]):
                target = neighbors[vertex][next_index]
                stack[-1] = (vertex, next_index + 1)
                if target not in visited:
                    visited.add(target)
                    stack.append((target, 0))
                continue
            stack.pop()
            finish_order.append(vertex)

    assigned: set[str] = set()
    components: list[tuple[str, ...]] = []
    for start in reversed(finish_order):
        if start in assigned:
            continue
        assigned.add(start)
        component = []
        reverse_stack = [start]
        while reverse_stack:
            vertex = reverse_stack.pop()
            component.append(vertex)
            for source in reversed(reverse_neighbors[vertex]):
                if source not in assigned:
                    assigned.add(source)
                    reverse_stack.append(source)
        components.append(tuple(sorted(component)))
    return tuple(sorted(components))


class AnalysisEngine:
    """Run deterministic snapshot tools and isolate individual tool failures."""

    def __init__(self, tools: Iterable[AnalysisTool] | None = None) -> None:
        selected = (
            (ComplexityTool(), StructureTool(), DependencyTool())
            if tools is None
            else tuple(tools)
        )
        self._tools = tuple(sorted(selected, key=lambda tool: tool.tool_id))

    def analyze(self, snapshot: ProjectSnapshot) -> list[AnalysisFinding]:
        findings = []
        for tool in self._tools:
            try:
                tool_findings = list(tool.analyze(snapshot))
                for finding in tool_findings:
                    _validate_finding(finding)
                tool_findings.sort(key=_finding_key)
                findings.extend(tool_findings)
            except Exception as error:
                findings.append(
                    AnalysisFinding(
                        rule_id="analysis.tool_failure",
                        message=(
                            f"Analysis tool '{tool.tool_id}' failed with "
                            f"{type(error).__name__}; other tools continued."
                        ),
                        severity="error",
                        relative_path="",
                        line=0,
                        symbol_id=None,
                    )
                )
        return sorted(findings, key=_finding_key)
