from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricResult:
    metric_name: str
    metric_version: str
    score: float
    detail: dict[str, object] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    score_total: float
    breakdown: dict[str, float]
    details: list[MetricResult] = field(default_factory=list)
    metric_suite_version: str = "v1"


@dataclass
class HistoricalTargetSet:
    target_set_version: str = "stub_v1"
    expected_snapshots_per_century: int = 10
