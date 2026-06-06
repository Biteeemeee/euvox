# Reproducibility

## Purpose

Every result must be traceable back to the exact mod, operations, game version, client, parser, metric, and model versions used.

## Required Metadata

For every simulation run, capture:

```text
run_id
simulation_job_id
experiment_id
mod_version_id
mod_artifact_hash
operation_ids
game_version
dlc_or_content_configuration if available
baseline_save_id
baseline_save_hash
seed if controllable
client_id
client_version
windows_version
start_date
end_date
snapshot_interval
parser_version
metric_suite_version
target_set_version
```

## Run Manifest

Each client should upload a run manifest.

```json
{
  "run_id": "run_001",
  "job_id": "job_001",
  "client_id": "win-sim-01",
  "mod_version_id": "mod_001",
  "mod_artifact_hash": "sha256:...",
  "baseline_save_hash": "sha256:...",
  "game_version": "EU5_X.Y.Z",
  "started_at": "...",
  "finished_at": "...",
  "exit_status": "completed",
  "snapshots": [
    {"game_date": "1500.1.1", "uri": "s3://...", "hash": "sha256:..."}
  ],
  "logs": {
    "error_log": "s3://...",
    "client_log": "s3://..."
  }
}
```

## Versioned Search Spaces

Search-space expansion must be explicit and versioned.

Old runs remain valid by assigning default values for new dimensions.

## Parser and Metric Versions

Parser outputs and metric outputs must never be treated as timeless truth.

When parser or metric logic changes:

- create a new version,
- keep old results,
- optionally re-evaluate old raw saves,
- store both evaluations.

## Artifact Hashing

Hash every artifact:

- mod zip,
- raw save,
- parsed snapshot,
- model artifact,
- target set file.

Use SHA-256.

## Audit Trail

Every generated event or structural operation should be explainable:

```text
Which deviation triggered it?
Which optimizer suggested it?
Which agents approved it?
Which constraints were applied?
Which renderer produced it?
Which simulations tested it?
What was its measured effect?
```
