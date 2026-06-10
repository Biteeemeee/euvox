import asyncio
from typing import Protocol, runtime_checkable

import structlog
from euvox.common_schemas import SimulationJobDTO

from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings
from simulation_client.eu5_locator import Eu5Locator
from simulation_client.eu5_runner import Eu5Runner
from simulation_client.runner import FakeRunner, RunManifest

logger = structlog.get_logger()


@runtime_checkable
class Runner(Protocol):
    async def run(self, job: SimulationJobDTO, **kwargs: object) -> tuple[RunManifest, object]: ...


def _build_runner(settings: Settings) -> object:
    """Return Eu5Runner when EU5 is available, otherwise FakeRunner."""
    locator = Eu5Locator()
    exe = locator.find_exe(settings.eu5_exe_path)
    if exe is not None:
        user_dir = locator.find_user_dir(settings.eu5_user_dir)
        logger.info("using_eu5_runner", exe=str(exe), user_dir=str(user_dir))
        return Eu5Runner(
            eu5_exe=exe,
            user_dir=user_dir,
            launch_timeout=settings.eu5_launch_timeout,
            run_timeout=settings.eu5_run_timeout,
            save_poll_interval=settings.eu5_save_poll_interval,
        )
    logger.info("eu5_not_found_using_fake_runner")
    return FakeRunner(settings.work_dir)


class SimulationWorker:
    def __init__(self, api: ControlApiClient, settings: Settings) -> None:
        self._api = api
        self._settings = settings
        self._runner = _build_runner(settings)

    def runner_name(self) -> str:
        return type(self._runner).__name__

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
                if isinstance(self._runner, Eu5Runner):
                    manifest, job_dir = await self._runner.run(claimed, mod_files={})
                else:
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
