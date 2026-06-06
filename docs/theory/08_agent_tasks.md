# 08 — Instructions for the Coding Agent

## Goal

Create the initial monorepo structure for the adaptive optimization platform.

The first implementation should establish boundaries and run a simple local optimization loop.

Do not implement complex evolutionary or Bayesian optimization yet.

## Step 1 — Create structure

Create this structure:

```text
docs/
packages/contracts/
packages/domain/
packages/optimizer-core/
packages/validator-core/
packages/evaluator-core/
packages/search-space-core/
packages/common/
services/orchestrator-service/
apps/cli/
tests/unit/
tests/integration/
tests/contract/
scripts/
```

Adjust folder naming to the selected Python packaging convention if needed, but preserve the logical boundaries.

## Step 2 — Add contract models

Implement initial Pydantic models:

- AbstractElementDTO
- ValidationRequest
- ValidationResult
- EvaluationRequest
- EvaluationResult
- TrialObservation
- SearchSpaceSpec
- NumericParameterSpec
- CategoricalParameterSpec

Keep contracts free of service logic.

## Step 3 — Add ports/interfaces

Define interfaces for:

- ValidatorPort
- EvaluatorPort
- OptimizerPort
- SearchSpaceManagerPort
- ObservationStorePort

Use Python Protocols unless there is a strong reason not to.

## Step 4 — Add simple implementations

Implement:

- SimpleSearchSpaceManager
- RandomCandidateGenerator or RandomOptimizer
- RuleBasedValidator
- SimpleEvaluator
- InMemoryObservationStore
- LocalOrchestrator

The simple evaluator can use a deterministic toy objective.

Example:

```text
score = x1 - abs(x2) + category_bonus
```

## Step 5 — Add CLI

Add a CLI command that runs a local optimization.

Example target behavior:

```bash
python -m apps.cli run --budget 100 --seed 42
```

The CLI should print:

- best element,
- best score,
- number of generated candidates,
- number of rejected candidates,
- number of evaluated candidates,
- final search-space version.

## Step 6 — Add tests

Add tests for:

- contract serialization,
- validator behavior,
- evaluator behavior,
- search-space expansion,
- end-to-end local optimization.

## Step 7 — Keep future extraction in mind

Do not import service internals from other services.

Do not put business logic in contracts.

Do not create a generic shared package unless the utility is truly generic.

## Non-goals for the first implementation

Do not add yet:

- HTTP APIs,
- gRPC,
- Kafka or RabbitMQ,
- Kubernetes,
- real database persistence,
- DEAP/pymoo/Optuna integration,
- surrogate models,
- distributed workers.

These can be added after the baseline works.

## Acceptance criteria

The first milestone is complete when:

1. The monorepo structure exists.
2. Contract models exist and are tested.
3. A local optimization can run end-to-end.
4. Invalid candidates are rejected before evaluation.
5. Valid candidates are evaluated and observed.
6. Search-space versioning exists.
7. At least one simple expansion trigger exists.
8. Tests pass.
