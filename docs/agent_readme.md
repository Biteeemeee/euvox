# EU5 Historical Plausibility Optimizer

This repository is intended as a Python monorepo for a distributed optimization platform for Europa Universalis V mod balancing and content generation.

The system optimizes a versioned EU5 mod by running expensive game simulations on one or more Windows desktop clients, extracting savegame snapshots, evaluating historical plausibility, and feeding results back into a surrogate-assisted evolutionary optimization loop.

The project is designed for development with coding agents such as Codex. Read these documents first:

1. `docs/PROJECT_OVERVIEW.md`
2. `docs/ARCHITECTURE.md`
3. `docs/CODEX_GUIDELINES.md`
4. `docs/MILESTONES.md`
5. `docs/OPERATION_REGISTRY.md`
6. `docs/OPTIMIZATION_STRATEGY.md`
7. `docs/SIMULATION_CLIENT.md`

Core idea:

```text
Server = brain and memory
Windows clients = simulation workers
Operations = versioned changes to the mod
Runs = expensive evidence
Evaluations = historical plausibility labels
Surrogate model = cheap predictor for candidate quality
Evolutionary optimizer = generator of structured candidates
Agents = controlled validators/enrichers for historical/event content
```

The MVP should start with fake simulations and numeric operations before real EU5 automation and generated events are added.
