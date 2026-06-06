import uuid
from datetime import UTC, datetime

from euvox.core.models.base import Base
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON


def _now() -> datetime:
    return datetime.now(UTC)


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False, index=True
    )
    parent_operation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("operations.id"), nullable=True
    )
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    operation_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    operation_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
