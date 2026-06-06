# Data Model

## Main Entities

### Experiment

Represents an optimization campaign.

Fields:

```text
id
name
description
objective_definition_json
target_set_version
search_space_version
status
created_at
updated_at
```

### Operation

A versioned change to the mod or search space.

Fields:

```text
id
experiment_id
parent_operation_id nullable
operation_type
operation_schema_version
operation_json
created_by
created_at
status
validation_status
```

### ModVersion

A buildable or built mod state.

Fields:

```text
id
experiment_id
parent_mod_version_id nullable
base_mod_version_id nullable
operation_ids
mod_schema_version
search_space_version
game_version
artifact_uri
artifact_hash
manifest_json
status
created_at
```

### SimulationJob

A scheduled expensive evaluation.

Fields:

```text
id
experiment_id
mod_version_id
baseline_save_id
seed
start_date
end_date
snapshot_interval_days
fidelity_level
required_game_version
status
assigned_client_id nullable
created_at
claimed_at nullable
completed_at nullable
```

### Client

A registered Windows worker.

Fields:

```text
id
name
client_version
machine_fingerprint
capabilities_json
last_heartbeat_at
status
```

### Run

Actual execution of a simulation job.

Fields:

```text
id
simulation_job_id
client_id
started_at
finished_at
exit_status
crash_reason nullable
run_manifest_json
artifact_root_uri
```

### Snapshot

A raw and/or parsed save snapshot.

Fields:

```text
id
run_id
game_date
raw_save_uri
raw_save_hash
parsed_state_uri nullable
parser_version nullable
parse_status
warnings_json
```

### Evaluation

Metric output for a run or mod version.

Fields:

```text
id
run_id
metric_suite_version
target_set_version
score_total
score_json
side_effect_score
created_at
```

### AgentReview

Persisted agent result.

Fields:

```text
id
operation_id
agent_name
agent_version
model_name nullable
prompt_version nullable
input_hash
output_json
verdict
created_at
```

### SurrogateModelArtifact

Persisted trained surrogate model.

Fields:

```text
id
model_type
model_version
feature_schema_version
training_sample_query_json
training_sample_count
artifact_uri
metrics_json
created_at
```

### SurrogateTrainingSample

A learning record derived from a candidate and its evaluation.

Fields:

```text
id
experiment_id
operation_id nullable
mod_version_id
information_vector_uri
operation_vector_uri
result_vector_uri
feature_schema_version
result_schema_version
fidelity_level
valid_for_training
created_at
```

## Versioning Requirements

Persist these fields whenever applicable:

```text
game_version
operation_schema_version
search_space_version
parser_version
metric_suite_version
target_set_version
feature_schema_version
surrogate_model_version
client_version
```

## Old Runs and Search Space Expansion

When the search space expands, old runs must remain valid. New dimensions must have explicit default values for old candidates.

Example:

```text
search_space_v12:
  no Louisiana event

search_space_v13:
  event_louisiana_transfer.enabled default false
```

Old mod versions can be vectorized under v13 by assigning defaults.

## Artifact URIs

Use URI fields for large artifacts:

```text
s3://bucket/mods/mod_0001.zip
s3://bucket/runs/run_0001/saves/1500.eu5
s3://bucket/runs/run_0001/logs/error.log
```

PostgreSQL must not store raw save files or large logs.
