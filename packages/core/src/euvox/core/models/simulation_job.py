import uuid
from datetime import UTC, datetime

from euvox.core.models.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(UTC)


class SimulationJob(Base):
    __tablename__ = "simulation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False, index=True
    )
    mod_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("mod_versions.id"), nullable=False
    )
    baseline_save_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    snapshot_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    fidelity_level: Mapped[str] = mapped_column(String(20), nullable=False, default="fake")
    required_game_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    assigned_client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clients.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
