"""Bounded, deterministic expansion over the frozen project graph contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from code_maintenance.domain import SymbolId
from code_maintenance.graph import (
    GraphEdge,
    GraphNode,
    GraphNodeKind,
    GraphRelationKind,
    ProjectGraph,
    canonicalize_graph,
)

from .domain import RetrievalDocument


class GraphTraversalDirection(str, Enum):
    """Explicit traversal direction of one graph expansion step.

    ``FORWARD`` follows an edge from its source to its target; ``REVERSE``
    follows the same (unchanged) graph edge from its target back to its source.
    Direction is a property of retrieval provenance only: it never changes the
    frozen ``ProjectGraph`` relation kinds.
    """

    FORWARD = "forward"
    REVERSE = "reverse"


class GraphExpansionError(Exception):
    """Base error for graph expansion failures."""


class GraphSnapshotMismatchError(GraphExpansionError):
    """Raised when expansion is attempted with a graph from another snapshot."""


def _node_key(node: GraphNode) -> tuple:
    identity = node.identity
    if isinstance(identity, SymbolId):
        identity_key = (
            "symbol",
            identity.language,
            identity.relative_path,
            identity.qualified_name,
            identity.kind.value,
            identity.semantic_disambiguator or "",
            identity.fallback_line if identity.fallback_line is not None else -1,
        )
    else:
        identity_key = ("string", str(identity))
    return (node.kind.value, identity_key, node.label)


def _edge_key(edge: GraphEdge) -> tuple:
    return (_node_key(edge.source), _node_key(edge.target), edge.relation.value)


def _identity_key(identity: object) -> tuple:
    if isinstance(identity, SymbolId):
        return (
            "symbol",
            identity.language,
            identity.relative_path,
            identity.qualified_name,
            identity.kind.value,
            identity.semantic_disambiguator or "",
            identity.fallback_line if identity.fallback_line is not None else -1,
        )
    if isinstance(identity, str):
        return ("string", identity)
    raise GraphExpansionError("graph identity must be a string or SymbolId")


def _node_ref_key(node: GraphNode) -> tuple:
    return (node.kind.value, _identity_key(node.identity))


@dataclass(frozen=True)
class GraphExpansionConfig:
    """Immutable safety limits for graph-aware context expansion."""

    max_hops: int = 1
    relations: tuple[GraphRelationKind, ...] = (
        GraphRelationKind.CONTAINS,
        GraphRelationKind.IMPORTS,
    )
    relation_whitelist: tuple[GraphRelationKind, ...] | None = None
    max_expanded_per_seed: int = 5
    max_total_context_nodes: int = 30

    def __post_init__(self) -> None:
        if type(self.max_hops) is not int or self.max_hops < 0:
            raise ValueError("max_hops must be a non-negative integer")
        if type(self.max_expanded_per_seed) is not int or self.max_expanded_per_seed < 0:
            raise ValueError("max_expanded_per_seed must be a non-negative integer")
        if type(self.max_total_context_nodes) is not int or self.max_total_context_nodes < 0:
            raise ValueError("max_total_context_nodes must be a non-negative integer")
        raw_relations = self.relation_whitelist if self.relation_whitelist is not None else self.relations
        try:
            relations = tuple(
                item if isinstance(item, GraphRelationKind) else GraphRelationKind(item)
                for item in raw_relations
            )
        except (TypeError, ValueError) as error:
            raise ValueError("relations must contain supported graph relations") from error
        if any(relation not in (GraphRelationKind.CONTAINS, GraphRelationKind.IMPORTS) for relation in relations):
            raise ValueError("only CONTAINS and IMPORTS relations are supported")
        normalized = tuple(sorted(set(relations), key=lambda item: item.value))
        object.__setattr__(self, "relations", normalized)
        object.__setattr__(self, "relation_whitelist", normalized)


@dataclass(frozen=True)
class GraphExpansionProvenance:
    seed_identity: object
    relation: GraphRelationKind
    direction: GraphTraversalDirection
    hop: int
    node_identity: object

    @property
    def seed_id(self) -> object:
        return self.seed_identity

    @property
    def relation_kind(self) -> GraphRelationKind:
        return self.relation


@dataclass(frozen=True)
class ExpandedContextCandidate:
    node: GraphNode
    document: RetrievalDocument | None
    provenance: GraphExpansionProvenance

    @property
    def document_id(self) -> SymbolId | None:
        return self.document.symbol_id if self.document is not None else None


@dataclass(frozen=True)
class GraphExpansionResult:
    candidates: tuple[ExpandedContextCandidate, ...]

    @property
    def documents(self) -> tuple[RetrievalDocument, ...]:
        return tuple(
            candidate.document
            for candidate in self.candidates
            if candidate.document is not None
        )

    @property
    def expanded(self) -> tuple[ExpandedContextCandidate, ...]:
        return self.candidates

    @property
    def hits(self) -> tuple[ExpandedContextCandidate, ...]:
        return self.candidates


def _seed_identity(seed: object) -> object:
    if isinstance(seed, GraphNode):
        return seed.identity
    if isinstance(seed, SymbolId):
        return seed
    if isinstance(seed, str):
        return seed
    candidate = getattr(seed, "document_id", None)
    if isinstance(candidate, SymbolId):
        return candidate
    candidate = getattr(seed, "symbol_id", None)
    if isinstance(candidate, SymbolId):
        return candidate
    raise GraphExpansionError("seed must be a GraphNode, SymbolId, or retrieval hit")


def expand_graph(
    graph: ProjectGraph,
    seeds: Iterable[object],
    documents: Iterable[RetrievalDocument] = (),
    config: GraphExpansionConfig | None = None,
    *,
    expected_graph: ProjectGraph | None = None,
    allowed_signals: tuple[tuple[GraphRelationKind, GraphTraversalDirection], ...] | None = None,
) -> GraphExpansionResult:
    """Expand valid retrieval seeds with bounded, deterministic graph traversal.

    Edges are traversable in either direction: this permits a symbol seed to reach
    its containing file and a file seed to reach imported files/symbols.  Only the
    two frozen relation kinds are admitted.  Each expansion step records the
    traversal direction explicitly: following ``edge.source -> edge.target`` is
    ``GraphTraversalDirection.FORWARD`` and following ``edge.target ->
    edge.source`` is ``GraphTraversalDirection.REVERSE``.  Direction is retrieval
    provenance and never rewrites the underlying directed project graph.
    External or otherwise non-retrievable nodes are visited for traversal but are
    not fabricated as documents.
    """

    if not isinstance(graph, ProjectGraph):
        raise GraphExpansionError("graph must be a ProjectGraph")
    if expected_graph is not None and graph != expected_graph:
        if canonicalize_graph(graph) != canonicalize_graph(expected_graph):
            raise GraphSnapshotMismatchError("graph does not belong to the target snapshot")
    cfg = config if config is not None else GraphExpansionConfig()
    if not isinstance(cfg, GraphExpansionConfig):
        raise GraphExpansionError("config must be a GraphExpansionConfig")
    if allowed_signals is not None and (
        type(allowed_signals) is not tuple
        or not allowed_signals
        or any(
            type(pair) is not tuple or len(pair) != 2
            or not isinstance(pair[0], GraphRelationKind)
            or not isinstance(pair[1], GraphTraversalDirection)
            for pair in allowed_signals
        )
        or len(set(allowed_signals)) != len(allowed_signals)
    ):
        raise GraphExpansionError("allowed_signals must contain unique supported pairs")

    node_by_ref: dict[tuple, GraphNode] = {}
    nodes_by_identity: dict[tuple, list[GraphNode]] = {}
    for node in sorted(graph.nodes, key=_node_key):
        node_by_ref.setdefault(_node_ref_key(node), node)
        nodes_by_identity.setdefault(_identity_key(node.identity), []).append(node)
    adjacency: dict[tuple, list[tuple[GraphRelationKind, GraphTraversalDirection, GraphNode]]] = {}
    allowed = set(cfg.relations)
    selected_signals = None if allowed_signals is None else set(allowed_signals)
    for edge in sorted(graph.edges, key=_edge_key):
        if edge.relation not in allowed:
            continue
        forward = (edge.relation, GraphTraversalDirection.FORWARD)
        reverse = (edge.relation, GraphTraversalDirection.REVERSE)
        if selected_signals is None or forward in selected_signals:
            adjacency.setdefault(_node_ref_key(edge.source), []).append(
                (edge.relation, GraphTraversalDirection.FORWARD, edge.target)
            )
        if selected_signals is None or reverse in selected_signals:
            adjacency.setdefault(_node_ref_key(edge.target), []).append(
                (edge.relation, GraphTraversalDirection.REVERSE, edge.source)
            )
    for key in adjacency:
        adjacency[key].sort(
            key=lambda pair: (pair[0].value, pair[1].value, _node_key(pair[2]))
        )

    by_symbol: dict[SymbolId, RetrievalDocument] = {}
    for document in documents:
        if not isinstance(document, RetrievalDocument):
            raise GraphExpansionError("documents must contain RetrievalDocument values")
        if document.symbol_id in by_symbol:
            raise GraphExpansionError("duplicate retrieval document")
        by_symbol[document.symbol_id] = document

    seed_nodes: list[tuple[object, GraphNode]] = []
    seen_seeds: set[tuple] = set()
    for seed in seeds:
        identity = _seed_identity(seed)
        if isinstance(seed, GraphNode):
            node = node_by_ref.get(_node_ref_key(seed))
        else:
            candidates = nodes_by_identity.get(_identity_key(identity), ())
            if isinstance(identity, SymbolId):
                node = next((item for item in candidates if item.kind == GraphNodeKind.SYMBOL), None)
            else:
                node = next((item for item in candidates if item.kind == GraphNodeKind.FILE), None)
        if node is not None and _node_ref_key(node) not in seen_seeds:
            seen_seeds.add(_node_ref_key(node))
            seed_nodes.append((identity, node))
    seed_nodes.sort(key=lambda item: _node_key(item[1]))

    def candidate_document(node: GraphNode) -> tuple[bool, RetrievalDocument | None]:
        if node.kind == GraphNodeKind.SYMBOL and isinstance(node.identity, SymbolId):
            document = by_symbol.get(node.identity)
            return (document is not None, document)
        if node.kind in (GraphNodeKind.FILE, GraphNodeKind.PROJECT):
            return (True, None)
        return (False, None)

    selected: dict[tuple, ExpandedContextCandidate] = {}
    for seed_identity, seed_node in seed_nodes:
        queue: list[tuple[GraphNode, int]] = [(seed_node, 0)]
        visited = {_node_ref_key(seed_node)}
        per_seed: list[ExpandedContextCandidate] = []
        cursor = 0
        while cursor < len(queue):
            current, hop = queue[cursor]
            cursor += 1
            if hop >= cfg.max_hops:
                continue
            for relation, direction, neighbor in adjacency.get(_node_ref_key(current), ()):
                neighbor_key = _node_ref_key(neighbor)
                if neighbor_key in visited:
                    continue
                visited.add(neighbor_key)
                next_hop = hop + 1
                queue.append((neighbor, next_hop))
                supported, document = candidate_document(neighbor)
                if not supported:
                    continue
                candidate = ExpandedContextCandidate(
                    node=neighbor,
                    document=document,
                    provenance=GraphExpansionProvenance(
                        seed_identity=seed_identity,
                        relation=relation,
                        direction=direction,
                        hop=next_hop,
                        node_identity=neighbor.identity,
                    ),
                )
                per_seed.append(candidate)
        per_seed.sort(
            key=lambda item: (
                item.provenance.hop,
                _node_key(item.node),
                item.provenance.relation.value,
                item.provenance.direction.value,
            )
        )
        for candidate in per_seed[: cfg.max_expanded_per_seed]:
            selected.setdefault(_node_ref_key(candidate.node), candidate)
            if len(selected) >= cfg.max_total_context_nodes:
                break
        if len(selected) >= cfg.max_total_context_nodes:
            break

    ordered = tuple(
        sorted(
            selected.values(),
            key=lambda item: (
                item.provenance.hop,
                _node_key(item.node),
                _identity_key(item.provenance.seed_identity),
                item.provenance.relation.value,
                item.provenance.direction.value,
            ),
        )[: cfg.max_total_context_nodes]
    )
    return GraphExpansionResult(ordered)


class GraphExpander:
    """Small object facade for callers that prefer a configured expander."""

    def __init__(self, config: GraphExpansionConfig | None = None) -> None:
        self.config = config if config is not None else GraphExpansionConfig()

    def expand(
        self,
        graph: ProjectGraph,
        seeds: Iterable[object],
        documents: Iterable[RetrievalDocument] = (),
        *,
        expected_graph: ProjectGraph | None = None,
    ) -> GraphExpansionResult:
        return expand_graph(
            graph,
            seeds,
            documents,
            self.config,
            expected_graph=expected_graph,
        )
