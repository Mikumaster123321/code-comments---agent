"""Frozen benchmark data binding and narrow production retrieval strategy."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping

from code_maintenance import SymbolId
from code_maintenance.graph import GraphRelationKind
from code_maintenance.scanner import ProjectScanner
from code_maintenance.snapshot import ProjectSnapshot, SnapshotBuilder, decode_source_bytes
from project_intelligence import (
    ContextBuilder, CorpusBuilder, HybridConfig, HybridRetriever,
    LocalE5EmbeddingProvider, RetrievalConfig, RetrievalDocument, RetrievalIndex,
)
from project_intelligence.embedding import EmbeddingProvider
from project_intelligence.graph_expansion import (
    GraphExpansionResult, GraphTraversalDirection, expand_graph,
)
from project_intelligence.hybrid import FusionStrategy, symbol_id_key

from .baselines import (
    AuthoritativeCandidate, DatasetEvidenceRegistry, ExperimentalBM25Index,
    FileSource, RuntimeDatasetFile, build_chunk_documents, build_file_documents,
    serialize_candidate_identity,
)
from .config import (
    BenchmarkConfig, ConfigValidationError, FROZEN_MATRIX_IDS,
    GraphExperimentConfig, HybridExperimentConfig, Population, RetrievalUnit,
    RunKind, SemanticMode, Strategy,
)
from .eligibility import ValidatedExecutionInputs, is_validator_issued
from .runner import BenchmarkRunner, BenchmarkRunResult, GraphProvenanceRecord, StrategyHit, StrategyResult
from .schemas import DatasetManifest, QueryRecord, RunMetadata
from .serialization import canonical_hash, normalize_lf, sha256_hex


class ExecutionWiringError(ValueError):
    pass


_MATRIX = {
    "RQ1-FILE": (RetrievalUnit.FILE, Strategy.LEXICAL, False, None),
    "RQ1-SYMBOL": (RetrievalUnit.SYMBOL, Strategy.LEXICAL, False, None),
    "RQ1-CHUNK": (RetrievalUnit.CHUNK, Strategy.LEXICAL, False, None),
    "RQ2-BM25": (RetrievalUnit.SYMBOL, Strategy.LEXICAL, False, None),
    "RQ2-E5": (RetrievalUnit.SYMBOL, Strategy.EMBEDDING, False, None),
    "RQ3-GRAPH-OFF": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, False, None),
    "RQ3-GRAPH-ON": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, True, None),
    "RQ3-CONTAINS-FORWARD": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, True, ("contains", "forward")),
    "RQ3-CONTAINS-REVERSE": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, True, ("contains", "reverse")),
    "RQ3-IMPORTS-FORWARD": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, True, ("imports", "forward")),
    "RQ3-IMPORTS-REVERSE": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, True, ("imports", "reverse")),
    "RQ4-LEXICAL": (RetrievalUnit.SYMBOL, Strategy.LEXICAL, False, None),
    "RQ4-EMBEDDING": (RetrievalUnit.SYMBOL, Strategy.EMBEDDING, False, None),
    "RQ4-HYBRID-NO-GRAPH": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, False, None),
    "RQ4-HYBRID-GRAPH": (RetrievalUnit.SYMBOL, Strategy.WEIGHTED, True, None),
    "RRF-HYBRID-NO-GRAPH": (RetrievalUnit.SYMBOL, Strategy.RRF, False, None),
    "RRF-HYBRID-GRAPH": (RetrievalUnit.SYMBOL, Strategy.RRF, True, None),
}
if tuple(_MATRIX) != FROZEN_MATRIX_IDS:
    raise RuntimeError("benchmark execution matrix differs from frozen configuration catalog")


def executable_config(template: BenchmarkConfig, matrix_run_id: str) -> BenchmarkConfig:
    """Resolve an existing frozen matrix row using the template's authority identities."""
    if (type(template) is not BenchmarkConfig or template.run_kind is RunKind.SYNTHETIC
            or matrix_run_id not in _MATRIX):
        raise ConfigValidationError("unknown frozen matrix configuration")
    unit, strategy, graph_on, pair = _MATRIX[matrix_run_id]
    signals = GraphExperimentConfig().signals if pair is None else (pair,)
    graph = GraphExperimentConfig(enabled=graph_on, signals=signals)
    semantic = strategy in {Strategy.EMBEDDING, Strategy.WEIGHTED, Strategy.RRF}
    lexical_weight = 0.0 if strategy is Strategy.EMBEDDING else 1.0
    semantic_weight = 1.0 if semantic else 0.0
    return replace(
        template, matrix_run_id=matrix_run_id, retrieval_unit=unit, strategy=strategy,
        graph=graph, hybrid=HybridExperimentConfig(
            lexical_weight=lexical_weight, semantic_weight=semantic_weight,
            graph_weight=0.25 if graph_on else 0.0,
        ),
        semantic_mode=SemanticMode.REAL_E5 if semantic else SemanticMode.NONE,
        embedding_fingerprint=template.embedding_fingerprint if semantic else None,
    )


@dataclass(frozen=True)
class BoundProject:
    snapshot: ProjectSnapshot
    documents: tuple[RetrievalDocument, ...]
    files: tuple[RuntimeDatasetFile, ...]


class _NamedScanner:
    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self._scanner = ProjectScanner()

    def scan(self, root):
        scan = self._scanner.scan(root)
        return replace(scan, project=replace(scan.project, id=self._project_id))


def _symbol_span(document: RetrievalDocument, source: str) -> tuple[int, int]:
    lines = source.split("\n")
    start = sum(len(line) + 1 for line in lines[: document.start_line - 1])
    end = start + len("\n".join(lines[document.start_line - 1:document.end_line]))
    if source[start:end] != document.source_text:
        raise ExecutionWiringError("symbol source span differs from frozen corpus")
    return start, end


def bind_project(project, source_bytes: Mapping[str, bytes]) -> BoundProject:
    """Rebuild production Snapshot/Corpus from exactly the manifest's verified files."""
    expected = {item.relative_path: item for item in project.files}
    if set(source_bytes) != set(expected):
        raise ExecutionWiringError("source path set differs from frozen manifest")
    for path, raw in source_bytes.items():
        if type(raw) is not bytes or sha256_hex(raw) != expected[path].content_hash:
            raise ExecutionWiringError("source bytes differ from frozen manifest")
    with TemporaryDirectory(prefix="benchmark-source-") as temporary:
        root = Path(temporary)
        for path, raw in sorted(source_bytes.items()):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        scanner = _NamedScanner(project.project_id)
        snapshot = SnapshotBuilder().build(scanner.scan(root))
        documents = CorpusBuilder(scanner=scanner).build(root, snapshot)
    if len(documents) != project.symbol_count or len(snapshot.files) != project.file_count:
        raise ExecutionWiringError("rebuilt corpus population differs from frozen manifest")
    files = tuple(
        RuntimeDatasetFile(project.project_id, path,
                           normalize_lf(decode_source_bytes(raw)), expected[path].content_hash)
        for path, raw in sorted(source_bytes.items())
    )
    return BoundProject(snapshot, documents, files)


def _frozen_source_bytes(repository_root: Path, project) -> dict[str, bytes]:
    fixtures = {
        "fixture-py-route-ledger": "route-ledger",
        "fixture-py-intake-queue": "intake-queue",
        "fixture-java-desk-queue": "desk-queue",
    }
    result = {}
    for item in project.files:
        if project.source_kind == "self_repository":
            revision = project.source_revision
            if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
                raise ExecutionWiringError("frozen source revision is invalid")
            command = ["git", "-C", str(repository_root), "show", f"{revision}:{item.relative_path}"]
            process = subprocess.run(command, capture_output=True, check=False)
            if process.returncode:
                raise ExecutionWiringError("frozen source blob is unavailable")
            raw = process.stdout
        else:
            name = fixtures.get(project.project_id)
            if name is None:
                raise ExecutionWiringError("unknown frozen fixture project")
            raw = (repository_root / "docs/experiments/datasets/v1/fixtures" / name / item.relative_path).read_bytes()
        result[item.relative_path] = raw
    return result


def bind_frozen_dataset(repository_root: str | Path, dataset: DatasetManifest):
    """Use only manifest-listed frozen blobs; never scan the current checkout."""
    root = Path(repository_root).resolve()
    projects = {
        project.project_id: bind_project(project, _frozen_source_bytes(root, project))
        for project in dataset.projects
    }
    return projects, registry_from_bound_projects(dataset, projects)


def registry_from_bound_projects(dataset: DatasetManifest, projects: Mapping[str, BoundProject]) -> DatasetEvidenceRegistry:
    if set(projects) != {project.project_id for project in dataset.projects}:
        raise ExecutionWiringError("bound project set differs from dataset manifest")
    files = tuple(item for project in projects.values() for item in project.files)
    candidates: list[AuthoritativeCandidate] = []
    for project_id, bound in projects.items():
        sources = tuple(FileSource(item.relative_path, item.source_text) for item in bound.files)
        hashes = {item.relative_path: item.content_hash for item in bound.files}
        for item in build_file_documents(sources):
            candidates.append(AuthoritativeCandidate(project_id, RetrievalUnit.FILE,
                                                     item.identity, hashes[item.relative_path]))
        for item in build_chunk_documents(sources):
            candidates.append(AuthoritativeCandidate(project_id, RetrievalUnit.CHUNK,
                                                     item.identity, hashes[item.relative_path]))
        source_by_path = {item.relative_path: item.source_text for item in bound.files}
        for document in bound.documents:
            start, end = _symbol_span(document, source_by_path[document.relative_path])
            candidates.append(AuthoritativeCandidate(
                project_id, RetrievalUnit.SYMBOL, document.symbol_id,
                hashes[document.relative_path], start, end,
            ))
    return DatasetEvidenceRegistry(dataset, files, candidates)


class ProductionBenchmarkStrategy:
    """Normalize production retrieval hits for the unchanged BenchmarkRunner."""

    def __init__(self, config: BenchmarkConfig, projects: Mapping[str, BoundProject],
                 registry: DatasetEvidenceRegistry, queries: tuple[QueryRecord, ...],
                 provider: EmbeddingProvider | None = None,
                 validated_inputs: ValidatedExecutionInputs | None = None) -> None:
        if type(config) is not BenchmarkConfig or not isinstance(registry, DatasetEvidenceRegistry):
            raise ExecutionWiringError("invalid production benchmark inputs")
        if (config.dataset_hash != registry.manifest.dataset_hash
                or config.dataset_version != registry.manifest.version):
            raise ExecutionWiringError("config dataset differs from bound frozen corpus")
        if (type(queries) is not tuple or not queries
                or not all(type(item) is QueryRecord for item in queries)
                or len({item.query_id for item in queries}) != len(queries)
                or canonical_hash([item.to_record() for item in sorted(queries, key=lambda x: x.query_id)])
                != config.query_set_hash):
            raise ExecutionWiringError("query records differ from frozen query identity")
        if config.run_kind is not RunKind.SYNTHETIC:
            config._validate_formal_matrix_binding()
            if (not is_validator_issued(validated_inputs)
                    or validated_inputs.config_identity != config.identity_hash
                    or validated_inputs.purpose is not config.run_kind):
                raise ExecutionWiringError("formal strategy requires validated authority")
        if config.population is Population.ENGLISH_TEST and config.run_kind is not RunKind.FORMAL:
            raise ExecutionWiringError("English Test execution requires formal eligibility")
        if config.semantic_required:
            if provider is None and config.semantic_mode is SemanticMode.REAL_E5:
                provider = LocalE5EmbeddingProvider(local_files_only=True)
            if provider is None or provider.fingerprint != config.embedding_fingerprint:
                raise ExecutionWiringError("embedding provider differs from frozen config")
            if config.semantic_mode is SemanticMode.REAL_E5 and (
                type(provider) is not LocalE5EmbeddingProvider
                or provider.device != "cpu"
                or provider.fingerprint.model_repository != "intfloat/multilingual-e5-base"
                or provider._local_files_only is not True
            ):
                raise ExecutionWiringError("real E5 execution requires the pinned local CPU adapter")
        elif provider is not None:
            raise ExecutionWiringError("lexical configuration cannot receive an embedding provider")
        self._config = config
        self._projects = dict(projects)
        self._registry = registry
        self._queries = {item.query_id: item for item in queries}
        self._provider = provider
        self._indices = {}
        self._baselines = {}
        self._document_diagnostics = {}
        self.context_packages = {}
        for project_id, bound in sorted(self._projects.items()):
            if config.retrieval_unit is RetrievalUnit.SYMBOL:
                retrieval_config = RetrievalConfig(
                    embedding_enabled=config.semantic_required,
                    embedding_fingerprint=config.embedding_fingerprint,
                )
                self._indices[project_id] = RetrievalIndex.build(
                    bound.snapshot, bound.documents, retrieval_config, provider=provider,
                )
                if type(provider) is LocalE5EmbeddingProvider:
                    diagnostics = provider.last_diagnostics
                    documents = self._indices[project_id].documents
                    if len(diagnostics) != len(documents):
                        raise ExecutionWiringError("real E5 document diagnostics are incomplete")
                    self._document_diagnostics[project_id] = tuple(
                        self._diagnostic(serialize_candidate_identity(document.symbol_id),
                                         "document", item)
                        for document, item in zip(documents, diagnostics)
                    )
            else:
                sources = tuple(FileSource(item.relative_path, item.source_text) for item in bound.files)
                documents = (build_file_documents(sources, config.file)
                             if config.retrieval_unit is RetrievalUnit.FILE else
                             build_chunk_documents(sources, config.chunk))
                self._baselines[project_id] = ExperimentalBM25Index(documents)
            actual = set(self._registry.candidates_for(project_id, config.retrieval_unit))
            indexed = (set(item.symbol_id for item in bound.documents)
                       if config.retrieval_unit is RetrievalUnit.SYMBOL else
                       set(self._baselines[project_id].candidate_identities))
            if actual != indexed:
                raise ExecutionWiringError("index candidates differ from authoritative registry")
        if set(self._projects) != {item.project_id for item in registry.manifest.projects}:
            raise ExecutionWiringError("project population differs from dataset manifest")
        self._index_identity = canonical_hash({
            "schema": "benchmark-production-index-v1", "config": config.identity_hash,
            "projects": [
                [project_id, bound.snapshot.content_hash,
                 self._indices[project_id].identity.identity_hash if project_id in self._indices else None]
                for project_id, bound in sorted(self._projects.items())
            ],
        })

    @property
    def semantic_mode(self) -> SemanticMode:
        return self._config.semantic_mode

    @property
    def embedding_fingerprint(self):
        return self._config.embedding_fingerprint

    @property
    def index_identity(self) -> str:
        return self._index_identity

    def retrieve(self, query: QueryRecord, config: BenchmarkConfig) -> StrategyResult:
        if (config != self._config or query.split != config.population.value
                or self._queries.get(query.query_id) != query):
            raise ExecutionWiringError("query split or configuration differs from bound execution")
        if query.dataset_id != self._registry.manifest.dataset_id or query.project_id not in self._projects:
            raise ExecutionWiringError("query lies outside frozen dataset")
        if config.population is Population.ENGLISH_TEST and config.run_kind is not RunKind.FORMAL:
            raise ExecutionWiringError("English Test requires formal execution")
        if config.retrieval_unit is not RetrievalUnit.SYMBOL:
            hits = self._baselines[query.project_id].search(query.query_text, config.top_k)
            maximum = max((item.score for item in hits), default=0.0)
            return StrategyResult(tuple(
                StrategyHit(item.identity, item.relative_path, item.rank,
                            start_offset=item.identity.start_offset if config.retrieval_unit is RetrievalUnit.CHUNK else None,
                            end_offset=item.identity.end_offset if config.retrieval_unit is RetrievalUnit.CHUNK else None,
                            raw_lexical_score=item.score,
                            normalized_lexical_score=item.score / maximum if maximum else 0.0,
                            final_score=item.score)
                for item in hits
            ))
        index = self._indices[query.project_id]
        if config.strategy is Strategy.LEXICAL:
            hits = index.lexical_search(query.query_text, config.top_k)
            maximum = max((item.score for item in hits), default=0.0)
            return StrategyResult(tuple(self._symbol_hit(
                query.project_id, item.document, item.rank,
                raw_lexical_score=item.score,
                normalized_lexical_score=item.score / maximum if maximum else 0.0,
                final_score=item.score,
            ) for item in hits))
        if config.strategy is Strategy.EMBEDDING:
            hits = index.semantic_search(query.query_text, config.top_k)
            return StrategyResult(tuple(self._symbol_hit(
                query.project_id, next(doc for doc in index.documents if doc.symbol_id == item.symbol_id),
                item.rank, raw_semantic_score=item.score,
                normalized_semantic_score=(max(-1.0, min(1.0, item.score)) + 1.0) / 2.0,
                final_score=item.score,
            ) for item in hits), token_diagnostics=self._query_diagnostics(query))
        fusion = FusionStrategy.RRF if config.strategy is Strategy.RRF else FusionStrategy.WEIGHTED
        retriever = HybridRetriever(index, HybridConfig(
            fusion_strategy=fusion, lexical_weight=config.hybrid.lexical_weight,
            semantic_weight=config.hybrid.semantic_weight, graph_weight=config.hybrid.graph_weight,
            graph_enabled=config.graph.enabled, top_k=config.top_k, rrf_k=config.hybrid.rrf_k,
        ))
        if config.graph.enabled and len(config.graph.signals) == 1:
            lexical = index.lexical_search(query.query_text, config.top_k)
            semantic = index.semantic_search(query.query_text, config.top_k)
            seeds = tuple(sorted({*(item.symbol_id for item in lexical),
                                  *(item.symbol_id for item in semantic)}, key=symbol_id_key))
            pair = config.graph.signals[0]
            graph = expand_graph(
                index.snapshot.graph, seeds, index.documents,
                index.config.graph_expansion_config, expected_graph=index.snapshot.graph,
                allowed_signals=((GraphRelationKind(pair[0]), GraphTraversalDirection(pair[1])),),
            ) if seeds else GraphExpansionResult(())
            result = retriever.fuse(lexical, semantic, index.documents, graph_result=graph)
        else:
            result = retriever.retrieve(query.query_text)
        if config.matrix_run_id in {"RQ4-HYBRID-NO-GRAPH", "RQ4-HYBRID-GRAPH"}:
            self.context_packages[query.query_id] = ContextBuilder().build(
                result, index.identity, 8000,
            )
        return StrategyResult(tuple(
            self._symbol_hit(
                query.project_id, hit.document, hit.rank,
                raw_lexical_score=hit.lexical_score,
                raw_semantic_score=hit.semantic_score,
                normalized_lexical_score=hit.normalized_lexical_score,
                normalized_semantic_score=hit.normalized_semantic_score,
                graph_score=hit.graph_score,
                graph_provenance=tuple(GraphProvenanceRecord(
                    serialize_candidate_identity(item.seed_identity) if isinstance(item.seed_identity, SymbolId)
                    else str(item.seed_identity), item.relation.value, item.direction.value,
                    item.hop, serialize_candidate_identity(item.node_identity)
                    if isinstance(item.node_identity, SymbolId) else str(item.node_identity),
                ) for item in hit.graph_provenance),
                final_score=hit.score,
            ) for hit in result.hits
        ), degraded=result.degraded,
           degradation_reason="semantic_branch_failure" if result.degraded else None,
           token_diagnostics=self._query_diagnostics(query))

    def _symbol_hit(self, project_id, document, rank, **scores):
        spans = {item.symbol_id: item for item in self._registry.symbol_ranges_for(project_id)}
        span = spans[document.symbol_id]
        return StrategyHit(document.symbol_id, document.relative_path, rank,
                           symbol_id=document.symbol_id, start_offset=span.start_offset,
                           end_offset=span.end_offset, **scores)

    def _query_diagnostics(self, query):
        if type(self._provider) is not LocalE5EmbeddingProvider:
            return ()
        diagnostic = self._provider.diagnose(query.query_text, kind="query")
        return (*self._document_diagnostics[query.project_id],
                self._diagnostic("query:" + query.query_id, "query", diagnostic))

    @staticmethod
    def _diagnostic(identity, kind, diagnostic):
        return {
            "identity": identity, "kind": kind,
            "untruncated_total_tokens": diagnostic.total_token_count,
            "effective_content_limit": diagnostic.effective_content_limit,
            "truncated": diagnostic.truncated,
            "dropped_token_count": max(0, diagnostic.total_token_count - 512),
        }


@dataclass(frozen=True)
class FrozenBenchmarkExecution:
    dataset: DatasetManifest
    queries: tuple[QueryRecord, ...]
    reference: tuple
    registry: DatasetEvidenceRegistry
    config: BenchmarkConfig
    strategy: ProductionBenchmarkStrategy
    validated_inputs: ValidatedExecutionInputs

    def run(self, metadata: RunMetadata, runner: BenchmarkRunner | None = None) -> BenchmarkRunResult:
        engine = runner if runner is not None else BenchmarkRunner()
        return engine.run(dataset=self.dataset, queries=self.queries, truth=self.reference,
                          config=self.config, strategy=self.strategy, metadata=metadata,
                          evidence_registry=self.registry, validated_inputs=self.validated_inputs)


def prepare_frozen_execution(config: BenchmarkConfig, validated_inputs: ValidatedExecutionInputs,
                             *, provider: EmbeddingProvider | None = None) -> FrozenBenchmarkExecution:
    """Prepare only; the Runner revalidates authority when run() is called."""
    if not is_validator_issued(validated_inputs) or config.run_kind is not validated_inputs.purpose:
        raise ExecutionWiringError("frozen execution requires validated authority")
    if config.identity_hash != validated_inputs.config_identity:
        raise ExecutionWiringError("validated configuration differs from request")
    projects, registry = bind_frozen_dataset(validated_inputs.repository_root, validated_inputs.dataset)
    strategy = ProductionBenchmarkStrategy(config, projects, registry,
                                           validated_inputs.queries, provider,
                                           validated_inputs)
    return FrozenBenchmarkExecution(validated_inputs.dataset, validated_inputs.queries,
                                    validated_inputs.reference, registry, config, strategy,
                                    validated_inputs)
