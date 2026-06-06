from datetime import UTC, datetime

from euvox.core.models.simulation_job import SimulationJob
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SimulationJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: SimulationJob) -> SimulationJob:
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def get(self, job_id: str) -> SimulationJob | None:
        return await self._session.get(SimulationJob, job_id)

    async def list_pending(self) -> list[SimulationJob]:
        result = await self._session.execute(
            select(SimulationJob).where(SimulationJob.status == "pending")
        )
        return list(result.scalars().all())

    async def claim(self, job_id: str, client_id: str) -> SimulationJob | None:
        job = await self.get(job_id)
        if job is None or job.status != "pending":
            return None
        job.status = "claimed"
        job.assigned_client_id = client_id
        job.claimed_at = datetime.now(UTC)
        await self._session.flush()
        return job

    async def complete(self, job_id: str, status: str) -> None:
        job = await self.get(job_id)
        if job is not None:
            job.status = status
            job.completed_at = datetime.now(UTC)
            await self._session.flush()
