import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OperationStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    SKIPPED = "skipped"


class OperationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    parent_operation_id: str | None = None
    operation_type: str
    operation_schema_version: str
    operation_spec: dict[str, object] = Field(default_factory=dict)
    created_by: str
    created_at: datetime
    status: OperationStatus = OperationStatus.PENDING
    validation_status: ValidationStatus = ValidationStatus.PENDING
