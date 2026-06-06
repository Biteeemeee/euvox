from datetime import UTC, datetime

from euvox.core.models.client import Client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, client: Client) -> Client:
        self._session.add(client)
        await self._session.flush()
        await self._session.refresh(client)
        return client

    async def get(self, client_id: str) -> Client | None:
        return await self._session.get(Client, client_id)

    async def get_by_fingerprint(self, fingerprint: str) -> Client | None:
        result = await self._session.execute(
            select(Client).where(Client.machine_fingerprint == fingerprint)
        )
        return result.scalar_one_or_none()

    async def list_online(self) -> list[Client]:
        result = await self._session.execute(select(Client).where(Client.status == "online"))
        return list(result.scalars().all())

    async def heartbeat(self, client_id: str) -> None:
        client = await self.get(client_id)
        if client is not None:
            client.last_heartbeat_at = datetime.now(UTC)
            client.status = "online"
            await self._session.flush()
