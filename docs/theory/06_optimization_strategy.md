# 06 — Optimization Strategy

## Initial strategy

Start simple.

The first optimizer should be easy to understand and test.

Recommended first implementation:

```text
RandomCandidateGenerator
RuleBasedValidator
SimpleEvaluator
BasicSearchSpaceManager
```

This gives an end-to-end system before introducing algorithmic complexity.

## Search-space expansion

The search space should be managed explicitly by a SearchSpaceManager.

Expansion should happen only through clear policies.

Possible expansion triggers:

- no improvement for N iterations,
- valid candidate ratio too low,
- candidate diversity too low,
- optimization budget remains but current space is exhausted,
- model uncertainty suggests unexplored regions.

Initial policy:

```text
if no improvement for N evaluated trials:
    expand search space by one level
```

## Evolutionary approach

Evolutionary optimization may be introduced after the simple baseline works.

Recommended role:

```text
Evolutionary algorithm as candidate generator, not necessarily as the only optimizer.
```

This is important because evaluations may be expensive.

The evolutionary generator may:

- mutate good valid candidates,
- recombine candidate values,
- introduce new categorical choices,
- generate expanded abstract elements,
- maintain population diversity.

## Expensive evaluation strategy

If full evaluations are expensive, avoid evaluating every generated candidate.

Preferred long-term flow:

```text
Generate many candidates cheaply
Validate candidates cheaply
Rank candidates using surrogate or heuristic
Evaluate only top-K diverse candidates
Observe results
Update model
```

## Surrogate-assisted optimization

The architecture should later support two learned models:

```text
validity_model(element) -> probability of validity
performance_model(element) -> expected score and uncertainty
```

Candidate ranking can then use:

```text
acquisition_score = expected_score * probability_valid + exploration_bonus - cost_penalty
```

## Optuna integration

Optuna may be added as an optimizer backend.

Recommended integration:

- use ask/tell style where possible,
- keep SearchSpaceManager outside Optuna,
- use constraints or penalties for invalid candidates,
- do not mutate categorical parameter distributions under the same parameter name.

## Framework direction

Potential frameworks:

- DEAP for flexible evolutionary algorithms,
- pymoo for constraints and multi-objective optimization,
- Optuna for Bayesian/TPE-style optimization,
- BoTorch/Ax for advanced Bayesian optimization,
- Nevergrad for black-box ask/tell optimization.

Do not introduce a heavy framework before the local baseline exists.
