"""Incident type endpoints — CRUD for incident categories."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_incident_types():
    """List active incident categories from incident_types table."""
    # TODO: return where is_active = true
    pass


@router.post("/")
async def create_incident_type():
    """Admin creates new incident type (type_name, severity_weight)."""
    # TODO: admin-only creation
    pass


@router.patch("/{incident_type_id}")
async def update_incident_type(incident_type_id: int):
    """Update incident type details or toggle is_active."""
    # TODO: partial update
    pass
