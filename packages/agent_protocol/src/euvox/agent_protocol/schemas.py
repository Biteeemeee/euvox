import hashlib
from enum import StrEnum

from pydantic import BaseModel, Field


class EventProposal(BaseModel):
    event_id: str
    title: str
    description: str = ""
    era: str = ""
    region: str = ""
    trigger_conditions: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    is_major: bool = False
    proposed_by: str = "optimizer"

    def canonical_hash(self) -> str:
        import json as _json

        blob = _json.dumps(self.model_dump(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()


class AgentVerdict(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"
    ABSTAINED = "abstained"


class AgentReview(BaseModel):
    agent_name: str
    agent_version: str
    verdict: AgentVerdict
    confidence: float
    reasoning: str
    suggestions: list[str] = Field(default_factory=list)
    modified_proposal: EventProposal | None = None
