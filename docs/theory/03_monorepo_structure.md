# 03 — Monorepo Structure

## Recommended structure

```text
.
├── docs/
├── packages/
│   ├── contracts/
│   ├── domain/
│   ├── optimizer-core/
│   ├── validator-core/
│   ├── evaluator-core/
│   ├── search-space-core/
│   └── common/
├── services/
│   ├── optimizer-service/
│   ├── validator-service/
│   ├── evaluator-service/
│   └── orchestrator-service/
├── apps/
│   └── cli/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── scripts/
```

## packages/contracts

Contains shared exchange models only.

Allowed content:

- DTOs,
- request models,
- result models,
- event models,
- enums,
- schema version constants.

Do not put service logic here.

## packages/domain

Contains domain concepts that are shared inside the monorepo but are not external contracts.

Examples:

- internal candidate representation,
- optimization run state,
- search-space domain objects.

Be careful: if a domain object is only needed by one package, keep it there.

## packages/optimizer-core

Contains optimizer algorithms and interfaces.

Examples:

- base optimizer protocol,
- random optimizer,
- evolutionary candidate generator,
- Optuna adapter later,
- surrogate-assisted optimizer later.

## packages/validator-core

Contains validation logic.

Examples:

- validator interface,
- local rule-based validator,
- constraint definitions,
- validation reason codes.

## packages/evaluator-core

Contains evaluation logic.

Examples:

- evaluator interface,
- dummy evaluator,
- expensive evaluator adapter,
- multi-fidelity evaluator interface.

## packages/search-space-core

Contains search-space definitions and expansion logic.

Examples:

- numeric parameter specs,
- categorical parameter specs,
- search-space versions,
- expansion policy,
- active search-space registry.

## packages/common

Only use for truly generic utilities.

Avoid turning this into a dumping ground.

Acceptable examples:

- logging setup,
- time utilities,
- id generation,
- serialization helpers.

## services

Services are deployable boundaries, even if they initially run locally.

Initial services may simply wrap core packages.

Later they may become REST, gRPC or message-based services.

## apps/cli

Provides a local command-line entry point for running an end-to-end optimization.

Initial CLI goal:

```bash
run-optimization --budget 100 --seed 42
```

## tests

Use tests to protect boundaries.

Suggested test types:

- unit tests for each package,
- contract serialization tests,
- integration test for local end-to-end optimization,
- regression tests for search-space expansion.
