"""Add evaluations and surrogate_samples tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column(
            "mod_version_id", sa.String(36), sa.ForeignKey("mod_versions.id"), nullable=False
        ),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("parser_version", sa.String(50), nullable=False),
        sa.Column("metric_suite_version", sa.String(50), nullable=False),
        sa.Column("score_total", sa.Float, nullable=False),
        sa.Column("score_breakdown", sa.JSON, nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluations_run_id", "evaluations", ["run_id"])
    op.create_index("ix_evaluations_experiment_id", "evaluations", ["experiment_id"])

    op.create_table(
        "surrogate_samples",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column(
            "mod_version_id", sa.String(36), sa.ForeignKey("mod_versions.id"), nullable=False
        ),
        sa.Column("evaluation_id", sa.String(36), sa.ForeignKey("evaluations.id"), nullable=False),
        sa.Column("search_space_version", sa.String(50), nullable=False),
        sa.Column("operation_vector", sa.JSON, nullable=False),
        sa.Column("score_total", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_surrogate_samples_experiment_id", "surrogate_samples", ["experiment_id"])


def downgrade() -> None:
    op.drop_table("surrogate_samples")
    op.drop_table("evaluations")
