"""Integration tests for the Control API."""

from httpx import AsyncClient


async def test_health(api_client: AsyncClient) -> None:
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_experiment(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/experiments",
        json={"name": "Test Exp", "target_set_version": "v1", "search_space_version": "v1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Exp"
    assert data["status"] == "active"
    assert "id" in data


async def test_get_experiment_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/experiments/no-such-id")
    assert response.status_code == 404


async def test_register_client(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/clients/register",
        json={"name": "worker-01", "client_version": "0.1.0", "machine_fingerprint": "fp-001"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "worker-01"
    assert data["status"] == "online"


async def test_register_client_idempotent(api_client: AsyncClient) -> None:
    payload = {"name": "worker", "client_version": "0.1.0", "machine_fingerprint": "fp-idem"}
    r1 = await api_client.post("/clients/register", json=payload)
    r2 = await api_client.post("/clients/register", json={**payload, "client_version": "0.2.0"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]
    assert r2.json()["client_version"] == "0.2.0"


async def test_client_heartbeat(api_client: AsyncClient) -> None:
    r = await api_client.post(
        "/clients/register",
        json={"name": "hb-worker", "client_version": "0.1.0", "machine_fingerprint": "fp-hb"},
    )
    client_id = r.json()["id"]
    response = await api_client.post(f"/clients/{client_id}/heartbeat")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


async def test_full_job_lifecycle(api_client: AsyncClient) -> None:
    """A fake client registers, claims a job, runs it, and completes it."""

    # Register client
    r = await api_client.post(
        "/clients/register",
        json={
            "name": "lifecycle-worker",
            "client_version": "0.1.0",
            "machine_fingerprint": "fp-lifecycle",
        },
    )
    assert r.status_code == 201
    client_id = r.json()["id"]

    # Create experiment
    r = await api_client.post(
        "/experiments",
        json={"name": "Lifecycle Test", "target_set_version": "v1", "search_space_version": "v1"},
    )
    assert r.status_code == 201
    experiment_id = r.json()["id"]

    # Create mod version
    r = await api_client.post(
        "/mod-versions",
        json={
            "experiment_id": experiment_id,
            "mod_schema_version": "v1",
            "search_space_version": "v1",
            "game_version": "1.0.0",
        },
    )
    assert r.status_code == 201
    mod_version_id = r.json()["id"]
    assert r.json()["status"] == "pending"

    # Mark mod version artifact as ready
    r = await api_client.patch(
        f"/mod-versions/{mod_version_id}/artifact",
        json={"artifact_uri": "s3://bucket/mv-1.zip", "artifact_hash": "abc123"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ready"

    # Create simulation job
    r = await api_client.post(
        "/jobs",
        json={
            "experiment_id": experiment_id,
            "mod_version_id": mod_version_id,
            "seed": 42,
            "start_date": "1444.11.11",
            "end_date": "1821.01.03",
            "required_game_version": "1.0.0",
        },
    )
    assert r.status_code == 201
    job_id = r.json()["id"]
    assert r.json()["status"] == "pending"

    # List pending jobs
    r = await api_client.get("/jobs?status=pending")
    assert r.status_code == 200
    assert any(j["id"] == job_id for j in r.json())

    # Claim the job
    r = await api_client.post(f"/jobs/{job_id}/claim", json={"client_id": client_id})
    assert r.status_code == 200
    assert r.json()["status"] == "claimed"
    assert r.json()["assigned_client_id"] == client_id

    # Claiming the same job again returns 409
    r2 = await api_client.post(f"/jobs/{job_id}/claim", json={"client_id": client_id})
    assert r2.status_code == 409

    # Start a run
    r = await api_client.post(
        "/runs", json={"simulation_job_id": job_id, "client_id": client_id}
    )
    assert r.status_code == 201
    run_id = r.json()["id"]
    assert r.json()["exit_status"] is None

    # Complete the run with results
    r = await api_client.patch(
        f"/runs/{run_id}",
        json={
            "exit_status": "success",
            "artifact_root_uri": "s3://bucket/runs/run-1/",
            "run_manifest": {"snapshots": 12},
        },
    )
    assert r.status_code == 200
    assert r.json()["exit_status"] == "success"
    assert r.json()["artifact_root_uri"] == "s3://bucket/runs/run-1/"
    assert r.json()["finished_at"] is not None

    # Complete the job
    r = await api_client.post(f"/jobs/{job_id}/complete", json={"status": "completed"})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["completed_at"] is not None
