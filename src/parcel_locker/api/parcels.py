from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from parcel_locker.api.deps import ParcelServiceDep
from parcel_locker.core.security import require_bearer_token
from parcel_locker.schemas.parcel import ParcelCreate, ParcelRead, ParcelTransition

router = APIRouter(prefix="/parcels", tags=["parcels"])
AuthDep = Depends(require_bearer_token)


@router.post(
    "",
    response_model=ParcelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a parcel and assign it to a slot",
    dependencies=[AuthDep],
)
async def create_parcel(payload: ParcelCreate, service: ParcelServiceDep) -> ParcelRead:
    parcel = await service.create(payload)
    return ParcelRead.model_validate(parcel)


@router.get("", response_model=list[ParcelRead], summary="List parcels")
async def list_parcels(
    service: ParcelServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ParcelRead]:
    parcels = await service.list(limit=limit, offset=offset)
    return [ParcelRead.model_validate(p) for p in parcels]


@router.get("/{parcel_id}", response_model=ParcelRead, summary="Get a parcel")
async def get_parcel(parcel_id: UUID, service: ParcelServiceDep) -> ParcelRead:
    parcel = await service.get(parcel_id)
    return ParcelRead.model_validate(parcel)


@router.post(
    "/{parcel_id}/transition",
    response_model=ParcelRead,
    summary="Transition parcel to a new state",
    dependencies=[AuthDep],
)
async def transition_parcel(
    parcel_id: UUID,
    payload: ParcelTransition,
    service: ParcelServiceDep,
) -> ParcelRead:
    parcel = await service.transition(parcel_id, payload.target_state)
    return ParcelRead.model_validate(parcel)
