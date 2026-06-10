"""Add agent_reviews table

Revision ID: 003
Revises: 002
Create Date: 2026-06-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False
        ),
        sa.Column("proposal_hash", sa.String(64), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("agent_version", sa.String(20), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("reasoning", sa.String(2000), nullable=False),
        sa.Column("suggestions", sa.JSON, nullable=False),
        sa.Column("modified_proposal", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_reviews_experiment_id", "agent_reviews", ["experiment_id"])
    op.create_index("ix_agent_reviews_proposal_hash", "agent_reviews", ["proposal_hash"])


def downgrade() -> None:
    op.drop_index("ix_agent_reviews_proposal_hash", "agent_reviews")
    op.drop_index("ix_agent_reviews_experiment_id", "agent_reviews")
    op.drop_table("agent_reviews")
