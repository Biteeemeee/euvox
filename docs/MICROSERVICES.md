# Microservices

## Overview

The platform is split into independently testable Python services plus shared packages.

Services live under `apps/`. Shared code lives under `packages/`.

## Services

### control-api

Public HTTP API used by clients, dashboards, and internal orchestration.

Primary endpoints:

```text
POST /experiments
GET  /experiments/{id}
POST /clients/register
POST /clients/{id}/heartbeat
POST /jobs/claim
POST /jobs/{id}/complete
POST /jobs/{id}/artifacts
GET  /mod-versions/{id}
GET  /runs/{id}
```

### optimizer-service

Runs optimization cycles.

Inputs:

- experiment definition,
- evaluation history,
- current search space,
- surrogate predictions,
- budget.

Outputs:

- candidate operations,
- build jobs,
- simulation jobs.

### surrogate-service

Trains and evaluates surrogate models.

Inputs:

- surrogate training samples,
- candidate operation vectors,
- information vectors.

Outputs:

- predicted gain,
- side-effect risk,
- uncertainty,
- validity probability,
- model artifact.

### agent-service

Provides rule-based and LLM-based agent reviews.

Agents:

- HistoryAgent,
- CounterfactualContextAgent,
- DesignerAgent,
- ScriptReviewAgent.

All outputs must be JSON-schema validated and persisted.

### mod-builder-service

Builds mod artifacts from operation chains.

Inputs:

- base mod version,
- operation list.

Outputs:

- mod zip,
- manifest,
- rendered file list,
- validation report.

### parser-service

Parses raw saves and produces normalized snapshots.

Inputs:

- raw save artifact URI,
- parser version.

Outputs:

- parsed state artifact,
- snapshot metadata,
- parser warnings/errors.

### evaluation-service

Computes metrics from parsed snapshots and target sets.

Inputs:

- parsed run,
- target set,
- metric suite.

Outputs:

- total score,
- score breakdown,
- side-effect scores,
- surrogate training samples.

### simulation-client

Windows worker process.

Inputs:

- simulation jobs from `control-api`,
- mod artifact,
- baseline save artifact,
- run configuration.

Outputs:

- raw saves,
- logs,
- run manifest,
- crash or timeout reports.

## Communication

Use two communication patterns:

1. HTTP API for client/server and direct service control.
2. Celery jobs over RabbitMQ for background tasks.

## Background Job Types

```text
build_mod
validate_mod
prepare_simulation_job
parse_snapshot
evaluate_run
train_surrogate
generate_candidates
agent_review
```

## Service Independence

Each service must:

- have its own app entrypoint,
- expose health checks,
- use shared schemas,
- not import internal modules from another app,
- be runnable in isolation with fake dependencies where practical.
