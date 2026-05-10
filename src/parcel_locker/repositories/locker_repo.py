from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
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

    async def find_nearest(
        self,
        *,
        latitude: float,
        longitude: float,
        limit: int,
    ) -> Sequence[tuple[Locker, float]]:
        """Return up to ``limit`` lockers ordered by distance, with meters distance.

        Uses PostGIS KNN (``<->``) on ``geography`` for great-circle ordering.
        """
        point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
        origin = func.ST_GeogFromText(point_wkt)
        # ST_Distance on geography returns meters.
        distance_expr = func.ST_Distance(Locker.geom, origin).label("distance_m")

        stmt = (
            select(Locker, distance_expr)
            .order_by(Locker.geom.op("<->")(origin))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]

    async def replace_slots(self, locker: Locker, slots: list[Slot]) -> None:
        locker.slots.clear()
        for slot in slots:
            slot.locker_id = locker.id
            locker.slots.append(slot)
        await self._session.flush()
