# ADR 0002: Use a Versioned Operation Registry

## Status

Accepted

## Context

The optimizer must modify numeric values and later add new events, situations, and other scripted mechanics. Old runs must remain useful after the search space expands.

## Decision

Represent all mod changes as versioned operations managed by an Operation Registry.

Each operation type implements:

- validation,
- rendering,
- vectorization,
- complexity scoring,
- description.

Operation schemas are additive and versioned.

## Consequences

Positive:

- old runs remain interpretable,
- optimizers are decoupled from rendering,
- search-space expansion is auditable,
- structural content can be validated before rendering.

Negative:

- more upfront schema work,
- every new operation type requires tests and docs.
