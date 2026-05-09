from __future__ import annotations

from collections import Counter
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from parcel_locker.domain.enums import SlotSize


class SlotsSpec(BaseModel):
    """Counts of slots per size when creating/updating a locker."""

    XS: int = Field(default=0, ge=0, le=1000)
    S: int = Field(default=0, ge=0, le=1000)
    M: int = Field(default=0, ge=0, le=1000)
    L: int = Field(default=0, ge=0, le=1000)
    XL: int = Field(default=0, ge=0, le=1000)

    def to_counter(self) -> Counter[SlotSize]:
        return Counter(
            {
                SlotSize.XS: self.XS,
                SlotSize.S: self.S,
                SlotSize.M: self.M,
                SlotSize.L: self.L,
                SlotSize.XL: self.XL,
            }
        )

    @field_validator("XS", "S", "M", "L", "XL", mode="after")
    @classmethod
    def _non_negative(cls, v: int) -> int:
        return v


class LockerCreate(BaseModel):
    address: str = Field(min_length=1, max_length=500)
    slots: SlotsSpec = Field(default_factory=SlotsSpec)


class LockerUpdate(BaseModel):
    """All fields optional. Slots, when provided, fully replace the configuration."""

    address: str | None = Field(default=None, min_length=1, max_length=500)
    slots: SlotsSpec | None = None


class SlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    size: SlotSize
    is_occupied: bool


class LockerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    address: str
    latitude: float
    longitude: float
    slots: list[SlotRead]
    created_at: datetime
    updated_at: datetime
