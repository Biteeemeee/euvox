# Codex Guidelines

These guidelines are for coding agents working on this repository.

## Read First

Before changing code, read:

1. `README.md`
2. `docs/PROJECT_OVERVIEW.md`
3. `docs/ARCHITECTURE.md`
4. `docs/MILESTONES.md`
5. relevant service or package docs

## Working Style

Make small, reviewable changes. Prefer narrow pull requests or commits.

Do not implement broad functionality by guessing. If a service interface is unclear, create or update the interface first and add tests.

## Core Rules

1. **Do not couple services directly to each other's internals.** Use shared schemas or APIs.
2. **Do not bypass versioning.** Any artifact, operation, parser output, metric result, model, or search-space change must carry version metadata.
3. **Do not make EU5-specific assumptions in generic packages.** Keep core abstractions game-agnostic where possible.
4. **Do not let LLM/agent output directly become executable/mod code without schema validation.**
5. **Do not break old operation schemas.** Add a new schema version instead.
6. **Do not compute final scores on Windows clients.** Clients may perform local sanity checks, but server-side evaluation is authoritative.
7. **Do not store large binary artifacts in PostgreSQL.** Store them in object storage and persist URIs.
8. **Do not silently swallow parser or runner errors.** Persist structured failures.

## Python Style

Use:

- Python 3.12+
- type hints everywhere
- Pydantic v2 for external/data schemas
- SQLAlchemy 2 for DB models
- pytest for tests
- ruff for formatting/linting
- mypy for static checking where practical

Prefer explicit, boring code over clever abstractions.

## Package Boundaries

Shared packages should be imported by apps. Apps should not import from other apps.

Allowed:

```python
from packages.common_schemas import OperationSpec
from packages.operation_registry import OperationRegistry
```

Avoid:

```python
from apps.mod_builder_service.internal import SomeClass
```

## Schema Design

Every persistent schema must include:

- stable ID,
- schema version,
- creation timestamp where relevant,
- source/version metadata where relevant.

For versioned data, prefer explicit fields:

```python
operation_type: str
operation_schema_version: str
search_space_version: str | None
```

Do not infer versions from object shape.

## Testing Requirements

For each feature, add at least one of:

- unit test,
- contract test,
- integration test,
- migration test,
- golden-file rendering test.

Important test categories:

- operation validation,
- operation rendering,
- operation vectorization,
- API request/response schemas,
- job lifecycle,
- artifact manifest integrity,
- parser version behavior,
- metric version behavior.

## Fake First

Implement fake adapters before real EU5 automation.

Examples:

- `FakeSimulationRunner`
- `FakeSaveParser`
- `FakeArtifactStore`
- `RuleBasedHistoryAgent`
- `RandomSearchOptimizer`

Then replace with real implementations behind the same interface.

## Documentation Updates

When adding or changing a major component, update:

- relevant docs under `docs/`,
- an ADR if the decision changes architecture,
- examples if schemas change.

## Pull Request Checklist

Before considering a task complete:

```text
[ ] Tests added or updated
[ ] Type hints added
[ ] No direct app-to-app imports
[ ] Persistent data includes version metadata
[ ] New operation schemas are additive
[ ] Docs updated where appropriate
[ ] Fake implementations still work
```
