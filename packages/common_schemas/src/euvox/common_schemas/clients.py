import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClientStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    DISABLED = "disabled"


class ClientDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    client_version: str
    machine_fingerprint: str
    capabilities: dict[str, object] = Field(default_factory=dict)
    last_heartbeat_at: datetime
    status: ClientStatus = ClientStatus.OFFLINE
