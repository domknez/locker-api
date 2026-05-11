def point_wkt(latitude: float, longitude: float) -> str:
    """SRID-tagged WKT for a single point.

    PostGIS uses ``(x y)`` order where ``x = longitude``, ``y = latitude``.
    Centralized here so callers think in (lat, lon) and never get the order wrong.
    """
    return f"SRID=4326;POINT({longitude} {latitude})"
