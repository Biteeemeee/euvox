# Adaptive Optimization Platform — Monorepo Plan

This repository is intended to become a modular platform for adaptive optimization over a large and dynamically expandable search space.

The system optimizes abstract elements consisting of numerical and categorical values. New abstract elements may be generated during optimization when the current search space is no longer sufficient. Each generated element must be validated before it may be evaluated or used as a candidate for further optimization.

The initial implementation should start as a monorepo, but the internal boundaries should be designed so that individual services or packages can later be extracted into separate repositories with minimal refactoring.

## Core idea

The platform should support the following loop:

```text
Generate candidate
  -> Build AbstractElement
  -> Validate AbstractElement
  -> Evaluate valid AbstractElement
  -> Observe result
  -> Update optimizer state
  -> Expand search space if needed
  -> Repeat
```

For expensive evaluations, the system should avoid blindly evaluating large numbers of candidates. The long-term architecture should support surrogate-assisted optimization, where many candidates are generated and filtered cheaply, but only a small selected subset is evaluated with the expensive objective function.

## Main architectural goals

1. Keep service boundaries clean even inside the monorepo.
2. Keep shared exchange models separate from internal domain models.
3. Make validators, evaluators, optimizers and search-space managers replaceable.
4. Allow dynamic search-space expansion without tightly coupling services.
5. Prepare the codebase for future extraction into multiple repositories.
6. Support both simple local execution and later distributed execution.

## Suggested package layout

```text
.
├── README.md
├── docs/
│   ├── 01_project_idea.md
│   ├── 02_architecture.md
│   ├── 03_monorepo_structure.md
│   ├── 04_contracts.md
│   ├── 05_services.md
│   ├── 06_optimization_strategy.md
│   ├── 07_development_guidelines.md
│   └── 08_agent_tasks.md
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
│   ├── integration/
│   └── contract/
└── scripts/
```

## First implementation milestone

The first milestone should not implement a complex optimizer yet. It should establish the structure and interfaces.

Minimum useful milestone:

1. Define contract models.
2. Implement a simple local validator.
3. Implement a simple local evaluator.
4. Implement a basic optimizer loop.
5. Implement a simple search-space manager.
6. Run an end-to-end local optimization from the CLI.

## Important rule

Packages may depend inward on shared contracts, but services should not directly depend on each other's internal implementation.

Allowed:

```text
optimizer-service -> contracts
validator-service -> contracts
optimizer-core    -> contracts
validator-core    -> contracts
```

Avoid:

```text
optimizer-service -> validator-service
validator-service -> optimizer-service
evaluator-service -> optimizer-service
```
