from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from parcel_locker.core.config import Settings, get_settings
from parcel_locker.db.models import Parcel
from parcel_locker.domain.enums import (
    PARCEL_TRANSITIONS,
    ParcelState,
)
from parcel_locker.domain.exceptions import (
    InvalidStateTransitionError,
    NoSlotAvailableError,
    NotFoundError,
)
from parcel_locker.repositories.parcel_repo import ParcelRepository
from parcel_locker.schemas.parcel import ParcelCreate


class ParcelService:
    """Application service for parcel lifecycle and slot assignment."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._repo = ParcelRepository(session)
        self._settings = settings or get_settings()

    async def create(self, payload: ParcelCreate) -> Parcel:
        submitted_at = (
            payload.submitted_at.astimezone(UTC)
            if payload.submitted_at
            else datetime.now(UTC)
        )
        expires_at = submitted_at + timedelta(
            hours=self._settings.parcel_submission_ttl_hours
        )

        slot = await self._repo.acquire_free_slot(payload.size)
        if slot is None:
            raise NoSlotAvailableError(
                f"No free slot available for size {payload.size}"
            )
        slot.is_occupied = True

        parcel = Parcel(
            sender=payload.sender,
            receiver=payload.receiver,
            size=payload.size,
            state=ParcelState.ASSIGNED,
            slot_id=slot.id,
            submitted_at=submitted_at,
            expires_at=expires_at,
        )
        await self._repo.add(parcel)
        await self._session.commit()
        await self._session.refresh(parcel)
        return parcel

    async def get(self, parcel_id: UUID) -> Parcel:
        parcel = await self._repo.get(parcel_id)
        if parcel is None:
            raise NotFoundError(f"Parcel {parcel_id} not found")
        return parcel

    async def list(self, *, limit: int, offset: int) -> Sequence[Parcel]:
        return await self._repo.list_all(limit=limit, offset=offset)

    async def transition(self, parcel_id: UUID, target: ParcelState) -> Parcel:
        parcel = await self.get(parcel_id)
        allowed = PARCEL_TRANSITIONS[parcel.state]
        if target not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition parcel from {parcel.state} to {target}"
            )

        parcel.state = target

        # Free the slot on terminal states that release the locker.
        terminal_releases = {
            ParcelState.PICKED_UP,
            ParcelState.EXPIRED,
            ParcelState.CANCELLED,
        }
        if target in terminal_releases and parcel.slot is not None:
            parcel.slot.is_occupied = False

        await self._session.commit()
        await self._session.refresh(parcel)
        return parcel
