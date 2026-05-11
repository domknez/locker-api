from __future__ import annotations

from functools import cache
from typing import Any

import httpx
from cachetools import TTLCache

from parcel_locker.core.config import Settings, get_settings
from parcel_locker.core.logging import get_logger
from parcel_locker.domain.exceptions import GeocodingError

log = get_logger(__name__)


class NominatimClient:
    """Async Nominatim geocoder. Caches successful resolutions in-process."""

    def __init__(
        self,
        settings: Settings | None = None,
        cache: TTLCache[str, tuple[float, float]] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        # 24h TTL, bounded size to avoid unbounded growth.
        self._cache = (
            cache if cache is not None else TTLCache(maxsize=1024, ttl=24 * 3600)
        )
        self._client = client

    async def geocode(self, address: str) -> tuple[float, float]:
        """Resolve an address to (lat, lon). Raises GeocodingError on failure."""
        normalized = address.strip()
        if not normalized:
            raise GeocodingError("Empty address")

        cached = self._cache.get(normalized)
        if cached is not None:
            return cached

        coords = await self._call_nominatim(normalized)
        self._cache[normalized] = coords
        return coords

    async def _call_nominatim(self, address: str) -> tuple[float, float]:
        url = f"{self._settings.nominatim_base_url.rstrip('/')}/search"
        params = {"q": address, "format": "json", "limit": "1"}
        headers = {
            "User-Agent": self._settings.nominatim_user_agent,
            "Accept": "application/json",
            "Accept-Language": "en",
        }
        timeout = httpx.Timeout(self._settings.nominatim_timeout_seconds)

        try:
            client = self._client or httpx.AsyncClient(timeout=timeout, headers=headers)
            close_after = self._client is None
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload: list[dict[str, Any]] = response.json()
            finally:
                if close_after:
                    await client.aclose()
        except httpx.HTTPError as exc:
            log.warning("nominatim.http_error", error=str(exc), address=address)
            raise GeocodingError(f"Geocoding request failed: {exc}") from exc

        if not payload:
            log.info("nominatim.no_match", address=address)
            raise GeocodingError(f"No geocoding result for address: {address}")

        first = payload[0]
        try:
            lat = float(first["lat"])
            lon = float(first["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("nominatim.bad_payload", payload=first)
            raise GeocodingError("Malformed geocoding response") from exc

        return lat, lon


@cache
def get_geocoder() -> NominatimClient:
    """Process-wide singleton so the in-process cache survives across requests."""
    return NominatimClient()
