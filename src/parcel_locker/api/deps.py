from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from parcel_locker.db.session import get_db_session
from parcel_locker.services.locker_service import LockerService
from parcel_locker.services.parcel_service import ParcelService

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_locker_service(session: DbSession) -> LockerService:
    return LockerService(session)


def get_parcel_service(session: DbSession) -> ParcelService:
    return ParcelService(session)


LockerServiceDep = Annotated[LockerService, Depends(get_locker_service)]
ParcelServiceDep = Annotated[ParcelService, Depends(get_parcel_service)]
