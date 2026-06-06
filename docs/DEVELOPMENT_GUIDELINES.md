# Development Guidelines

## Tooling

Recommended baseline:

```text
Python 3.12+
uv
ruff
mypy
pytest
pre-commit
Docker Compose
```

Recommended services for local development:

```text
PostgreSQL
RabbitMQ
MinIO
```

## Local Development Flow

1. Start infrastructure with Docker Compose.
2. Run database migrations.
3. Start `control-api`.
4. Run fake worker/client.
5. Submit a fake experiment.
6. Verify end-to-end job lifecycle.

## Configuration

Use environment variables and `.env` files for local configuration. Do not hardcode paths, credentials, or game locations.

Common config groups:

```text
DATABASE_URL
RABBITMQ_URL
MINIO_ENDPOINT
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
ARTIFACT_BUCKET
CONTROL_API_URL
CLIENT_WORK_DIR
EU5_EXE_PATH
EU5_USER_DIR
```

## Logging

Use structured logs where possible.

Every service log should include:

- service name,
- request/job ID if available,
- experiment ID if available,
- mod version ID if available,
- run ID if available.

## Error Handling

Prefer explicit result objects for expected failures.

Examples:

```text
ValidationResult(valid=False, errors=[...])
BuildResult(status="failed", error_code="RENDER_ERROR")
RunResult(status="crashed", crash_reason="PROCESS_EXITED")
```

Do not raise generic exceptions for domain-level validation failures.

## Dependency Direction

```text
apps/*
  depend on packages/*

packages/*
  may depend on lower-level packages

packages/core
  should have minimal dependencies
```

## Database Migrations

All schema changes require Alembic migrations. Migrations should be small and reversible when practical.

Never modify historical migration files after they have been used.

## Artifact Handling

Large artifacts must be stored in MinIO/S3-compatible storage:

- mod zips,
- raw saves,
- parsed snapshots,
- logs,
- model artifacts.

PostgreSQL stores only metadata and URIs.

## Security Basics

- Validate artifact hashes.
- Use job tokens for client uploads.
- Do not execute arbitrary scripts from mod artifacts.
- Keep clients in isolated working directories.
- Prefer least-privilege local users for simulation workers.

## Versioning Discipline

The following must be versioned:

```text
operation_schema_version
search_space_version
mod_schema_version
parser_version
metric_version
target_set_version
surrogate_model_version
feature_schema_version
game_version
client_version
```

Old versions must remain readable.
