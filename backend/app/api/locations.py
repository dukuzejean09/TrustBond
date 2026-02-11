"""Location endpoints — Musanze administrative boundaries."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.location import Location
from app.schemas.location import LocationResponse, LocationDetailResponse

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
            from geoalchemy2.functions import ST_AsGeoJSON
            geojson_str = db.scalar(ST_AsGeoJSON(location.geometry))
            result.geometry = json.loads(geojson_str) if geojson_str else None
        except Exception:
            result.geometry = None

    return result
