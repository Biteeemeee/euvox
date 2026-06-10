"""Unit tests for eu5_parser, metrics, and the evaluation pipeline."""

import json
from pathlib import Path

import pytest
from euvox.eu5_parser import CountrySnapshot, FakeParser, ParsedRun, RunMetadata
from euvox.metrics import (
    GreatPowerRankStubMetric,
    HistoricalTargetSet,
    MetricSuite,
    NoCrashMetric,
    SnapshotCompletenessMetric,
    TerritorialScoreStubMetric,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_parsed_run(
    exit_status: str = "success",
    snapshots: int = 6,
    start_year: int = 1444,
    end_year: int = 1450,
) -> ParsedRun:
    country_snapshots = [
        CountrySnapshot(
            date=f"{start_year + i}.01.01",
            great_power_score=0.3 + i * 0.01,
            economy_score=0.5 + i * 0.005,
            stability_score=0.6,
            provinces_owned=50 + i,
            provinces_total=1000,
        )
        for i in range(snapshots)
    ]
    return ParsedRun(
        metadata=RunMetadata(
            seed=42,
            mod_version_id="mv-1",
            start_date=f"{start_year}.11.11",
            end_date=f"{end_year}.01.01",
            game_version="1.0.0",
            fidelity_level="fake",
        ),
        country_snapshots=country_snapshots,
        snapshot_dates=[s.date for s in country_snapshots],
        total_snapshots=len(country_snapshots),
        exit_status=exit_status,
        parser_version="fake@v1",
    )


# ── NoCrashMetric ─────────────────────────────────────────────────────────────


def test_no_crash_success() -> None:
    metric = NoCrashMetric()
    result = metric.evaluate(_make_parsed_run(exit_status="success"), HistoricalTargetSet())
    assert result.score == 1.0


def test_no_crash_failure() -> None:
    metric = NoCrashMetric()
    result = metric.evaluate(_make_parsed_run(exit_status="crash"), HistoricalTargetSet())
    assert result.score == 0.0


# ── SnapshotCompletenessMetric ────────────────────────────────────────────────


def test_snapshot_completeness_full() -> None:
    metric = SnapshotCompletenessMetric()
    parsed = _make_parsed_run(snapshots=6, start_year=1444, end_year=1450)
    result = metric.evaluate(parsed, HistoricalTargetSet())
    assert result.score == 1.0


def test_snapshot_completeness_zero() -> None:
    metric = SnapshotCompletenessMetric()
    parsed = _make_parsed_run(snapshots=0)
    result = metric.evaluate(parsed, HistoricalTargetSet())
    assert result.score == 0.0


# ── GreatPowerRankStubMetric ──────────────────────────────────────────────────


def test_great_power_rank_uses_last_snapshot() -> None:
    metric = GreatPowerRankStubMetric()
    parsed = _make_parsed_run(snapshots=5)
    result = metric.evaluate(parsed, HistoricalTargetSet())
    last_gp = parsed.country_snapshots[-1].great_power_score
    assert abs(result.score - last_gp) < 1e-9


def test_great_power_rank_empty_run() -> None:
    metric = GreatPowerRankStubMetric()
    parsed = _make_parsed_run(snapshots=0)
    assert metric.evaluate(parsed, HistoricalTargetSet()).score == 0.0


# ── TerritorialScoreStubMetric ────────────────────────────────────────────────


def test_territorial_score_last_snapshot() -> None:
    metric = TerritorialScoreStubMetric()
    parsed = _make_parsed_run(snapshots=3)
    result = metric.evaluate(parsed, HistoricalTargetSet())
    last = parsed.country_snapshots[-1]
    expected = last.provinces_owned / last.provinces_total
    assert abs(result.score - expected) < 1e-9


# ── MetricSuite ───────────────────────────────────────────────────────────────


def test_metric_suite_default_keys() -> None:
    suite = MetricSuite.default()
    result = suite.evaluate(_make_parsed_run(), HistoricalTargetSet())
    assert "no_crash" in result.breakdown
    assert "snapshot_completeness" in result.breakdown
    assert "great_power_rank" in result.breakdown
    assert "territorial_score" in result.breakdown


def test_metric_suite_score_total_range() -> None:
    suite = MetricSuite.default()
    result = suite.evaluate(_make_parsed_run(), HistoricalTargetSet())
    assert 0.0 <= result.score_total <= 1.0


def test_metric_suite_crash_lowers_score() -> None:
    suite = MetricSuite.default()
    good = suite.evaluate(_make_parsed_run(exit_status="success"), HistoricalTargetSet())
    bad = suite.evaluate(_make_parsed_run(exit_status="crash"), HistoricalTargetSet())
    assert good.score_total > bad.score_total


def test_metric_suite_version() -> None:
    suite = MetricSuite.default()
    result = suite.evaluate(_make_parsed_run(), HistoricalTargetSet())
    assert result.metric_suite_version == "v1"


# ── FakeParser ────────────────────────────────────────────────────────────────


def _write_fake_saves(base_dir: Path, dates: list[str], seed: int = 42) -> dict:
    saves_dir = base_dir / "saves"
    saves_dir.mkdir(parents=True)
    snapshots = []
    for i, date in enumerate(dates):
        payload = {
            "date": date,
            "seed": seed,
            "mod_version_id": "mv-test",
            "scores": {
                "great_power_score": 0.3 + i * 0.01,
                "economy_score": 0.5,
                "stability_score": 0.6,
            },
            "provinces": {"total": 1000, "owned": 50 + i},
        }
        fname = f"{date}.json"
        (saves_dir / fname).write_text(json.dumps(payload))
        snapshots.append({"date": date, "filename": fname, "size_bytes": 100})
    return {
        "seed": seed,
        "start_date": dates[0].replace(".01.01", ".11.11") if dates else "1444.11.11",
        "end_date": dates[-1] if dates else "1450.01.01",
        "game_version": "1.0.0",
        "fidelity_level": "fake",
        "snapshots": snapshots,
    }


def test_fake_parser_reads_saves(tmp_path: Path) -> None:
    manifest = _write_fake_saves(tmp_path, ["1444.01.01", "1445.01.01", "1446.01.01"])
    parser = FakeParser()
    parsed = parser.parse(f"file://{tmp_path}", manifest)
    assert parsed.total_snapshots == 3
    assert parsed.parser_version == "fake@v1"
    assert len(parsed.country_snapshots) == 3
    assert parsed.country_snapshots[0].date == "1444.01.01"


def test_fake_parser_scores_correct(tmp_path: Path) -> None:
    manifest = _write_fake_saves(tmp_path, ["1444.01.01"])
    parser = FakeParser()
    parsed = parser.parse(f"file://{tmp_path}", manifest)
    snap = parsed.country_snapshots[0]
    assert snap.great_power_score == pytest.approx(0.3)
    assert snap.provinces_owned == 50
    assert snap.provinces_total == 1000


def test_fake_parser_missing_file_skipped(tmp_path: Path) -> None:
    manifest = {
        "seed": 1,
        "start_date": "1444.11.11",
        "end_date": "1450.01.01",
        "game_version": "1.0.0",
        "fidelity_level": "fake",
        "snapshots": [{"date": "1444.01.01", "filename": "missing.json", "size_bytes": 0}],
    }
    (tmp_path / "saves").mkdir()
    parser = FakeParser()
    parsed = parser.parse(f"file://{tmp_path}", manifest)
    assert parsed.total_snapshots == 0


# ── Vectorization ─────────────────────────────────────────────────────────────


def test_vectorize_numeric_patch_ops() -> None:
    from evaluation_service.tasks import vectorize_operations

    class FakeOp:
        operation_type = "numeric_patch"
        operation_schema_version = "v1"
        operation_spec = {"target": "war_cost_factor", "value": 1.15}

    vector = vectorize_operations([FakeOp()])
    assert vector == {"numeric_patch.war_cost_factor": 1.15}


def test_vectorize_unknown_op_skipped() -> None:
    from evaluation_service.tasks import vectorize_operations

    class UnknownOp:
        operation_type = "create_event"
        operation_schema_version = "v1"
        operation_spec = {"event_id": "foo.1"}

    vector = vectorize_operations([UnknownOp()])
    assert vector == {}
