from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from parcel_locker.domain.enums import ParcelState, SlotSize


class ParcelCreate(BaseModel):
    sender: str = Field(min_length=1, max_length=255)
    receiver: str = Field(min_length=1, max_length=255)
    size: SlotSize
    submitted_at: AwareDatetime | None = Field(
        default=None,
        description="Optional client timestamp; server uses now() if omitted. Must be tz-aware.",
    )


class ParcelTransition(BaseModel):
    target_state: ParcelState


class ParcelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender: str
    receiver: str
    size: SlotSize
    state: ParcelState
    slot_id: UUID | None
    submitted_at: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
