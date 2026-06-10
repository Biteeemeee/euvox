import asyncio
from pathlib import Path

import numpy as np
import structlog
from euvox.core.db import make_engine, make_session_factory
from euvox.core.repositories import ExperimentRepository, SurrogateSampleRepository
from euvox.search_space import default_search_space_v1
from euvox.surrogate import ExtraTreesSurrogate, FeatureEncoder

from surrogate_service.celery_app import celery_app
from surrogate_service.config import Settings, get_settings

logger = structlog.get_logger()


@celery_app.task(name="surrogate.train_surrogate", bind=True, max_retries=3)
def train_surrogate(self, experiment_id: str) -> str | None:  # type: ignore[misc]
    try:
        return asyncio.run(_train_surrogate_async(experiment_id, get_settings()))
    except Exception as exc:
        logger.error("train_surrogate_failed", experiment_id=experiment_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30) from exc


async def _train_surrogate_async(experiment_id: str, settings: Settings) -> str | None:
    """Fits a surrogate on all scored samples for the experiment.

    Returns the path to the saved model file, or None if insufficient data.
    """
    log = logger.bind(experiment_id=experiment_id)
    log.info("surrogate_training_started")

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

        if len(samples) < settings.min_samples_to_train:
            log.info(
                "surrogate_skipped_insufficient_data",
                n_samples=len(samples),
                required=settings.min_samples_to_train,
            )
            return None

        space = default_search_space_v1()
        encoder = FeatureEncoder.from_space(space)

        X = encoder.transform_batch([dict(s.operation_vector) for s in samples])
        y = np.array([s.score_total for s in samples], dtype=np.float64)

        surrogate = ExtraTreesSurrogate()
        surrogate.fit(X, y)

        model_path = Path(settings.surrogate_model_dir) / f"{experiment_id}.joblib"
        surrogate.save(model_path)

        log.info("surrogate_trained", n_samples=len(samples), model_path=str(model_path))
        return str(model_path)

    finally:
        await engine.dispose()
