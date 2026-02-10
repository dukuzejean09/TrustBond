"""Incident group endpoints — duplicate incident grouping."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_incident_groups():
    """List grouped duplicate reports."""
    pass


@router.get("/{group_id}")
async def get_incident_group(group_id: str):
    """Get group detail with linked reports."""
    pass
