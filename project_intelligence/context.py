"""Model-agnostic, deterministic context construction from retrieval values."""

from __future__ import annotations

from dataclasses import dataclass

from code_maintenance.domain import SymbolId

from .domain import ProjectIntelligenceError, RetrievalDocument
from .graph_expansion import ExpandedContextCandidate, GraphExpansionProvenance
from .hybrid import HybridHit, HybridRetrievalResult, symbol_id_key
from .index import RetrievalIndexIdentity


class ContextBuildError(ProjectIntelligenceError):
    """Raised when an authoritative ContextPackage cannot be constructed."""


@dataclass(frozen=True)
class RetrievalQuery:
    task_text: str
    top_k: int = 10
    context_budget: int = 8_000

    def __post_init__(self) -> None:
        if not isinstance(self.task_text, str):
            raise ValueError("task_text must be a string")
        if type(self.top_k) is not int or self.top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if type(self.context_budget) is not int or self.context_budget <= 0:
            raise ValueError("context_budget must be a positive integer")


@dataclass(frozen=True)
class ContextSnippet:
    symbol_id: SymbolId
    text: str
    hybrid_rank: int | None
    graph_provenance: tuple[GraphExpansionProvenance, ...]
    truncated: bool

    def __post_init__(self) -> None:
        if not isinstance(self.symbol_id, SymbolId):
            raise ContextBuildError("symbol_id must be a SymbolId")
        if not isinstance(self.text, str):
            raise ContextBuildError("text must be a string")
        if self.hybrid_rank is not None and (
            type(self.hybrid_rank) is not int or self.hybrid_rank <= 0
        ):
            raise ContextBuildError("hybrid_rank must be a positive integer")
        if type(self.graph_provenance) is not tuple or not all(
            isinstance(item, GraphExpansionProvenance)
            for item in self.graph_provenance
        ):
            raise ContextBuildError("graph_provenance must be an immutable tuple")
        if type(self.truncated) is not bool:
            raise ContextBuildError("truncated must be a bool")


@dataclass(frozen=True)
class ContextPackage:
    hits: tuple[HybridHit, ...]
    context_text: str
    index_identity: RetrievalIndexIdentity
    snippets: tuple[ContextSnippet, ...]
    graph_provenance: tuple[GraphExpansionProvenance, ...]
    truncated: bool
    degraded: bool
    degradation_reason: str | None
    failure_provenance: tuple[str, ...]
    budget: int
    budget_used: int
    budget_unit: str = "characters"

    def __post_init__(self) -> None:
        if not isinstance(self.index_identity, RetrievalIndexIdentity):
            raise ContextBuildError("index_identity must be a RetrievalIndexIdentity")
        if type(self.budget) is not int or self.budget <= 0:
            raise ContextBuildError("budget must be a positive integer")
        if type(self.budget_used) is not int or self.budget_used < 0:
            raise ContextBuildError("budget_used must be a non-negative integer")
        if self.budget_used != len(self.context_text) or self.budget_used > self.budget:
            raise ContextBuildError("context size does not match its character budget")
        if self.budget_unit != "characters":
            raise ContextBuildError("budget_unit must be 'characters'")
        if type(self.truncated) is not bool or type(self.degraded) is not bool:
            raise ContextBuildError("truncated and degraded must be bool values")
        if self.degraded != (self.degradation_reason is not None):
            raise ContextBuildError("degraded state and reason must agree")
        for name, expected_type in (
            ("hits", HybridHit),
            ("snippets", ContextSnippet),
            ("graph_provenance", GraphExpansionProvenance),
        ):
            value = getattr(self, name)
            if type(value) is not tuple or not all(
                isinstance(item, expected_type) for item in value
            ):
                raise ContextBuildError(f"{name} must be an immutable tuple")
        if type(self.failure_provenance) is not tuple or not all(
            isinstance(item, str) and item for item in self.failure_provenance
        ):
            raise ContextBuildError(
                "failure_provenance must be an immutable string tuple"
            )


def _graph_key(candidate: ExpandedContextCandidate) -> tuple:
    provenance = candidate.provenance
    seed_key = (
        symbol_id_key(provenance.seed_identity)
        if isinstance(provenance.seed_identity, SymbolId)
        else ("string", str(provenance.seed_identity))
    )
    node_key = (
        symbol_id_key(candidate.document.symbol_id)
        if candidate.document is not None
        else (candidate.node.kind.value, str(candidate.node.identity))
    )
    return (
        seed_key,
        provenance.hop,
        provenance.relation.value,
        provenance.direction.value,
        node_key,
    )


def _render(document: RetrievalDocument) -> str:
    return (
        f"[symbol] {document.qualified_name} "
        f"({document.relative_path}:{document.start_line}-{document.end_line})\n"
        f"{document.source_text}"
    )


class ContextBuilder:
    """Build character-budgeted source context without filesystem access."""

    def build(
        self,
        result: HybridRetrievalResult,
        index_identity: RetrievalIndexIdentity,
        budget: int,
    ) -> ContextPackage:
        if not isinstance(result, HybridRetrievalResult):
            raise ContextBuildError("result must be a HybridRetrievalResult")
        if not isinstance(index_identity, RetrievalIndexIdentity):
            raise ContextBuildError("index_identity must be a RetrievalIndexIdentity")
        if type(budget) is not int or budget <= 0:
            raise ContextBuildError("budget must be a positive integer")

        hits = tuple(sorted(result.hits, key=lambda hit: (hit.rank, symbol_id_key(hit.symbol_id))))
        if len({hit.symbol_id for hit in hits}) != len(hits):
            raise ContextBuildError("Hybrid hits contain duplicate SymbolId values")
        primary_ids = {hit.symbol_id for hit in hits}
        graph = tuple(sorted(result.graph_context, key=_graph_key))
        all_graph_provenance = tuple(candidate.provenance for candidate in graph)

        by_seed: dict[SymbolId, list[ExpandedContextCandidate]] = {}
        trailing: list[ExpandedContextCandidate] = []
        for candidate in graph:
            if candidate.document is None or candidate.document.symbol_id in primary_ids:
                continue
            seed = candidate.provenance.seed_identity
            if isinstance(seed, SymbolId) and seed in primary_ids:
                by_seed.setdefault(seed, []).append(candidate)
            else:
                trailing.append(candidate)

        planned: list[
            tuple[RetrievalDocument, int | None, tuple[GraphExpansionProvenance, ...]]
        ] = []
        seen: set[SymbolId] = set()
        for hit in hits:
            if hit.symbol_id not in seen:
                planned.append((hit.document, hit.rank, hit.graph_provenance))
                seen.add(hit.symbol_id)
            for candidate in by_seed.get(hit.symbol_id, ()):
                assert candidate.document is not None
                if candidate.document.symbol_id not in seen:
                    planned.append((candidate.document, None, (candidate.provenance,)))
                    seen.add(candidate.document.symbol_id)
        for candidate in trailing:
            assert candidate.document is not None
            if candidate.document.symbol_id not in seen:
                planned.append((candidate.document, None, (candidate.provenance,)))
                seen.add(candidate.document.symbol_id)

        pieces: list[str] = []
        snippets: list[ContextSnippet] = []
        truncated = False
        used = 0
        for document, rank, provenance in planned:
            rendered = _render(document)
            separator = "\n\n" if pieces else ""
            remaining = budget - used
            required = len(separator) + len(rendered)
            if required <= remaining:
                pieces.extend((separator, rendered) if separator else (rendered,))
                used += required
                snippets.append(
                    ContextSnippet(document.symbol_id, rendered, rank, provenance, False)
                )
                continue
            truncated = True
            available = remaining - len(separator)
            if available > 0:
                partial = rendered[:available]
                if separator:
                    pieces.extend((separator, partial))
                else:
                    pieces.append(partial)
                used += len(separator) + len(partial)
                snippets.append(
                    ContextSnippet(document.symbol_id, partial, rank, provenance, True)
                )
            break

        context_text = "".join(pieces)
        return ContextPackage(
            hits=hits,
            context_text=context_text,
            index_identity=index_identity,
            snippets=tuple(snippets),
            graph_provenance=all_graph_provenance,
            truncated=truncated,
            degraded=result.degraded,
            degradation_reason=result.degradation_reason,
            failure_provenance=result.failure_provenance,
            budget=budget,
            budget_used=len(context_text),
        )
