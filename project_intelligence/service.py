"""Stable Phase 5 facade for future V3.2 consumers."""

from __future__ import annotations

from .context import ContextBuilder, ContextPackage, RetrievalQuery
from .hybrid import HybridConfig, HybridRetriever, HybridRetrievalResult
from .index import RetrievalIndex


class RetrievalService:
    """The recommended retrieval/context entry point for future Agent code."""

    def __init__(
        self,
        index: RetrievalIndex,
        hybrid_config: HybridConfig | None = None,
        *,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        if not isinstance(index, RetrievalIndex):
            raise TypeError("index must be a RetrievalIndex")
        self._index = index
        self._hybrid = HybridRetriever(index, hybrid_config)
        self._context_builder = (
            context_builder if context_builder is not None else ContextBuilder()
        )
        if not isinstance(self._context_builder, ContextBuilder):
            raise TypeError("context_builder must be a ContextBuilder")

    @property
    def index_identity(self):
        return self._index.identity

    @property
    def hybrid_config(self) -> HybridConfig:
        return self._hybrid.config

    def retrieve(self, query: RetrievalQuery) -> ContextPackage:
        if not isinstance(query, RetrievalQuery):
            raise TypeError("query must be a RetrievalQuery")
        if not query.task_text.strip():
            result = HybridRetrievalResult(
                hits=(),
                graph_context=(),
                degraded=False,
                degradation_reason=None,
                failure_provenance=(),
                fusion_strategy=self._hybrid.config.fusion_strategy,
            )
        else:
            result = self._hybrid.retrieve(query.task_text, query.top_k)
        return self._context_builder.build(
            result, self._index.identity, query.context_budget
        )
