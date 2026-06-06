from datetime import UTC, datetime

from euvox.common_schemas import SimulationJobDTO
from euvox.core.models.simulation_job import SimulationJob
from euvox.core.repositories import SimulationJobRepository
from fastapi import APIRouter, HTTPException

from control_api.database import SessionDep
from control_api.schemas import ClaimJobRequest, CompleteJobRequest, CreateJobRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=201, response_model=SimulationJobDTO)
async def create_job(body: CreateJobRequest, session: SessionDep) -> SimulationJobDTO:
    job = SimulationJob(
        experiment_id=body.experiment_id,
        mod_version_id=body.mod_version_id,
        baseline_save_id=body.baseline_save_id,
        seed=body.seed,
        start_date=body.start_date,
        end_date=body.end_date,
        snapshot_interval_days=body.snapshot_interval_days,
        fidelity_level=body.fidelity_level,
        required_game_version=body.required_game_version,
        created_at=datetime.now(UTC),
    )
    repo = SimulationJobRepository(session)
    await repo.create(job)
    return SimulationJobDTO.model_validate(job)


@router.get("", response_model=list[SimulationJobDTO])
async def list_jobs(session: SessionDep, status: str | None = None) -> list[SimulationJobDTO]:
    repo = SimulationJobRepository(session)
    if status == "pending":
        jobs = await repo.list_pending()
    else:
        jobs = await repo.list_pending()
    return [SimulationJobDTO.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=SimulationJobDTO)
async def get_job(job_id: str, session: SessionDep) -> SimulationJobDTO:
    repo = SimulationJobRepository(session)
    job = await repo.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return SimulationJobDTO.model_validate(job)


@router.post("/{job_id}/claim", response_model=SimulationJobDTO)
async def claim_job(job_id: str, body: ClaimJobRequest, session: SessionDep) -> SimulationJobDTO:
    repo = SimulationJobRepository(session)
    job = await repo.claim(job_id, body.client_id)
    if job is None:
        raise HTTPException(status_code=409, detail="Job not found or already claimed")
    return SimulationJobDTO.model_validate(job)


@router.post("/{job_id}/complete", response_model=SimulationJobDTO)
async def complete_job(
    job_id: str, body: CompleteJobRequest, session: SessionDep
) -> SimulationJobDTO:
    repo = SimulationJobRepository(session)
    await repo.complete(job_id, body.status)
    job = await repo.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return SimulationJobDTO.model_validate(job)
