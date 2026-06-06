from euvox.core.models.mod_version import ModVersion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ModVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, mod_version: ModVersion) -> ModVersion:
        self._session.add(mod_version)
        await self._session.flush()
        await self._session.refresh(mod_version)
        return mod_version

    async def get(self, mod_version_id: str) -> ModVersion | None:
        return await self._session.get(ModVersion, mod_version_id)

    async def list_by_experiment(self, experiment_id: str) -> list[ModVersion]:
        result = await self._session.execute(
            select(ModVersion).where(ModVersion.experiment_id == experiment_id)
        )
        return list(result.scalars().all())

    async def update_artifact(
        self, mod_version_id: str, artifact_uri: str, artifact_hash: str
    ) -> ModVersion | None:
        mv = await self.get(mod_version_id)
        if mv is None:
            return None
        mv.artifact_uri = artifact_uri
        mv.artifact_hash = artifact_hash
        mv.status = "ready"
        await self._session.flush()
        return mv
