"""Integration test: a completed fake run is parsed, evaluated, and persisted."""

from pathlib import Path

import httpx
import pytest
from control_api.main import app
from euvox.core.models import Base
from euvox.core.repositories import EvaluationRepository, SurrogateSampleRepository
from evaluation_service.config import Settings as EvalSettings
from evaluation_service.tasks import _evaluate_run_async
from httpx import ASGITransport
from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings as SimSettings
from simulation_client.worker import SimulationWorker
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def full_db(tmp_path: Path):
    """File-based SQLite DB with all tables (including evaluation tables)."""
    db_file = tmp_path / "test.db"
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


async def test_evaluate_completed_run(full_db, tmp_path: Path) -> None:
    """Full pipeline: fake client completes a job → evaluate_run stores scores."""
    engine, factory, db_url = full_db

    # ── Step 1: run the simulation client to create a completed run ──────────
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        ctrl = ControlApiClient(http)

        r = await http.post(
            "/experiments",
            json={"name": "Eval Test", "target_set_version": "v1", "search_space_version": "v1"},
        )
        experiment_id = r.json()["id"]

        r = await http.post(
            "/mod-versions",
            json={
                "experiment_id": experiment_id,
                "mod_schema_version": "v1",
                "search_space_version": "v1",
                "game_version": "1.0.0",
            },
        )
        mod_version_id = r.json()["id"]

        r = await http.post(
            "/jobs",
            json={
                "experiment_id": experiment_id,
                "mod_version_id": mod_version_id,
                "seed": 99,
                "start_date": "1444.11.11",
                "end_date": "1450.01.01",
                "required_game_version": "1.0.0",
            },
        )
        job_id = r.json()["id"]

        client_dto = await ctrl.register("eval-worker", "0.1.0", "fp-eval")
        sim_settings = SimSettings(
            control_api_url="http://test",
            work_dir=tmp_path,
            poll_interval=0.0,
            heartbeat_interval=999.0,
        )
        worker = SimulationWorker(ctrl, sim_settings)
        processed = await worker.run_once(client_dto.id)
        assert processed is True

        r = await http.get("/runs", params={"job_id": job_id})
        runs = r.json()
        assert len(runs) == 1
        run_id = runs[0]["id"]

    # ── Step 2: run evaluation directly (no Celery broker needed) ────────────
    eval_settings = EvalSettings(
        database_url=db_url,
        broker_url="memory://",
    )

    await _evaluate_run_async(run_id, eval_settings)

    # ── Step 3: verify Evaluation and SurrogateSample records in DB ──────────
    async with factory() as session:
        eval_repo = EvaluationRepository(session)
        sample_repo = SurrogateSampleRepository(session)

        evals = await eval_repo.list_by_run(run_id)
        assert len(evals) == 1
        ev = evals[0]
        assert ev.run_id == run_id
        assert ev.experiment_id == experiment_id
        assert ev.parser_version == "fake@v1"
        assert ev.metric_suite_version == "v1"
        assert 0.0 <= ev.score_total <= 1.0
        assert "no_crash" in ev.score_breakdown
        assert ev.score_breakdown["no_crash"] == 1.0

        samples = await sample_repo.list_by_experiment(experiment_id)
        assert len(samples) == 1
        s = samples[0]
        assert s.evaluation_id == ev.id
        assert s.score_total == ev.score_total
        assert s.search_space_version == "v1"
