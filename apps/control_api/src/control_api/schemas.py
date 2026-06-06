from pydantic import BaseModel


class CreateExperimentRequest(BaseModel):
    name: str
    description: str = ""
    objective_definition: dict[str, object] = {}
    target_set_version: str
    search_space_version: str


class RegisterClientRequest(BaseModel):
    name: str
    client_version: str
    machine_fingerprint: str
    capabilities: dict[str, object] = {}


class CreateModVersionRequest(BaseModel):
    experiment_id: str
    parent_mod_version_id: str | None = None
    base_mod_version_id: str | None = None
    operation_ids: list[str] = []
    mod_schema_version: str
    search_space_version: str
    game_version: str


class UpdateArtifactRequest(BaseModel):
    artifact_uri: str
    artifact_hash: str


class CreateJobRequest(BaseModel):
    experiment_id: str
    mod_version_id: str
    baseline_save_id: str | None = None
    seed: int
    start_date: str
    end_date: str
    snapshot_interval_days: int = 365
    fidelity_level: str = "fake"
    required_game_version: str


class ClaimJobRequest(BaseModel):
    client_id: str


class CompleteJobRequest(BaseModel):
    status: str


class CreateRunRequest(BaseModel):
    simulation_job_id: str
    client_id: str


class CompleteRunRequest(BaseModel):
    exit_status: str
    crash_reason: str | None = None
    run_manifest: dict[str, object] = {}
    artifact_root_uri: str | None = None
