from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from parcel_locker.api.deps import ParcelServiceDep
from parcel_locker.core.security import BearerAuth
from parcel_locker.db.models import Parcel
from parcel_locker.schemas.parcel import ParcelCreate, ParcelRead, ParcelTransition

router = APIRouter(prefix="/parcels", tags=["parcels"])


@router.post(
    "",
    response_model=ParcelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a parcel and assign it to a slot",
    dependencies=[BearerAuth],
)
async def create_parcel(payload: ParcelCreate, service: ParcelServiceDep) -> Parcel:
    return await service.create(payload)


@router.get("", response_model=list[ParcelRead], summary="List parcels")
async def list_parcels(
    service: ParcelServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Parcel]:
    return await service.list_parcels(limit=limit, offset=offset)


@router.get("/{parcel_id}", response_model=ParcelRead, summary="Get a parcel")
async def get_parcel(parcel_id: UUID, service: ParcelServiceDep) -> Parcel:
    return await service.get(parcel_id)


@router.post(
    "/{parcel_id}/transition",
    response_model=ParcelRead,
    summary="Transition parcel to a new state",
    dependencies=[BearerAuth],
)
async def transition_parcel(
    parcel_id: UUID,
    payload: ParcelTransition,
    service: ParcelServiceDep,
) -> Parcel:
    return await service.transition(parcel_id, payload.target_state)
