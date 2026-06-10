from euvox.core.models.surrogate_sample import SurrogateSample
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SurrogateSampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, sample: SurrogateSample) -> SurrogateSample:
        self._session.add(sample)
        await self._session.flush()
        await self._session.refresh(sample)
        return sample

    async def list_by_experiment(
        self, experiment_id: str, limit: int = 1000
    ) -> list[SurrogateSample]:
        result = await self._session.execute(
            select(SurrogateSample)
            .where(SurrogateSample.experiment_id == experiment_id)
            .order_by(SurrogateSample.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
