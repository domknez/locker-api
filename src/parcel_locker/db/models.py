from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography, WKBElement, WKTElement
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parcel_locker.db.base import Base
from parcel_locker.domain.enums import ParcelState, SlotSize


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
    # Reads return WKBElement; writes accept WKTElement (or raw string via bind processor).
    geom: Mapped[WKBElement | WKTElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

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
    parcel: Mapped[Parcel | None] = relationship(
        back_populates="slot",
        uselist=False,
        foreign_keys="Parcel.slot_id",
    )


class Parcel(Base, TimestampMixin):
    __tablename__ = "parcels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[SlotSize] = mapped_column(
        SAEnum(SlotSize, name="slot_size", native_enum=True, create_type=False),
        nullable=False,
        index=True,
    )
    state: Mapped[ParcelState] = mapped_column(
        SAEnum(ParcelState, name="parcel_state", native_enum=True),
        nullable=False,
        default=ParcelState.CREATED,
        index=True,
    )
    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locker_slots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    slot: Mapped[Slot | None] = relationship(
        back_populates="parcel",
        foreign_keys=[slot_id],
        lazy="joined",
    )
