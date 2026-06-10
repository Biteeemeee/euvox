import json
from pathlib import Path

from euvox.eu5_parser.types import CountrySnapshot, ParsedRun, RunMetadata


def _uri_to_path(uri: str) -> Path:
    if uri.startswith("file://"):
        return Path(uri[7:])
    raise ValueError(f"FakeParser only supports file:// URIs, got: {uri!r}")


class FakeParser:
    """Reads the JSON save files produced by FakeRunner."""

    parser_version = "fake@v1"

    def parse(self, artifact_root_uri: str, run_manifest: dict[str, object]) -> ParsedRun:
        root = _uri_to_path(artifact_root_uri)
        saves_dir = root / "saves"

        raw_snapshots: list[dict[str, object]] = []
        country_snapshots: list[CountrySnapshot] = []

        for rec in run_manifest.get("snapshots", []):  # type: ignore[union-attr]
            filename = str(rec["filename"])
            path = saves_dir / filename
            if not path.exists():
                continue
            data: dict[str, object] = json.loads(path.read_text())
            raw_snapshots.append(data)

            scores = data.get("scores") or {}
            provinces = data.get("provinces") or {}
            country_snapshots.append(
                CountrySnapshot(
                    date=str(data.get("date", "")),
                    great_power_score=float(scores.get("great_power_score", 0.0)),  # type: ignore[arg-type]
                    economy_score=float(scores.get("economy_score", 0.0)),  # type: ignore[arg-type]
                    stability_score=float(scores.get("stability_score", 0.0)),  # type: ignore[arg-type]
                    provinces_owned=int(provinces.get("owned", 0)),  # type: ignore[arg-type]
                    provinces_total=int(provinces.get("total", 1000)),  # type: ignore[arg-type]
                )
            )

        metadata = RunMetadata(
            seed=int(run_manifest.get("seed", 0)),  # type: ignore[arg-type]
            mod_version_id="",
            start_date=str(run_manifest.get("start_date", "")),
            end_date=str(run_manifest.get("end_date", "")),
            game_version=str(run_manifest.get("game_version", "")),
            fidelity_level=str(run_manifest.get("fidelity_level", "fake")),
        )

        return ParsedRun(
            metadata=metadata,
            country_snapshots=country_snapshots,
            snapshot_dates=[s.date for s in country_snapshots],
            total_snapshots=len(country_snapshots),
            exit_status=str(run_manifest.get("exit_status", "success")),
            parser_version=self.parser_version,
            raw_snapshots=raw_snapshots,
        )
