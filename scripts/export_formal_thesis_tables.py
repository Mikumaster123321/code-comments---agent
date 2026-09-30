"""Export thesis tables from the frozen V3.1 Formal artifact set.

Use --check to verify committed CSVs without writing anything. This script never
runs a benchmark or modifies its source artifacts.
"""

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.serialization import canonical_hash


ARTIFACT = ROOT / "docs/experiments/audits/phase64_formal_english_test/artifact_set.json"
OUTPUT = ROOT / "docs/experiments"
EXPECTED_IDENTITY = "acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3"
EXPECTED_SHA256 = "2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41"
EXPECTED_REVISION = "2749969cd3a2d4d6e1e8d81160eebd5fb360879b"
METRICS = (
    ("Recall@1", "recall_at_1"),
    ("Recall@5", "recall_at_5"),
    ("Recall@10", "recall_at_10"),
    ("MRR", "mrr"),
    ("nDCG@5", "ndcg_at_5"),
    ("Precision@5", "precision_at_5"),
    ("Hit Rate@5", "hit_rate_at_5"),
)
CONTEXT = (
    ("budget_used", "budget_used"),
    ("budget_total", "budget"),
    ("budget_utilization_ratio", "budget_utilization_ratio"),
    ("gt_evidence_rendered", "relevant_ground_truth_evidence_rendered"),
    ("gt_evidence_total", "relevant_ground_truth_evidence_total"),
    ("snippet_count", "snippet_count"),
    ("truncated_packages", "package_truncation_count"),
    ("graph_only_snippets", "graph_only_rendered_snippets"),
    ("retained_but_unrendered_graph_provenance", "retained_but_unrendered_graph_provenance_count"),
)


class ExportValidationError(RuntimeError):
    """Raised when frozen inputs or committed exports fail validation."""


def _require(condition, message):
    if not condition:
        raise ExportValidationError(message)


def _verify_equal(actual, expected, label):
    _require(actual == expected, f"{label} mismatch: expected {expected!r}, got {actual!r}")


def verified_json(path, expected_sha256):
    raw = (ROOT / path).read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    _verify_equal(actual_sha256, expected_sha256, f"checksum for {path}")
    return json.loads(raw)


def csv_text(header, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def export():
    artifact = verified_json(ARTIFACT.relative_to(ROOT), EXPECTED_SHA256)
    _verify_equal(canonical_hash(artifact), EXPECTED_IDENTITY, "artifact identity")
    _require(artifact["execution_revision"] == EXPECTED_REVISION,
             "artifact execution revision mismatch")
    _require(artifact["mode"] == "formal" and artifact["split"] == "english_test",
             "artifact mode/split mismatch")
    _require(artifact["query_count"] == 48 and artifact["config_count"] == 17,
             "artifact query/config count mismatch")
    _require(artifact["query_config_pair_count"] == 816,
             "artifact query-config pair count mismatch")
    _require(len(artifact["runs"]) == 17, "artifact run count mismatch")

    main, extended, figures, context = [], [], [], []
    for rq, configurations in artifact["rq_mapping"].items():
        for configuration in configurations:
            run = next(r for r in artifact["runs"] if r["matrix_run_id"] == configuration)
            aggregate = verified_json(run["aggregate_path"], run["aggregate_sha256"])
            _require(aggregate["matrix_run_id"] == configuration,
                     f"aggregate matrix ID mismatch for {configuration}")
            _require(aggregate["code_commit"] == EXPECTED_REVISION,
                     f"aggregate revision mismatch for {configuration}")
            _require(aggregate["denominator_count"] == 48,
                     f"aggregate denominator mismatch for {configuration}")
            _require(aggregate["macro_metrics"] == run["overall"],
                     f"aggregate metric mismatch for {configuration}")
            _require(aggregate["strata"] == run["strata"],
                     f"aggregate strata mismatch for {configuration}")
            secondary = str(configuration.startswith("RRF-")).lower()
            metrics = run["overall"]
            main.append((rq, configuration, secondary, metrics["recall_at_5"], metrics["mrr"]))
            extended.append((rq, configuration, secondary, "overall", "english_test", 48,
                             *(metrics[key] for _, key in METRICS)))
            for stratum in run["strata"]:
                if stratum["dimension"] not in ("language", "task_type"):
                    continue
                extended.append((rq, configuration, secondary, stratum["dimension"],
                                 stratum["value"], stratum["query_count"],
                                 *(stratum["metrics"][key] for _, key in METRICS)))
            figures.append(("ABCD"[int(rq[-1]) - 1], rq, configuration, secondary,
                            metrics["recall_at_5"], metrics["mrr"]))

            if configuration in ("RQ4-HYBRID-NO-GRAPH", "RQ4-HYBRID-GRAPH"):
                diagnostic = verified_json(run["context_diagnostic_path"], run["context_diagnostic_sha256"])
                _require(diagnostic["artifact_identity"] == run["context_diagnostic_identity"],
                         f"context diagnostic identity mismatch for {configuration}")
                _require(diagnostic["matrix_run_id"] == configuration,
                         f"context diagnostic matrix ID mismatch for {configuration}")
                _require(diagnostic["execution_revision"] == EXPECTED_REVISION,
                         f"context diagnostic revision mismatch for {configuration}")
                summary = diagnostic["summary"]
                _require(summary["query_count"] == 48,
                         f"context diagnostic query count mismatch for {configuration}")
                context.append((configuration, *(summary[key] for _, key in CONTEXT)))

    _require(len(main) == 17 and len(extended) == 17 * 9,
             "exported Formal table row count mismatch")
    _require(len(context) == 2, "exported context diagnostic row count mismatch")
    return {
        "Formal_Result_Table_RQ1_RQ4_V3_1_0.csv": csv_text(
            ("RQ", "configuration", "secondary", "Recall@5", "MRR"), main),
        "Formal_Result_Extended_RQ1_RQ4_V3_1_0.csv": csv_text(
            ("RQ", "configuration", "secondary", "subgroup_dimension", "subgroup_value", "query_count",
             *(name for name, _ in METRICS)), extended),
        "Formal_ContextBuilder_Diagnostics_V3_1_0.csv": csv_text(
            ("configuration", *(name for name, _ in CONTEXT)), context),
        "Formal_Figure_Data_A_D_V3_1_0.csv": csv_text(
            ("figure", "RQ", "configuration", "secondary", "Recall@5", "MRR"), figures),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        for name, content in export().items():
            path = OUTPUT / name
            if args.check:
                actual = path.read_text(encoding="utf-8")
                _verify_equal(actual, content, f"committed CSV {name}")
            else:
                path.write_text(content, encoding="utf-8")
            print(f"{'verified' if args.check else 'wrote'} {path.relative_to(ROOT)}")
    except (
        ExportValidationError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        StopIteration,
    ) as error:
        print(f"Formal CSV validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
