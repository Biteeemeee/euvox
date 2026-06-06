# ADR 0005: Prefer Baseline Saves Over New-Game GUI Automation

## Status

Accepted for MVP

## Context

Autonomously starting a new EU5 game from the main menu may require fragile GUI automation. Loading a prepared baseline save in debug mode is expected to be more robust.

## Decision

The MVP simulation client will load versioned baseline saves instead of creating new games through the GUI.

New baseline save creation may be added later as a separate, less frequent workflow.

## Consequences

Positive:

- fewer UI automation risks,
- better reproducibility,
- stable simulation job input,
- easier client implementation.

Negative:

- baseline saves must be created and versioned,
- game/mod version changes may require new baselines.
