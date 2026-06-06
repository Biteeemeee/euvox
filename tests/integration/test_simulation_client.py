"""End-to-end test: fake simulation client registers, claims a job, runs it, uploads artifacts."""

from pathlib import Path

import httpx
from control_api.main import app
from httpx import ASGITransport, AsyncClient
from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings
from simulation_client.worker import SimulationWorker


async def _create_pending_job(api_client: AsyncClient) -> tuple[str, str]:
    """Create experiment + mod_version + job; return (experiment_id, job_id)."""
    r = await api_client.post(
        "/experiments",
        json={"name": "E2E Sim", "target_set_version": "v1", "search_space_version": "v1"},
    )
    exp_id = r.json()["id"]

    r = await api_client.post(
        "/mod-versions",
        json={
            "experiment_id": exp_id,
            "mod_schema_version": "v1",
            "search_space_version": "v1",
            "game_version": "1.0.0",
        },
    )
    mv_id = r.json()["id"]

    r = await api_client.post(
        "/jobs",
        json={
            "experiment_id": exp_id,
            "mod_version_id": mv_id,
            "seed": 7,
            "start_date": "1444.11.11",
            "end_date": "1450.01.01",
            "required_game_version": "1.0.0",
        },
    )
    return exp_id, r.json()["id"]


async def test_fake_runner_produces_snapshots(tmp_path: Path) -> None:
    """FakeRunner writes correctly structured save files for a short sim window."""
    from datetime import UTC, datetime

    from euvox.common_schemas import SimulationJobDTO
    from simulation_client.runner import FakeRunner

    job = SimulationJobDTO(
        experiment_id="exp-1",
        mod_version_id="mv-1",
        seed=42,
        start_date="1444.11.11",
        end_date="1450.01.01",
        required_game_version="1.0.0",
        created_at=datetime.now(UTC),
    )
    runner = FakeRunner(tmp_path)
    manifest, job_dir = await runner.run(job)

    assert (job_dir / "error.log").exists()
    saves = list((job_dir / "saves").glob("*.json"))
    assert len(saves) == len(manifest.snapshots)
    assert len(saves) >= 1
    assert manifest.runner == "fake"
    assert manifest.elapsed_seconds >= 0


async def test_end_to_end_fake_job(api_client: AsyncClient, tmp_path: Path) -> None:
    """Prove milestone 3: register → claim → run → upload artifacts → complete."""

    _, job_id = await _create_pending_job(api_client)

    # Reuse the same in-process app (with the SQLite DB already set on app.state)
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        api = ControlApiClient(http)
        client_dto = await api.register("e2e-worker", "0.1.0", "fp-e2e")

        settings = Settings(
            control_api_url="http://test",
            work_dir=tmp_path,
            poll_interval=0.0,
            heartbeat_interval=999.0,
        )
        worker = SimulationWorker(api, settings)
        processed = await worker.run_once(client_dto.id)

    assert processed is True

    # Job must be completed
    r = await api_client.get(f"/jobs/{job_id}")
    assert r.json()["status"] == "completed"
    assert r.json()["completed_at"] is not None

    # Run must exist with success status and artifact URI
    r = await api_client.get("/runs", params={"job_id": job_id})
    runs = r.json()
    assert len(runs) == 1
    assert runs[0]["exit_status"] == "success"
    assert runs[0]["finished_at"] is not None
    assert runs[0]["artifact_root_uri"].startswith("file://")
    manifest = runs[0]["run_manifest"]
    assert manifest["runner"] == "fake"
    assert len(manifest["snapshots"]) >= 1

    # Artifact files must exist on disk
    saves_dir = tmp_path / job_id / "saves"
    assert saves_dir.exists()
    snapshots_on_disk = list(saves_dir.glob("*.json"))
    assert len(snapshots_on_disk) == len(manifest["snapshots"])


async def test_no_job_returns_false(api_client: AsyncClient, tmp_path: Path) -> None:
    """Worker run_once returns False when there are no pending jobs."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        api = ControlApiClient(http)
        client_dto = await api.register("idle-worker", "0.1.0", "fp-idle")

        settings = Settings(
            control_api_url="http://test",
            work_dir=tmp_path,
            poll_interval=0.0,
            heartbeat_interval=999.0,
        )
        worker = SimulationWorker(api, settings)
        processed = await worker.run_once(client_dto.id)

    assert processed is False


async def test_double_claim_handled(api_client: AsyncClient, tmp_path: Path) -> None:
    """Second worker skips a job that is already claimed by the first."""
    _, job_id = await _create_pending_job(api_client)

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        api1 = ControlApiClient(http)
        api2 = ControlApiClient(http)

        c1 = await api1.register("worker-a", "0.1.0", "fp-a")
        c2 = await api2.register("worker-b", "0.1.0", "fp-b")

        settings = Settings(work_dir=tmp_path, poll_interval=0.0, heartbeat_interval=999.0)

        w1 = SimulationWorker(api1, settings)
        w2 = SimulationWorker(api2, settings)

        # Both workers try to process; only one should succeed
        p1 = await w1.run_once(c1.id)
        p2 = await w2.run_once(c2.id)

    # w1 ran first and succeeded; w2 found nothing left
    assert p1 is True
    assert p2 is False
