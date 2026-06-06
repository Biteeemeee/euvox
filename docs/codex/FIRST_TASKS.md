# Suggested First Codex Tasks

## Task 1: Create Monorepo Skeleton

Create:

```text
apps/control_api
apps/simulation_client
packages/core
packages/common_schemas
packages/operation_registry
packages/search_space
tests/unit
```

Add minimal `pyproject.toml`, pytest config, ruff config, and importable packages.

## Task 2: Define Core Schemas

Implement Pydantic models for:

```text
ExperimentSpec
OperationSpec
ModVersionManifest
SimulationJobSpec
ClientRegistration
ClientHeartbeat
RunManifest
EvaluationResult
```

Add unit tests.

## Task 3: Implement Operation Registry Skeleton

Implement:

```text
OperationType protocol
OperationRegistry
ValidationResult
RenderResult
OperationVector placeholder
numeric_patch@v1
```

Add tests for registration and validation.

## Task 4: Implement Control API Skeleton

Implement FastAPI app with:

```text
GET /health
POST /clients/register
POST /clients/{client_id}/heartbeat
POST /jobs/claim
POST /jobs/{job_id}/complete
```

Use in-memory repository first if DB is not ready.

## Task 5: Implement Fake Simulation Client

Implement a Python client that:

```text
registers
heartbeats
claims fake job
creates fake logs and fake save artifact
reports completion
```
