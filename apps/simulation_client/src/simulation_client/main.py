import asyncio

import httpx
import structlog

from simulation_client.api_client import ControlApiClient
from simulation_client.config import Settings, get_settings
from simulation_client.worker import SimulationWorker

logger = structlog.get_logger()


async def _heartbeat_loop(api: ControlApiClient, client_id: str, interval: float) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await api.heartbeat(client_id)
            logger.debug("heartbeat_sent", client_id=client_id)
        except Exception as exc:
            logger.warning("heartbeat_failed", error=str(exc))


async def run(settings: Settings | None = None) -> None:
    if settings is None:
        settings = get_settings()

    settings.work_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "starting",
        control_api_url=settings.control_api_url,
        work_dir=str(settings.work_dir),
    )

    async with httpx.AsyncClient(base_url=settings.control_api_url, timeout=30.0) as http:
        api = ControlApiClient(http)

        client_dto = await api.register(
            name=settings.client_name,
            client_version=settings.client_version,
            fingerprint=settings.machine_fingerprint,
            capabilities={"runner": "fake", "platform": "python"},
        )
        client_id = client_dto.id
        logger.info("registered", client_id=client_id)

        worker = SimulationWorker(api, settings)
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(api, client_id, settings.heartbeat_interval)
        )

        try:
            await worker.run_loop(client_id)
        finally:
            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
