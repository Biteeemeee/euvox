# Operation Registry

## Purpose

The Operation Registry defines all structured changes the optimizer may apply to the mod or search space.

Operations are the central abstraction of the project. They allow the system to evolve a mod while preserving lineage, validation, rendering, and vectorization.

## Core Concept

```text
ModVersion = ParentModVersion + Operation[]
```

Each operation is:

- typed,
- schema-versioned,
- validated,
- renderable,
- vectorizable,
- auditable.

## Operation Interface

```python
from typing import Protocol

class OperationType(Protocol):
    type_name: str
    schema_version: str

    def validate(self, spec: dict) -> "ValidationResult":
        ...

    def render(self, spec: dict, context: "RenderContext") -> "RenderResult":
        ...

    def vectorize(self, spec: dict, context: "VectorizationContext") -> "OperationVector":
        ...

    def complexity(self, spec: dict) -> float:
        ...

    def describe(self, spec: dict) -> str:
        ...
```

## Initial Operation Types

### numeric_patch@v1

Changes a numeric parameter in a known file/key path.

Example:

```json
{
  "operation_type": "numeric_patch",
  "operation_schema_version": "v1",
  "spec": {
    "target": "war_cost_factor",
    "value": 1.15,
    "bounds": [0.5, 2.0]
  }
}
```

### update_event_weight@v1

Changes chance or AI weight of an existing event or option.

```json
{
  "operation_type": "update_event_weight",
  "operation_schema_version": "v1",
  "spec": {
    "event_id": "some_namespace.42",
    "weight_key": "monthly_chance",
    "value": 5
  }
}
```

### create_event@v1

Adds a generated event from a structured event spec.

```json
{
  "operation_type": "create_event",
  "operation_schema_version": "v1",
  "spec": {
    "event_id": "gen_colonial_louisiana_transfer_001",
    "namespace": "opt_colonial_transfers",
    "scope": "country",
    "primary_tag": "FRA",
    "secondary_tag": "SPA",
    "rival_tag": "GBR",
    "time_window": {
      "start_year": 1756,
      "end_year": 1770,
      "preferred_year": 1762
    },
    "mechanism": "colonial_transfer",
    "trigger_profile": {
      "requires_region_control": "louisiana",
      "requires_colonial_pressure": true,
      "requires_receiver_not_hostile": true
    },
    "effect_profile": {
      "effect_type": "transfer_region",
      "region": "louisiana",
      "from": "FRA",
      "to": "SPA"
    },
    "ai_weight_historical": 90,
    "enabled": true
  }
}
```

### create_situation@v1

Reserved for later milestones. Do not implement before event operations work.

## Validation Layers

Each operation should pass:

1. schema validation,
2. operation-specific validation,
3. historical validation if structural,
4. rendering validation,
5. optional runtime validation.

## Rendering

Operation rendering must be deterministic when possible.

Do not let raw LLM output directly become EU5 files. LLM/agent output must first populate structured specs such as `EventSpec`, then the renderer writes script and localization.

## Vectorization

Each operation type must define vectorization into a stable feature schema.

Vectorization must include default values for missing dimensions when older runs are evaluated under newer search-space versions.

## Schema Evolution

Never mutate old schemas destructively.

Good:

```text
create_event@v1
create_event@v2
```

Bad:

```text
change meaning of create_event@v1.effect_strength
```

## Complexity Score

Every operation should expose a complexity estimate.

Examples:

```text
numeric_patch: low
update_event_weight: low
create_event: medium
create_event_chain: high
create_situation: high
```

The optimizer and acquisition function use complexity to prefer simpler interventions when scores are similar.
