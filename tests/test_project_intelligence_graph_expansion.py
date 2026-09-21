import random
from dataclasses import FrozenInstanceError, replace

import pytest

from code_maintenance import (
    GraphEdge,
    GraphNode,
    GraphNodeKind,
    GraphRelationKind,
    ProjectGraph,
    SymbolId,
    SymbolKind,
)
from project_intelligence import (
    GraphExpansionConfig,
    GraphExpansionProvenance,
    GraphSnapshotMismatchError,
    GraphTraversalDirection,
    expand_graph,
)
from project_intelligence.domain import RetrievalDocument


def document(path, name):
    symbol_id = SymbolId("python", path, name, SymbolKind.FUNCTION)
    return RetrievalDocument(
        symbol_id=symbol_id,
        language="python",
        relative_path=path,
        qualified_name=name,
        kind=SymbolKind.FUNCTION,
        signature=None,
        source_text=f"def {name}(): pass",
        documentation_text=None,
        content_hash=name,
        start_line=1,
        end_line=1,
    )


def test_expansion_is_bounded_deduplicated_and_explained():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    c = GraphNode(GraphNodeKind.FILE, "c.py", "c.py")
    graph = ProjectGraph(
        nodes=(c, b, a),
        edges=(
            GraphEdge(a, b, GraphRelationKind.IMPORTS),
            GraphEdge(b, a, GraphRelationKind.IMPORTS),
            GraphEdge(b, c, GraphRelationKind.IMPORTS),
            GraphEdge(a, b, GraphRelationKind.IMPORTS),
        ),
    )
    docs = (document("b.py", "b"), document("c.py", "c"))
    result = expand_graph(
        graph,
        (a,),
        docs,
        GraphExpansionConfig(max_hops=2, max_expanded_per_seed=10, max_total_context_nodes=10),
    )
    assert [candidate.node.identity for candidate in result.candidates] == ["b.py", "c.py"]
    assert all(candidate.document is None for candidate in result.candidates)
    assert result.candidates[0].provenance.hop == 1
    assert result.candidates[1].provenance.hop == 2


def test_relation_whitelist_budget_and_input_order_are_deterministic():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    c = GraphNode(GraphNodeKind.EXTERNAL_MODULE, "external", "external")
    graph_one = ProjectGraph(
        nodes=(a, b, c),
        edges=(
            GraphEdge(a, c, GraphRelationKind.IMPORTS),
            GraphEdge(a, b, GraphRelationKind.CONTAINS),
        ),
    )
    graph_two = ProjectGraph(
        nodes=(c, b, a),
        edges=tuple(reversed(graph_one.edges)),
    )
    docs = (document("b.py", "b"),)
    config = GraphExpansionConfig(relations=(GraphRelationKind.CONTAINS,), max_expanded_per_seed=1)
    first = expand_graph(graph_one, (a,), docs, config)
    second = expand_graph(graph_two, (a,), docs, config)
    assert first == second
    assert len(first.candidates) == 1
    assert first.candidates[0].provenance.relation == GraphRelationKind.CONTAINS
    assert expand_graph(graph_one, ("a.py",), docs, config) == first


def test_symbol_seed_maps_only_to_real_retrieval_documents():
    first = document("a.py", "first")
    second = document("a.py", "second")
    first_node = GraphNode(GraphNodeKind.SYMBOL, first.symbol_id, "first")
    second_node = GraphNode(GraphNodeKind.SYMBOL, second.symbol_id, "second")
    file_node = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    graph = ProjectGraph(
        nodes=(file_node, first_node, second_node),
        edges=(
            GraphEdge(file_node, first_node, GraphRelationKind.CONTAINS),
            GraphEdge(file_node, second_node, GraphRelationKind.CONTAINS),
        ),
    )
    result = expand_graph(graph, (first.symbol_id,), (first, second), GraphExpansionConfig(max_hops=2))
    assert result.candidates[0].node == file_node
    assert result.candidates[0].document is None
    assert result.candidates[1].document == second
    assert result.candidates[1].provenance.seed_identity == first.symbol_id
    assert result.candidates[1].provenance.hop == 2


def test_missing_symbol_document_and_external_module_are_not_fabricated():
    stale = document("stale.py", "stale")
    seed = GraphNode(GraphNodeKind.FILE, "seed.py", "seed.py")
    stale_node = GraphNode(GraphNodeKind.SYMBOL, stale.symbol_id, "stale")
    external = GraphNode(GraphNodeKind.EXTERNAL_MODULE, "outside", "outside")
    graph = ProjectGraph(
        nodes=(seed, stale_node, external),
        edges=(
            GraphEdge(seed, stale_node, GraphRelationKind.CONTAINS),
            GraphEdge(seed, external, GraphRelationKind.IMPORTS),
        ),
    )
    assert expand_graph(graph, (seed,), ()).candidates == ()


def test_per_seed_global_budget_and_shared_neighbor_suppression():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    shared = GraphNode(GraphNodeKind.FILE, "shared.py", "shared.py")
    other = GraphNode(GraphNodeKind.FILE, "other.py", "other.py")
    graph = ProjectGraph(
        nodes=(a, b, shared, other),
        edges=(
            GraphEdge(a, shared, GraphRelationKind.IMPORTS),
            GraphEdge(a, other, GraphRelationKind.IMPORTS),
            GraphEdge(b, shared, GraphRelationKind.IMPORTS),
            GraphEdge(b, other, GraphRelationKind.IMPORTS),
        ),
    )
    result = expand_graph(
        graph,
        (b, a),
        (),
        GraphExpansionConfig(max_expanded_per_seed=2, max_total_context_nodes=2),
    )
    assert len(result.candidates) == 2
    assert len({candidate.node.identity for candidate in result.candidates}) == 2
    assert result.candidates == expand_graph(graph, (a, b), (), GraphExpansionConfig(max_expanded_per_seed=2, max_total_context_nodes=2)).candidates


def test_hop_zero_and_zero_budgets_return_no_expansion():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    graph = ProjectGraph((a, b), (GraphEdge(a, b, GraphRelationKind.IMPORTS),))
    assert expand_graph(graph, (a,), (), GraphExpansionConfig(max_hops=0)).candidates == ()
    assert expand_graph(graph, (a,), (), GraphExpansionConfig(max_expanded_per_seed=0)).candidates == ()
    assert expand_graph(graph, (a,), (), GraphExpansionConfig(max_total_context_nodes=0)).candidates == ()


def test_graph_mismatch_fails_closed():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    first = ProjectGraph((a,), ())
    second = ProjectGraph((), ())
    with pytest.raises(GraphSnapshotMismatchError):
        expand_graph(first, (a,), (), expected_graph=second)


def test_100_graph_input_permutations_have_identical_output():
    nodes = tuple(GraphNode(GraphNodeKind.FILE, f"{number}.py", f"{number}.py") for number in range(7))
    edges = tuple(
        GraphEdge(nodes[number], nodes[number + 1], GraphRelationKind.IMPORTS)
        for number in range(len(nodes) - 1)
    )
    config = GraphExpansionConfig(max_hops=6, max_expanded_per_seed=10)
    expected = expand_graph(ProjectGraph(nodes, edges), (nodes[0],), (), config)
    randomizer = random.Random(310)
    for _ in range(100):
        shuffled_nodes = list(nodes)
        shuffled_edges = list(edges)
        randomizer.shuffle(shuffled_nodes)
        randomizer.shuffle(shuffled_edges)
        assert expand_graph(ProjectGraph(tuple(shuffled_nodes), tuple(shuffled_edges)), (nodes[0],), (), config) == expected


def test_imports_forward_direction_from_importer_seed():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    graph = ProjectGraph((a, b), (GraphEdge(a, b, GraphRelationKind.IMPORTS),))
    result = expand_graph(graph, (a,), ())
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.node == b
    assert candidate.provenance.seed_identity == "a.py"
    assert candidate.provenance.node_identity == "b.py"
    assert candidate.provenance.relation is GraphRelationKind.IMPORTS
    assert candidate.provenance.direction is GraphTraversalDirection.FORWARD
    assert candidate.provenance.hop == 1


def test_imports_reverse_direction_from_dependency_seed():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    graph = ProjectGraph((a, b), (GraphEdge(a, b, GraphRelationKind.IMPORTS),))
    result = expand_graph(graph, (b,), ())
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.node == a
    assert candidate.provenance.seed_identity == "b.py"
    assert candidate.provenance.node_identity == "a.py"
    assert candidate.provenance.relation is GraphRelationKind.IMPORTS
    assert candidate.provenance.direction is GraphTraversalDirection.REVERSE
    assert candidate.provenance.hop == 1


def test_contains_forward_direction_from_container_seed():
    file_node = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    alpha = document("a.py", "alpha")
    symbol_node = GraphNode(GraphNodeKind.SYMBOL, alpha.symbol_id, "alpha")
    graph = ProjectGraph(
        (file_node, symbol_node),
        (GraphEdge(file_node, symbol_node, GraphRelationKind.CONTAINS),),
    )
    result = expand_graph(graph, (file_node,), (alpha,))
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.node == symbol_node
    assert candidate.document == alpha
    assert candidate.provenance.seed_identity == "a.py"
    assert candidate.provenance.relation is GraphRelationKind.CONTAINS
    assert candidate.provenance.direction is GraphTraversalDirection.FORWARD


def test_contains_reverse_direction_from_contained_symbol_seed():
    file_node = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    alpha = document("a.py", "alpha")
    symbol_node = GraphNode(GraphNodeKind.SYMBOL, alpha.symbol_id, "alpha")
    graph = ProjectGraph(
        (file_node, symbol_node),
        (GraphEdge(file_node, symbol_node, GraphRelationKind.CONTAINS),),
    )
    result = expand_graph(graph, (alpha.symbol_id,), (alpha,))
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.node == file_node
    assert candidate.document is None
    assert candidate.provenance.seed_identity == alpha.symbol_id
    assert candidate.provenance.node_identity == "a.py"
    assert candidate.provenance.relation is GraphRelationKind.CONTAINS
    assert candidate.provenance.direction is GraphTraversalDirection.REVERSE


def test_direction_is_part_of_provenance_and_immutable():
    assert [member.value for member in GraphTraversalDirection] == ["forward", "reverse"]
    base = GraphExpansionProvenance(
        seed_identity="a.py",
        relation=GraphRelationKind.IMPORTS,
        direction=GraphTraversalDirection.FORWARD,
        hop=1,
        node_identity="b.py",
    )
    assert base.direction is GraphTraversalDirection.FORWARD
    assert base != replace(base, direction=GraphTraversalDirection.REVERSE)
    with pytest.raises(FrozenInstanceError):
        base.direction = GraphTraversalDirection.REVERSE


def test_shared_neighbor_direction_and_provenance_follow_the_winning_seed():
    forward_seed = GraphNode(GraphNodeKind.FILE, "z_forward.py", "z_forward.py")
    reverse_seed = GraphNode(GraphNodeKind.FILE, "a_reverse.py", "a_reverse.py")
    shared = GraphNode(GraphNodeKind.FILE, "shared.py", "shared.py")
    graph = ProjectGraph(
        (forward_seed, reverse_seed, shared),
        (
            GraphEdge(forward_seed, shared, GraphRelationKind.IMPORTS),
            GraphEdge(shared, reverse_seed, GraphRelationKind.IMPORTS),
        ),
    )
    budget = GraphExpansionConfig(max_expanded_per_seed=1, max_total_context_nodes=1)
    forward_only = expand_graph(graph, (forward_seed,), (), budget)
    reverse_only = expand_graph(graph, (reverse_seed,), (), budget)
    assert forward_only.candidates[0].node == shared
    assert forward_only.candidates[0].provenance.seed_identity == "z_forward.py"
    assert forward_only.candidates[0].provenance.direction is GraphTraversalDirection.FORWARD
    assert reverse_only.candidates[0].node == shared
    assert reverse_only.candidates[0].provenance.seed_identity == "a_reverse.py"
    assert reverse_only.candidates[0].provenance.direction is GraphTraversalDirection.REVERSE
    combined = expand_graph(graph, (reverse_seed, forward_seed), (), budget)
    assert combined.candidates[0].node == shared
    assert combined.candidates[0].provenance.seed_identity == "a_reverse.py"
    assert combined.candidates[0].provenance.direction is GraphTraversalDirection.REVERSE
    assert combined == expand_graph(graph, (forward_seed, reverse_seed), (), budget)


def test_direction_is_deterministic_under_graph_input_permutations():
    nodes = tuple(GraphNode(GraphNodeKind.FILE, f"{number}.py", f"{number}.py") for number in range(6))
    edges = tuple(
        GraphEdge(nodes[number], nodes[number + 1], GraphRelationKind.IMPORTS)
        for number in range(len(nodes) - 1)
    )
    config = GraphExpansionConfig(max_hops=2, max_expanded_per_seed=10, max_total_context_nodes=20)
    expected = expand_graph(ProjectGraph(nodes, edges), (nodes[2],), (), config)
    assert {
        candidate.provenance.direction for candidate in expected.candidates
    } == {GraphTraversalDirection.FORWARD, GraphTraversalDirection.REVERSE}
    randomizer = random.Random(410)
    for _ in range(100):
        shuffled_nodes = list(nodes)
        shuffled_edges = list(edges)
        randomizer.shuffle(shuffled_nodes)
        randomizer.shuffle(shuffled_edges)
        assert (
            expand_graph(
                ProjectGraph(tuple(shuffled_nodes), tuple(shuffled_edges)),
                (nodes[2],),
                (),
                config,
            )
            == expected
        )


def test_empty_seeds_empty_graph_and_duplicate_inputs_are_safe():
    empty = ProjectGraph((), ())
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    assert expand_graph(empty, (), ()).candidates == ()
    assert expand_graph(empty, (a,), ()).candidates == ()
    assert expand_graph(ProjectGraph((a,), ()), (), ()).candidates == ()
    single_edge = ProjectGraph((a, b), (GraphEdge(a, b, GraphRelationKind.IMPORTS),))
    duplicate_edge = ProjectGraph(
        (a, b),
        (
            GraphEdge(a, b, GraphRelationKind.IMPORTS),
            GraphEdge(a, b, GraphRelationKind.IMPORTS),
        ),
    )
    assert expand_graph(duplicate_edge, (a,), ()) == expand_graph(single_edge, (a,), ())
    assert expand_graph(single_edge, (a, a), ()) == expand_graph(single_edge, (a,), ())


def test_invalid_hop_and_budget_configs_are_rejected():
    for value in (-1, 1.0, "1", True, None):
        with pytest.raises(ValueError):
            GraphExpansionConfig(max_hops=value)
    for field_name in ("max_expanded_per_seed", "max_total_context_nodes"):
        for value in (-1, 1.0, "1"):
            with pytest.raises(ValueError):
                GraphExpansionConfig(**{field_name: value})


def test_expected_graph_with_equivalent_tuple_order_is_accepted():
    a = GraphNode(GraphNodeKind.FILE, "a.py", "a.py")
    b = GraphNode(GraphNodeKind.FILE, "b.py", "b.py")
    edges = (GraphEdge(a, b, GraphRelationKind.IMPORTS),)
    graph = ProjectGraph((a, b), edges)
    reordered = ProjectGraph((b, a), tuple(reversed(edges)))
    result = expand_graph(graph, (a,), (), expected_graph=reordered)
    assert result.candidates[0].node == b
    with pytest.raises(GraphSnapshotMismatchError):
        expand_graph(graph, (a,), (), expected_graph=ProjectGraph((a, b), ()))
