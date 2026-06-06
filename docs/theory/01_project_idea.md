# 01 — Project Idea

## Problem statement

We want to solve optimization problems over a large search space. The search space is not necessarily fixed. During optimization, the system may need to expand the search space by creating new abstract elements.

An abstract element consists of numerical and categorical values. Before an element may be evaluated, it must be checked by a validator. The validator either accepts or rejects the element based on its values.

The optimizer should learn from valid evaluations and, where useful, from rejected candidates.

## Abstract element concept

An abstract element is the main candidate object exchanged between components.

Conceptually:

```text
AbstractElement
  id
  schema_version
  numeric_values
  categorical_values
  metadata
```

Example:

```json
{
  "id": "candidate-001",
  "schema_version": "1.0",
  "numeric_values": {
    "x1": 0.73,
    "x2": 12.5
  },
  "categorical_values": {
    "type": "A",
    "strategy": "fast"
  },
  "metadata": {
    "search_space_version": "v1"
  }
}
```

## Optimization loop

The intended loop is:

```text
1. Optimizer asks search-space manager for the current search space.
2. Optimizer generates candidate values.
3. AbstractElementFactory builds an AbstractElement.
4. Validator accepts or rejects the element.
5. Valid elements are evaluated.
6. Optimizer observes the result.
7. Search-space manager may expand the search space.
8. Repeat until budget or convergence criterion is reached.
```

## Expensive evaluation assumption

The project should assume that real evaluations may be expensive.

Therefore the architecture should support:

- cheap validation before expensive evaluation,
- cheap candidate generation,
- candidate ranking before full evaluation,
- surrogate models in the future,
- multi-fidelity evaluation in the future,
- strict evaluation budgets.

## Long-term optimization direction

The system should eventually support several strategies:

1. Simple random or rule-based search.
2. Evolutionary candidate generation.
3. Bayesian optimization or Optuna-based optimization.
4. Surrogate-assisted evolutionary optimization.
5. Multi-fidelity optimization.

The first implementation should remain simple but should not block these future strategies.
