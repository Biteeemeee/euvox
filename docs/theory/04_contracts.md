# 04 — Contracts

## Purpose

Contracts define the shared language between components and future services.

They should be stable, versioned and small.

Contracts are not internal domain models. They are exchange models.

## Recommended technology

Use Pydantic models for Python contracts.

Reasons:

- explicit schemas,
- validation,
- JSON serialization,
- type hints,
- easy OpenAPI integration later.

## Initial contract models

### AbstractElementDTO

Represents an element exchanged between optimizer, validator and evaluator.

Fields:

```text
id: optional string
schema_version: string
numeric_values: dict[string, float]
categorical_values: dict[string, string]
metadata: dict[string, any]
```

### ValidationRequest

```text
element: AbstractElementDTO
```

### ValidationResult

```text
valid: bool
reason: optional string
violated_constraints: list[string]
metadata: dict[string, any]
```

### EvaluationRequest

```text
element: AbstractElementDTO
evaluation_mode: cheap | full
```

### EvaluationResult

```text
score: float
metrics: dict[string, float]
duration_seconds: optional float
cost: optional float
metadata: dict[string, any]
```

### TrialObservation

Represents what happened to one candidate.

```text
trial_id: string
element: AbstractElementDTO
validation_result: ValidationResult
evaluation_result: optional EvaluationResult
status: generated | rejected | evaluated | failed
search_space_version: string
created_at: datetime
```

### SearchSpaceSpec

Describes the active search space.

```text
version: string
numeric_parameters: list[NumericParameterSpec]
categorical_parameters: list[CategoricalParameterSpec]
metadata: dict[string, any]
```

### NumericParameterSpec

```text
name: string
low: float
high: float
log: bool
default: optional float
```

### CategoricalParameterSpec

```text
name: string
choices: list[string]
default: optional string
```

## Versioning rules

Contract changes must be deliberate.

Compatible changes:

- adding an optional field,
- adding a new enum value only if consumers can ignore unknown values,
- adding metadata fields.

Breaking changes:

- removing a field,
- renaming a field,
- changing field meaning,
- changing a required field type,
- making an optional field required.

## Dependency rule

All services and core packages may depend on contracts.

Contracts must not depend on services or core packages.

## Anti-patterns

Do not put these in contracts:

- optimizer algorithms,
- validator implementation,
- evaluator implementation,
- database repositories,
- service clients,
- business workflows.
