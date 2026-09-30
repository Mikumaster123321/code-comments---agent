import ast
from pathlib import Path

import pytest

from code_maintenance import ProjectScanner, SnapshotBuilder
from project_intelligence import (
    ContextBuildError,
    ContextBuilder,
    ContextPackage,
    CorpusBuilder,
    DeterministicFakeEmbeddingProvider,
    HybridConfig,
    RetrievalConfig,
    RetrievalIndex,
    RetrievalQuery,
    RetrievalService,
)


class CountingProvider(DeterministicFakeEmbeddingProvider):
    def __init__(self, *, fail_query=False):
        super().__init__()
        self.query_calls = 0
        self.fail_query = fail_query

    def embed_query(self, text):
        self.query_calls += 1
        if self.fail_query:
            raise RuntimeError("offline")
        return super().embed_query(text)


def make_service(tmp_path, *, provider=None, config=None, context_builder=None):
    (tmp_path / "sample.py").write_text(
        "def alpha():\n    return 1\n\ndef beta():\n    return alpha()\n",
        encoding="utf-8",
    )
    snapshot = SnapshotBuilder().build(ProjectScanner().scan(tmp_path))
    docs = CorpusBuilder().build(tmp_path, snapshot)
    if provider is None:
        index = RetrievalIndex.build(snapshot, docs, RetrievalConfig())
        hybrid = config or HybridConfig(
            lexical_weight=1,
            semantic_weight=0,
            graph_enabled=False,
            graph_weight=0,
        )
    else:
        index = RetrievalIndex.build(
            snapshot,
            docs,
            RetrievalConfig(
                embedding_enabled=True, embedding_fingerprint=provider.fingerprint
            ),
            provider=provider,
        )
        hybrid = config or HybridConfig(graph_enabled=False, graph_weight=0)
    return RetrievalService(index, hybrid, context_builder=context_builder), docs


def test_retrieval_service_returns_context_package(tmp_path):
    service, docs = make_service(tmp_path)
    package = service.retrieve(RetrievalQuery("alpha", top_k=1, context_budget=500))
    assert isinstance(package, ContextPackage)
    assert len(package.hits) == 1
    assert package.hits[0].document in docs
    assert package.index_identity == service.index_identity


def test_empty_query_skips_embedding_provider(tmp_path):
    provider = CountingProvider()
    service, _ = make_service(tmp_path, provider=provider)
    package = service.retrieve(RetrievalQuery("  ", top_k=2, context_budget=100))
    assert package.hits == ()
    assert package.context_text == ""
    assert provider.query_calls == 0


def test_service_propagates_degraded_mode_and_provenance(tmp_path):
    provider = CountingProvider(fail_query=True)
    service, _ = make_service(tmp_path, provider=provider)
    package = service.retrieve(RetrievalQuery("alpha", context_budget=500))
    assert package.degraded is True
    assert package.failure_provenance == (
        "semantic_branch_failure:IndexBuildError",
    )
    assert package.hits


def test_query_top_k_controls_final_hits(tmp_path):
    provider = CountingProvider()
    service, _ = make_service(tmp_path, provider=provider)
    package = service.retrieve(RetrievalQuery("return", top_k=1, context_budget=500))
    assert len(package.hits) == 1


class ExplodingContextBuilder(ContextBuilder):
    def build(self, result, index_identity, budget):
        raise ContextBuildError("construction failed")


def test_context_failure_is_atomic_and_returns_no_partial_package(tmp_path):
    service, _ = make_service(tmp_path, context_builder=ExplodingContextBuilder())
    with pytest.raises(ContextBuildError):
        service.retrieve(RetrievalQuery("alpha"))


def test_service_requires_retrieval_query(tmp_path):
    service, _ = make_service(tmp_path)
    with pytest.raises(TypeError):
        service.retrieve("alpha")


def test_phase5_dependency_boundary():
    root = Path(__file__).parents[1] / "project_intelligence"
    banned = {
        "credits",
        "managed_access",
        "admin_operations",
        "providers",
        "gradio",
        "openai",
    }
    for name in ("hybrid.py", "context.py", "service.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports |= {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        }
        assert imports.isdisjoint(banned)
