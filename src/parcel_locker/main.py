from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from parcel_locker import __version__
from parcel_locker.api.health import router as health_router
from parcel_locker.core.config import get_settings
from parcel_locker.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger(__name__)
    log.info("app.startup", env=settings.app_env, version=__version__)
    yield
    log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Parcel Locker API",
        version=__version__,
        description="REST API for parcel locker registration and parcel-to-slot assignment.",
        lifespan=lifespan,
        debug=settings.app_env == "dev",
    )

    app.include_router(health_router)

    return app


app = create_app()
