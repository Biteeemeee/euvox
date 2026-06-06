# EU5 Historical Plausibility Optimizer

A distributed optimization platform for improving the historical plausibility of Europa Universalis V simulations.

The system optimizes a versioned EU5 mod by running game simulations on Windows clients, evaluating savegame snapshots for historical plausibility, and feeding results back into a surrogate-assisted evolutionary optimization loop.

## Quick Start

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker + Docker Compose.

```bash
# Install all workspace dependencies
uv sync

# Copy and configure environment
cp .env.example .env

# Start local infrastructure (Postgres, RabbitMQ, MinIO)
docker compose up -d

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy packages/ apps/
```

## Structure

```
packages/   shared libraries — euvox.* namespace
apps/       deployable services
infra/      docker and migration scripts
docs/       architecture, ADRs, development guidelines
tests/      integration and contract tests
```

## Packages

| Package | Import | Purpose |
|---|---|---|
| core | `euvox.core` | Shared base types and interfaces |
| common_schemas | `euvox.common_schemas` | Pydantic DTOs exchanged between services |
| operation_registry | `euvox.operation_registry` | Versioned operation types (validate/render/vectorize) |
| search_space | `euvox.search_space` | Search space definitions and expansion |
| mod_rendering | `euvox.mod_rendering` | EU5 file rendering from operation specs |
| eu5_parser | `euvox.eu5_parser` | Savegame and snapshot parsing |
| metrics | `euvox.metrics` | Historical plausibility metric computation |
| client_protocol | `euvox.client_protocol` | Client↔server job protocol schemas |
| artifact_store | `euvox.artifact_store` | MinIO/S3 artifact storage adapter |

## Services

| App | Purpose |
|---|---|
| control_api | FastAPI — experiments, jobs, client registration |
| optimizer_service | Candidate generation and optimization loop |
| surrogate_service | Surrogate model training and inference |
| agent_service | LLM/rule-based historical validation |
| mod_builder_service | Build versioned mod artifacts from operations |
| parser_service | Parse raw EU5 savegames into snapshots |
| evaluation_service | Compute historical plausibility scores |
| simulation_client | Windows-side EU5 simulation worker |

## Documentation

- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Milestones](docs/MILESTONES.md)
- [Operation Registry](docs/OPERATION_REGISTRY.md)
- [Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md)
- [ADRs](docs/adr/)
