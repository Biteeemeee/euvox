# ADR 0004: Version Parser, Metrics, Targets, and Search Spaces

## Status

Accepted

## Context

Save parsing, metric definitions, historical targets, and search spaces will change over time. Old simulation runs are expensive and must not become worthless when evaluation logic improves.

## Decision

Every parsed snapshot and evaluation must carry explicit versions:

```text
parser_version
metric_suite_version
target_set_version
search_space_version
feature_schema_version
```

New evaluations do not overwrite old evaluations.

## Consequences

Positive:

- old raw saves can be re-evaluated,
- model training data is traceable,
- score changes can be explained,
- search-space expansion remains compatible.

Negative:

- more metadata,
- more database rows,
- dashboards must handle multiple evaluation versions.
