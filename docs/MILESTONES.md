# Milestones

## Milestone 0 — Monorepo Foundation

Goal: establish the repository and development baseline.

Tasks:

```text
- create monorepo structure
- configure uv / pyproject.toml
- configure ruff, mypy, pytest, pre-commit
- add Docker Compose for Postgres, RabbitMQ, MinIO
- add base packages and app skeletons
- add docs and ADR structure
```

Done when:

```text
- tests run locally
- infrastructure starts
- apps import shared packages
- docs exist
```

## Milestone 1 — Core Schemas and DB

Goal: create the shared language of the system.

Tasks:

```text
- Pydantic schemas for experiments, operations, jobs, runs, artifacts
- SQLAlchemy models
- Alembic migrations
- initial repository layer
- unit tests for schemas
```

Done when:

```text
- experiments, operations, jobs, and runs can be persisted
```

## Milestone 2 — Control API MVP

Goal: expose server API for clients and orchestration.

Tasks:

```text
- FastAPI app
- health endpoints
- create experiment endpoint
- register client endpoint
- claim job endpoint
- complete job endpoint
- artifact metadata endpoint
```

Done when:

```text
- a fake client can register, claim, and complete a job
```

## Milestone 3 — Simulation Client MVP with Fake Runner

Goal: prove client/server lifecycle without EU5.

Tasks:

```text
- Python simulation client app
- register and heartbeat
- claim job
- download/upload fake artifacts
- fake simulation runner
- structured run manifest
```

Done when:

```text
- end-to-end fake job produces uploaded artifacts and completed run
```

## Milestone 4 — Artifact Store and Mod Builder MVP

Goal: build and store versioned mod artifacts.

Tasks:

```text
- MinIO adapter
- artifact hash validation
- OperationRegistry skeleton
- numeric_patch@v1
- mod manifest
- zip packaging
- build_mod Celery task
```

Done when:

```text
- numeric operation builds a versioned mod zip with manifest
```

## Milestone 5 — Parser and Evaluation MVP

Goal: produce scores from fake or sample snapshots.

Tasks:

```text
- parser interface
- fake parser
- metric interface
- basic metric suite
- evaluation persistence
- surrogate sample persistence
```

Done when:

```text
- a fake run can be parsed and evaluated
```

## Milestone 6 — Optimizer MVP

Goal: generate candidate numeric operations.

Tasks:

```text
- SearchSpace model
- RandomSearchOptimizer
- simple EvolutionaryOptimizer
- candidate persistence
- job creation from candidates
```

Done when:

```text
- automatic loop creates candidates, builds mods, schedules fake runs, evaluates them
```

## Milestone 7 — Surrogate MVP

Goal: prioritize candidates with a simple surrogate model.

Tasks:

```text
- feature encoder
- operation vectorization
- ExtraTrees or RandomForest surrogate
- model artifact persistence
- acquisition score
- surrogate-guided selection
```

Done when:

```text
- optimizer ranks candidates using surrogate predictions
```

## Milestone 8 — Agent Layer MVP

Goal: support structured validation of event operations.

Tasks:

```text
- Agent interface
- AgentReview schema
- RuleBasedHistoryAgent
- RuleBasedCounterfactualAgent
- TemplateDesignerAgent
- persistence of agent outputs
```

Done when:

```text
- create_event proposals can be accepted/rejected/enriched by agents
```

## Milestone 9 — create_event@v1

Goal: expand the search space with generated events.

Tasks:

```text
- EventSpec schema
- create_event@v1 operation
- event renderer
- localization renderer
- event validation
- search-space expansion record
- golden-file tests
```

Done when:

```text
- a structured EventSpec renders into deterministic mod files
```

## Milestone 10 — Real EU5 Windows Runner

Goal: run actual EU5 simulations on a Windows client.

Tasks:

```text
- detect EU5 installation
- install mod artifact
- launch EU5 with -debug_mode
- console automation proof-of-concept
- load baseline save
- observe mode
- periodic saves
- error.log collection
- crash/timeout reporting
```

Done when:

```text
- one real EU5 run returns saves and logs to the server
```

## Milestone 11 — Reproducibility and Re-Evaluation

Goal: ensure old runs remain useful.

Tasks:

```text
- full run manifests
- parser/metric version handling
- re-evaluation task
- search-space version defaults
- artifact hash checks
```

Done when:

```text
- old raw saves can be re-parsed and re-evaluated with new metric versions
```

## Milestone 12 — Dashboard

Goal: observe the system.

Tasks:

```text
- simple dashboard or admin UI
- clients overview
- job queue status
- run results
- score history
- mod version lineage
- agent review display
```

Done when:

```text
- current optimization progress is visible without reading logs
```
