# Mod Build Pipeline

## Purpose

The mod build pipeline turns structured, validated operations into a versioned EU5 mod artifact.

## Pipeline

```text
Operation chain
→ Operation validation
→ Agent validation/enrichment if needed
→ Render context creation
→ Deterministic file rendering
→ Localization rendering
→ Manifest generation
→ ZIP packaging
→ Hashing
→ Artifact upload
→ ModVersion persistence
```

## Build Inputs

```json
{
  "base_mod_version_id": "mod_base_001",
  "operations": [
    {
      "operation_type": "numeric_patch",
      "operation_schema_version": "v1",
      "spec": {}
    }
  ],
  "game_version": "EU5_X.Y.Z",
  "search_space_version": "ss_v1"
}
```

## Build Outputs

```json
{
  "mod_version_id": "mod_000123",
  "artifact_uri": "s3://mods/mod_000123.zip",
  "artifact_hash": "sha256:...",
  "manifest": {
    "game_version": "EU5_X.Y.Z",
    "operations": [],
    "rendered_files": [],
    "build_tool_version": "v1"
  }
}
```

## Manifest Requirements

Every mod artifact must include a manifest file with:

```text
mod_version_id
parent_mod_version_id
operation_ids
game_version
search_space_version
builder_version
rendered_files
artifact_hash
created_at
```

## Rendering Rules

- Prefer additive files over replacing vanilla files.
- Generated files must include comments identifying operation ID and mod version.
- Generated localization keys must be unique and deterministic.
- Generated events must include instrumentation where possible.
- Do not overwrite unrelated files.

## Validation

Build validation stages:

1. operation schema validation,
2. operation-specific validation,
3. agent gate if structural,
4. render validation,
5. package validation,
6. optional runtime smoke-test.

## Event Instrumentation

Generated events should leave traces for later evaluation.

Possible strategies:

- set persistent country/global variables,
- add temporary marker modifiers,
- write detectable state changes,
- include event IDs in generated metadata.

Exact implementation depends on EU5 script support discovered during modding research.
