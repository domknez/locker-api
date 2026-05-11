from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from parcel_locker.api.deps import LockerServiceDep
from parcel_locker.core.security import require_bearer_token
from parcel_locker.schemas.locker import (
    LockerCreate,
    LockerRead,
    LockerUpdate,
    LockerWithDistance,
)

router = APIRouter(prefix="/lockers", tags=["lockers"])
AuthDep = Depends(require_bearer_token)


@router.post(
    "",
    response_model=LockerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a locker",
    dependencies=[AuthDep],
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
    lockers = await service.list_lockers(limit=limit, offset=offset)
    return [LockerRead.model_validate(loc) for loc in lockers]


@router.get(
    "/nearest",
    response_model=list[LockerWithDistance],
    summary="Find lockers nearest to an address",
)
async def nearest_lockers(
    service: LockerServiceDep,
    address: Annotated[str, Query(min_length=1, max_length=500)],
    limit: Annotated[int, Query(ge=1, le=50)] = 5,
) -> list[LockerWithDistance]:
    results = await service.nearest_by_address(address, limit=limit)
    return [
        LockerWithDistance(
            locker=LockerRead.model_validate(loc),
            distance_meters=dist,
        )
        for loc, dist in results
    ]


@router.get("/{locker_id}", response_model=LockerRead, summary="Get a locker")
async def get_locker(locker_id: UUID, service: LockerServiceDep) -> LockerRead:
    locker = await service.get(locker_id)
    return LockerRead.model_validate(locker)


@router.put(
    "/{locker_id}",
    response_model=LockerRead,
    summary="Update a locker",
    dependencies=[AuthDep],
)
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
    dependencies=[AuthDep],
)
async def delete_locker(locker_id: UUID, service: LockerServiceDep) -> Response:
    await service.delete(locker_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
