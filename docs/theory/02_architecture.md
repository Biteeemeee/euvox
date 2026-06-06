# 02 — Architecture

## High-level components

The system should be split into the following logical components:

```text
Orchestrator
Optimizer
SearchSpaceManager
CandidateGenerator
AbstractElementFactory
Validator
Evaluator
ObservationStore
Contracts
```

## Component responsibilities

### Orchestrator

Coordinates the complete optimization run.

Responsibilities:

- start and stop optimization runs,
- call optimizer steps,
- route candidates to validator and evaluator,
- persist observations,
- trigger search-space expansion,
- expose CLI or service APIs later.

The orchestrator should not contain optimization logic itself.

### Optimizer

Decides which candidates should be tried next.

Responsibilities:

- suggest candidate values,
- observe evaluation results,
- track optimization state,
- respect evaluation budgets,
- signal stagnation or uncertainty.

The optimizer should not directly know the internal implementation of the validator or evaluator.

### SearchSpaceManager

Owns the current definition of the search space.

Responsibilities:

- define active numeric parameters,
- define active categorical parameters,
- version the search space,
- expand the search space when needed,
- keep expansion decisions explicit and traceable.

### CandidateGenerator

Produces raw candidate parameter values based on the current search space.

This may initially be simple random sampling. Later, it can be replaced with an evolutionary generator or a surrogate-assisted generator.

### AbstractElementFactory

Converts raw candidate values into an AbstractElement contract object.

This boundary is important because candidate values and domain elements may evolve independently.

### Validator

Checks whether an AbstractElement is admissible.

Responsibilities:

- accept valid elements,
- reject invalid elements,
- return rejection reasons,
- optionally return violated constraints.

The validator should be cheap compared to the evaluator.

### Evaluator

Computes the objective score for a valid AbstractElement.

Responsibilities:

- evaluate valid elements,
- return score and metrics,
- record duration and cost if available,
- support cheap, medium and full evaluation modes later.

### ObservationStore

Stores what happened during an optimization run.

Responsibilities:

- store generated candidates,
- store validation results,
- store evaluation results,
- store rejected candidates,
- support later analysis and model training.

## Dependency direction

Prefer this direction:

```text
services -> packages -> contracts
```

Avoid dependencies from shared packages back into services.

## Boundary principle

Each component should communicate through explicit request and result objects.

For example:

```text
ValidationRequest -> ValidationResult
EvaluationRequest -> EvaluationResult
CandidateProposal -> TrialObservation
```

This makes later service extraction easier.
