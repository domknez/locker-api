from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from parcel_locker.api.deps import LockerServiceDep
from parcel_locker.schemas.locker import LockerCreate, LockerRead, LockerUpdate

router = APIRouter(prefix="/lockers", tags=["lockers"])


@router.post(
    "",
    response_model=LockerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a locker",
)
async def create_locker(payload: LockerCreate, service: LockerServiceDep) -> LockerRead:
    locker = await service.create(payload)
    return LockerRead.model_validate(locker)


@router.get("", response_model=list[LockerRead], summary="List lockers")
async def list_lockers(
    service: LockerServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LockerRead]:
    lockers = await service.list(limit=limit, offset=offset)
    return [LockerRead.model_validate(loc) for loc in lockers]


@router.get("/{locker_id}", response_model=LockerRead, summary="Get a locker")
async def get_locker(locker_id: UUID, service: LockerServiceDep) -> LockerRead:
    locker = await service.get(locker_id)
    return LockerRead.model_validate(locker)


@router.put("/{locker_id}", response_model=LockerRead, summary="Update a locker")
async def update_locker(
    locker_id: UUID,
    payload: LockerUpdate,
    service: LockerServiceDep,
) -> LockerRead:
    locker = await service.update(locker_id, payload)
    return LockerRead.model_validate(locker)


@router.delete(
    "/{locker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a locker",
)
async def delete_locker(locker_id: UUID, service: LockerServiceDep) -> Response:
    await service.delete(locker_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
