#!/usr/bin/env python3
"""Explicit Phase 3.2 real-model validation.

This is intentionally outside the default pytest suite.  Run it only from an
environment containing ``requirements-embedding.txt`` and a cache outside the
repository, for example::

    HF_HOME=/path/to/cache python scripts/validate_phase32_real_model.py \
        --cache-dir /path/to/cache --device cpu

The script performs no model work when imported; all loading is behind ``main``.
"""

from __future__ import annotations

import argparse
import math
import platform
import resource
import statistics
import sys
import time
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _rss_mb() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux reports KiB.
    return float(value) / (1024 * 1024 if sys.platform == "darwin" else 1024)


def _percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run explicit Phase 3.2 real E5 validation")
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    from code_maintenance import ProjectScanner, SnapshotBuilder
    from project_intelligence import (
        CorpusBuilder,
        LocalE5EmbeddingProvider,
        PRIMARY_MODEL_DIMENSION,
        PRIMARY_MODEL_REPOSITORY,
        PRIMARY_MODEL_REVISION,
        SemanticIndex,
    )

    root = REPOSITORY_ROOT
    provider = LocalE5EmbeddingProvider(
        cache_dir=args.cache_dir,
        model_path=args.model_path,
        local_files_only=args.offline,
        device=args.device,
        batch_size=args.batch_size,
    )
    if provider.fingerprint.revision != PRIMARY_MODEL_REVISION:
        raise SystemExit("primary validation requires the frozen revision")

    print("=== PHASE 3.2 REAL MODEL VALIDATION ===")
    print(f"python={platform.python_version()} platform={platform.platform()}")
    print(f"repository={PRIMARY_MODEL_REPOSITORY}")
    print(f"revision={PRIMARY_MODEL_REVISION}")
    print(f"device={args.device} batch_size={args.batch_size} offline={args.offline}")
    print(f"fingerprint_hash={provider.fingerprint.fingerprint_hash}")

    before = _rss_mb()
    cold_start = time.perf_counter()
    provider.load()
    cold_seconds = time.perf_counter() - cold_start
    after = _rss_mb()
    print(f"cold_load_seconds={cold_seconds:.3f} rss_before_mb={before:.1f} rss_after_mb={after:.1f}")

    # Real tokenizer boundary evidence: counts include the model's special tokens.
    boundary = {}
    for target in (510, 511, 512, 513, 514):
        # ``a`` is one tokenizer token in the frozen XLM-R tokenizer, so the
        # labels below are actual raw-token counts rather than character counts.
        # The adapter's ``passage: `` instruction contributes two raw tokens;
        # subtract them so the diagnostic reports the requested boundary.
        text = "a " * max(0, target - 2)
        diagnostic = provider.diagnose(text, kind="document")
        boundary[target] = diagnostic
        print(
            "boundary_raw={target} raw={raw} special={special} total={total} "
            "effective_limit={limit} truncated={truncated}".format(
                target=target,
                raw=diagnostic.raw_token_count,
                special=diagnostic.special_token_count,
                total=diagnostic.total_token_count,
                limit=diagnostic.effective_content_limit,
                truncated=diagnostic.truncated,
            )
        )

    texts = (
        "credit ledger balance",
        "信用额度余额",
        "日本語の識別子",
        "def 计算余额(账户):\n    # 注释\n    return 账户",
        "public class Créditeur { String 名称; }",
    )
    warm_start = time.perf_counter()
    query_vector = provider.embed_query(texts[0])
    warm_seconds = time.perf_counter() - warm_start
    documents = provider.embed_documents(texts)
    assert len(query_vector) == PRIMARY_MODEL_DIMENSION
    assert all(len(vector) == PRIMARY_MODEL_DIMENSION for vector in documents)
    assert all(math.isfinite(value) for value in query_vector)
    assert abs(math.sqrt(math.fsum(value * value for value in query_vector.values)) - 1.0) < 1e-5
    print(f"warm_query_seconds={warm_seconds:.3f} vector_dimension={len(query_vector)}")

    long_probe = "a " * 2000
    diagnostic_before = provider.diagnose(long_probe, kind="document")
    provider.embed_query("diagnostic state probe")
    diagnostic_after_query = provider.diagnose(long_probe, kind="document")
    provider.embed_documents(("diagnostic document", "another document"))
    diagnostic_after_documents = provider.diagnose(long_probe, kind="document")
    assert diagnostic_before == diagnostic_after_query == diagnostic_after_documents
    long_vectors = provider.embed_documents((long_probe,))
    assert provider.last_diagnostics[0] == diagnostic_before
    print(
        "diagnostic_history_stable=True "
        f"long_total={diagnostic_before.total_token_count} "
        f"long_truncated={diagnostic_before.truncated} "
        f"long_vector_dimension={len(long_vectors[0])}"
    )

    repeated = [provider.embed_query(texts[0]).values for _ in range(100)]
    max_delta = max(
        max(abs(a - b) for a, b in zip(repeated[0], values)) for values in repeated[1:]
    )
    print(f"determinism_repeats=100 max_abs_delta={max_delta:.9g}")
    single = provider.embed_documents((texts[0],))[0]
    batched = provider.embed_documents((texts[0], texts[1]))[0]
    batch_delta = max(abs(a - b) for a, b in zip(single.values, batched.values))
    print(f"batch_consistency_max_abs_delta={batch_delta:.9g}")

    # Build the current immutable corpus and use the frozen SemanticIndex path.
    snapshot = SnapshotBuilder().build(ProjectScanner().scan(root))
    corpus_start = time.perf_counter()
    corpus = CorpusBuilder().build(root, snapshot)
    corpus_build_seconds = time.perf_counter() - corpus_start
    token_lengths: list[int] = []
    truncated = 0
    documents_over_limit = 0
    for document in corpus:
        diagnostic = provider.diagnose(document.qualified_name + "\n" + document.source_text)
        token_lengths.append(diagnostic.total_token_count)
        truncated += int(diagnostic.truncated)
        documents_over_limit += int(diagnostic.total_token_count > 512)
    print(
        "corpus_documents={count} documents_le_limit={within} documents_over_limit={over} "
        "corpus_build_seconds={seconds:.3f} "
        "token_min={min_} token_median={median} token_p90={p90} token_p95={p95} "
        "token_p99={p99} token_max={max_} truncated={truncated} truncated_percent={percent:.2f}".format(
            count=len(corpus),
            within=len(corpus) - documents_over_limit,
            over=documents_over_limit,
            seconds=corpus_build_seconds,
            min_=min(token_lengths, default=0),
            median=int(statistics.median(token_lengths)) if token_lengths else 0,
            p90=_percentile(token_lengths, 0.90),
            p95=_percentile(token_lengths, 0.95),
            p99=_percentile(token_lengths, 0.99),
            max_=max(token_lengths, default=0),
            truncated=truncated,
            percent=(100.0 * truncated / len(corpus)) if corpus else 0.0,
        )
    )
    index_start = time.perf_counter()
    index = SemanticIndex(corpus, provider)
    index_seconds = time.perf_counter() - index_start
    print(f"corpus_embedding_seconds={index_seconds:.3f} rss_peak_mb={_rss_mb():.1f}")

    for query in (
        "credit ledger",
        "managed access",
        "snapshot diff",
        "admin credit",
        "symbol id",
        "信用额度",
    ):
        query_start = time.perf_counter()
        hits = index.search(query, top_k=3)
        duration = time.perf_counter() - query_start
        print(
            f"query={query!r} seconds={duration:.4f} "
            f"hits={[str(hit.symbol_id) for hit in hits]} "
            f"scores={[round(hit.score, 6) for hit in hits]}"
        )

    print("semantic_index_fingerprint_stable=" + str(index.fingerprint == provider.fingerprint))
    print("=== END OF PHASE 3.2 REAL MODEL VALIDATION ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
