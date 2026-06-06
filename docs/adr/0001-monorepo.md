# ADR 0001: Use a Python Monorepo

## Status

Accepted

## Context

The project contains multiple services and shared domain abstractions. Many components depend on shared schemas, operation definitions, and versioning rules.

## Decision

Use a Python monorepo with:

```text
apps/      runtime services
packages/  shared libraries
infra/     Docker, migrations, scripts
docs/      architecture and guidelines
tests/     integration and contract tests
```

## Consequences

Positive:

- easier shared schema changes,
- easier Codex work across boundaries,
- simpler local development,
- centralized documentation,
- consistent tooling.

Negative:

- requires discipline around package boundaries,
- CI may need path-aware optimization later.
