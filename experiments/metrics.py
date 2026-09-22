from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Iterable, Mapping, Sequence

from .config import MetricConfig


class MetricValidationError(ValueError):
    pass


@dataclass(frozen=True)
class MetricValues:
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_5: float
    precision_at_5: float
    hit_rate_at_5: float

    def __post_init__(self) -> None:
        for name, value in self.to_record().items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise MetricValidationError(f"{name} must be numeric")
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise MetricValidationError(f"{name} must be finite and between zero and one")

    def to_record(self) -> dict:
        return {
            "recall_at_1": self.recall_at_1,
            "recall_at_5": self.recall_at_5,
            "recall_at_10": self.recall_at_10,
            "mrr": self.mrr,
            "ndcg_at_5": self.ndcg_at_5,
            "precision_at_5": self.precision_at_5,
            "hit_rate_at_5": self.hit_rate_at_5,
        }

    @classmethod
    def zero(cls) -> "MetricValues":
        return cls(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value:
            raise MetricValidationError("ranked identities must be non-empty strings")
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def compute_metrics(
    ranked_identities: Iterable[str],
    relevance: Mapping[str, int],
    *,
    failed: bool = False,
    config: MetricConfig = MetricConfig(),
) -> MetricValues:
    if not isinstance(config, MetricConfig):
        raise MetricValidationError("config must be MetricConfig")
    if type(failed) is not bool:
        raise MetricValidationError("failed must be bool")
    grades: dict[str, int] = {}
    for identity, grade in relevance.items():
        if not isinstance(identity, str) or not identity:
            raise MetricValidationError("truth identities must be non-empty strings")
        if type(grade) is not int or grade not in {0, 1, 2}:
            raise MetricValidationError("truth grades must be 0, 1, or 2")
        grades[identity] = grade
    relevant = {identity for identity, grade in grades.items() if grade > 0}
    if not relevant:
        raise MetricValidationError("metric truth requires a relevant identity")
    if failed:
        return MetricValues.zero()

    ranked = _unique(ranked_identities)

    def recall(k: int) -> float:
        return len(relevant.intersection(ranked[:k])) / len(relevant)

    first_relevant = next(
        (rank for rank, identity in enumerate(ranked[: config.mrr_cutoff], start=1) if identity in relevant),
        None,
    )
    mrr = 0.0 if first_relevant is None else 1.0 / first_relevant
    observed_grades = [grades.get(identity, 0) for identity in ranked[: config.ndcg_k]]
    dcg = math.fsum(
        (2**grade - 1) / math.log2(rank + 1)
        for rank, grade in enumerate(observed_grades, start=1)
    )
    ideal_grades = sorted((grade for grade in grades.values() if grade > 0), reverse=True)[
        : config.ndcg_k
    ]
    ideal_dcg = math.fsum(
        (2**grade - 1) / math.log2(rank + 1)
        for rank, grade in enumerate(ideal_grades, start=1)
    )
    if ideal_dcg <= 0:
        raise MetricValidationError("ideal DCG must be positive")
    relevant_at_five = len(relevant.intersection(ranked[: config.precision_k]))
    return MetricValues(
        recall_at_1=recall(1),
        recall_at_5=recall(5),
        recall_at_10=recall(10),
        mrr=mrr,
        ndcg_at_5=dcg / ideal_dcg,
        precision_at_5=relevant_at_five / config.precision_k,
        hit_rate_at_5=1.0 if relevant_at_five else 0.0,
    )


@dataclass(frozen=True)
class MetricSummary:
    query_count: int
    success_count: int
    failure_count: int
    invalid_count: int
    degraded_count: int
    metrics: MetricValues
    latency_median_ns: int
    latency_p95_ns: int

    def __post_init__(self) -> None:
        counts = (
            self.query_count,
            self.success_count,
            self.failure_count,
            self.invalid_count,
            self.degraded_count,
        )
        if any(type(value) is not int or value < 0 for value in counts):
            raise MetricValidationError("aggregate counts must be non-negative integers")
        if self.success_count + self.failure_count + self.invalid_count != self.query_count:
            raise MetricValidationError("aggregate status counts do not match query_count")
        if self.degraded_count > self.query_count:
            raise MetricValidationError("degraded_count exceeds query_count")
        if type(self.latency_median_ns) is not int or self.latency_median_ns < 0:
            raise MetricValidationError("latency_median_ns must be non-negative")
        if type(self.latency_p95_ns) is not int or self.latency_p95_ns < 0:
            raise MetricValidationError("latency_p95_ns must be non-negative")

    def to_record(self) -> dict:
        return {
            "query_count": self.query_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "invalid_count": self.invalid_count,
            "degraded_count": self.degraded_count,
            "metrics": self.metrics.to_record(),
            "latency": {
                "median_ns": self.latency_median_ns,
                "p95_ns": self.latency_p95_ns,
            },
        }


def summarize_metrics(records: Sequence[object]) -> MetricSummary:
    if not records:
        raise MetricValidationError("cannot aggregate an empty population")
    values = []
    latencies = []
    statuses = []
    degraded = []
    for record in records:
        metric = getattr(record, "metrics", None)
        latency = getattr(record, "latency_ns", None)
        status = getattr(record, "status", None)
        is_degraded = getattr(record, "degraded", None)
        if not isinstance(metric, MetricValues):
            raise MetricValidationError("records must expose MetricValues")
        if type(latency) is not int or latency < 0:
            raise MetricValidationError("record latency must be non-negative integer")
        if status not in {"success", "failed", "invalid"}:
            raise MetricValidationError("record status is invalid")
        if type(is_degraded) is not bool:
            raise MetricValidationError("record degraded must be bool")
        values.append(metric)
        latencies.append(latency)
        statuses.append(status)
        degraded.append(is_degraded)
    count = len(values)
    means = {
        key: math.fsum(item.to_record()[key] for item in values) / count
        for key in values[0].to_record()
    }
    ordered_latency = sorted(latencies)
    p95_index = max(0, math.ceil(0.95 * count) - 1)
    return MetricSummary(
        query_count=count,
        success_count=statuses.count("success"),
        failure_count=statuses.count("failed"),
        invalid_count=statuses.count("invalid"),
        degraded_count=sum(degraded),
        metrics=MetricValues(**means),
        latency_median_ns=int(median(ordered_latency)),
        latency_p95_ns=ordered_latency[p95_index],
    )
