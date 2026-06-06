"""Schema serialization and validation tests."""

from datetime import UTC, datetime

import pytest
from euvox.common_schemas import (
    ClientDTO,
    ClientStatus,
    ExitStatus,
    ExperimentDTO,
    ExperimentStatus,
    FidelityLevel,
    JobStatus,
    ModVersionDTO,
    ModVersionStatus,
    OperationDTO,
    OperationStatus,
    RunDTO,
    SimulationJobDTO,
    ValidationStatus,
)

NOW = datetime.now(UTC)


# ── ExperimentDTO ──────────────────────────────────────────────────────────────


def test_experiment_roundtrip() -> None:
    original = ExperimentDTO(
        name="Test run",
        target_set_version="v1",
        search_space_version="v1",
        created_at=NOW,
        updated_at=NOW,
    )
    restored = ExperimentDTO.model_validate(original.model_dump())
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.status == ExperimentStatus.ACTIVE


def test_experiment_json_roundtrip() -> None:
    dto = ExperimentDTO(
        name="JSON run",
        target_set_version="v1",
        search_space_version="v1",
        created_at=NOW,
        updated_at=NOW,
    )
    restored = ExperimentDTO.model_validate_json(dto.model_dump_json())
    assert restored.id == dto.id


def test_experiment_status_values() -> None:
    assert set(ExperimentStatus) == {"active", "paused", "completed", "failed"}


# ── OperationDTO ───────────────────────────────────────────────────────────────


def test_operation_roundtrip() -> None:
    dto = OperationDTO(
        experiment_id="exp-1",
        operation_type="numeric_patch",
        operation_schema_version="v1",
        operation_spec={"target": "war_cost_factor", "value": 1.15},
        created_by="optimizer_service",
        created_at=NOW,
    )
    restored = OperationDTO.model_validate(dto.model_dump())
    assert restored.operation_type == "numeric_patch"
    assert restored.operation_spec["value"] == 1.15
    assert restored.validation_status == ValidationStatus.PENDING
    assert restored.parent_operation_id is None


def test_operation_status_values() -> None:
    assert set(OperationStatus) == {"pending", "active", "deprecated", "failed"}
    assert set(ValidationStatus) == {"pending", "valid", "invalid", "skipped"}


# ── ModVersionDTO ──────────────────────────────────────────────────────────────


def test_mod_version_roundtrip() -> None:
    dto = ModVersionDTO(
        experiment_id="exp-1",
        operation_ids=["op-1", "op-2"],
        mod_schema_version="v1",
        search_space_version="v1",
        game_version="1.0.0",
        created_at=NOW,
    )
    restored = ModVersionDTO.model_validate(dto.model_dump())
    assert restored.operation_ids == ["op-1", "op-2"]
    assert restored.status == ModVersionStatus.PENDING
    assert restored.artifact_uri is None


# ── SimulationJobDTO ───────────────────────────────────────────────────────────


def test_simulation_job_roundtrip() -> None:
    dto = SimulationJobDTO(
        experiment_id="exp-1",
        mod_version_id="mv-1",
        seed=42,
        start_date="1444.11.11",
        end_date="1821.01.03",
        required_game_version="1.0.0",
        created_at=NOW,
    )
    restored = SimulationJobDTO.model_validate(dto.model_dump())
    assert restored.seed == 42
    assert restored.fidelity_level == FidelityLevel.FAKE
    assert restored.status == JobStatus.PENDING
    assert restored.claimed_at is None


# ── ClientDTO ──────────────────────────────────────────────────────────────────


def test_client_roundtrip() -> None:
    dto = ClientDTO(
        name="worker-01",
        client_version="0.1.0",
        machine_fingerprint="abc123",
        last_heartbeat_at=NOW,
    )
    restored = ClientDTO.model_validate(dto.model_dump())
    assert restored.name == "worker-01"
    assert restored.status == ClientStatus.OFFLINE


# ── RunDTO ─────────────────────────────────────────────────────────────────────


def test_run_roundtrip() -> None:
    dto = RunDTO(
        simulation_job_id="job-1",
        client_id="client-1",
        started_at=NOW,
    )
    restored = RunDTO.model_validate(dto.model_dump())
    assert restored.exit_status is None
    assert restored.finished_at is None


def test_run_with_exit_status() -> None:
    dto = RunDTO(
        simulation_job_id="job-1",
        client_id="client-1",
        started_at=NOW,
        finished_at=NOW,
        exit_status=ExitStatus.SUCCESS,
    )
    assert dto.exit_status == ExitStatus.SUCCESS


# ── Cross-schema ID defaults ───────────────────────────────────────────────────


def test_ids_are_unique() -> None:
    exp1 = ExperimentDTO(
        name="A",
        target_set_version="v1",
        search_space_version="v1",
        created_at=NOW,
        updated_at=NOW,
    )
    exp2 = ExperimentDTO(
        name="B",
        target_set_version="v1",
        search_space_version="v1",
        created_at=NOW,
        updated_at=NOW,
    )
    assert exp1.id != exp2.id


@pytest.mark.parametrize(
    "dto_class,kwargs",
    [
        (
            ExperimentDTO,
            {
                "name": "x",
                "target_set_version": "v1",
                "search_space_version": "v1",
                "created_at": NOW,
                "updated_at": NOW,
            },
        ),
        (
            OperationDTO,
            {
                "experiment_id": "e",
                "operation_type": "t",
                "operation_schema_version": "v1",
                "created_by": "svc",
                "created_at": NOW,
            },
        ),
        (
            ClientDTO,
            {
                "name": "c",
                "client_version": "0.1",
                "machine_fingerprint": "fp",
                "last_heartbeat_at": NOW,
            },
        ),
    ],
)
def test_default_id_is_uuid_format(dto_class: type, kwargs: dict) -> None:  # type: ignore[type-arg]
    import uuid

    dto = dto_class(**kwargs)
    uuid.UUID(dto.id)  # raises if not valid UUID
