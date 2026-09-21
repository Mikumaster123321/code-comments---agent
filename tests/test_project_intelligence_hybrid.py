import math
import random
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from code_maintenance import (
    GraphNode,
    GraphNodeKind,
    GraphRelationKind,
    ProjectGraph,
    ProjectSnapshot,
    SnapshotMetadata,
    SymbolId,
    SymbolKind,
    SymbolState,
)
from project_intelligence import (
    DeterministicFakeEmbeddingProvider,
    ExpandedContextCandidate,
    FusionStrategy,
    GraphExpansionProvenance,
    GraphExpansionResult,
    GraphTraversalDirection,
    HybridConfig,
    HybridRetrievalError,
    HybridRetriever,
    InvalidHybridConfigError,
    LexicalHit,
    RetrievalConfig,
    RetrievalDocument,
    RetrievalIndex,
    SemanticHit,
)


def document(name, *, path=None, disambiguator=None, fallback_line=None, source=None):
    relative_path = path or f"{name}.py"
    symbol_id = SymbolId(
        "python",
        relative_path,
        name,
        SymbolKind.FUNCTION,
        disambiguator,
        fallback_line,
    )
    return RetrievalDocument(
        symbol_id=symbol_id,
        language="python",
        relative_path=relative_path,
        qualified_name=name,
        kind=SymbolKind.FUNCTION,
        signature=f"def {name}()",
        source_text=source or f"def {name}():\n    return {name!r}",
        documentation_text=None,
        content_hash=f"hash-{name}-{disambiguator}-{fallback_line}",
        start_line=1,
        end_line=2,
    )


def make_index(documents, *, provider=None, graph=None):
    docs = tuple(documents)
    selected_graph = graph if graph is not None else ProjectGraph((), ())
    snapshot = ProjectSnapshot(
        project_id="project",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        files=(),
        symbols=tuple(SymbolState(item.symbol_id, item.content_hash) for item in docs),
        graph=selected_graph,
        content_hash="snapshot-hash",
        metadata=SnapshotMetadata(0, len(docs), len(selected_graph.nodes), len(selected_graph.edges)),
    )
    if provider is None:
        return RetrievalIndex.build(snapshot, docs, RetrievalConfig())
    config = RetrievalConfig(
        embedding_enabled=True, embedding_fingerprint=provider.fingerprint
    )
    return RetrievalIndex.build(snapshot, docs, config, provider=provider)


def graph_candidate(seed, target, *, relation, direction, hop=1):
    return ExpandedContextCandidate(
        node=GraphNode(GraphNodeKind.SYMBOL, target.symbol_id, target.qualified_name),
        document=target,
        provenance=GraphExpansionProvenance(
            seed_identity=seed.symbol_id,
            relation=relation,
            direction=direction,
            hop=hop,
            node_identity=target.symbol_id,
        ),
    )


def test_weighted_fusion_uses_independent_math_oracle():
    a, b, c = document("a"), document("b"), document("c")
    provider = DeterministicFakeEmbeddingProvider()
    index = make_index((a, b, c), provider=provider)
    config = HybridConfig(
        lexical_weight=2,
        semantic_weight=3,
        graph_weight=4,
        graph_enabled=True,
        top_k=3,
    )
    retriever = HybridRetriever(index, config)
    lexical = (LexicalHit(a, 4.0, 1), LexicalHit(b, 2.0, 2))
    semantic = (
        SemanticHit(b.symbol_id, b.content_hash, 0.6, 1, provider.fingerprint),
        SemanticHit(c.symbol_id, c.content_hash, -0.2, 2, provider.fingerprint),
    )
    graph = GraphExpansionResult(
        (
            graph_candidate(
                a,
                b,
                relation=GraphRelationKind.IMPORTS,
                direction=GraphTraversalDirection.FORWARD,
                hop=2,
            ),
        )
    )

    result = retriever.fuse(lexical, semantic, (a, b, c), graph_result=graph)
    by_id = {hit.symbol_id: hit for hit in result.hits}

    # Independent oracle: lexical max normalization => a=1, b=.5;
    # cosine mapping => b=.8, c=.4; graph IMPORTS/FORWARD/hop2 => .5.
    assert by_id[a.symbol_id].score == pytest.approx(2.0)
    assert by_id[b.symbol_id].score == pytest.approx(2 * 0.5 + 3 * 0.8 + 4 * 0.5)
    assert by_id[c.symbol_id].score == pytest.approx(3 * 0.4)
    assert result.hits[0].symbol_id == b.symbol_id
    assert by_id[b.symbol_id].lexical_score == 2.0
    assert by_id[b.symbol_id].semantic_rank == 1


def test_normalization_is_finite_empty_safe_and_missing_branches_are_zero():
    a, b = document("a"), document("b")
    provider = DeterministicFakeEmbeddingProvider()
    retriever = HybridRetriever(
        make_index((a, b), provider=provider),
        HybridConfig(graph_enabled=False, graph_weight=0),
    )
    result = retriever.fuse(
        (LexicalHit(a, 0.0, 1),),
        (SemanticHit(b.symbol_id, b.content_hash, -4.0, 1, provider.fingerprint),),
        (a, b),
    )
    by_id = {hit.symbol_id: hit for hit in result.hits}
    assert by_id[a.symbol_id].normalized_lexical_score == 0.0
    assert by_id[a.symbol_id].normalized_semantic_score == 0.0
    assert by_id[b.symbol_id].normalized_lexical_score == 0.0
    assert by_id[b.symbol_id].normalized_semantic_score == 0.0
    assert all(math.isfinite(hit.score) for hit in result.hits)


def test_candidate_union_and_symbol_id_dedup():
    a, b, c = document("a"), document("b"), document("c")
    provider = DeterministicFakeEmbeddingProvider()
    retriever = HybridRetriever(
        make_index((a, b, c), provider=provider),
        HybridConfig(graph_enabled=False, graph_weight=0),
    )
    result = retriever.fuse(
        (LexicalHit(a, 2, 1), LexicalHit(b, 1, 2)),
        (
            SemanticHit(b.symbol_id, b.content_hash, 0.5, 1, provider.fingerprint),
            SemanticHit(c.symbol_id, c.content_hash, 0.4, 2, provider.fingerprint),
        ),
        (c, b, a),
    )
    assert {hit.symbol_id for hit in result.hits} == {
        a.symbol_id,
        b.symbol_id,
        c.symbol_id,
    }
    assert len([hit for hit in result.hits if hit.symbol_id == b.symbol_id]) == 1


def test_tie_breaking_preserves_optional_field_types():
    none = document("same", path="same.py", disambiguator=None, fallback_line=None)
    empty = document("same", path="same.py", disambiguator="", fallback_line=-1)
    index = make_index((empty, none))
    retriever = HybridRetriever(
        index,
        HybridConfig(
            lexical_weight=1,
            semantic_weight=0,
            graph_enabled=False,
            graph_weight=0,
        ),
    )
    forward = retriever.fuse(
        (LexicalHit(empty, 1, 1), LexicalHit(none, 1, 2)), (), (empty, none)
    )
    reverse = retriever.fuse(
        (LexicalHit(none, 1, 2), LexicalHit(empty, 1, 1)), (), (none, empty)
    )
    assert [hit.symbol_id for hit in forward.hits] == [hit.symbol_id for hit in reverse.hits]
    assert len({hit.symbol_id for hit in forward.hits}) == 2


@pytest.mark.parametrize(
    "changes",
    (
        {"lexical_weight": True},
        {"semantic_weight": float("nan")},
        {"graph_weight": float("inf")},
        {"lexical_weight": -1},
        {"lexical_weight": 0, "semantic_weight": 0},
        {"top_k": True},
        {"top_k": 0},
        {"rrf_k": 0},
        {"fusion_strategy": "unknown"},
        {"graph_enabled": False, "graph_weight": 1},
    ),
)
def test_config_validation(changes):
    with pytest.raises(InvalidHybridConfigError):
        HybridConfig(**changes)


def test_config_and_hits_are_immutable():
    config = HybridConfig()
    with pytest.raises(FrozenInstanceError):
        config.top_k = 2
    doc = document("immutable")
    retriever = HybridRetriever(
        make_index((doc,)),
        HybridConfig(
            lexical_weight=1,
            semantic_weight=0,
            graph_enabled=False,
            graph_weight=0,
        ),
    )
    hit = retriever.retrieve("immutable").hits[0]
    with pytest.raises(FrozenInstanceError):
        hit.rank = 99


def test_lexical_only_semantic_only_and_hybrid_modes():
    a, b = document("alpha"), document("beta")
    lexical = HybridRetriever(
        make_index((a, b)),
        HybridConfig(
            lexical_weight=1,
            semantic_weight=0,
            graph_enabled=False,
            graph_weight=0,
        ),
    ).retrieve("alpha")
    provider = DeterministicFakeEmbeddingProvider()
    semantic_retriever = HybridRetriever(
        make_index((a, b), provider=provider),
        HybridConfig(
            lexical_weight=0,
            semantic_weight=1,
            graph_enabled=False,
            graph_weight=0,
        ),
    )
    semantic = semantic_retriever.retrieve("alpha")
    hybrid = HybridRetriever(
        make_index((a, b), provider=provider),
        HybridConfig(graph_enabled=False, graph_weight=0),
    ).retrieve("alpha")
    assert lexical.hits and all(hit.semantic_rank is None for hit in lexical.hits)
    assert semantic.hits and all(hit.lexical_rank is None for hit in semantic.hits)
    assert hybrid.hits and any(hit.lexical_rank is not None for hit in hybrid.hits)


def test_rrf_matches_independent_rank_oracle():
    a, b = document("a"), document("b")
    provider = DeterministicFakeEmbeddingProvider()
    retriever = HybridRetriever(
        make_index((a, b), provider=provider),
        HybridConfig(
            fusion_strategy=FusionStrategy.RRF,
            lexical_weight=2,
            semantic_weight=3,
            graph_enabled=False,
            graph_weight=0,
            rrf_k=10,
        ),
    )
    result = retriever.fuse(
        (LexicalHit(a, 99, 1), LexicalHit(b, 1, 2)),
        (
            SemanticHit(b.symbol_id, b.content_hash, 0.9, 1, provider.fingerprint),
            SemanticHit(a.symbol_id, a.content_hash, 0.1, 2, provider.fingerprint),
        ),
        (a, b),
    )
    by_id = {hit.symbol_id: hit for hit in result.hits}
    assert by_id[a.symbol_id].score == pytest.approx(2 / 11 + 3 / 12)
    assert by_id[b.symbol_id].score == pytest.approx(2 / 12 + 3 / 11)


def test_graph_signal_keeps_relation_direction_hop_and_raw_scores_isolated():
    seed, target = document("seed"), document("target")
    provider = DeterministicFakeEmbeddingProvider()
    retriever = HybridRetriever(
        make_index((seed, target), provider=provider),
        HybridConfig(graph_weight=2),
    )
    graph = GraphExpansionResult(
        (
            graph_candidate(
                seed,
                target,
                relation=GraphRelationKind.IMPORTS,
                direction=GraphTraversalDirection.REVERSE,
            ),
            graph_candidate(
                seed,
                target,
                relation=GraphRelationKind.CONTAINS,
                direction=GraphTraversalDirection.FORWARD,
                hop=2,
            ),
        )
    )
    result = retriever.fuse(
        (LexicalHit(target, 7.0, 1),),
        (SemanticHit(target.symbol_id, target.content_hash, 0.25, 1, provider.fingerprint),),
        (seed, target),
        graph_result=graph,
    )
    hit = result.hits[0]
    assert hit.lexical_score == 7.0
    assert hit.semantic_score == 0.25
    assert hit.graph_score == pytest.approx(0.8)
    assert {(item.relation, item.direction, item.hop) for item in hit.graph_provenance} == {
        (GraphRelationKind.IMPORTS, GraphTraversalDirection.REVERSE, 1),
        (GraphRelationKind.CONTAINS, GraphTraversalDirection.FORWARD, 2),
    }


class QueryFailingProvider(DeterministicFakeEmbeddingProvider):
    def __init__(self):
        super().__init__()
        self.query_calls = 0

    def embed_query(self, text):
        self.query_calls += 1
        raise RuntimeError("provider unavailable")


def test_semantic_failure_degrades_explicitly_to_lexical_only():
    provider = QueryFailingProvider()
    doc = document("alpha")
    result = HybridRetriever(
        make_index((doc,), provider=provider),
        HybridConfig(graph_enabled=False, graph_weight=0),
    ).retrieve("alpha")
    assert result.degraded is True
    assert result.degradation_reason == "semantic_branch_failure:IndexBuildError"
    assert result.failure_provenance == (result.degradation_reason,)
    assert result.hits[0].semantic_score is None


def test_semantic_only_failure_is_explicit_not_fake_success():
    provider = QueryFailingProvider()
    retriever = HybridRetriever(
        make_index((document("alpha"),), provider=provider),
        HybridConfig(
            lexical_weight=0,
            semantic_weight=1,
            graph_enabled=False,
            graph_weight=0,
        ),
    )
    with pytest.raises(HybridRetrievalError):
        retriever.retrieve("alpha")


def test_graph_failure_does_not_publish_a_partial_result(monkeypatch):
    doc = document("alpha")
    provider = DeterministicFakeEmbeddingProvider()
    index = make_index((doc,), provider=provider)
    retriever = HybridRetriever(index, HybridConfig())

    def fail(*args, **kwargs):
        raise RuntimeError("graph unavailable")

    monkeypatch.setattr(RetrievalIndex, "expand_graph", fail)
    with pytest.raises(RuntimeError, match="graph unavailable"):
        retriever.retrieve("alpha")


def test_top_k_and_empty_query_are_stable():
    docs = tuple(document(f"name{number}") for number in range(4))
    provider = DeterministicFakeEmbeddingProvider()
    retriever = HybridRetriever(
        make_index(docs, provider=provider),
        HybridConfig(graph_enabled=False, graph_weight=0),
    )
    assert len(retriever.retrieve("name", top_k=2).hits) <= 2
    assert retriever.retrieve("   ").hits == ()
    with pytest.raises(HybridRetrievalError):
        retriever.retrieve("name", top_k=True)


def test_100_input_permutations_have_one_deterministic_result():
    docs = tuple(document(name) for name in "abcd")
    provider = DeterministicFakeEmbeddingProvider()
    retriever = HybridRetriever(
        make_index(docs, provider=provider),
        HybridConfig(graph_enabled=False, graph_weight=0),
    )
    lexical = [LexicalHit(doc, 4 - index, index + 1) for index, doc in enumerate(docs)]
    semantic = [
        SemanticHit(doc.symbol_id, doc.content_hash, index / 10, index + 1, provider.fingerprint)
        for index, doc in enumerate(reversed(docs))
    ]
    graph = [
        graph_candidate(
            docs[0],
            docs[1],
            relation=GraphRelationKind.IMPORTS,
            direction=GraphTraversalDirection.FORWARD,
        ),
        graph_candidate(
            docs[2],
            docs[3],
            relation=GraphRelationKind.CONTAINS,
            direction=GraphTraversalDirection.REVERSE,
        ),
    ]

    def digest(result):
        return tuple(
            (
                hit.symbol_id,
                hit.rank,
                hit.lexical_score,
                hit.semantic_score,
                hit.normalized_lexical_score,
                hit.normalized_semantic_score,
                hit.score,
                tuple(hit.graph_provenance),
            )
            for hit in result.hits
        )

    expected = digest(
        retriever.fuse(
            lexical, semantic, docs, graph_result=GraphExpansionResult(tuple(graph))
        )
    )
    rng = random.Random(310)
    for _ in range(100):
        rng.shuffle(lexical)
        rng.shuffle(semantic)
        rng.shuffle(graph)
        shuffled_docs = list(docs)
        rng.shuffle(shuffled_docs)
        assert digest(
            retriever.fuse(
                lexical,
                semantic,
                shuffled_docs,
                graph_result=GraphExpansionResult(tuple(graph)),
            )
        ) == expected
