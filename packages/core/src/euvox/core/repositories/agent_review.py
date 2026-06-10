from euvox.core.models.agent_review import AgentReviewRecord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AgentReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: AgentReviewRecord) -> AgentReviewRecord:
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def list_by_proposal(
        self, experiment_id: str, proposal_hash: str
    ) -> list[AgentReviewRecord]:
        result = await self._session.execute(
            select(AgentReviewRecord)
            .where(
                AgentReviewRecord.experiment_id == experiment_id,
                AgentReviewRecord.proposal_hash == proposal_hash,
            )
            .order_by(AgentReviewRecord.created_at)
        )
        return list(result.scalars().all())

    async def list_by_experiment(self, experiment_id: str) -> list[AgentReviewRecord]:
        result = await self._session.execute(
            select(AgentReviewRecord)
            .where(AgentReviewRecord.experiment_id == experiment_id)
            .order_by(AgentReviewRecord.created_at)
        )
        return list(result.scalars().all())
