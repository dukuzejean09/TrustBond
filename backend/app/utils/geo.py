"""GPS utilities — bounds checking, distance calculations."""

import math

# Rwanda bounding box
RWANDA_BOUNDS = {
    "min_lat": -2.8400,
    "max_lat": -1.0500,
    "min_lon": 28.8600,
    "max_lon": 30.8990,
}

# Musanze District approximate bounds
MUSANZE_BOUNDS = {
    "min_lat": -1.6200,
    "max_lat": -1.4200,
    "min_lon": 29.4500,
    "max_lon": 29.7000,
}


def is_within_rwanda(lat: float, lon: float) -> bool:
    return (RWANDA_BOUNDS["min_lat"] <= lat <= RWANDA_BOUNDS["max_lat"] and
            RWANDA_BOUNDS["min_lon"] <= lon <= RWANDA_BOUNDS["max_lon"])


def is_within_musanze(lat: float, lon: float) -> bool:
    return (MUSANZE_BOUNDS["min_lat"] <= lat <= MUSANZE_BOUNDS["max_lat"] and
            MUSANZE_BOUNDS["min_lon"] <= lon <= MUSANZE_BOUNDS["max_lon"])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two GPS points."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
