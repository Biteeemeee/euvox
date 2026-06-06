# ADR 0003: Use RabbitMQ and Celery for Background Jobs

## Status

Proposed

## Context

The system needs background jobs for mod building, parsing, evaluation, training, candidate generation, and agent review. It also needs retries and routing.

## Decision

Use RabbitMQ as broker and Celery as Python task framework for server-side background jobs.

## Consequences

Positive:

- mature Python ecosystem,
- supports retries,
- supports multiple job types,
- suitable for local Docker Compose,
- can scale later.

Negative:

- adds operational complexity,
- Celery task boundaries must be kept clean,
- result backend strategy must be defined.

## Alternatives Considered

- Redis + RQ: simpler, good for MVP, less flexible for complex routing.
- Dramatiq: good alternative, simpler than Celery in some cases.
- Plain database queue: simple but likely too limited later.
