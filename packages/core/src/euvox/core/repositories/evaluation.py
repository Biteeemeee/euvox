from euvox.core.models.evaluation import Evaluation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class EvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, evaluation: Evaluation) -> Evaluation:
        self._session.add(evaluation)
        await self._session.flush()
        await self._session.refresh(evaluation)
        return evaluation

    async def get(self, evaluation_id: str) -> Evaluation | None:
        return await self._session.get(Evaluation, evaluation_id)

    async def list_by_experiment(self, experiment_id: str) -> list[Evaluation]:
        result = await self._session.execute(
            select(Evaluation)
            .where(Evaluation.experiment_id == experiment_id)
            .order_by(Evaluation.evaluated_at)
        )
        return list(result.scalars().all())

    async def list_by_run(self, run_id: str) -> list[Evaluation]:
        result = await self._session.execute(
            select(Evaluation).where(Evaluation.run_id == run_id)
        )
        return list(result.scalars().all())
