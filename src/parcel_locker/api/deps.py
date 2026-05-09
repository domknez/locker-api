from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from parcel_locker.db.session import get_db_session
from parcel_locker.services.locker_service import LockerService

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_locker_service(session: DbSession) -> LockerService:
    return LockerService(session)


LockerServiceDep = Annotated[LockerService, Depends(get_locker_service)]
