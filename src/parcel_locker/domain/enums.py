from enum import StrEnum


class SlotSize(StrEnum):
    """Parcel/slot size. Ordering reflects physical capacity (XS smallest)."""

    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

    @property
    def rank(self) -> int:
        return _SIZE_ORDER[self]


_SIZE_ORDER: dict[SlotSize, int] = {
    SlotSize.XS: 0,
    SlotSize.S: 1,
    SlotSize.M: 2,
    SlotSize.L: 3,
    SlotSize.XL: 4,
}


class ParcelState(StrEnum):
    """Lifecycle of a parcel from submission to terminal state."""

    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    IN_LOCKER = "IN_LOCKER"
    PICKED_UP = "PICKED_UP"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# Allowed state transitions. Empty set = terminal.
PARCEL_TRANSITIONS: dict[ParcelState, frozenset[ParcelState]] = {
    ParcelState.CREATED: frozenset({ParcelState.ASSIGNED, ParcelState.CANCELLED}),
    ParcelState.ASSIGNED: frozenset(
        {ParcelState.IN_LOCKER, ParcelState.EXPIRED, ParcelState.CANCELLED}
    ),
    ParcelState.IN_LOCKER: frozenset({ParcelState.PICKED_UP, ParcelState.EXPIRED}),
    ParcelState.PICKED_UP: frozenset(),
    ParcelState.EXPIRED: frozenset(),
    ParcelState.CANCELLED: frozenset(),
}


def is_terminal(state: ParcelState) -> bool:
    return not PARCEL_TRANSITIONS[state]
