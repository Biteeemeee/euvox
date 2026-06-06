from euvox.core.models.experiment import Experiment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, experiment: Experiment) -> Experiment:
        self._session.add(experiment)
        await self._session.flush()
        await self._session.refresh(experiment)
        return experiment

    async def get(self, experiment_id: str) -> Experiment | None:
        return await self._session.get(Experiment, experiment_id)

    async def list_all(self) -> list[Experiment]:
        result = await self._session.execute(select(Experiment))
        return list(result.scalars().all())

    async def list_by_status(self, status: str) -> list[Experiment]:
        result = await self._session.execute(select(Experiment).where(Experiment.status == status))
        return list(result.scalars().all())

    async def update_status(self, experiment_id: str, status: str) -> None:
        experiment = await self.get(experiment_id)
        if experiment is not None:
            experiment.status = status
            await self._session.flush()
