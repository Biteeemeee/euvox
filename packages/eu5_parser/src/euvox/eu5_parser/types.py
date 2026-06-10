from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CountrySnapshot:
    date: str
    great_power_score: float
    economy_score: float
    stability_score: float
    provinces_owned: int
    provinces_total: int


@dataclass
class RunMetadata:
    seed: int
    mod_version_id: str
    start_date: str
    end_date: str
    game_version: str
    fidelity_level: str


@dataclass
class ParsedRun:
    metadata: RunMetadata
    country_snapshots: list[CountrySnapshot]
    snapshot_dates: list[str]
    total_snapshots: int
    exit_status: str
    parser_version: str
    raw_snapshots: list[dict[str, object]] = field(default_factory=list)
