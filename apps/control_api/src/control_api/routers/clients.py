from datetime import UTC, datetime

from euvox.common_schemas import ClientDTO
from euvox.core.models.client import Client
from euvox.core.repositories import ClientRepository
from fastapi import APIRouter, HTTPException

from control_api.database import SessionDep
from control_api.schemas import RegisterClientRequest

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/register", status_code=201, response_model=ClientDTO)
async def register_client(body: RegisterClientRequest, session: SessionDep) -> ClientDTO:
    repo = ClientRepository(session)
    existing = await repo.get_by_fingerprint(body.machine_fingerprint)
    if existing is not None:
        existing.client_version = body.client_version
        existing.capabilities = body.capabilities
        existing.last_heartbeat_at = datetime.now(UTC)
        existing.status = "online"
        await session.flush()
        return ClientDTO.model_validate(existing)
    client = Client(
        name=body.name,
        client_version=body.client_version,
        machine_fingerprint=body.machine_fingerprint,
        capabilities=body.capabilities,
        last_heartbeat_at=datetime.now(UTC),
        status="online",
    )
    await repo.create(client)
    return ClientDTO.model_validate(client)


@router.post("/{client_id}/heartbeat", response_model=ClientDTO)
async def client_heartbeat(client_id: str, session: SessionDep) -> ClientDTO:
    repo = ClientRepository(session)
    await repo.heartbeat(client_id)
    client = await repo.get(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientDTO.model_validate(client)
