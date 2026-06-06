from euvox.core.models.run import Run
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: Run) -> Run:
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get(self, run_id: str) -> Run | None:
        return await self._session.get(Run, run_id)

    async def list_by_job(self, simulation_job_id: str) -> list[Run]:
        result = await self._session.execute(
            select(Run).where(Run.simulation_job_id == simulation_job_id)
        )
        return list(result.scalars().all())
