"""Location endpoints — Musanze administrative boundaries."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.location import Location
from app.schemas.location import LocationResponse, LocationDetailResponse
from app.utils.geo import is_within_musanze

# Geo functions
from geoalchemy2.functions import ST_AsGeoJSON, ST_Contains, ST_SetSRID, ST_Point

router = APIRouter()


@router.get("/", response_model=List[LocationResponse])
async def list_locations(
    location_type: Optional[str] = None,
    parent_location_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List Musanze admin boundaries (sectors → cells → villages).

    If no filters are given, returns top-level sectors.
    Use `parent_location_id` to drill down the hierarchy.
    """
    query = db.query(Location).filter(Location.is_active == True)  # noqa: E712

    if location_type:
        query = query.filter(Location.location_type == location_type)
    if parent_location_id is not None:
        query = query.filter(Location.parent_location_id == parent_location_id)
    elif location_type is None:
        # Default: return top-level sectors
        query = query.filter(Location.parent_location_id == None)  # noqa: E711

    return query.order_by(Location.location_name).all()


@router.get("/{location_id}", response_model=LocationDetailResponse)
async def get_location(
    location_id: int,
    db: Session = Depends(get_db),
):
    """Single location with geometry and child locations."""
    location = db.query(Location).filter(
        Location.location_id == location_id
    ).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found",
        )

    # Get children
    children = (
        db.query(Location)
        .filter(
            Location.parent_location_id == location_id,
            Location.is_active == True,  # noqa: E712
        )
        .order_by(Location.location_name)
        .all()
    )

    result = LocationDetailResponse.model_validate(location)
    result.children = children

    # Convert PostGIS geometry to GeoJSON if available
    if location.geometry is not None:
        try:
            geojson_str = db.scalar(ST_AsGeoJSON(location.geometry))
            result.geometry = json.loads(geojson_str) if geojson_str else None
        except Exception:
            result.geometry = None

    return result


@router.get('/reverse', response_model=LocationResponse)
async def reverse_geocode(
    lat: float,
    lon: float,
    location_type: Optional[str] = 'village',
    db: Session = Depends(get_db),
):
    """Reverse-geocode a GPS point to the containing location.

    - Attempts point-in-polygon (PostGIS ST_Contains) for accuracy.
    - Falls back to nearest centroid if no containing polygon is found.
    Returns 404 if no matching location exists.
    """
    # Basic bounds check for Musanze (reject obviously invalid input)
    if not is_within_musanze(lat, lon):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Point outside Musanze bounds')

    # 1) Try point-in-polygon using PostGIS
    try:
        point = ST_SetSRID(ST_Point(lon, lat), 4326)
        loc = (
            db.query(Location)
            .filter(
                Location.location_type == location_type,
                Location.is_active == True,  # noqa: E712
                Location.geometry != None,  # noqa: E711
                ST_Contains(Location.geometry, point),
            )
            .first()
        )
        if loc:
            return loc
    except Exception:
        # If spatial function fails, continue to centroid fallback
        pass

    # 2) Fallback — nearest centroid (in Python; dataset is small)
    candidates = (
        db.query(Location)
        .filter(
            Location.location_type == location_type,
            Location.centroid_lat != None,  # noqa: E711
            Location.centroid_long != None,  # noqa: E711
            Location.is_active == True,  # noqa: E712
        )
        .all()
    )

    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No location data available')

    # Haversine distance (approx) to choose nearest centroid
    import math

    def _deg2rad(d):
        return d * (math.pi / 180.0)

    def _haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000.0
        dLat = _deg2rad(lat2 - lat1)
        dLon = _deg2rad(lon2 - lon1)
        a = math.sin(dLat / 2) ** 2 + math.cos(_deg2rad(lat1)) * math.cos(_deg2rad(lat2)) * math.sin(dLon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    best = None
    best_dist = float('inf')
    for c in candidates:
        if c.centroid_lat is None or c.centroid_long is None:
            continue
        try:
            d = _haversine_m(float(lat), float(lon), float(c.centroid_lat), float(c.centroid_long))
        except Exception:
            continue
        if d < best_dist:
            best_dist = d
            best = c

    if best:
        return best

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No matching location found')
