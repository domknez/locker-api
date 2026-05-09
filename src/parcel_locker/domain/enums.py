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
