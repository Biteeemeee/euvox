import uuid
from datetime import UTC, datetime

from euvox.core.models.base import Base
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON


def _now() -> datetime:
    return datetime.now(UTC)


class ModVersion(Base):
    __tablename__ = "mod_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False, index=True
    )
    parent_mod_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("mod_versions.id"), nullable=True
    )
    base_mod_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    operation_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    mod_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    search_space_version: Mapped[str] = mapped_column(String(50), nullable=False)
    game_version: Mapped[str] = mapped_column(String(50), nullable=False)
    artifact_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
