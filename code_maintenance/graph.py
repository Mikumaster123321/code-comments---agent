from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .adapters import JavaAdapter, PythonAdapter
from .domain import ScanResult, SourceFile, Symbol, SymbolId, SymbolKind


class GraphNodeKind(str, Enum):
    PROJECT = "project"
    FILE = "file"
    SYMBOL = "symbol"
    EXTERNAL_MODULE = "external_module"


class GraphRelationKind(str, Enum):
    CONTAINS = "contains"
    IMPORTS = "imports"


@dataclass(frozen=True)
class GraphNode:
    kind: GraphNodeKind
    identity: str | SymbolId
    label: str


@dataclass(frozen=True)
class GraphEdge:
    source: GraphNode
    target: GraphNode
    relation: GraphRelationKind


def _identity_key(identity: str | SymbolId) -> str:
    return str(identity)


def _node_key(node: GraphNode) -> tuple[str, str, str]:
    return node.kind.value, _identity_key(node.identity), node.label


def _edge_key(edge: GraphEdge) -> tuple[str, tuple[str, str, str], tuple[str, str, str]]:
    return edge.relation.value, _node_key(edge.source), _node_key(edge.target)


@dataclass(frozen=True)
class ProjectGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def nodes_of_kind(self, kind: GraphNodeKind) -> tuple[GraphNode, ...]:
        return tuple(node for node in self.nodes if node.kind == kind)

    def edges_of_kind(self, relation: GraphRelationKind) -> tuple[GraphEdge, ...]:
        return tuple(edge for edge in self.edges if edge.relation == relation)


def _python_imports(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    targets = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            for alias in node.names:
                separator = "" if prefix.endswith(".") else "."
                targets.append(f"{prefix}{separator}{alias.name}")
    return tuple(sorted(set(targets)))


_JAVA_MASK_PATTERN = re.compile(
    r"//[^\n]*|/\*[\s\S]*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'"
)


def _mask_java_comments_and_strings(source: str) -> str:
    return _JAVA_MASK_PATTERN.sub(
        lambda match: "".join(
            "\n" if character == "\n" else " " for character in match.group()
        ),
        source,
    )


def _java_package(source: str) -> str:
    masked = _mask_java_comments_and_strings(source)
    match = re.search(
        r"\bpackage\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*;",
        masked,
    )
    return match.group(1) if match else ""


def _java_imports(source: str) -> tuple[str, ...]:
    masked = _mask_java_comments_and_strings(source)
    targets = re.findall(
        r"\bimport\s+(?:static\s+)?([A-Za-z_$][\w$]*(?:\.[A-Za-z_$*][\w$*]*)*)\s*;",
        masked,
    )
    return tuple(sorted(set(targets)))


def _python_module(relative_path: str) -> str:
    path = relative_path.removesuffix(".py")
    if path.endswith("/__init__"):
        path = path[: -len("/__init__")]
    return path.replace("/", ".")


def _resolve_python_target(target: str, importer_path: str) -> str:
    if not target.startswith("."):
        return target
    level = len(target) - len(target.lstrip("."))
    suffix = target[level:]
    importer_module = _python_module(importer_path)
    package_parts = importer_module.split(".")
    if not importer_path.endswith("/__init__.py"):
        package_parts = package_parts[:-1]
    trim = level - 1
    if trim > len(package_parts):
        return target
    base = package_parts[: len(package_parts) - trim] if trim else package_parts
    return ".".join([*base, *([suffix] if suffix else [])])


def _unique_lookup(pairs: Iterable[tuple[str, GraphNode]]) -> dict[str, GraphNode]:
    candidates: dict[str, list[GraphNode]] = {}
    for name, node in pairs:
        candidates.setdefault(name, []).append(node)
    return {name: nodes[0] for name, nodes in candidates.items() if len(nodes) == 1}


class ProjectGraphBuilder:
    """Build a deterministic, in-memory relationship graph from a scan result."""

    def __init__(self) -> None:
        self._adapters = {
            "python": PythonAdapter(),
            "java": JavaAdapter(),
        }

    def build(self, scan_result: ScanResult) -> ProjectGraph:
        nodes: set[GraphNode] = set()
        edges: set[GraphEdge] = set()
        project_node = GraphNode(
            GraphNodeKind.PROJECT,
            scan_result.project.id,
            scan_result.project.name,
        )
        nodes.add(project_node)

        root = Path(scan_result.project.root_path)
        file_nodes: dict[str, GraphNode] = {}
        languages: dict[str, str] = {}
        sources: dict[str, str] = {}
        symbols_by_file: dict[str, tuple[Symbol, ...]] = {}

        for project_file in scan_result.files:
            file_node = GraphNode(
                GraphNodeKind.FILE,
                project_file.relative_path,
                project_file.relative_path,
            )
            file_nodes[project_file.relative_path] = file_node
            languages[project_file.relative_path] = project_file.language
            nodes.add(file_node)
            edges.add(GraphEdge(project_node, file_node, GraphRelationKind.CONTAINS))

            adapter = self._adapters.get(project_file.language)
            if adapter is None:
                continue
            try:
                source = (root / project_file.relative_path).read_text(
                    encoding="utf-8", errors="replace"
                )
                source_file = SourceFile(
                    scan_result.project.id,
                    project_file.relative_path,
                    project_file.language,
                    source,
                )
                symbols = tuple(adapter.parse_symbols(source_file))
            except (OSError, SyntaxError):
                continue
            sources[project_file.relative_path] = source
            symbols_by_file[project_file.relative_path] = symbols
            symbol_nodes = self._add_symbols(file_node, symbols, nodes, edges)
            self._add_class_containment(symbols, symbol_nodes, edges)

        python_modules = _unique_lookup(
            (_python_module(path), node)
            for path, node in file_nodes.items()
            if path.endswith(".py")
        )
        java_types = self._java_type_lookup(file_nodes, sources, symbols_by_file)

        external_nodes: dict[str, GraphNode] = {}
        for relative_path in sorted(sources):
            file_node = file_nodes[relative_path]
            try:
                if languages[relative_path] == "python":
                    imports = _python_imports(sources[relative_path])
                    resolved = (
                        (
                            target,
                            python_modules.get(
                                _resolve_python_target(target, relative_path)
                            ),
                        )
                        for target in imports
                    )
                else:
                    imports = _java_imports(sources[relative_path])
                    resolved = ((target, java_types.get(target)) for target in imports)
            except SyntaxError:
                continue
            for target, internal_node in resolved:
                target_node = internal_node
                if target_node is None:
                    target_node = external_nodes.setdefault(
                        target,
                        GraphNode(GraphNodeKind.EXTERNAL_MODULE, target, target),
                    )
                    nodes.add(target_node)
                edges.add(GraphEdge(file_node, target_node, GraphRelationKind.IMPORTS))

        return ProjectGraph(
            nodes=tuple(sorted(nodes, key=_node_key)),
            edges=tuple(sorted(edges, key=_edge_key)),
        )

    @staticmethod
    def _add_symbols(
        file_node: GraphNode,
        symbols: tuple[Symbol, ...],
        nodes: set[GraphNode],
        edges: set[GraphEdge],
    ) -> dict[SymbolId, GraphNode]:
        symbol_nodes = {}
        for symbol in symbols:
            symbol_node = GraphNode(GraphNodeKind.SYMBOL, symbol.id, symbol.qualified_name)
            symbol_nodes[symbol.id] = symbol_node
            nodes.add(symbol_node)
            edges.add(GraphEdge(file_node, symbol_node, GraphRelationKind.CONTAINS))
        return symbol_nodes

    @staticmethod
    def _add_class_containment(
        symbols: tuple[Symbol, ...],
        symbol_nodes: dict[SymbolId, GraphNode],
        edges: set[GraphEdge],
    ) -> None:
        classes = {
            symbol.qualified_name: symbol_nodes[symbol.id]
            for symbol in symbols
            if symbol.kind == SymbolKind.CLASS
        }
        for symbol in symbols:
            parent_name = symbol.qualified_name.rpartition(".")[0]
            parent = classes.get(parent_name)
            if parent is not None:
                edges.add(
                    GraphEdge(parent, symbol_nodes[symbol.id], GraphRelationKind.CONTAINS)
                )

    @staticmethod
    def _java_type_lookup(
        file_nodes: dict[str, GraphNode],
        sources: dict[str, str],
        symbols_by_file: dict[str, tuple[Symbol, ...]],
    ) -> dict[str, GraphNode]:
        pairs = []
        for path, symbols in symbols_by_file.items():
            if not path.endswith(".java"):
                continue
            package = _java_package(sources[path])
            class_names = [
                symbol.qualified_name
                for symbol in symbols
                if symbol.kind == SymbolKind.CLASS
            ]
            if not class_names:
                class_names = [Path(path).stem]
            for class_name in class_names:
                qualified_name = f"{package}.{class_name}" if package else class_name
                pairs.append((qualified_name, file_nodes[path]))
        return _unique_lookup(pairs)
