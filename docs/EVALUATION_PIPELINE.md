# Evaluation Pipeline

## Purpose

The evaluation pipeline turns raw EU5 save snapshots into historical plausibility scores and surrogate training samples.

## Pipeline

```text
Raw save snapshots
→ Save parser
→ Normalized world-state snapshots
→ Metric suite
→ Score breakdown
→ Evaluation record
→ Surrogate training sample
```

## Parser Outputs

Initial normalized tables or JSON structures:

```text
country_snapshot
region_control_snapshot
war_snapshot
colonial_snapshot
event_trace_snapshot
run_metadata
```

## Metric Interface

```python
class Metric(Protocol):
    metric_name: str
    metric_version: str

    def evaluate(self, parsed_run: ParsedRun, targets: HistoricalTargetSet) -> MetricResult:
        ...
```

## Initial Metrics

MVP metrics may be simple stubs:

```text
CountryExistsMetric
GreatPowerRankStubMetric
TerritorialScoreStubMetric
NoCrashMetric
SnapshotCompletenessMetric
```

Later metrics:

```text
TerritorialPlausibilityMetric
ColonialControlMetric
StateContinuityMetric
ReligionCultureMetric
RegionalSideEffectMetric
EventFireRateMetric
InterventionComplexityMetric
```

## Metric Output

Store full breakdown, not only total score.

```json
{
  "score_total": 0.72,
  "metrics": {
    "territorial_plausibility": 0.68,
    "great_power_rank": 0.81,
    "colonial_plausibility": 0.63,
    "side_effect_penalty": -0.04,
    "technical_stability": 1.0
  }
}
```

## Target Sets

Historical targets should be versioned data, not hardcoded logic.

MVP can use YAML/JSON files.

Example:

```yaml
target_set_version: targets_v1
countries:
  FRA:
    1763:
      expected_colonial_regions_not_controlled:
        - louisiana
      expected_major_power_rank_range: [1, 5]
```

## Re-Evaluation

Old runs should be re-evaluable with new parser or metric versions.

Do not overwrite old evaluations. Create new evaluation records.
