"""Hotspot endpoints — DBSCAN cluster management."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_hotspots():
    """Retrieve hotspots (center_lat, center_long, radius_meters, incident_count, risk_level)."""
    pass


@router.get("/{hotspot_id}/reports")
async def get_hotspot_reports(hotspot_id: int):
    """Get linked reports via hotspot_reports join table."""
    pass


@router.get("/map-data")
async def get_map_data():
    """GeoJSON for map rendering using locations.geometry."""
    pass


@router.post("/recalculate")
async def recalculate_hotspots():
    """Trigger DBSCAN reclustering, rebuild hotspot_reports."""
    pass
