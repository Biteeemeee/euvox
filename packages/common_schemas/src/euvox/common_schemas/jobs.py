import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FidelityLevel(StrEnum):
    FAKE = "fake"
    LOW = "low"
    MEDIUM = "medium"
    FULL = "full"


class JobStatus(StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationJobDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    mod_version_id: str
    baseline_save_id: str | None = None
    seed: int
    start_date: str
    end_date: str
    snapshot_interval_days: int = 365
    fidelity_level: FidelityLevel = FidelityLevel.FAKE
    required_game_version: str
    status: JobStatus = JobStatus.PENDING
    assigned_client_id: str | None = None
    created_at: datetime
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
