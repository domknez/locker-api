from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from parcel_locker.api.deps import get_locker_service, get_parcel_service
from parcel_locker.core.config import get_settings
from parcel_locker.db.session import get_db_session
from parcel_locker.main import create_app
from parcel_locker.services.locker_service import LockerService
from parcel_locker.services.parcel_service import ParcelService


@pytest.fixture(scope="session")
def settings() -> Any:
    return get_settings()


@pytest_asyncio.fixture
async def db_session(settings: Any) -> AsyncIterator[AsyncSession]:
    """One savepoint-scoped session per test, rolled back at teardown.

    Requires the schema to already exist (alembic upgrade head run before pytest).
    """
    engine = create_async_engine(settings.database_url, future=True)
    sessionmaker = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )

    async with sessionmaker() as session:
        # Wipe app tables so tests are independent.
        await session.execute(
            text("TRUNCATE parcels, locker_slots, lockers RESTART IDENTITY CASCADE")
        )
        await session.commit()
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client wired against an app where the locker service uses a stub geocoder."""
    app = create_app()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    geocoder_stub = AsyncMock()
    geocoder_stub.geocode = AsyncMock(return_value=(48.1374, 11.5755))  # Munich-ish

    def _override_locker_service() -> LockerService:
        return LockerService(db_session, geocoder=geocoder_stub)

    def _override_parcel_service() -> ParcelService:
        return ParcelService(db_session)

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_locker_service] = _override_locker_service
    app.dependency_overrides[get_parcel_service] = _override_parcel_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {get_settings().api_bearer_token}"
        yield ac
