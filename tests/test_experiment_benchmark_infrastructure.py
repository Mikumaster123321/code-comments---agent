import json
import math
import random
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from code_maintenance import SymbolId, SymbolKind
from project_intelligence import DeterministicFakeEmbeddingProvider, EmbeddingFingerprint

from experiments import (
    ArtifactCollisionError,
    BenchmarkConfig,
    BenchmarkRunner,
    ChunkIdentity,
    ConfigValidationError,
    DatasetFile,
    DatasetManifest,
    DatasetProject,
    EvidenceRecord,
    ExperimentalBM25Index,
    FileIdentity,
    FileSource,
    FormalRunGuardError,
    GroundTruthRecord,
    GraphExperimentConfig,
    HybridExperimentConfig,
    QueryRecord,
    RetrievalUnit,
    RunKind,
    RunMetadata,
    RuntimeMetadata,
    SchemaValidationError,
    SemanticMode,
    SerializationError,
    Strategy,
    StrategyHit,
    StrategyResult,
    SymbolSourceRange,
    TruthMapper,
    build_chunk_documents,
    build_file_documents,
    canonical_hash,
    canonical_json,
    compute_metrics,
    load_dataset_manifest,
    load_ground_truth,
    load_queries,
    write_run_artifacts,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "experiments"


def symbol(name="target", path="src/a.py"):
    return SymbolId("python", path, name, SymbolKind.FUNCTION)


def dataset():
    project = DatasetProject(
        project_id="fixture-python",
        version="v1",
        source_kind="fixture",
        source_revision="fixture-v1",
        fixture_hash="b" * 64,
        language="python",
        files=(DatasetFile("src/a.py", "a" * 64, "fixture"),),
        file_count=1,
        symbol_count=2,
        limitations=("synthetic infrastructure fixture only",),
    )
    return DatasetManifest("synthetic-dataset", "v1", (project,))


def query(query_id="q-1", truth_id="gt-1", task="symbol_lookup"):
    return QueryRecord(
        query_id=query_id,
        query_set_version="queries-v1",
        split="english_dev",
        language="python",
        task_type=task,
        dataset_id="synthetic-dataset",
        project_id="fixture-python",
        query_text="find the target behavior",
        ground_truth_id=truth_id,
        authoring_source="fixture",
        notes=None,
    )


def truth(query_id="q-1", truth_id="gt-1", target=None, relevance=2):
    target = target or symbol()
    return GroundTruthRecord(
        ground_truth_id=truth_id,
        ground_truth_version="truth-v1",
        query_id=query_id,
        dataset_id="synthetic-dataset",
        project_id="fixture-python",
        evidence=(
            EvidenceRecord(
                "src/a.py", target, None, None, 1, 2, relevance, "direct target"
            ),
        ),
        annotation_status="frozen",
        primary_annotator_id="annotator-a",
        reviewer_id="reviewer-b",
        adjudicator_id=None,
        created_at="2026-09-22T08:00:00+00:00",
        reviewed_at="2026-09-22T09:00:00+00:00",
    )


def config_for(queries, truths, *, strategy=Strategy.LEXICAL, unit=RetrievalUnit.SYMBOL,
               run_kind=RunKind.SYNTHETIC, semantic_mode=SemanticMode.NONE,
               fingerprint=None, graph_enabled=False):
    manifest = dataset()
    if strategy is Strategy.EMBEDDING:
        hybrid = HybridExperimentConfig(lexical_weight=0.0, semantic_weight=1.0)
    elif strategy in {Strategy.WEIGHTED, Strategy.RRF}:
        hybrid = HybridExperimentConfig(
            lexical_weight=1.0,
            semantic_weight=1.0,
            graph_weight=0.25 if graph_enabled else 0.0,
        )
    else:
        hybrid = HybridExperimentConfig()
    return BenchmarkConfig(
        dataset_version=manifest.version,
        dataset_hash=manifest.dataset_hash,
        query_set_version="queries-v1",
        query_set_hash=canonical_hash([item.to_record() for item in sorted(queries, key=lambda x: x.query_id)]),
        ground_truth_version="truth-v1",
        ground_truth_hash=canonical_hash([item.to_record() for item in sorted(truths, key=lambda x: x.query_id)]),
        strategy=strategy,
        retrieval_unit=unit,
        run_kind=run_kind,
        semantic_mode=semantic_mode,
        embedding_fingerprint=fingerprint,
        hybrid=hybrid,
        graph=GraphExperimentConfig(enabled=graph_enabled),
    )


def runtime():
    return RuntimeMetadata(
        python_implementation="CPython",
        python_version="3.12.14",
        dependencies=(("pytest", "8.3.4"),),
        os_name="test-os",
        os_build="test-build",
        cpu_model="test-cpu",
        physical_cores=4,
        logical_cores=8,
        ram_bytes=16_000_000_000,
        power_mode="test",
        device="cpu",
        dtype="float32",
        thread_settings=(("OMP_NUM_THREADS", "1"),),
    )


def metadata_for(config, *, index_identity="index-v1", run_id="synthetic-run-1"):
    manifest = dataset()
    return RunMetadata(
        run_id=run_id,
        protocol_id="phase6",
        protocol_version=config.protocol_version,
        protocol_hash="c" * 64,
        dataset_id=manifest.dataset_id,
        dataset_version=manifest.version,
        dataset_hash=manifest.dataset_hash,
        path_manifest_hash="d" * 64,
        query_set_version=config.query_set_version,
        query_set_hash=config.query_set_hash,
        ground_truth_version=config.ground_truth_version,
        ground_truth_hash=config.ground_truth_hash,
        config_hashes=(config.identity_hash,),
        self_repository_commit="12391233daa2149ead4f451e920b2e0d8a1a6beb",
        runner_code_commit="7a224c456f7615e4f4dbc79b1065755df3c8033f",
        dirty_state=True,
        embedding_fingerprint=None,
        model_cache_verified=None,
        index_identity=index_identity,
        runtime=runtime(),
        random_seed=310,
        python_hash_seed="not applicable",
        started_at="2026-09-22T10:00:00+00:00",
        ended_at="2026-09-22T10:00:01+00:00",
        output_checksums=(),
        operator_id="phase6.1-test",
        independent_audit_status="pending",
    )


class TinyStrategy:
    semantic_mode = SemanticMode.NONE
    embedding_fingerprint = None
    index_identity = "index-v1"

    def __init__(self, candidates, *, fail_query=None, degraded=False):
        self.candidates = tuple(candidates)
        self.fail_query = fail_query
        self.degraded = degraded

    def candidate_identities(self, query):
        return self.candidates

    def symbol_ranges(self, query):
        return ()

    def retrieve(self, query, config):
        if query.query_id == self.fail_query:
            raise RuntimeError("provider detail must not leak")
        hit = StrategyHit(
            self.candidates[0],
            self.candidates[0].relative_path,
            symbol_id=self.candidates[0] if isinstance(self.candidates[0], SymbolId) else None,
            raw_lexical_score=2.0,
            normalized_lexical_score=1.0,
            final_score=1.0,
        )
        return StrategyResult(
            (hit,), self.degraded, "semantic_branch_failure" if self.degraded else None
        )


def test_config_identity_is_immutable_deterministic_sensitive_and_path_free():
    queries, truths = (query(),), (truth(),)
    base = config_for(queries, truths)
    assert base.identity_hash == config_for(queries, truths).identity_hash
    variants = (
        replace(base, dataset_version="v2"),
        replace(base, dataset_hash="e" * 64),
        replace(base, query_set_version="q2"),
        replace(base, query_set_hash="f" * 64),
        replace(base, ground_truth_version="t2"),
        replace(base, ground_truth_hash="0" * 64),
        replace(base, retrieval_unit=RetrievalUnit.FILE),
    )
    assert len({base.identity_hash, *(item.identity_hash for item in variants)}) == 8
    assert "/Users/" not in canonical_json(base.to_record())
    with pytest.raises(FrozenInstanceError):
        base.top_k = 5
    with pytest.raises(ConfigValidationError):
        replace(base, dataset_version="/Users/person/private")


def test_config_identity_covers_metric_hybrid_graph_embedding_and_chunk_fields():
    queries, truths = (query(),), (truth(),)
    fake = DeterministicFakeEmbeddingProvider().fingerprint
    base = config_for(
        queries,
        truths,
        strategy=Strategy.WEIGHTED,
        semantic_mode=SemanticMode.FAKE_TEST,
        fingerprint=fake,
    )
    variants = (
        replace(
            base,
            hybrid=replace(base.hybrid, graph_weight=0.25),
            graph=replace(base.graph, enabled=True),
        ),
        replace(base, graph=replace(base.graph, signals=(("imports", "forward"),))),
        replace(base, file=replace(base.file)),
        replace(base, embedding_fingerprint=DeterministicFakeEmbeddingProvider(9).fingerprint),
    )
    assert variants[2].identity_hash == base.identity_hash
    assert len({base.identity_hash, variants[0].identity_hash, variants[1].identity_hash, variants[3].identity_hash}) == 4
    with pytest.raises(ConfigValidationError):
        replace(base, chunk=replace(base.chunk, size=1199))


def test_schema_round_trip_strict_validation_and_input_order_canonicalization(tmp_path):
    manifest = dataset()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_record()), encoding="utf-8")
    assert load_dataset_manifest(manifest_path) == manifest
    query_path = tmp_path / "queries.jsonl"
    records = [query("q-2", "gt-2"), query()]
    query_path.write_text("".join(json.dumps(item.to_record()) + "\n" for item in records), encoding="utf-8")
    assert [item.query_id for item in load_queries(query_path)] == ["q-1", "q-2"]
    truth_path = tmp_path / "truth.jsonl"
    truths = [truth("q-2", "gt-2"), truth()]
    truth_path.write_text("".join(json.dumps(item.to_record()) + "\n" for item in truths), encoding="utf-8")
    assert [item.query_id for item in load_ground_truth(truth_path)] == ["q-1", "q-2"]
    bad = manifest.to_record()
    bad["unexpected"] = True
    manifest_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SchemaValidationError, match="fields mismatch"):
        load_dataset_manifest(manifest_path)


def test_ground_truth_rejects_missing_relevance_invalid_spans_and_duplicates():
    evidence = EvidenceRecord("src/a.py", symbol(), None, None, 1, 2, 2, "target")
    with pytest.raises(SchemaValidationError, match="relevant"):
        replace(truth(), evidence=(replace(evidence, relevance=0),))
    with pytest.raises(SchemaValidationError, match="offsets"):
        replace(evidence, start_offset=4, end_offset=4)
    with pytest.raises(SchemaValidationError, match="duplicate"):
        replace(truth(), evidence=(evidence, evidence))
    with pytest.raises(SchemaValidationError, match="duplicate"):
        replace(truth(), evidence=(evidence, replace(evidence, relevance=1)))


def test_file_baseline_identity_text_lf_normalization_empty_file_and_order():
    sources = [FileSource("z.py", ""), FileSource("a.py", "one\r\ntwo\r")]
    documents = build_file_documents(sources)
    assert [item.identity for item in documents] == [FileIdentity("a.py"), FileIdentity("z.py")]
    assert documents[0].text == "a.py\none\ntwo\n"
    assert documents[1].text == "z.py\n"
    assert build_file_documents(reversed(sources)) == documents


def test_chunk_boundaries_overlap_final_partial_unicode_and_empty_file():
    source = "界" * 2201
    chunks = build_chunk_documents((FileSource("unicode.py", source), FileSource("empty.py", "")))
    assert [item.identity for item in chunks] == [
        ChunkIdentity("unicode.py", 0, 1200),
        ChunkIdentity("unicode.py", 1000, 2200),
        ChunkIdentity("unicode.py", 2000, 2201),
    ]
    assert chunks[0].source_text[-200:] == chunks[1].source_text[:200]
    assert "empty.py" not in {item.relative_path for item in chunks}
    assert all(len(item.source_text) == item.end_offset - item.start_offset for item in chunks)


def test_experiment_bm25_uses_frozen_text_and_is_input_order_independent():
    documents = build_file_documents((
        FileSource("b.py", "def beta(): pass"),
        FileSource("a.py", "def alpha(): pass"),
    ))
    expected = ExperimentalBM25Index(documents).search("alpha")
    assert expected[0].identity == FileIdentity("a.py")
    for seed in range(20):
        shuffled = list(documents)
        random.Random(seed).shuffle(shuffled)
        assert ExperimentalBM25Index(shuffled).search("alpha") == expected


def test_rq1_truth_mapping_symbol_file_chunk_and_max_overlap_grade():
    target = symbol()
    supporting = symbol("support")
    record = replace(
        truth(target=target),
        evidence=(
            EvidenceRecord("src/a.py", target, None, None, 1, 2, 1, "symbol target"),
            EvidenceRecord("src/a.py", None, 15, 25, 2, 3, 2, "overlapping span"),
            EvidenceRecord("src/a.py", supporting, None, None, 4, 5, 1, "support"),
        ),
    )
    mapper = TruthMapper(
        record,
        (
            SymbolSourceRange(target, 10, 30),
            SymbolSourceRange(supporting, 40, 50),
        ),
    )
    assert mapper.grade(target) == 2
    assert mapper.grade(FileIdentity("src/a.py")) == 2
    assert mapper.grade(ChunkIdentity("src/a.py", 20, 40)) == 2
    assert mapper.grade(ChunkIdentity("src/a.py", 30, 40)) == 0


def test_chunk_mapping_fails_closed_without_symbol_source_range():
    mapper = TruthMapper(truth())
    with pytest.raises(SchemaValidationError, match="source range"):
        mapper.grade(ChunkIdentity("src/a.py", 0, 10))


def test_independent_metric_oracle_all_frozen_metrics():
    oracle = json.loads((FIXTURE_DIR / "metric_oracle.json").read_text(encoding="utf-8"))
    values = compute_metrics(oracle["ranked_identities"], oracle["relevance"])
    expected = oracle["expected"]
    assert values.recall_at_1 == expected["recall_at_1"]
    assert values.recall_at_5 == expected["recall_at_5"]
    assert values.recall_at_10 == expected["recall_at_10"]
    assert values.mrr == expected["mrr"]
    assert values.ndcg_at_5 == pytest.approx(expected["ndcg_at_5"])
    assert values.precision_at_5 == expected["precision_at_5"]
    assert values.hit_rate_at_5 == expected["hit_rate_at_5"]
    independent_ndcg = (
        1 / math.log2(3) + 3 / math.log2(5) + 1 / math.log2(6)
    ) / (3 + 1 / math.log2(3) + 1 / math.log2(4))
    assert values.ndcg_at_5 == pytest.approx(independent_ndcg)


def test_metrics_empty_short_duplicate_k_beyond_results_and_failed_query():
    relevance = {"a": 2, "b": 1}
    empty = compute_metrics((), relevance)
    assert empty == empty.zero()
    short = compute_metrics(("x", "a", "a"), relevance)
    assert short.recall_at_10 == 0.5
    assert short.mrr == 0.5
    assert short.precision_at_5 == 0.2
    assert compute_metrics(("a",), relevance, failed=True) == empty.zero()


def test_graded_ndcg_distinguishes_grade_two_from_binary_metrics():
    high_first = compute_metrics(("high", "low"), {"high": 2, "low": 1})
    low_first = compute_metrics(("low", "high"), {"high": 2, "low": 1})
    assert high_first.recall_at_5 == low_first.recall_at_5 == 1.0
    assert high_first.ndcg_at_5 == 1.0
    assert low_first.ndcg_at_5 < 1.0


def test_runner_raw_aggregate_groups_and_failed_query_denominator():
    target = symbol()
    queries = (query(), query("q-2", "gt-2", "bug_localization"))
    truths = (truth(), truth("q-2", "gt-2"))
    config = config_for(queries, truths)
    metadata = metadata_for(config)
    ticks = iter((0, 10, 20, 50))
    result = BenchmarkRunner(clock_ns=lambda: next(ticks)).run(
        dataset=dataset(),
        queries=reversed(queries),
        truth=reversed(truths),
        config=config,
        strategy=TinyStrategy((target,), fail_query="q-2"),
        metadata=metadata,
        matrix_run_id="SYNTHETIC-SMOKE",
    )
    assert [item.query_id for item in result.raw_results] == ["q-1", "q-2"]
    assert result.raw_results[1].status == "failed"
    assert result.raw_results[1].failure_type == "RuntimeError"
    assert "provider detail" not in canonical_json(result)
    assert result.aggregate.overall.query_count == 2
    assert result.aggregate.overall.failure_count == 1
    assert result.aggregate.overall.metrics.recall_at_5 == 0.5
    dimensions = {item.dimension for item in result.aggregate.strata}
    assert dimensions == {"task_type", "language", "dataset_id", "split"}


def test_runner_serialization_is_deterministic_under_input_permutations():
    target = symbol()
    queries = (query(), query("q-2", "gt-2"))
    truths = (truth(), truth("q-2", "gt-2"))
    config = config_for(queries, truths)

    def run(qs, ts):
        ticks = iter((0, 5, 10, 15))
        return BenchmarkRunner(clock_ns=lambda: next(ticks)).run(
            dataset=dataset(), queries=qs, truth=ts, config=config,
            strategy=TinyStrategy((target,)), metadata=metadata_for(config),
            matrix_run_id="SYNTHETIC-SMOKE",
        )

    first = run(queries, truths)
    second = run(reversed(queries), reversed(truths))
    assert canonical_json(first) == canonical_json(second)


def test_fake_vs_formal_semantic_guard_and_frozen_real_e5_identity():
    queries, truths = (query(),), (truth(),)
    fake = DeterministicFakeEmbeddingProvider().fingerprint
    with pytest.raises(ConfigValidationError, match="real E5"):
        config_for(
            queries, truths, strategy=Strategy.EMBEDDING,
            run_kind=RunKind.FORMAL, semantic_mode=SemanticMode.FAKE_TEST,
            fingerprint=fake,
        )
    real = EmbeddingFingerprint(
        runtime_kind="transformers-torch",
        model_repository="intfloat/multilingual-e5-base",
        revision="d128750597153bb5987e10b1c3493a34e5a4502a",
        dimension=768,
    )
    formal = config_for(
        queries, truths, strategy=Strategy.EMBEDDING,
        run_kind=RunKind.FORMAL, semantic_mode=SemanticMode.REAL_E5,
        fingerprint=real,
    )
    assert formal.semantic_mode is SemanticMode.REAL_E5


def test_runner_phase61_formal_execution_gate_and_degraded_formal_guard():
    queries, truths = (query(),), (truth(),)
    lexical_formal = config_for(queries, truths, run_kind=RunKind.FORMAL)
    args = dict(
        dataset=dataset(), queries=queries, truth=truths, config=lexical_formal,
        strategy=TinyStrategy((symbol(),)), metadata=metadata_for(lexical_formal),
        matrix_run_id="FORMAL-FORBIDDEN",
    )
    with pytest.raises(FormalRunGuardError, match="Phase 6.1"):
        BenchmarkRunner().run(**args)

    real = EmbeddingFingerprint(
        runtime_kind="transformers-torch",
        model_repository="intfloat/multilingual-e5-base",
        revision="d128750597153bb5987e10b1c3493a34e5a4502a",
        dimension=768,
    )
    semantic_formal = config_for(
        queries, truths, strategy=Strategy.WEIGHTED,
        run_kind=RunKind.FORMAL, semantic_mode=SemanticMode.REAL_E5,
        fingerprint=real,
    )

    class DegradedRealStrategy(TinyStrategy):
        semantic_mode = SemanticMode.REAL_E5
        embedding_fingerprint = real

    with pytest.raises(FormalRunGuardError, match="degraded"):
        BenchmarkRunner(allow_formal=True, clock_ns=iter((0, 1)).__next__).run(
            **{
                **args,
                "config": semantic_formal,
                "metadata": metadata_for(semantic_formal),
                "strategy": DegradedRealStrategy((symbol(),), degraded=True),
            }
        )


def test_strategy_semantic_mode_and_fingerprint_must_match_config():
    queries, truths = (query(),), (truth(),)
    fake = DeterministicFakeEmbeddingProvider().fingerprint
    config = config_for(
        queries, truths, strategy=Strategy.EMBEDDING,
        semantic_mode=SemanticMode.FAKE_TEST, fingerprint=fake,
    )
    with pytest.raises(FormalRunGuardError, match="semantic mode"):
        BenchmarkRunner().run(
            dataset=dataset(), queries=queries, truth=truths, config=config,
            strategy=TinyStrategy((symbol(),)), metadata=metadata_for(config),
            matrix_run_id="SYNTHETIC",
        )


def test_append_only_artifacts_checksums_and_collision(tmp_path):
    queries, truths = (query(),), (truth(),)
    config = config_for(queries, truths)
    metadata = metadata_for(config)
    result = BenchmarkRunner(clock_ns=iter((0, 5)).__next__).run(
        dataset=dataset(), queries=queries, truth=truths, config=config,
        strategy=TinyStrategy((symbol(),)), metadata=metadata,
        matrix_run_id="SYNTHETIC-SMOKE",
    )
    run_path = write_run_artifacts(tmp_path, result, metadata)
    assert sorted(item.name for item in run_path.iterdir()) == [
        "aggregate_results.json", "checksums.sha256", "raw_results.jsonl", "run_manifest.json"
    ]
    assert result.aggregate.raw_results_sha256 in (run_path / "aggregate_results.json").read_text()
    with pytest.raises(ArtifactCollisionError):
        write_run_artifacts(tmp_path, result, metadata)


def test_artifact_privacy_rejects_credentials_and_raw_schema_excludes_source_vectors():
    with pytest.raises(SerializationError, match="credential"):
        canonical_json({"api_key": "never-store-this"})
    with pytest.raises(SerializationError, match="credential-like"):
        canonical_json({"value": "sk-proj-abcdefghijklmnop"})
    fields = set(__import__("experiments.runner", fromlist=["RawQueryResult"]).RawQueryResult.__dataclass_fields__)
    assert "source_text" not in fields
    assert "embedding_vector" not in fields
    with pytest.raises(SchemaValidationError, match="safe fields"):
        StrategyResult((), token_diagnostics=({"source_text": "private source"},))


def test_run_metadata_separates_deterministic_identity_from_environment_and_time():
    queries, truths = (query(),), (truth(),)
    config = config_for(queries, truths)
    metadata = metadata_for(config)
    deterministic = metadata.deterministic_record()
    assert "environment" not in deterministic
    assert "started_at" not in canonical_json(deterministic)
    record = metadata.to_record()
    assert record["environment"]["device"] == "cpu"
    assert record["execution"]["started_at"].endswith("+00:00")


def test_no_formal_dataset_truth_or_result_artifacts_were_added():
    root = Path(__file__).parents[1]
    assert not (root / "docs" / "experiments" / "datasets").exists()
    assert not (root / "docs" / "experiments" / "queries").exists()
    assert not (root / "docs" / "experiments" / "ground_truth").exists()
    assert not (root / "docs" / "experiments" / "runs").exists()
