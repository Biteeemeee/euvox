from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from euvox.core.db import make_engine, make_session_factory
from fastapi import FastAPI

from control_api.config import get_settings
from control_api.routers import clients, experiments, health, jobs, mod_versions, runs

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not hasattr(app.state, "engine"):
        settings = get_settings()
        app.state.engine = make_engine(settings.database_url, echo=settings.debug)
        app.state.session_factory = make_session_factory(app.state.engine)
        logger.info("database_connected", url=settings.database_url)
        owned = True
    else:
        owned = False
    yield
    if owned:
        await app.state.engine.dispose()
        logger.info("database_disconnected")


app = FastAPI(title="EU5 Optimizer Control API", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(experiments.router)
app.include_router(clients.router)
app.include_router(jobs.router)
app.include_router(mod_versions.router)
app.include_router(runs.router)
