# Project Overview

## Purpose

Build a distributed optimization platform that improves the historical plausibility of Europa Universalis V simulations by iteratively modifying a mod, running simulations, evaluating savegame snapshots, and updating an optimization model.

The project targets two classes of changes:

1. **Parameter changes**: numeric or categorical values such as costs, weights, probabilities, AI preferences, or modifiers.
2. **Structural changes**: new or modified events, event chains, situations, AI weights, or other scripted mechanics.

The long-term goal is not to maximize fun or player satisfaction. The initial objective is historical plausibility of simulated world states.

## Main Concept

The optimizer does not directly write arbitrary EU5 script. It produces structured, versioned operations.

```text
Candidate = BaseMod + list[Operation]

Operation =
  NumericPatch
  | UpdateEventWeight
  | CreateEvent
  | CreateSituation
  | UpdateAiWeight
  | ...
```

Each operation has:

- a type name,
- a schema version,
- a JSON spec,
- validation logic,
- rendering logic,
- vectorization logic for surrogate models,
- lineage metadata.

This keeps old runs useful even when the search space expands later.

## Distributed Execution Model

The system is split into a server side and one or more Windows simulation clients.

```text
Server:
  - experiment orchestration
  - operation registry
  - mod building
  - job queue
  - databases
  - artifact storage
  - optimizer
  - surrogate model
  - agent layer
  - parser and evaluation services

Windows clients:
  - claim simulation jobs
  - download mod artifacts and baseline saves
  - install/activate the test mod
  - start EU5 in debug mode
  - load a prepared baseline save
  - run observer simulations
  - create save snapshots
  - collect logs and crash reports
  - upload artifacts to the server
```

## Optimization Strategy

The chosen strategy is:

```text
SearchSpaceManager
→ Population / Archive
→ Evolutionary Candidate Generator
→ Validator Layer
→ Feature Encoder
→ Surrogate Ensemble
→ Acquisition / Infill Selection
→ Multi-Fidelity Expensive Evaluation
→ Result Normalization
→ Archive Update
→ Model Update
→ Search Space Expansion
```

The system should support surrogate-assisted evolutionary optimization, multi-objective evaluation, multi-fidelity simulation budgets, and versioned search-space expansion.

## Core Design Principles

1. **Version everything**: operations, search spaces, parser outputs, metrics, models, targets, game versions, mod artifacts.
2. **Keep old runs valuable**: new dimensions must have explicit default values for older runs.
3. **Separate mechanism from text**: agents may write descriptions and context, but mechanics are structured operation specs.
4. **Use deterministic renderers where possible**: LLMs should not directly emit final EU5 files except behind validation.
5. **Prefer baseline saves over GUI new-game automation**: autonomous simulations should load versioned baseline saves.
6. **Use fake simulation first**: the platform must work end-to-end before real EU5 automation is attempted.
7. **Treat the server as source of truth**: clients execute jobs but do not decide optimization policy.
8. **Make each component replaceable**: optimizers, surrogates, metrics, parsers, and operation types must be plug-in-like.

## Non-Goals for MVP

The MVP should not attempt:

- full EU5 GUI automation from main menu,
- free-form LLM-written mods,
- complex event chains,
- situations,
- reinforcement learning,
- large-scale orchestration such as Kubernetes,
- perfect historical target databases.

Start small and prove the loop.
