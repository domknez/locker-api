from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from parcel_locker.db.models import Locker, Slot
from parcel_locker.domain.enums import SlotSize
from parcel_locker.domain.exceptions import NotFoundError
from parcel_locker.repositories.locker_repo import LockerRepository
from parcel_locker.schemas.locker import LockerCreate, LockerUpdate, SlotsSpec
from parcel_locker.services.geocoding import NominatimClient, get_geocoder


class LockerService:
    """Application service for locker lifecycle. Coordinates repo + geocoding."""

    def __init__(
        self,
        session: AsyncSession,
        geocoder: NominatimClient | None = None,
    ) -> None:
        self._session = session
        self._repo = LockerRepository(session)
        self._geocoder = geocoder or get_geocoder()

    async def create(self, payload: LockerCreate) -> Locker:
        # Geocoding integrated in Phase 4. For now, placeholder coordinates (0, 0).
        latitude, longitude = await self._resolve_coordinates(payload.address)

        locker = Locker(
            address=payload.address,
            latitude=latitude,
            longitude=longitude,
            slots=_build_slots(payload.slots),
        )
        await self._repo.add(locker)
        await self._session.commit()
        return locker

    async def get(self, locker_id: UUID) -> Locker:
        locker = await self._repo.get(locker_id)
        if locker is None:
            raise NotFoundError(f"Locker {locker_id} not found")
        return locker

    async def list(self, *, limit: int, offset: int) -> Sequence[Locker]:
        return await self._repo.list(limit=limit, offset=offset)

    async def update(self, locker_id: UUID, payload: LockerUpdate) -> Locker:
        locker = await self.get(locker_id)

        if payload.address is not None and payload.address != locker.address:
            locker.address = payload.address
            locker.latitude, locker.longitude = await self._resolve_coordinates(payload.address)

        if payload.slots is not None:
            await self._repo.replace_slots(locker, _build_slots(payload.slots))

        await self._session.commit()
        await self._session.refresh(locker)
        await self._session.refresh(locker, attribute_names=["slots"])
        return locker

    async def delete(self, locker_id: UUID) -> None:
        locker = await self.get(locker_id)
        await self._repo.delete(locker)
        await self._session.commit()

    async def _resolve_coordinates(self, address: str) -> tuple[float, float]:
        return await self._geocoder.geocode(address)


def _build_slots(spec: SlotsSpec) -> list[Slot]:
    slots: list[Slot] = []
    for size, count in spec.to_counter().items():
        slots.extend(Slot(size=SlotSize(size)) for _ in range(count))
    return slots
