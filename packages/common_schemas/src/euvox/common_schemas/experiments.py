import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ExperimentStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    objective_definition: dict[str, object] = Field(default_factory=dict)
    target_set_version: str
    search_space_version: str
    status: ExperimentStatus = ExperimentStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
