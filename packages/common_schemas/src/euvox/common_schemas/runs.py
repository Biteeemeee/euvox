import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ExitStatus(StrEnum):
    SUCCESS = "success"
    CRASH = "crash"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RunDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    simulation_job_id: str
    client_id: str
    started_at: datetime
    finished_at: datetime | None = None
    exit_status: ExitStatus | None = None
    crash_reason: str | None = None
    run_manifest: dict[str, object] = Field(default_factory=dict)
    artifact_root_uri: str | None = None
