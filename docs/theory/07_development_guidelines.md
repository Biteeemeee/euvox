# 07 — Development Guidelines

## General principles

1. Prefer explicit interfaces over implicit coupling.
2. Keep contracts small and stable.
3. Keep internal domain models separate from DTOs.
4. Start with local in-process execution.
5. Make service extraction possible, but do not over-engineer too early.
6. Make every optimization run reproducible where possible.

## DTO vs domain model

Do not use contract DTOs as rich domain entities.

Example:

```text
AbstractElementDTO        exchange model
OptimizerCandidate        optimizer-internal model
ValidatorElement          validator-internal model
```

Each component should map at its boundary.

## Error handling

Failures should be explicit.

Validation rejection is not a system error.

Evaluation failure is a system or evaluation error and should be represented separately.

Suggested statuses:

```text
generated
rejected
evaluated
failed
pruned
```

## Logging and traceability

Each trial should have:

- run id,
- trial id,
- search-space version,
- random seed if applicable,
- validation result,
- evaluation result if available,
- timestamps.

## Testing strategy

Minimum tests:

1. Contract serialization roundtrip.
2. Validator accepts known valid examples.
3. Validator rejects known invalid examples.
4. Evaluator returns deterministic score for deterministic inputs.
5. Search-space manager expands version correctly.
6. End-to-end local optimization run completes.

## Style preferences

Use type hints everywhere.

Prefer small classes with single responsibility.

Prefer Protocols or abstract base classes for ports.

Avoid global mutable state.

Inject dependencies explicitly.

## Package extraction readiness

Before adding a dependency between packages, ask:

```text
Would this dependency still make sense if these packages lived in different repositories?
```

If not, introduce a port/interface or contract instead.

## Avoid premature infrastructure

Do not add Kubernetes, message queues, distributed workers or databases in the first milestone unless absolutely necessary.

Start with:

- in-memory observation store,
- local CLI,
- deterministic dummy evaluator,
- simple file-based configuration.
