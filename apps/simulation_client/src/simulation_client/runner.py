import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from euvox.common_schemas import SimulationJobDTO


@dataclass
class SnapshotRecord:
    date: str
    filename: str
    size_bytes: int


@dataclass
class RunManifest:
    runner: str
    game_version: str
    seed: int
    start_date: str
    end_date: str
    fidelity_level: str
    elapsed_seconds: float
    snapshots: list[SnapshotRecord]

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "snapshots": [asdict(s) for s in self.snapshots]}


class FakeRunner:
    """Simulates EU5 by writing JSON snapshot files without launching any real process."""

    def __init__(self, work_dir: Path) -> None:
        self._work_dir = work_dir

    async def run(self, job: SimulationJobDTO) -> tuple[RunManifest, Path]:
        job_dir = self._work_dir / job.id
        saves_dir = job_dir / "saves"
        saves_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.monotonic()
        snapshots = await self._write_snapshots(job, saves_dir)
        (job_dir / "error.log").write_text("")

        manifest = RunManifest(
            runner="fake",
            game_version=job.required_game_version,
            seed=job.seed,
            start_date=job.start_date,
            end_date=job.end_date,
            fidelity_level=job.fidelity_level,
            elapsed_seconds=round(time.monotonic() - t0, 3),
            snapshots=snapshots,
        )
        return manifest, job_dir

    async def _write_snapshots(
        self, job: SimulationJobDTO, saves_dir: Path
    ) -> list[SnapshotRecord]:
        start_year = int(job.start_date.split(".")[0])
        end_year = int(job.end_date.split(".")[0])
        interval_years = max(1, job.snapshot_interval_days // 365)

        records: list[SnapshotRecord] = []
        for year in range(start_year, end_year + 1, interval_years):
            date = f"{year}.01.01"
            path = saves_dir / f"{date}.json"
            years_elapsed = year - start_year
            payload = {
                "date": date,
                "seed": job.seed,
                "mod_version_id": job.mod_version_id,
                "scores": {
                    "great_power_score": round(0.3 + years_elapsed * 0.002, 4),
                    "economy_score": round(0.5 + years_elapsed * 0.001, 4),
                    "stability_score": round(0.6 - years_elapsed * 0.0005, 4),
                },
                "provinces": {"total": 1000, "owned": 50 + years_elapsed * 2},
            }
            path.write_text(json.dumps(payload, indent=2))
            records.append(
                SnapshotRecord(date=date, filename=path.name, size_bytes=path.stat().st_size)
            )
            await asyncio.sleep(0)  # yield to event loop between snapshots

        return records
