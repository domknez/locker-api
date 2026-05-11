from geoalchemy2 import WKTElement


def point_wkt(latitude: float, longitude: float) -> str:
    """SRID-tagged WKT string for a single point.

    PostGIS uses ``(x y)`` order where ``x = longitude``, ``y = latitude``.
    Centralized here so callers think in (lat, lon) and never get the order wrong.
    """
    return f"SRID=4326;POINT({longitude} {latitude})"


def point_element(latitude: float, longitude: float) -> WKTElement:
    """WKTElement suitable for assignment to a Geography column."""
    return WKTElement(point_wkt(latitude, longitude), srid=4326, extended=True)
