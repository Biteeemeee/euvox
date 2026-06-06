"""Initial schema: experiments, operations, mod_versions, clients, simulation_jobs, runs

Revision ID: 001
Revises:
Create Date: 2026-06-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("objective_definition", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("target_set_version", sa.String(50), nullable=False),
        sa.Column("search_space_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_experiments_status", "experiments", ["status"])

    op.create_table(
        "operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("experiments.id"),
            nullable=False,
        ),
        sa.Column(
            "parent_operation_id",
            sa.String(36),
            sa.ForeignKey("operations.id"),
            nullable=True,
        ),
        sa.Column("operation_type", sa.String(100), nullable=False),
        sa.Column("operation_schema_version", sa.String(20), nullable=False),
        sa.Column("operation_spec", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("validation_status", sa.String(50), nullable=False, server_default="pending"),
    )
    op.create_index("ix_operations_experiment_id", "operations", ["experiment_id"])
    op.create_index("ix_operations_status", "operations", ["status"])

    op.create_table(
        "mod_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("experiments.id"),
            nullable=False,
        ),
        sa.Column(
            "parent_mod_version_id",
            sa.String(36),
            sa.ForeignKey("mod_versions.id"),
            nullable=True,
        ),
        sa.Column("base_mod_version_id", sa.String(36), nullable=True),
        sa.Column("operation_ids", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("mod_schema_version", sa.String(20), nullable=False),
        sa.Column("search_space_version", sa.String(50), nullable=False),
        sa.Column("game_version", sa.String(50), nullable=False),
        sa.Column("artifact_uri", sa.String(500), nullable=True),
        sa.Column("artifact_hash", sa.String(64), nullable=True),
        sa.Column("manifest", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mod_versions_experiment_id", "mod_versions", ["experiment_id"])
    op.create_index("ix_mod_versions_status", "mod_versions", ["status"])

    op.create_table(
        "clients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("client_version", sa.String(50), nullable=False),
        sa.Column("machine_fingerprint", sa.String(255), nullable=False, unique=True),
        sa.Column("capabilities", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="offline"),
    )
    op.create_index("ix_clients_status", "clients", ["status"])

    op.create_table(
        "simulation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("experiments.id"),
            nullable=False,
        ),
        sa.Column(
            "mod_version_id",
            sa.String(36),
            sa.ForeignKey("mod_versions.id"),
            nullable=False,
        ),
        sa.Column("baseline_save_id", sa.String(36), nullable=True),
        sa.Column("seed", sa.Integer, nullable=False),
        sa.Column("start_date", sa.String(20), nullable=False),
        sa.Column("end_date", sa.String(20), nullable=False),
        sa.Column("snapshot_interval_days", sa.Integer, nullable=False, server_default="365"),
        sa.Column("fidelity_level", sa.String(20), nullable=False, server_default="fake"),
        sa.Column("required_game_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column(
            "assigned_client_id",
            sa.String(36),
            sa.ForeignKey("clients.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_simulation_jobs_experiment_id", "simulation_jobs", ["experiment_id"])
    op.create_index("ix_simulation_jobs_status", "simulation_jobs", ["status"])

    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "simulation_job_id",
            sa.String(36),
            sa.ForeignKey("simulation_jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.String(36),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_status", sa.String(50), nullable=True),
        sa.Column("crash_reason", sa.Text, nullable=True),
        sa.Column("run_manifest", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("artifact_root_uri", sa.String(500), nullable=True),
    )
    op.create_index("ix_runs_simulation_job_id", "runs", ["simulation_job_id"])


def downgrade() -> None:
    op.drop_table("runs")
    op.drop_table("simulation_jobs")
    op.drop_table("clients")
    op.drop_table("mod_versions")
    op.drop_table("operations")
    op.drop_table("experiments")
