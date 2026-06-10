from __future__ import annotations

from typing import Protocol

from euvox.eu5_parser.types import ParsedRun
from euvox.metrics.types import EvaluationResult, HistoricalTargetSet, MetricResult

SUITE_VERSION = "v1"


class Metric(Protocol):
    metric_name: str
    metric_version: str

    def evaluate(self, parsed: ParsedRun, targets: HistoricalTargetSet) -> MetricResult:
        ...


class NoCrashMetric:
    metric_name = "no_crash"
    metric_version = "v1"

    def evaluate(self, parsed: ParsedRun, targets: HistoricalTargetSet) -> MetricResult:
        score = 1.0 if parsed.exit_status == "success" else 0.0
        return MetricResult(
            metric_name=self.metric_name,
            metric_version=self.metric_version,
            score=score,
            detail={"exit_status": parsed.exit_status},
        )


class SnapshotCompletenessMetric:
    metric_name = "snapshot_completeness"
    metric_version = "v1"

    def evaluate(self, parsed: ParsedRun, targets: HistoricalTargetSet) -> MetricResult:
        if parsed.total_snapshots == 0:
            return MetricResult(
                metric_name=self.metric_name,
                metric_version=self.metric_version,
                score=0.0,
                detail={"snapshots": 0},
            )
        start_year = int(parsed.metadata.start_date.split(".")[0])
        end_year = int(parsed.metadata.end_date.split(".")[0])
        years = max(1, end_year - start_year)
        expected = max(1, years // max(1, 100 // targets.expected_snapshots_per_century))
        score = min(1.0, parsed.total_snapshots / expected)
        return MetricResult(
            metric_name=self.metric_name,
            metric_version=self.metric_version,
            score=score,
            detail={"actual": parsed.total_snapshots, "expected": expected},
        )


class GreatPowerRankStubMetric:
    metric_name = "great_power_rank"
    metric_version = "stub_v1"

    def evaluate(self, parsed: ParsedRun, targets: HistoricalTargetSet) -> MetricResult:
        if not parsed.country_snapshots:
            return MetricResult(
                metric_name=self.metric_name,
                metric_version=self.metric_version,
                score=0.0,
            )
        last = parsed.country_snapshots[-1]
        return MetricResult(
            metric_name=self.metric_name,
            metric_version=self.metric_version,
            score=min(1.0, max(0.0, last.great_power_score)),
            detail={"great_power_score": last.great_power_score, "date": last.date},
        )


class TerritorialScoreStubMetric:
    metric_name = "territorial_score"
    metric_version = "stub_v1"

    def evaluate(self, parsed: ParsedRun, targets: HistoricalTargetSet) -> MetricResult:
        if not parsed.country_snapshots:
            return MetricResult(
                metric_name=self.metric_name,
                metric_version=self.metric_version,
                score=0.0,
            )
        last = parsed.country_snapshots[-1]
        total = last.provinces_total or 1
        score = min(1.0, last.provinces_owned / total)
        return MetricResult(
            metric_name=self.metric_name,
            metric_version=self.metric_version,
            score=score,
            detail={"owned": last.provinces_owned, "total": total},
        )


_WEIGHTS: dict[str, float] = {
    "no_crash": 0.30,
    "snapshot_completeness": 0.30,
    "great_power_rank": 0.20,
    "territorial_score": 0.20,
}


class MetricSuite:
    def __init__(self, metrics: list[Metric], version: str = SUITE_VERSION) -> None:
        self._metrics = metrics
        self.version = version

    @classmethod
    def default(cls) -> MetricSuite:
        return cls(
            [
                NoCrashMetric(),
                SnapshotCompletenessMetric(),
                GreatPowerRankStubMetric(),
                TerritorialScoreStubMetric(),
            ]
        )

    def evaluate(self, parsed: ParsedRun, targets: HistoricalTargetSet) -> EvaluationResult:
        results = [m.evaluate(parsed, targets) for m in self._metrics]
        breakdown: dict[str, float] = {r.metric_name: r.score for r in results}
        score_total = sum(
            _WEIGHTS.get(r.metric_name, 0.0) * r.score for r in results
        )
        return EvaluationResult(
            score_total=round(score_total, 6),
            breakdown=breakdown,
            details=results,
            metric_suite_version=self.version,
        )
