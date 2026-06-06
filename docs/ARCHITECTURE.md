# Architecture

## High-Level System

```text
┌─────────────────────────────────────────────────────────────────────┐
│                              SERVER                                 │
│                                                                     │
│  ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Control API    │   │ Experiment DB    │   │ Artifact Store   │  │
│  └───────┬────────┘   └────────┬─────────┘   └────────┬─────────┘  │
│          │                     │                      │            │
│          ▼                     ▼                      ▼            │
│  ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Job Queue      │   │ Mod Builder      │   │ Operation        │  │
│  │ RabbitMQ/Celery│   │ Service          │   │ Registry         │  │
│  └───────┬────────┘   └────────┬─────────┘   └────────┬─────────┘  │
│          │                     │                      │            │
│          ▼                     ▼                      ▼            │
│  ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Optimizer      │   │ Surrogate Model  │   │ Agent Service    │  │
│  │ Service        │   │ Service          │   │                  │  │
│  └───────┬────────┘   └────────┬─────────┘   └────────┬─────────┘  │
│          │                     │                      │            │
│          ▼                     ▼                      ▼            │
│  ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Parser Service │   │ Evaluation       │   │ Historical       │  │
│  │                │   │ Service          │   │ Targets          │  │
│  └────────────────┘   └──────────────────┘   └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                 ▲                              │
                 │                              ▼
        Artifacts, status, logs          Simulation jobs
                 │                              │
                 ▼                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WINDOWS CLIENTS                             │
│                                                                     │
│  Simulation Client                                                  │
│    - register and heartbeat                                         │
│    - claim job                                                      │
│    - download mod and baseline save                                 │
│    - launch EU5 in debug mode                                       │
│    - load save / observe / run / snapshot                           │
│    - collect saves and logs                                         │
│    - upload artifacts                                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Monorepo Structure

Use a Python monorepo with apps and shared packages.

```text
eu5-optimizer/
  README.md
  pyproject.toml
  uv.lock
  docker-compose.yml
  apps/
    control_api/
    optimizer_service/
    surrogate_service/
    agent_service/
    mod_builder_service/
    parser_service/
    evaluation_service/
    simulation_client/
  packages/
    core/
    common_schemas/
    operation_registry/
    search_space/
    mod_rendering/
    eu5_parser/
    metrics/
    client_protocol/
    artifact_store/
  infra/
    docker/
    migrations/
    scripts/
  docs/
    adr/
    codex/
  tests/
    unit/
    integration/
    contract/
```

## Runtime Services

### control-api

FastAPI application acting as the stable external API.

Responsibilities:

- experiments,
- mod versions,
- operations,
- job creation and claiming,
- client registration,
- run status,
- artifact metadata,
- health endpoints.

### mod-builder-service

Builds mod artifacts from operation lists.

Responsibilities:

- validate operation specs,
- render EU5 files,
- create manifest,
- package zip,
- upload artifact,
- record build result.

### optimizer-service

Generates candidate operations or candidate mod versions.

Responsibilities:

- read experiment history,
- query search space,
- query surrogate predictions,
- generate candidates,
- submit operations and build jobs.

### surrogate-service

Trains and serves surrogate models.

Responsibilities:

- build feature matrices,
- train models,
- store model artifacts,
- predict candidate impact/risk/uncertainty.

### agent-service

Handles LLM/rule-based agents.

Responsibilities:

- historical plausibility validation,
- counterfactual context enrichment,
- localization and text generation,
- structured JSON outputs,
- persisted agent reviews.

### parser-service

Parses raw saves and snapshots.

Responsibilities:

- parse raw savegames,
- normalize world-state snapshots,
- extract country/region/event traces,
- store parsed outputs with parser version.

### evaluation-service

Computes historical plausibility metrics.

Responsibilities:

- read parsed snapshots,
- read target sets,
- compute metrics,
- store score breakdowns,
- produce surrogate training samples.

### simulation-client

Windows-side worker.

Responsibilities:

- claim jobs,
- install mod artifacts,
- start EU5,
- run simulations,
- snapshot saves,
- upload logs and saves.

## Infrastructure Recommendation

Use the following stack for the first implementation:

```text
Python: 3.12+
Package manager: uv
API: FastAPI + Pydantic v2
ORM: SQLAlchemy 2
Migrations: Alembic
DB: PostgreSQL
Queue: RabbitMQ + Celery
Artifact storage: MinIO via boto3-compatible API
ML: scikit-learn first, optional XGBoost/Optuna later
Testing: pytest
Quality: ruff, mypy, pre-commit
```

## Source of Truth

The server is the source of truth. Clients must not make optimization decisions. Clients only execute assigned jobs and report evidence.
