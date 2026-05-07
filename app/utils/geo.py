from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    lat: float
    lon: float


def haversine_km(a: Point, b: Point) -> float:
    """
    Great-circle distance between two lat/lon points.
    Accurate enough for city-scale route optimization prototypes.
    """

    r = 6371.0
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)

    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


