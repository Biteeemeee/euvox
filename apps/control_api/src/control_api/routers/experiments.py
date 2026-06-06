from datetime import UTC, datetime

from euvox.common_schemas import ExperimentDTO
from euvox.core.models.experiment import Experiment
from euvox.core.repositories import ExperimentRepository
from fastapi import APIRouter, HTTPException

from control_api.database import SessionDep
from control_api.schemas import CreateExperimentRequest

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", status_code=201, response_model=ExperimentDTO)
async def create_experiment(body: CreateExperimentRequest, session: SessionDep) -> ExperimentDTO:
    now = datetime.now(UTC)
    experiment = Experiment(
        name=body.name,
        description=body.description,
        objective_definition=body.objective_definition,
        target_set_version=body.target_set_version,
        search_space_version=body.search_space_version,
        created_at=now,
        updated_at=now,
    )
    repo = ExperimentRepository(session)
    await repo.create(experiment)
    return ExperimentDTO.model_validate(experiment)


@router.get("/{experiment_id}", response_model=ExperimentDTO)
async def get_experiment(experiment_id: str, session: SessionDep) -> ExperimentDTO:
    repo = ExperimentRepository(session)
    experiment = await repo.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentDTO.model_validate(experiment)
