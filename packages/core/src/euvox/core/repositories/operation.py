from euvox.core.models.operation import Operation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, operation: Operation) -> Operation:
        self._session.add(operation)
        await self._session.flush()
        await self._session.refresh(operation)
        return operation

    async def get(self, operation_id: str) -> Operation | None:
        return await self._session.get(Operation, operation_id)

    async def list_by_experiment(self, experiment_id: str) -> list[Operation]:
        result = await self._session.execute(
            select(Operation).where(Operation.experiment_id == experiment_id)
        )
        return list(result.scalars().all())

    async def list_by_status(self, experiment_id: str, status: str) -> list[Operation]:
        result = await self._session.execute(
            select(Operation).where(
                Operation.experiment_id == experiment_id,
                Operation.status == status,
            )
        )
        return list(result.scalars().all())

    async def update_validation_status(self, operation_id: str, validation_status: str) -> None:
        operation = await self.get(operation_id)
        if operation is not None:
            operation.validation_status = validation_status
            await self._session.flush()
