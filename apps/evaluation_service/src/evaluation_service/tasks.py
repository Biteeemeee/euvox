import asyncio
from datetime import UTC, datetime

import structlog
from euvox.core.db import make_engine, make_session_factory
from euvox.core.models.evaluation import Evaluation
from euvox.core.models.surrogate_sample import SurrogateSample
from euvox.core.repositories import (
    EvaluationRepository,
    ModVersionRepository,
    OperationRepository,
    RunRepository,
    SimulationJobRepository,
    SurrogateSampleRepository,
)
from euvox.eu5_parser import FakeParser
from euvox.metrics import HistoricalTargetSet, MetricSuite

from evaluation_service.celery_app import celery_app
from evaluation_service.config import Settings, get_settings

logger = structlog.get_logger()


def vectorize_operations(ops: list) -> dict[str, float]:
    """Produce a flat float vector from a list of Operation ORM objects."""
    vector: dict[str, float] = {}
    for op in ops:
        if op.operation_type == "numeric_patch" and op.operation_schema_version == "v1":
            target = op.operation_spec.get("target", "")
            value = op.operation_spec.get("value", 0.0)
            if target and isinstance(value, (int, float)):
                vector[f"numeric_patch.{target}"] = float(value)
    return vector


@celery_app.task(name="evaluation.evaluate_run", bind=True, max_retries=3)
def evaluate_run(self, run_id: str) -> None:  # type: ignore[misc]
    try:
        asyncio.run(_evaluate_run_async(run_id, get_settings()))
    except Exception as exc:
        logger.error("evaluate_run_failed", run_id=run_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30) from exc


async def _evaluate_run_async(run_id: str, settings: Settings) -> None:
    log = logger.bind(run_id=run_id)
    log.info("evaluation_started")

    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)

    try:
        async with factory() as session, session.begin():
            run_repo = RunRepository(session)
            job_repo = SimulationJobRepository(session)
            mv_repo = ModVersionRepository(session)
            op_repo = OperationRepository(session)

            run = await run_repo.get(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            if not run.artifact_root_uri:
                raise ValueError(f"Run {run_id} has no artifact_root_uri")

            job = await job_repo.get(run.simulation_job_id)
            if job is None:
                raise ValueError(f"Job for run {run_id} not found")

            mv = await mv_repo.get(job.mod_version_id)
            if mv is None:
                raise ValueError(f"ModVersion {job.mod_version_id} not found")

            ops = [op for op_id in mv.operation_ids if (op := await op_repo.get(op_id))]

        parser = FakeParser()
        parsed = parser.parse(run.artifact_root_uri, dict(run.run_manifest))

        targets = HistoricalTargetSet()
        suite = MetricSuite.default()
        result = suite.evaluate(parsed, targets)

        log.info(
            "evaluation_computed",
            score_total=result.score_total,
            breakdown=result.breakdown,
        )

        vector = vectorize_operations(ops)

        async with factory() as session, session.begin():
            eval_repo = EvaluationRepository(session)
            sample_repo = SurrogateSampleRepository(session)

            evaluation = Evaluation(
                run_id=run_id,
                mod_version_id=job.mod_version_id,
                experiment_id=job.experiment_id,
                parser_version=parser.parser_version,
                metric_suite_version=suite.version,
                score_total=result.score_total,
                score_breakdown=result.breakdown,
                evaluated_at=datetime.now(UTC),
            )
            await eval_repo.create(evaluation)

            sample = SurrogateSample(
                experiment_id=job.experiment_id,
                mod_version_id=job.mod_version_id,
                evaluation_id=evaluation.id,
                search_space_version=mv.search_space_version,
                operation_vector=vector,
                score_total=result.score_total,
            )
            await sample_repo.create(sample)

        log.info("evaluation_persisted", evaluation_id=evaluation.id)

    finally:
        await engine.dispose()
