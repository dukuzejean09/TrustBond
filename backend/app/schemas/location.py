"""Pydantic schemas for locations (Musanze admin boundaries)."""

from pydantic import BaseModel
from typing import Optional, List, Any
from decimal import Decimal


class LocationResponse(BaseModel):
    location_id: int
    location_type: str
    location_name: str
    parent_location_id: Optional[int] = None
    centroid_lat: Optional[Decimal] = None
    centroid_long: Optional[Decimal] = None
    is_active: bool

    class Config:
        from_attributes = True


class LocationDetailResponse(LocationResponse):
    geometry: Optional[Any] = None       # GeoJSON when available
    children: List[LocationResponse] = []
