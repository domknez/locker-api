from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from parcel_locker.db.models import Locker, Slot


class LockerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, locker_id: UUID) -> Locker | None:
        return await self._session.get(Locker, locker_id)

    async def list(self, *, limit: int, offset: int) -> Sequence[Locker]:
        stmt = select(Locker).order_by(Locker.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, locker: Locker) -> Locker:
        self._session.add(locker)
        await self._session.flush()
        await self._session.refresh(locker, attribute_names=["slots"])
        return locker

    async def delete(self, locker: Locker) -> None:
        await self._session.delete(locker)
        await self._session.flush()

    async def replace_slots(self, locker: Locker, slots: list[Slot]) -> None:
        locker.slots.clear()
        for slot in slots:
            slot.locker_id = locker.id
            locker.slots.append(slot)
        await self._session.flush()
