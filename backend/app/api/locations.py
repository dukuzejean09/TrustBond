"""Location endpoints — Musanze administrative boundaries."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_locations():
    """List Musanze admin boundaries (sectors → cells → villages hierarchy)."""
    # TODO: return locations with parent hierarchy
    pass


@router.get("/{location_id}")
async def get_location(location_id: int):
    """Single location with geometry polygon."""
    # TODO: return with PostGIS geometry
    pass
