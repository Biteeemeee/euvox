import httpx
from euvox.common_schemas import ClientDTO, RunDTO, SimulationJobDTO


class ControlApiClient:
    """Thin async wrapper around the Control API HTTP interface."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def register(
        self,
        name: str,
        client_version: str,
        fingerprint: str,
        capabilities: dict[str, object] | None = None,
    ) -> ClientDTO:
        r = await self._http.post(
            "/clients/register",
            json={
                "name": name,
                "client_version": client_version,
                "machine_fingerprint": fingerprint,
                "capabilities": capabilities or {},
            },
        )
        r.raise_for_status()
        return ClientDTO.model_validate(r.json())

    async def heartbeat(self, client_id: str) -> None:
        r = await self._http.post(f"/clients/{client_id}/heartbeat")
        r.raise_for_status()

    async def list_pending_jobs(self) -> list[SimulationJobDTO]:
        r = await self._http.get("/jobs", params={"status": "pending"})
        r.raise_for_status()
        return [SimulationJobDTO.model_validate(j) for j in r.json()]

    async def claim_job(self, job_id: str, client_id: str) -> SimulationJobDTO | None:
        r = await self._http.post(f"/jobs/{job_id}/claim", json={"client_id": client_id})
        if r.status_code == 409:
            return None
        r.raise_for_status()
        return SimulationJobDTO.model_validate(r.json())

    async def create_run(self, job_id: str, client_id: str) -> RunDTO:
        r = await self._http.post(
            "/runs", json={"simulation_job_id": job_id, "client_id": client_id}
        )
        r.raise_for_status()
        return RunDTO.model_validate(r.json())

    async def complete_run(
        self,
        run_id: str,
        exit_status: str,
        run_manifest: dict[str, object],
        artifact_root_uri: str | None = None,
        crash_reason: str | None = None,
    ) -> RunDTO:
        r = await self._http.patch(
            f"/runs/{run_id}",
            json={
                "exit_status": exit_status,
                "run_manifest": run_manifest,
                "artifact_root_uri": artifact_root_uri,
                "crash_reason": crash_reason,
            },
        )
        r.raise_for_status()
        return RunDTO.model_validate(r.json())

    async def complete_job(self, job_id: str, status: str) -> None:
        r = await self._http.post(f"/jobs/{job_id}/complete", json={"status": status})
        r.raise_for_status()
