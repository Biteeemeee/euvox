"""Integration test: optimizer generates candidates → simulation + evaluation loop."""

from pathlib import Path

import httpx
import pytest
from control_api.main import app
from euvox.core.models import Base
from euvox.core.repositories import SimulationJobRepository, SurrogateSampleRepository
from evaluation_service.config import Settings as EvalSettings
from evaluation_service.tasks import _evaluate_run_async
from httpx import ASGITransport
from optimizer_service.config import Settings as OptSettings
from optimizer_service.tasks import _generate_candidates_async
from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings as SimSettings
from simulation_client.worker import SimulationWorker
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def opt_db(tmp_path: Path):
    db_file = tmp_path / "opt_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.engine = engine
    app.state.session_factory = factory

    yield engine, factory, db_url

    del app.state.engine
    del app.state.session_factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_optimizer_generates_candidates_and_runs(opt_db, tmp_path: Path) -> None:
    """Optimizer creates 3 candidate mod_versions+jobs; sim+eval pipeline processes them."""
    engine, factory, db_url = opt_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={"name": "Opt Test", "target_set_version": "v1", "search_space_version": "v1"},
        )
        assert r.status_code == 201
        experiment_id = r.json()["id"]

    # ── Generate candidates directly (no Celery) ─────────────────────────────
    opt_settings = OptSettings(
        database_url=db_url,
        broker_url="memory://",
    )
    await _generate_candidates_async(experiment_id, n_candidates=3, settings=opt_settings)

    # ── Verify 3 pending jobs were created ────────────────────────────────────
    async with factory() as session:
        job_repo = SimulationJobRepository(session)
        jobs = await job_repo.list_pending()
    assert len(jobs) == 3

    # ── Run simulation client for each job ────────────────────────────────────
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        ctrl = ControlApiClient(http)
        client_dto = await ctrl.register("opt-worker", "0.1.0", "fp-opt")
        sim_settings = SimSettings(
            control_api_url="http://test",
            work_dir=tmp_path,
            poll_interval=0.0,
            heartbeat_interval=999.0,
        )
        worker = SimulationWorker(ctrl, sim_settings)

        for _ in range(3):
            processed = await worker.run_once(client_dto.id)
            assert processed is True

        # All 3 jobs consumed, no more pending
        processed = await worker.run_once(client_dto.id)
        assert processed is False

    # ── Evaluate all 3 runs ───────────────────────────────────────────────────
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.get("/runs", params={"job_id": jobs[0].id})
        run_ids = []
        for job in jobs:
            r = await http.get("/runs", params={"job_id": job.id})
            assert len(r.json()) == 1
            run_ids.append(r.json()[0]["id"])

    eval_settings = EvalSettings(database_url=db_url, broker_url="memory://")
    for run_id in run_ids:
        await _evaluate_run_async(run_id, eval_settings)

    # ── Verify surrogate samples created for all 3 ────────────────────────────
    async with factory() as session:
        sample_repo = SurrogateSampleRepository(session)
        samples = await sample_repo.list_by_experiment(experiment_id)

    assert len(samples) == 3
    for s in samples:
        assert 0.0 <= s.score_total <= 1.0
        assert s.operation_vector  # non-empty vector
        assert s.search_space_version == "v1"


async def test_random_optimizer_below_threshold(opt_db, tmp_path: Path) -> None:
    """With no prior samples, optimizer uses random search."""
    _, _, db_url = opt_db

    opt_settings = OptSettings(database_url=db_url, broker_url="memory://")

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={"name": "Rand Test", "target_set_version": "v1", "search_space_version": "v1"},
        )
        experiment_id = r.json()["id"]

    await _generate_candidates_async(experiment_id, n_candidates=2, settings=opt_settings)

    engine = opt_db[0]
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        job_repo = SimulationJobRepository(session)
        jobs = await job_repo.list_pending()

    assert len(jobs) == 2
