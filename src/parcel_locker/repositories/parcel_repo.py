from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from parcel_locker.db.models import Parcel, Slot
from parcel_locker.domain.enums import SlotSize


class ParcelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, parcel_id: UUID) -> Parcel | None:
        return await self._session.get(Parcel, parcel_id)

    async def list_all(self, *, limit: int, offset: int) -> Sequence[Parcel]:
        stmt = (
            select(Parcel)
            .order_by(Parcel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().unique().all()

    async def add(self, parcel: Parcel) -> Parcel:
        self._session.add(parcel)
        await self._session.flush()
        return parcel

    async def acquire_free_slot(self, size: SlotSize) -> Slot | None:
        """Lock and return the first unoccupied slot of the requested size.

        Uses ``FOR UPDATE SKIP LOCKED`` so concurrent assignments do not
        contend on the same slot. Caller must mark the slot as occupied
        before commit.
        """
        stmt = (
            select(Slot)
            .where(Slot.size == size, Slot.is_occupied.is_(False))
            .order_by(Slot.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
            .options(selectinload(Slot.locker))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
