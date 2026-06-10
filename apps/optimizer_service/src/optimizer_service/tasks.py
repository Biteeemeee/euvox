import asyncio
import random
from pathlib import Path

import structlog
from euvox.core.db import make_engine, make_session_factory
from euvox.core.models.mod_version import ModVersion
from euvox.core.models.operation import Operation
from euvox.core.models.simulation_job import SimulationJob
from euvox.core.repositories import (
    ExperimentRepository,
    ModVersionRepository,
    OperationRepository,
    SimulationJobRepository,
    SurrogateSampleRepository,
)
from euvox.search_space import default_search_space_v1
from euvox.surrogate import ExtraTreesSurrogate, FeatureEncoder, SurrogateGuidedOptimizer

from optimizer_service.celery_app import celery_app
from optimizer_service.config import Settings, get_settings
from optimizer_service.optimizers import RandomSearchOptimizer, SimpleEvolutionaryOptimizer

logger = structlog.get_logger()


def _resolve_optimizer(
    experiment_id: str,
    samples: list,
    settings: Settings,
) -> SurrogateGuidedOptimizer | SimpleEvolutionaryOptimizer | RandomSearchOptimizer:
    model_path = Path(settings.surrogate_model_dir) / f"{experiment_id}.joblib"
    if model_path.exists():
        space = default_search_space_v1()
        surrogate = ExtraTreesSurrogate.load(model_path)
        encoder = FeatureEncoder.from_space(space)
        logger.info("surrogate_guided_optimizer_selected", experiment_id=experiment_id)
        return SurrogateGuidedOptimizer(surrogate, encoder)

    if len(samples) >= settings.evolutionary_threshold:
        return SimpleEvolutionaryOptimizer()

    return RandomSearchOptimizer()


@celery_app.task(name="optimizer.generate_candidates", bind=True, max_retries=3)
def generate_candidates(
    self,  # type: ignore[misc]
    experiment_id: str,
    n_candidates: int = 5,
) -> None:
    try:
        asyncio.run(_generate_candidates_async(experiment_id, n_candidates, get_settings()))
    except Exception as exc:
        logger.error("generate_candidates_failed", experiment_id=experiment_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30) from exc


async def _generate_candidates_async(
    experiment_id: str, n_candidates: int, settings: Settings
) -> None:
    log = logger.bind(experiment_id=experiment_id, n_candidates=n_candidates)
    log.info("generating_candidates")

    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)

    try:
        async with factory() as session, session.begin():
            exp_repo = ExperimentRepository(session)
            sample_repo = SurrogateSampleRepository(session)

            exp = await exp_repo.get(experiment_id)
            if exp is None:
                raise ValueError(f"Experiment {experiment_id} not found")

            samples = await sample_repo.list_by_experiment(experiment_id)

        space = default_search_space_v1()
        optimizer = _resolve_optimizer(experiment_id, samples, settings)
        candidate_vectors = optimizer.suggest(samples, space, n=n_candidates)

        for vec in candidate_vectors:
            await _create_candidate(
                factory, experiment_id, vec, exp.search_space_version, settings
            )

        log.info(
            "candidates_generated",
            n=len(candidate_vectors),
            optimizer=type(optimizer).__name__,
        )

    finally:
        await engine.dispose()


async def _create_candidate(
    factory,
    experiment_id: str,
    vec: dict[str, float],
    search_space_version: str,
    settings: Settings,
) -> None:
    async with factory() as session, session.begin():
        op_repo = OperationRepository(session)
        mv_repo = ModVersionRepository(session)
        job_repo = SimulationJobRepository(session)

        ops = []
        for param_name, value in vec.items():
            op = Operation(
                experiment_id=experiment_id,
                operation_type="numeric_patch",
                operation_schema_version="v1",
                operation_spec={"target": param_name, "value": value},
                created_by="optimizer",
                status="ready",
                validation_status="valid",
            )
            await op_repo.create(op)
            ops.append(op)

        mv = ModVersion(
            experiment_id=experiment_id,
            operation_ids=[op.id for op in ops],
            mod_schema_version="v1",
            search_space_version=search_space_version,
            game_version=settings.game_version,
        )
        await mv_repo.create(mv)

        job = SimulationJob(
            experiment_id=experiment_id,
            mod_version_id=mv.id,
            seed=random.randint(1, 1_000_000),
            start_date=settings.default_start_date,
            end_date=settings.default_end_date,
            snapshot_interval_days=365,
            fidelity_level="fake",
            required_game_version=settings.game_version,
        )
        await job_repo.create(job)

        logger.info(
            "candidate_created",
            mod_version_id=mv.id,
            job_id=job.id,
            n_ops=len(ops),
        )
