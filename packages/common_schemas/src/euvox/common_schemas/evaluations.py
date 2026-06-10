import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvaluationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    mod_version_id: str
    experiment_id: str
    parser_version: str
    metric_suite_version: str
    score_total: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    evaluated_at: datetime
