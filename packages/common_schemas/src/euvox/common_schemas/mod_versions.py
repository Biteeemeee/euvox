import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ModVersionStatus(StrEnum):
    PENDING = "pending"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"


class ModVersionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    parent_mod_version_id: str | None = None
    base_mod_version_id: str | None = None
    operation_ids: list[str] = Field(default_factory=list)
    mod_schema_version: str
    search_space_version: str
    game_version: str
    artifact_uri: str | None = None
    artifact_hash: str | None = None
    manifest: dict[str, object] = Field(default_factory=dict)
    status: ModVersionStatus = ModVersionStatus.PENDING
    created_at: datetime
