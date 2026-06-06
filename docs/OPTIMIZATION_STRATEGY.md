# Optimization Strategy

## Chosen Approach

Use surrogate-assisted evolutionary optimization with search-space expansion.

Core loop:

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

## Why This Approach

The problem is:

- expensive to evaluate,
- noisy across seeds,
- mixed continuous/discrete,
- hierarchical,
- structurally expandable,
- not smooth,
- multi-objective.

Evolutionary candidate generation can handle structured mod candidates. The surrogate reduces the number of expensive EU5 simulations.

## Candidate Lifecycle

```text
1. Candidate generated from population/archive/search-space expansion.
2. Candidate validated structurally.
3. Candidate reviewed by history/agent gates if structural.
4. Candidate vectorized.
5. Surrogate predicts impact, risk, uncertainty, and cost.
6. Acquisition function selects candidates for real evaluation.
7. Mod is built.
8. Simulation jobs are run on clients.
9. Saves are parsed and evaluated.
10. Results update archive and surrogate training set.
```

## Surrogate Ensemble

Use multiple models or heads:

```text
ImpactModel:
  predicts historical plausibility gain

RiskModel:
  predicts side effects in other regions/epochs

ValidityModel:
  predicts technical failure or validation risk

CostModel:
  predicts evaluation cost or crash likelihood
```

MVP can use `ExtraTreesRegressor` or `RandomForestRegressor` from scikit-learn.

## Acquisition Function

Initial acquisition score:

```text
A(x) =
  expected_gain
  - λ1 * expected_side_effect
  - λ2 * complexity
  - λ3 * invalidity_risk
  - λ4 * evaluation_cost
  + β * uncertainty
  + γ * diversity_bonus
```

All terms should be logged separately.

## Multi-Fidelity Evaluation

Use multiple budgets:

```text
low:
  short run, few seeds, quick rejection

medium:
  relevant epoch, several seeds

high:
  long run, many seeds, final validation
```

Do not send every candidate to full-length evaluation.

## Archive / Hall of Fame

Maintain:

- best candidates by total score,
- Pareto frontier candidates,
- diverse candidates by behavior descriptors,
- failed candidates with reasons,
- historically interesting but risky candidates.

## Multi-Objective Scoring

Historical plausibility is not a single natural number. Treat it as multi-objective.

Example objectives:

```text
territorial plausibility
major power ranking plausibility
state continuity
colonial development
regional side-effect minimization
technical stability
intervention simplicity
```

The first MVP can use one weighted score, but store the full breakdown from the start.

## Search Space Expansion

The optimizer may decide that existing dimensions cannot solve a deviation. It may propose adding a new structured operation family.

Example:

```text
Deviation:
  France and Britain have plausible 18th-century colonial rivalry,
  but no Louisiana transfer mechanism exists.

Expansion:
  Add create_event family: louisiana_transfer_to_spain.
```

Expansion process:

```text
1. Optimizer proposes expansion.
2. HistoryAgent validates plausibility.
3. CounterfactualAgent adds ahistorical constraints.
4. SearchSpaceManager registers new dimensions.
5. Default values are defined for old candidates.
6. New search_space_version is created.
```

## Optimizer Interface

```python
class Optimizer(Protocol):
    optimizer_name: str
    optimizer_version: str

    def suggest(
        self,
        context: OptimizationContext,
        history: EvaluationHistory,
        search_space: SearchSpace,
        n: int,
    ) -> list[CandidateOperation]:
        ...
```

Initial implementations:

```text
RandomSearchOptimizer
EvolutionaryOptimizer
SurrogateAssistedEvolutionaryOptimizer
```

## MVP Strategy

1. Random evolutionary search over numeric operations.
2. Add archive and simple metrics.
3. Add ExtraTrees surrogate preselection.
4. Add `create_event@v1` operation with rule-based history gate.
5. Add search-space expansion.
6. Add multi-fidelity evaluation.
7. Add Pareto archive.
