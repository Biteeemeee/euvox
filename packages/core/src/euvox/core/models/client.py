import uuid
from datetime import UTC, datetime

from euvox.core.models.base import Base
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON


def _now() -> datetime:
    return datetime.now(UTC)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_version: Mapped[str] = mapped_column(String(50), nullable=False)
    machine_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    capabilities: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="offline", index=True)
