import asyncio
import hashlib
from pathlib import Path

import structlog
from euvox.artifact_store import LocalArtifactStore, MinioArtifactStore
from euvox.artifact_store.store import ArtifactStore
from euvox.core.db import make_engine, make_session_factory
from euvox.core.repositories import ModVersionRepository, OperationRepository
from euvox.mod_rendering import BuildInput, ModBuilder, OperationInput

from mod_builder_service.celery_app import celery_app
from mod_builder_service.config import Settings, get_settings

logger = structlog.get_logger()


def _make_store(settings: Settings) -> ArtifactStore:
    if settings.use_local_store:
        return LocalArtifactStore(Path(settings.local_store_dir))
    return MinioArtifactStore(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
    )


@celery_app.task(name="mod_builder.build_mod", bind=True, max_retries=3)
def build_mod(self, mod_version_id: str) -> None:  # type: ignore[misc]
    try:
        asyncio.run(_build_mod_async(mod_version_id, get_settings()))
    except Exception as exc:
        logger.error("build_mod_failed", mod_version_id=mod_version_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30) from exc


async def _build_mod_async(mod_version_id: str, settings: Settings) -> None:
    log = logger.bind(mod_version_id=mod_version_id)
    log.info("build_started")

    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)

    try:
        async with factory() as session, session.begin():
            mv_repo = ModVersionRepository(session)
            op_repo = OperationRepository(session)

            mv = await mv_repo.get(mod_version_id)
            if mv is None:
                raise ValueError(f"ModVersion {mod_version_id} not found")

            mv.status = "building"
            await session.flush()

            ops = []
            for op_id in mv.operation_ids:
                op = await op_repo.get(op_id)
                if op is not None:
                    ops.append(op)

        build_input = BuildInput(
            mod_version_id=mv.id,
            parent_mod_version_id=mv.parent_mod_version_id,
            operation_ids=list(mv.operation_ids),
            game_version=mv.game_version,
            search_space_version=mv.search_space_version,
            operations=[
                OperationInput(
                    id=op.id,
                    operation_type=op.operation_type,
                    schema_version=op.operation_schema_version,
                    spec=dict(op.operation_spec),
                )
                for op in ops
            ],
        )

        builder = ModBuilder()
        zip_bytes, manifest = builder.build(build_input)
        artifact_hash = f"sha256:{hashlib.sha256(zip_bytes).hexdigest()}"

        store = _make_store(settings)
        key = f"mods/{mod_version_id}.zip"
        artifact_uri = await store.upload_bytes(settings.artifact_bucket, key, zip_bytes)
        log.info("artifact_uploaded", uri=artifact_uri, bytes=len(zip_bytes))

        async with factory() as session, session.begin():
            mv_repo = ModVersionRepository(session)
            updated = await mv_repo.update_artifact(mod_version_id, artifact_uri, artifact_hash)
            if updated is not None:
                updated.manifest = manifest.to_dict()

        log.info("build_completed", artifact_uri=artifact_uri, hash=artifact_hash)

    finally:
        await engine.dispose()
