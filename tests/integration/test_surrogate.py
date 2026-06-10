"""Integration test: train surrogate from scored samples → optimizer uses it to rank candidates."""

from pathlib import Path

import httpx
import pytest
from control_api.main import app
from euvox.core.models import Base, Run
from euvox.core.repositories import SimulationJobRepository, SurrogateSampleRepository
from evaluation_service.config import Settings as EvalSettings
from evaluation_service.tasks import _evaluate_run_async
from httpx import ASGITransport
from optimizer_service.config import Settings as OptSettings
from optimizer_service.tasks import _generate_candidates_async
from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings as SimSettings
from simulation_client.worker import SimulationWorker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from surrogate_service.config import Settings as SurSettings
from surrogate_service.tasks import _train_surrogate_async


@pytest.fixture
async def sur_db(tmp_path: Path):
    db_file = tmp_path / "sur_test.db"
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


async def test_surrogate_training_and_guided_selection(sur_db, tmp_path: Path) -> None:
    """Train surrogate on 6 scored samples, then optimizer uses surrogate for next round."""
    engine, factory, db_url = sur_db
    surrogate_dir = tmp_path / "surrogates"

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={
                "name": "Surrogate Test",
                "target_set_version": "v1",
                "search_space_version": "v1",
            },
        )
        experiment_id = r.json()["id"]

    opt_settings = OptSettings(
        database_url=db_url,
        broker_url="memory://",
        surrogate_model_dir=str(surrogate_dir),
    )
    eval_settings = EvalSettings(database_url=db_url, broker_url="memory://")

    # ── Step 1: bootstrap 6 scored samples ───────────────────────────────────
    await _generate_candidates_async(experiment_id, n_candidates=6, settings=opt_settings)

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        ctrl = ControlApiClient(http)
        client_dto = await ctrl.register("sur-worker", "0.1.0", "fp-sur")
        sim_settings = SimSettings(
            control_api_url="http://test",
            work_dir=tmp_path,
            poll_interval=0.0,
            heartbeat_interval=999.0,
        )
        worker = SimulationWorker(ctrl, sim_settings)
        for _ in range(6):
            await worker.run_once(client_dto.id)

    async with factory() as session:
        result = await session.execute(select(Run))
        runs = list(result.scalars().all())

    for run in runs:
        await _evaluate_run_async(run.id, eval_settings)

    async with factory() as session:
        samples = await SurrogateSampleRepository(session).list_by_experiment(experiment_id)
    assert len(samples) == 6

    # ── Step 2: train surrogate ───────────────────────────────────────────────
    sur_settings = SurSettings(
        database_url=db_url,
        broker_url="memory://",
        surrogate_model_dir=str(surrogate_dir),
        min_samples_to_train=5,
    )
    model_path = await _train_surrogate_async(experiment_id, sur_settings)
    assert model_path is not None
    assert Path(model_path).exists()

    # ── Step 3: optimizer uses surrogate (model file present) ─────────────────
    await _generate_candidates_async(experiment_id, n_candidates=3, settings=opt_settings)

    async with factory() as session:
        new_jobs = await SimulationJobRepository(session).list_pending()
    assert len(new_jobs) == 3


async def test_surrogate_skipped_below_threshold(sur_db, tmp_path: Path) -> None:
    """Surrogate training returns None when insufficient samples exist."""
    _, _, db_url = sur_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        r = await http.post(
            "/experiments",
            json={"name": "Skip Test", "target_set_version": "v1", "search_space_version": "v1"},
        )
        experiment_id = r.json()["id"]

    sur_settings = SurSettings(
        database_url=db_url,
        broker_url="memory://",
        surrogate_model_dir=str(tmp_path / "surrogates"),
        min_samples_to_train=5,
    )
    result = await _train_surrogate_async(experiment_id, sur_settings)
    assert result is None
