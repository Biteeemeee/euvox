# Search Space

## Purpose

The SearchSpaceManager defines what the optimizer is allowed to modify and how candidates can be generated, mutated, crossed over, validated, and vectorized.

## Requirements

The search space must support:

- continuous numeric dimensions,
- integer dimensions,
- categorical dimensions,
- conditional dimensions,
- hierarchical operation structures,
- structural expansion through new events/situations,
- versioning,
- defaults for old candidates.

## Candidate Representation

A candidate is a mod version proposal represented as an operation chain.

```json
{
  "candidate_id": "cand_001",
  "parent_candidate_ids": ["cand_000"],
  "base_mod_version_id": "mod_base_001",
  "operations": [
    {"operation_type": "numeric_patch", "operation_schema_version": "v1", "spec": {}},
    {"operation_type": "create_event", "operation_schema_version": "v1", "spec": {}}
  ],
  "search_space_version": "ss_v3"
}
```

## Search Space Versioning

Every search space change gets a new version.

Examples of changes requiring new versions:

- new operation type,
- new dimension,
- changed bounds,
- changed default,
- changed categorical choices,
- changed mutation rules,
- changed validation constraints.

## Defaults for Old Runs

When new dimensions are introduced, define defaults for old candidates.

Example:

```yaml
new_dimension: event_louisiana_transfer.enabled
default_for_previous_versions: false
```

## Mutation Operators

Initial mutation operators:

```text
mutate_numeric_value
mutate_categorical_value
mutate_event_weight
mutate_event_time_window
mutate_trigger_strictness
add_numeric_patch
add_create_event
remove_operation
disable_operation
```

Later mutation operators:

```text
add_event_option
add_counterfactual_branch
specialize_event_to_region
generalize_event_to_region_group
create_situation_from_event_cluster
```

## Crossover Operators

Initial crossover:

```text
single_point_operation_crossover
operation_subset_crossover
best_region_mechanic_crossover
```

Candidates must remain valid after crossover.

## Constraints

Search space constraints should be declarative where possible:

```yaml
constraints:
  max_new_events_per_candidate: 3
  max_total_operations: 25
  max_complexity_score: 10.0
  forbidden_effects:
    - unconditional_world_annexation
  require_history_gate_for:
    - create_event
    - create_situation
```

## Search Space Expansion

Search space expansion is allowed when the optimizer or deviation detector identifies a missing mechanism.

Example:

```text
Finding:
  France develops plausibly but no Louisiana transfer occurs.

Expansion:
  Add create_event candidate family: colonial_transfer_louisiana.

New dimensions:
  enabled
  trigger_strictness
  time_window_start
  time_window_end
  ai_weight_historical
  effect_variant
```

Expansion must be persisted and linked to evidence.
