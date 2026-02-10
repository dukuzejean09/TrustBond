"""Report assignment endpoints — case handling workflow."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_assignment():
    """Assign report to officer with priority (low/medium/high/urgent)."""
    pass


@router.get("/")
async def list_assignments():
    """List assignments filterable by status, priority, officer."""
    pass


@router.patch("/{assignment_id}")
async def update_assignment(assignment_id: str):
    """Update assignment status: assigned → investigating → resolved → closed."""
    pass
