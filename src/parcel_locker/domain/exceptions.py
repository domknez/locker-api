class DomainError(Exception):
    """Base for all domain-level errors."""


class NotFoundError(DomainError):
    """Aggregate not found."""


class ConflictError(DomainError):
    """Operation violates a business rule or invariant."""


class GeocodingError(DomainError):
    """Failed to resolve an address to coordinates."""


class NoSlotAvailableError(ConflictError):
    """No free slot fits the parcel size."""
