from datetime import UTC, datetime

from euvox.common_schemas import RunDTO
from euvox.core.models.run import Run
from euvox.core.repositories import RunRepository
from fastapi import APIRouter, HTTPException

from control_api.database import SessionDep
from control_api.schemas import CompleteRunRequest, CreateRunRequest

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunDTO])
async def list_runs(session: SessionDep, job_id: str | None = None) -> list[RunDTO]:
    repo = RunRepository(session)
    runs = await repo.list_by_job(job_id) if job_id else []
    return [RunDTO.model_validate(r) for r in runs]


@router.post("", status_code=201, response_model=RunDTO)
async def create_run(body: CreateRunRequest, session: SessionDep) -> RunDTO:
    run = Run(
        simulation_job_id=body.simulation_job_id,
        client_id=body.client_id,
        started_at=datetime.now(UTC),
    )
    repo = RunRepository(session)
    await repo.create(run)
    return RunDTO.model_validate(run)


@router.get("/{run_id}", response_model=RunDTO)
async def get_run(run_id: str, session: SessionDep) -> RunDTO:
    repo = RunRepository(session)
    run = await repo.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunDTO.model_validate(run)


@router.patch("/{run_id}", response_model=RunDTO)
async def complete_run(run_id: str, body: CompleteRunRequest, session: SessionDep) -> RunDTO:
    repo = RunRepository(session)
    run = await repo.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run.exit_status = body.exit_status
    run.crash_reason = body.crash_reason
    run.run_manifest = body.run_manifest
    run.artifact_root_uri = body.artifact_root_uri
    run.finished_at = datetime.now(UTC)
    await session.flush()
    return RunDTO.model_validate(run)
