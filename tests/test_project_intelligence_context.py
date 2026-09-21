from dataclasses import FrozenInstanceError

import pytest

from code_maintenance import (
    GraphNode,
    GraphNodeKind,
    GraphRelationKind,
    SymbolId,
    SymbolKind,
)
from project_intelligence import (
    ContextBuildError,
    ContextBuilder,
    ContextPackage,
    ExpandedContextCandidate,
    FusionStrategy,
    GraphExpansionProvenance,
    GraphTraversalDirection,
    HybridHit,
    HybridRetrievalResult,
    RetrievalDocument,
    RetrievalIndexIdentity,
    RetrievalQuery,
)


def document(name, source=None):
    symbol_id = SymbolId("python", f"{name}.py", name, SymbolKind.FUNCTION)
    text = source if source is not None else f"def {name}():\n    return {name!r}"
    return RetrievalDocument(
        symbol_id,
        "python",
        f"{name}.py",
        name,
        SymbolKind.FUNCTION,
        None,
        text,
        None,
        f"hash-{name}",
        1,
        text.count("\n") + 1,
    )


def hit(doc, rank, score=None):
    value = float(rank if score is None else score)
    return HybridHit(
        document=doc,
        lexical_score=value,
        lexical_rank=rank,
        semantic_score=None,
        semantic_rank=None,
        normalized_lexical_score=1.0,
        normalized_semantic_score=0.0,
        graph_score=0.0,
        graph_provenance=(),
        fusion_strategy=FusionStrategy.WEIGHTED,
        lexical_weight=1.0,
        semantic_weight=0.0,
        graph_weight=0.0,
        score=value,
        rank=rank,
    )


def provenance(seed, target, *, direction=GraphTraversalDirection.FORWARD):
    return GraphExpansionProvenance(
        seed_identity=seed.symbol_id,
        relation=GraphRelationKind.IMPORTS,
        direction=direction,
        hop=1,
        node_identity=target.symbol_id,
    )


def candidate(seed, target, *, direction=GraphTraversalDirection.FORWARD):
    return ExpandedContextCandidate(
        GraphNode(GraphNodeKind.SYMBOL, target.symbol_id, target.qualified_name),
        target,
        provenance(seed, target, direction=direction),
    )


def result(hits, graph=(), *, degraded=False):
    reason = "semantic_branch_failure:IndexBuildError" if degraded else None
    return HybridRetrievalResult(
        tuple(hits),
        tuple(graph),
        degraded,
        reason,
        () if reason is None else (reason,),
        FusionStrategy.WEIGHTED,
    )


def identity():
    return RetrievalIndexIdentity("project", "snapshot", "config")


def test_context_dedup_and_hybrid_rank_ordering():
    a, b = document("a"), document("b")
    package = ContextBuilder().build(
        result((hit(b, 2), hit(a, 1)), (candidate(a, b),)), identity(), 10_000
    )
    assert [snippet.symbol_id for snippet in package.snippets] == [a.symbol_id, b.symbol_id]
    assert package.context_text.count(a.source_text) == 1
    assert package.context_text.count(b.source_text) == 1


def test_graph_only_source_is_adjacent_to_its_seed_and_direction_is_preserved():
    a, b, c = document("a"), document("b"), document("c")
    package = ContextBuilder().build(
        result(
            (hit(a, 1), hit(c, 2)),
            (candidate(a, b, direction=GraphTraversalDirection.REVERSE),),
        ),
        identity(),
        10_000,
    )
    assert [snippet.symbol_id for snippet in package.snippets] == [
        a.symbol_id,
        b.symbol_id,
        c.symbol_id,
    ]
    assert package.snippets[1].hybrid_rank is None
    assert package.snippets[1].graph_provenance[0].direction == GraphTraversalDirection.REVERSE


def test_budget_exact_fit_does_not_truncate():
    doc = document("exact")
    builder = ContextBuilder()
    full = builder.build(result((hit(doc, 1),)), identity(), 10_000)
    exact = builder.build(result((hit(doc, 1),)), identity(), len(full.context_text))
    assert exact.context_text == full.context_text
    assert exact.truncated is False
    assert exact.budget_used == exact.budget


def test_budget_overflow_and_single_oversized_snippet_are_observable():
    first = document("first", "x" * 100)
    second = document("second", "y" * 100)
    package = ContextBuilder().build(
        result((hit(first, 1), hit(second, 2))), identity(), 25
    )
    assert len(package.context_text) == 25
    assert package.truncated is True
    assert package.snippets[0].truncated is True
    assert package.snippets[0].text == package.context_text


def test_source_integrity_uses_retrieval_document_text():
    doc = document("source", "AUTHORITATIVE SNAPSHOT SOURCE")
    package = ContextBuilder().build(result((hit(doc, 1),)), identity(), 1_000)
    assert "AUTHORITATIVE SNAPSHOT SOURCE" in package.context_text


def test_structural_graph_context_keeps_provenance_without_fabricating_source():
    doc = document("seed")
    file_node = GraphNode(GraphNodeKind.FILE, "seed.py", "seed.py")
    graph_provenance = GraphExpansionProvenance(
        doc.symbol_id,
        GraphRelationKind.CONTAINS,
        GraphTraversalDirection.REVERSE,
        1,
        "seed.py",
    )
    structural = ExpandedContextCandidate(file_node, None, graph_provenance)
    package = ContextBuilder().build(
        result((hit(doc, 1),), (structural,)), identity(), 1_000
    )
    assert package.graph_provenance == (graph_provenance,)
    assert len(package.snippets) == 1


@pytest.mark.parametrize("budget", (0, -1, True, 1.5, "10"))
def test_budget_validation_is_strict(budget):
    with pytest.raises(ContextBuildError):
        ContextBuilder().build(result(()), identity(), budget)


@pytest.mark.parametrize(
    "changes",
    (
        {"top_k": 0},
        {"top_k": True},
        {"context_budget": 0},
        {"context_budget": 1.5},
        {"task_text": None},
    ),
)
def test_retrieval_query_validation(changes):
    with pytest.raises(ValueError):
        RetrievalQuery(**({"task_text": "task"} | changes))


def test_context_package_is_immutable_and_reports_degradation():
    doc = document("alpha")
    package = ContextBuilder().build(result((hit(doc, 1),), degraded=True), identity(), 1_000)
    assert package.degraded is True
    assert package.degradation_reason == "semantic_branch_failure:IndexBuildError"
    assert package.budget_unit == "characters"
    with pytest.raises(FrozenInstanceError):
        package.truncated = True
    query = RetrievalQuery("task")
    with pytest.raises(FrozenInstanceError):
        query.top_k = 1


def test_context_input_order_is_independent():
    a, b, c = document("a"), document("b"), document("c")
    builder = ContextBuilder()
    first = builder.build(
        result((hit(b, 2), hit(a, 1)), (candidate(a, c),)), identity(), 10_000
    )
    second = builder.build(
        result((hit(a, 1), hit(b, 2)), tuple(reversed((candidate(a, c),)))),
        identity(),
        10_000,
    )
    assert first == second
