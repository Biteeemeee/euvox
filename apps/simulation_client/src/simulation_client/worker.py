import asyncio

import structlog

from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings
from simulation_client.runner import FakeRunner

logger = structlog.get_logger()


class SimulationWorker:
    def __init__(self, api: ControlApiClient, settings: Settings) -> None:
        self._api = api
        self._settings = settings
        self._runner = FakeRunner(settings.work_dir)

    async def run_once(self, client_id: str) -> bool:
        """Claim and execute one pending job. Returns True if a job was processed."""
        jobs = await self._api.list_pending_jobs()
        if not jobs:
            return False

        for job in jobs:
            claimed = await self._api.claim_job(job.id, client_id)
            if claimed is None:
                continue

            log = logger.bind(job_id=job.id)
            log.info("job_claimed")
            run = await self._api.create_run(job.id, client_id)

            try:
                manifest, job_dir = await self._runner.run(claimed)
                await self._api.complete_run(
                    run.id,
                    exit_status="success",
                    run_manifest=manifest.to_dict(),
                    artifact_root_uri=f"file://{job_dir}",
                )
                await self._api.complete_job(job.id, "completed")
                log.info("job_completed", snapshots=len(manifest.snapshots))
            except Exception as exc:
                log.error("job_failed", error=str(exc))
                await self._api.complete_run(
                    run.id,
                    exit_status="crash",
                    run_manifest={},
                    crash_reason=str(exc),
                )
                await self._api.complete_job(job.id, "failed")

            return True

        return False

    async def run_loop(self, client_id: str) -> None:
        """Poll forever, processing jobs as they appear."""
        while True:
            try:
                processed = await self.run_once(client_id)
                if not processed:
                    await asyncio.sleep(self._settings.poll_interval)
            except Exception as exc:
                logger.error("worker_error", error=str(exc))
                await asyncio.sleep(self._settings.poll_interval)
