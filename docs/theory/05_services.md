# 05 — Services

## Service boundaries

Even though the project starts as a monorepo, services should be treated as future deployment boundaries.

Initial services can be simple local wrappers. They should not directly import each other's internal code.

## Optimizer service

Responsible for suggesting candidates and observing results.

Initial API shape:

```text
start_run(config) -> run_id
suggest_candidate(run_id) -> CandidateProposal
observe_trial(run_id, TrialObservation) -> OptimizerState
```

The optimizer service should not validate or evaluate candidates directly. It may call abstractions provided by the orchestrator.

## Validator service

Responsible for validating AbstractElementDTO objects.

Initial API shape:

```text
validate(ValidationRequest) -> ValidationResult
```

The validator should return structured rejection information.

## Evaluator service

Responsible for computing objective values for valid elements.

Initial API shape:

```text
evaluate(EvaluationRequest) -> EvaluationResult
```

The evaluator should assume candidates have already been validated, but may still fail gracefully.

## Orchestrator service

Responsible for connecting optimizer, validator and evaluator.

Initial API shape:

```text
run_optimization(OptimizationRunConfig) -> OptimizationRunResult
```

The orchestrator owns the high-level flow:

```text
while budget remains:
  candidate = optimizer.suggest_candidate()
  validation = validator.validate(candidate.element)
  if validation.valid:
      evaluation = evaluator.evaluate(candidate.element)
  observation = build TrialObservation
  optimizer.observe_trial(observation)
  store observation
```

## Local-first implementation

Initially, services do not need HTTP or gRPC.

Start with in-process interfaces:

```python
class ValidatorPort(Protocol):
    def validate(self, request: ValidationRequest) -> ValidationResult: ...
```

Later, this can be replaced by HTTP or message-based adapters without changing core logic.

## Future communication options

Possible future options:

1. REST for simple synchronous calls.
2. gRPC for typed service-to-service communication.
3. Message queue for asynchronous expensive evaluations.
4. Event log for trial observations.

The contracts should work for all of these options.
