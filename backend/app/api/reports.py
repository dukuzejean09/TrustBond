"""Report endpoints — CRUD for incident reports."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_report():
    """Submit a new incident report (anonymous, from mobile app)."""
    # TODO: create report in reports table, trigger rule-based verification
    pass


@router.get("/")
async def list_reports():
    """List/filter reports (for dashboard). Joins incident_types, devices, ml_predictions."""
    # TODO: paginated, filterable list
    pass


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Single report with evidence_files, ml_predictions, police_reviews, assignments."""
    # TODO: full detail view
    pass


@router.patch("/{report_id}")
async def update_report(report_id: str):
    """Update rule_status, is_flagged."""
    # TODO: partial update
    pass
