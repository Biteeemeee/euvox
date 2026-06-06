from euvox.common_schemas import ModVersionDTO
from euvox.core.models.mod_version import ModVersion
from euvox.core.repositories import ModVersionRepository
from fastapi import APIRouter, HTTPException

from control_api.database import SessionDep
from control_api.schemas import CreateModVersionRequest, UpdateArtifactRequest

router = APIRouter(prefix="/mod-versions", tags=["mod-versions"])


@router.post("", status_code=201, response_model=ModVersionDTO)
async def create_mod_version(body: CreateModVersionRequest, session: SessionDep) -> ModVersionDTO:
    mv = ModVersion(
        experiment_id=body.experiment_id,
        parent_mod_version_id=body.parent_mod_version_id,
        base_mod_version_id=body.base_mod_version_id,
        operation_ids=body.operation_ids,
        mod_schema_version=body.mod_schema_version,
        search_space_version=body.search_space_version,
        game_version=body.game_version,
    )
    repo = ModVersionRepository(session)
    await repo.create(mv)
    return ModVersionDTO.model_validate(mv)


@router.get("/{mod_version_id}", response_model=ModVersionDTO)
async def get_mod_version(mod_version_id: str, session: SessionDep) -> ModVersionDTO:
    repo = ModVersionRepository(session)
    mv = await repo.get(mod_version_id)
    if mv is None:
        raise HTTPException(status_code=404, detail="ModVersion not found")
    return ModVersionDTO.model_validate(mv)


@router.patch("/{mod_version_id}/artifact", response_model=ModVersionDTO)
async def update_artifact(
    mod_version_id: str, body: UpdateArtifactRequest, session: SessionDep
) -> ModVersionDTO:
    repo = ModVersionRepository(session)
    mv = await repo.update_artifact(mod_version_id, body.artifact_uri, body.artifact_hash)
    if mv is None:
        raise HTTPException(status_code=404, detail="ModVersion not found")
    return ModVersionDTO.model_validate(mv)
