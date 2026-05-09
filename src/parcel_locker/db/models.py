from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parcel_locker.db.base import Base
from parcel_locker.domain.enums import SlotSize


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Locker(Base, TimestampMixin):
    __tablename__ = "lockers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    slots: Mapped[list[Slot]] = relationship(
        back_populates="locker",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Slot(Base, TimestampMixin):
    __tablename__ = "locker_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    locker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lockers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    size: Mapped[SlotSize] = mapped_column(
        SAEnum(SlotSize, name="slot_size", native_enum=True),
        nullable=False,
        index=True,
    )
    is_occupied: Mapped[bool] = mapped_column(default=False, nullable=False)

    locker: Mapped[Locker] = relationship(back_populates="slots")
