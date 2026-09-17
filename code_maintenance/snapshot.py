from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from .adapters import JavaAdapter, PythonAdapter
from .domain import ProjectFile, ScanResult, SourceFile, SymbolId
from .graph import (
    GraphEdge,
    GraphNode,
    GraphNodeKind,
    ProjectGraph,
    ProjectGraphBuilder,
    canonicalize_graph,
)


@dataclass(frozen=True)
class FileState:
    relative_path: str
    language: str
    content_hash: str


@dataclass(frozen=True)
class SymbolState:
    id: SymbolId
    content_hash: str


@dataclass(frozen=True)
class SnapshotMetadata:
    file_count: int
    symbol_count: int
    graph_node_count: int
    graph_edge_count: int


@dataclass(frozen=True)
class SnapshotDiff:
    added_files: tuple[str, ...]
    removed_files: tuple[str, ...]
    changed_files: tuple[str, ...]
    unchanged_files: tuple[str, ...]
    added_symbols: tuple[SymbolId, ...]
    removed_symbols: tuple[SymbolId, ...]
    changed_symbols: tuple[SymbolId, ...]
    unchanged_symbols: tuple[SymbolId, ...]


@dataclass(frozen=True)
class ProjectSnapshot:
    project_id: str
    created_at: datetime
    files: tuple[FileState, ...]
    symbols: tuple[SymbolState, ...]
    graph: ProjectGraph
    content_hash: str
    metadata: SnapshotMetadata

    def compare(self, newer: ProjectSnapshot) -> SnapshotDiff:
        return compare_snapshots(self, newer)

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "files": [
                {
                    "relative_path": file.relative_path,
                    "language": file.language,
                    "content_hash": file.content_hash,
                }
                for file in self.files
            ],
            "symbols": [
                {"id": _symbol_id_record(symbol.id), "content_hash": symbol.content_hash}
                for symbol in self.symbols
            ],
            "graph": _graph_record(self.graph),
            "content_hash": self.content_hash,
            "metadata": {
                "file_count": self.metadata.file_count,
                "symbol_count": self.metadata.symbol_count,
                "graph_node_count": self.metadata.graph_node_count,
                "graph_edge_count": self.metadata.graph_edge_count,
            },
        }


def _symbol_id_key(symbol_id: SymbolId) -> tuple[str, str, str, str, str, int]:
    return (
        symbol_id.language,
        symbol_id.relative_path,
        symbol_id.qualified_name,
        symbol_id.kind.value,
        symbol_id.semantic_disambiguator or "",
        symbol_id.fallback_line if symbol_id.fallback_line is not None else -1,
    )


def _symbol_id_record(symbol_id: SymbolId) -> dict:
    return {
        "language": symbol_id.language,
        "relative_path": symbol_id.relative_path,
        "qualified_name": symbol_id.qualified_name,
        "kind": symbol_id.kind.value,
        "semantic_disambiguator": symbol_id.semantic_disambiguator,
        "fallback_line": symbol_id.fallback_line,
    }


def _node_record(node: GraphNode) -> dict:
    identity = (
        {"type": "symbol", "value": _symbol_id_record(node.identity)}
        if isinstance(node.identity, SymbolId)
        else {"type": "string", "value": node.identity}
    )
    return {"kind": node.kind.value, "identity": identity, "label": node.label}


def _edge_record(edge: GraphEdge) -> dict:
    return {
        "source": _node_record(edge.source),
        "target": _node_record(edge.target),
        "relation": edge.relation.value,
    }


def _graph_record(graph: ProjectGraph) -> dict:
    return {
        "nodes": [_node_record(node) for node in graph.nodes],
        "edges": [_edge_record(edge) for edge in graph.edges],
    }


def _snapshot_hash(
    project_id: str,
    files: tuple[FileState, ...],
    symbols: tuple[SymbolState, ...],
    graph: ProjectGraph,
) -> str:
    state = {
        "schema": "project-snapshot-v1",
        "project_id": project_id,
        "files": [
            [file.relative_path, file.language, file.content_hash] for file in files
        ],
        "symbols": [
            [_symbol_id_record(symbol.id), symbol.content_hash] for symbol in symbols
        ],
        "graph": _graph_record(graph),
    }
    canonical = json.dumps(
        state, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


class SnapshotBuilder:
    """Build an immutable project-state value from one project scan."""

    def __init__(self) -> None:
        self._graph_builder = ProjectGraphBuilder()
        self._adapters = {
            "python": PythonAdapter(),
            "java": JavaAdapter(),
        }

    def build(
        self,
        scan_result: ScanResult,
        *,
        created_at: datetime | None = None,
        graph: ProjectGraph | None = None,
    ) -> ProjectSnapshot:
        files = tuple(
            sorted(
                (self._file_state(project_file) for project_file in scan_result.files),
                key=lambda state: state.relative_path,
            )
        )
        symbols = self._read_symbol_states(scan_result)
        normalized_graph = canonicalize_graph(
            graph if graph is not None else self._graph_builder.build(scan_result)
        )
        self._validate_graph(scan_result, normalized_graph)
        metadata = SnapshotMetadata(
            file_count=len(files),
            symbol_count=len(symbols),
            graph_node_count=len(normalized_graph.nodes),
            graph_edge_count=len(normalized_graph.edges),
        )
        return ProjectSnapshot(
            project_id=scan_result.project.id,
            created_at=created_at if created_at is not None else datetime.now(timezone.utc),
            files=files,
            symbols=symbols,
            graph=normalized_graph,
            content_hash=_snapshot_hash(
                scan_result.project.id, files, symbols, normalized_graph
            ),
            metadata=metadata,
        )

    @staticmethod
    def _file_state(project_file: ProjectFile) -> FileState:
        return FileState(
            relative_path=project_file.relative_path,
            language=project_file.language,
            content_hash=project_file.content_hash,
        )

    @staticmethod
    def _validate_graph(scan_result: ScanResult, graph: ProjectGraph) -> None:
        project_nodes = tuple(
            node for node in graph.nodes if node.kind == GraphNodeKind.PROJECT
        )
        if (
            len(project_nodes) != 1
            or project_nodes[0].identity != scan_result.project.id
        ):
            raise ValueError("graph must belong to the scanned project")

    def _read_symbol_states(self, scan_result: ScanResult) -> tuple[SymbolState, ...]:
        root = Path(scan_result.project.root_path)
        states = []
        for project_file in scan_result.files:
            adapter = self._adapters.get(project_file.language)
            if adapter is None:
                continue
            try:
                source_file = SourceFile(
                    project_id=scan_result.project.id,
                    relative_path=project_file.relative_path,
                    language=project_file.language,
                    content=(root / project_file.relative_path).read_text(
                        encoding="utf-8", errors="replace"
                    ),
                )
                states.extend(
                    SymbolState(symbol.id, symbol.content_hash)
                    for symbol in adapter.parse_symbols(source_file)
                )
            except (OSError, SyntaxError, ValueError):
                continue
        return tuple(sorted(states, key=lambda state: _symbol_id_key(state.id)))


def compare_snapshots(old: ProjectSnapshot, new: ProjectSnapshot) -> SnapshotDiff:
    if old.project_id != new.project_id:
        raise ValueError("snapshots must belong to the same project")

    old_files = {file.relative_path: file for file in old.files}
    new_files = {file.relative_path: file for file in new.files}
    old_paths = set(old_files)
    new_paths = set(new_files)
    shared_paths = old_paths & new_paths

    old_symbols = {symbol.id: symbol for symbol in old.symbols}
    new_symbols = {symbol.id: symbol for symbol in new.symbols}
    old_ids = set(old_symbols)
    new_ids = set(new_symbols)
    shared_ids = old_ids & new_ids

    return SnapshotDiff(
        added_files=tuple(sorted(new_paths - old_paths)),
        removed_files=tuple(sorted(old_paths - new_paths)),
        changed_files=tuple(
            sorted(path for path in shared_paths if old_files[path] != new_files[path])
        ),
        unchanged_files=tuple(
            sorted(path for path in shared_paths if old_files[path] == new_files[path])
        ),
        added_symbols=tuple(sorted(new_ids - old_ids, key=_symbol_id_key)),
        removed_symbols=tuple(sorted(old_ids - new_ids, key=_symbol_id_key)),
        changed_symbols=tuple(
            sorted(
                (
                    symbol_id
                    for symbol_id in shared_ids
                    if old_symbols[symbol_id] != new_symbols[symbol_id]
                ),
                key=_symbol_id_key,
            )
        ),
        unchanged_symbols=tuple(
            sorted(
                (
                    symbol_id
                    for symbol_id in shared_ids
                    if old_symbols[symbol_id] == new_symbols[symbol_id]
                ),
                key=_symbol_id_key,
            )
        ),
    )
