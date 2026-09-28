"""Synthetic execution wiring checks; no formal split or real model inference."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from experiments.config import (
    BenchmarkConfig, ConfigValidationError, FROZEN_MATRIX_IDS,
    GraphExperimentConfig, HybridExperimentConfig, Population, RetrievalUnit,
    RunKind, SemanticMode, Strategy,
)
from experiments.execution import (
    ExecutionWiringError, ProductionBenchmarkStrategy, bind_frozen_dataset,
    bind_project, executable_config, registry_from_bound_projects,
)
from experiments.runner import BenchmarkRunner
from experiments.schemas import DatasetFile, DatasetManifest, load_dataset_manifest
from experiments.serialization import canonical_hash
from project_intelligence import DeterministicFakeEmbeddingProvider, LocalE5EmbeddingProvider
from project_intelligence.local_embedding import TokenizationDiagnostic
from test_experiment_benchmark_infrastructure import (
    config_for, dataset, metadata_for, query, truth,
)


SOURCE = b"def target():\n    pass\n\ndef support():\n    pass\n"


def _bound():
    manifest = dataset()
    project = bind_project(manifest.projects[0], {"src/a.py": SOURCE})
    projects = {manifest.projects[0].project_id: project}
    return manifest, projects, registry_from_bound_projects(manifest, projects)


def _strategy(config, *, provider=None):
    _, projects, registry = _bound()
    return ProductionBenchmarkStrategy(config, projects, registry, (query(),), provider), registry


def test_all_17_frozen_rows_resolve_without_new_rows():
    provider = LocalE5EmbeddingProvider(local_files_only=True)
    template = BenchmarkConfig(
        "v1", "a" * 64, "q-v1", "b" * 64, "ref-v1", "c" * 64,
        Strategy.LEXICAL, RetrievalUnit.SYMBOL, matrix_run_id="RQ1-SYMBOL",
        run_kind=RunKind.DRY_RUN, approved_reference_identity="d" * 64,
        embedding_fingerprint=provider.fingerprint,
    )
    configs = [executable_config(template, row) for row in FROZEN_MATRIX_IDS]
    assert len(configs) == len({config.matrix_run_id for config in configs}) == 17
    assert len({config.identity_hash for config in configs}) == 17
    assert {config.retrieval_unit for config in configs} == set(RetrievalUnit)
    assert {config.strategy for config in configs} == set(Strategy)
    assert sum(config.graph.enabled for config in configs) == 7
    assert all(config.top_k == 10 and config.hybrid.rrf_k == 60 for config in configs)
    with pytest.raises(ConfigValidationError, match="unknown"):
        executable_config(template, "RQ5-UNREGISTERED")


@pytest.mark.parametrize("unit", (RetrievalUnit.FILE, RetrievalUnit.SYMBOL, RetrievalUnit.CHUNK))
def test_real_source_to_production_bm25_to_runner_metrics(unit):
    questions, truths = (query(),), (truth(),)
    config = config_for(questions, truths, unit=unit)
    strategy, registry = _strategy(config)
    output = strategy.retrieve(questions[0], config)
    assert output.hits
    assert output.hits[0].identity in registry.candidates_for("fixture-python", unit)
    if unit is RetrievalUnit.SYMBOL:
        assert strategy._indices["fixture-python"].lexical_index.__class__.__name__ == "BM25Index"
    else:
        assert strategy._baselines["fixture-python"].__class__.__name__ == "ExperimentalBM25Index"
    result = BenchmarkRunner(clock_ns=iter((10, 20)).__next__).run(
        dataset=dataset(), queries=questions, truth=truths, config=config,
        strategy=strategy, metadata=metadata_for(config, index_identity=strategy.index_identity),
        evidence_registry=registry,
    )
    assert result.raw_results[0].status == "success"
    assert result.raw_results[0].metrics.recall_at_5 > 0


def test_weighted_rrf_graph_and_stable_order_use_production_stack():
    questions, truths = (query(),), (truth(),)
    provider = DeterministicFakeEmbeddingProvider()
    template = config_for(questions, truths, strategy=Strategy.WEIGHTED,
                          semantic_mode=SemanticMode.FAKE_TEST, fingerprint=provider.fingerprint)
    outputs = {}
    modes = {
        "embedding": config_for(questions, truths, strategy=Strategy.EMBEDDING,
                                semantic_mode=SemanticMode.FAKE_TEST, fingerprint=provider.fingerprint),
        "weighted_off": template,
        "weighted_on": config_for(questions, truths, strategy=Strategy.WEIGHTED,
                                  semantic_mode=SemanticMode.FAKE_TEST, fingerprint=provider.fingerprint,
                                  graph_enabled=True),
        "rrf_on": config_for(questions, truths, strategy=Strategy.RRF,
                             semantic_mode=SemanticMode.FAKE_TEST, fingerprint=provider.fingerprint,
                             graph_enabled=True),
    }
    modes["contains_reverse"] = replace(
        modes["weighted_on"], graph=replace(modes["weighted_on"].graph,
                                             signals=(("contains", "reverse"),)),
    )
    for row, config in modes.items():
        strategy, _ = _strategy(config, provider=provider)
        first = strategy.retrieve(questions[0], config)
        second = strategy.retrieve(questions[0], config)
        assert first == second
        assert [hit.rank for hit in first.hits] == list(range(1, len(first.hits) + 1))
        assert strategy._indices["fixture-python"].__class__.__name__ == "RetrievalIndex"
        outputs[row] = first
    assert outputs["embedding"].hits
    assert outputs["rrf_on"].hits


def test_graph_on_and_pair_filter_reach_symbol_provenance():
    source = b"class Target:\n    def run(self):\n        return 1\n"
    original = dataset().projects[0]
    project = replace(original, files=(DatasetFile("src/a.py", sha256(source).hexdigest(), "fixture"),),
                      symbol_count=2)
    manifest = DatasetManifest("synthetic-dataset", "v1", (project,))
    bound = bind_project(project, {"src/a.py": source})
    projects = {project.project_id: bound}
    registry = registry_from_bound_projects(manifest, projects)
    question = replace(query(), query_text="run")
    provider = DeterministicFakeEmbeddingProvider()
    base = config_for((query(),), (truth(),), strategy=Strategy.WEIGHTED,
                      semantic_mode=SemanticMode.FAKE_TEST, fingerprint=provider.fingerprint)
    common = dict(dataset_hash=manifest.dataset_hash,
                  query_set_hash=canonical_hash([question.to_record()]))
    off = replace(base, **common)
    on = replace(base, **common, graph=GraphExperimentConfig(enabled=True),
                 hybrid=HybridExperimentConfig(1.0, 1.0, 0.25))
    pair = replace(on, graph=GraphExperimentConfig(enabled=True,
                                                   signals=(("contains", "reverse"),)))
    off_hits = ProductionBenchmarkStrategy(off, projects, registry, (question,), provider).retrieve(question, off).hits
    on_hits = ProductionBenchmarkStrategy(on, projects, registry, (question,), provider).retrieve(question, on).hits
    pair_hits = ProductionBenchmarkStrategy(pair, projects, registry, (question,), provider).retrieve(question, pair).hits
    assert all(not hit.graph_provenance for hit in off_hits)
    assert any(hit.graph_provenance for hit in on_hits)
    assert any(provenance.direction == "reverse" for hit in pair_hits
               for provenance in hit.graph_provenance)
    assert all(provenance.direction == "reverse" for hit in pair_hits
               for provenance in hit.graph_provenance)


def test_wrong_split_and_english_test_guard():
    questions, truths = (query(),), (truth(),)
    config = config_for(questions, truths)
    strategy, _ = _strategy(config)
    with pytest.raises(ExecutionWiringError, match="split"):
        strategy.retrieve(replace(questions[0], split="chinese_coverage"), config)
    with pytest.raises(ExecutionWiringError, match="English Test"):
        _strategy(replace(config, population=Population.ENGLISH_TEST))


def test_chinese_coverage_split_can_run_on_synthetic_fixture():
    question = replace(query(), split="chinese_coverage")
    annotation = truth()
    config = config_for((question,), (annotation,), population=Population.CHINESE_COVERAGE)
    manifest, projects, registry = _bound()
    strategy = ProductionBenchmarkStrategy(config, projects, registry, (question,))
    result = BenchmarkRunner(clock_ns=iter((10, 20)).__next__).run(
        dataset=manifest, queries=(question,), truth=(annotation,), config=config,
        strategy=strategy, metadata=metadata_for(config, index_identity=strategy.index_identity),
        evidence_registry=registry,
    )
    assert result.raw_results[0].split == "chinese_coverage"
    assert result.raw_results[0].status == "success"


def test_real_e5_wiring_is_pinned_and_fails_closed_without_optional_runtime():
    provider = LocalE5EmbeddingProvider(local_files_only=True)
    questions, truths = (query(),), (truth(),)
    synthetic = config_for(questions, truths)
    formal_template = BenchmarkConfig(
        synthetic.dataset_version, synthetic.dataset_hash,
        synthetic.query_set_version, synthetic.query_set_hash,
        synthetic.ground_truth_version, synthetic.ground_truth_hash,
        Strategy.LEXICAL, RetrievalUnit.SYMBOL, matrix_run_id="RQ1-SYMBOL",
        run_kind=RunKind.DRY_RUN, approved_reference_identity="d" * 64,
        embedding_fingerprint=provider.fingerprint,
    )
    real = executable_config(formal_template, "RQ2-E5")
    real.validate_formal_semantics()
    assert real.semantic_mode is SemanticMode.REAL_E5
    assert provider.fingerprint.dimension == 768
    assert provider.fingerprint.revision == "d128750597153bb5987e10b1c3493a34e5a4502a"
    assert provider._local_files_only is True
    class ForgedProvider:
        fingerprint = provider.fingerprint

    synthetic_real = config_for(questions, truths, strategy=Strategy.EMBEDDING,
                                semantic_mode=SemanticMode.REAL_E5,
                                fingerprint=provider.fingerprint)
    with pytest.raises(ExecutionWiringError, match="pinned local CPU adapter"):
        ProductionBenchmarkStrategy(synthetic_real, _bound()[1], _bound()[2], (query(),),
                                    ForgedProvider())


def test_pinned_e5_adapter_reaches_index_and_result_with_offline_unit_stub(monkeypatch):
    questions, truths = (query(),), (truth(),)
    provider = LocalE5EmbeddingProvider(local_files_only=True)
    fake = DeterministicFakeEmbeddingProvider(768)
    diagnostic = TokenizationDiagnostic(5, 2, 7, 510, False)

    def documents(self, texts):
        self._last_diagnostics = (diagnostic,) * len(texts)
        return fake.embed_documents(texts)

    monkeypatch.setattr(LocalE5EmbeddingProvider, "embed_documents", documents)
    monkeypatch.setattr(LocalE5EmbeddingProvider, "embed_query",
                        lambda self, text: fake.embed_query(text))
    monkeypatch.setattr(LocalE5EmbeddingProvider, "diagnose",
                        lambda self, text, kind="document": diagnostic)
    config = config_for(questions, truths, strategy=Strategy.EMBEDDING,
                        semantic_mode=SemanticMode.REAL_E5,
                        fingerprint=provider.fingerprint)
    strategy, _ = _strategy(config, provider=provider)
    result = strategy.retrieve(questions[0], config)
    assert result.hits
    assert len(result.token_diagnostics) == 3
    assert result.token_diagnostics[-1]["identity"] == "query:q-1"


def test_frozen_dataset_binding_uses_manifest_only():
    root = Path(__file__).resolve().parents[1]
    manifest = load_dataset_manifest(root / "docs/experiments/datasets/v1/manifest.json")
    projects, registry = bind_frozen_dataset(root, manifest)
    assert set(projects) == {project.project_id for project in manifest.projects}
    assert sum(len(project.documents) for project in projects.values()) == sum(
        project.symbol_count for project in manifest.projects
    )
    assert registry.manifest.dataset_hash == manifest.dataset_hash


def test_production_retrieval_has_no_reverse_experiment_import():
    root = Path(__file__).resolve().parents[1]
    for path in (root / "project_intelligence").glob("*.py"):
        assert "from experiments" not in path.read_text(encoding="utf-8")
        assert "import experiments" not in path.read_text(encoding="utf-8")
    baseline = (root / "experiments/baselines.py").read_text(encoding="utf-8")
    assert "BM25TextScorer" in baseline
    assert "math.log1p" not in baseline
