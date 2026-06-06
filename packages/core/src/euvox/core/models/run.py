import uuid
from datetime import UTC, datetime

from euvox.core.models.base import Base
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON


def _now() -> datetime:
    return datetime.now(UTC)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("simulation_jobs.id"), nullable=False, index=True
    )
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crash_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    artifact_root_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
