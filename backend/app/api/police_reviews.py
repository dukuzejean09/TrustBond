"""Police review endpoints — ground truth decisions on reports."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_review():
    """Officer reviews report: decision (confirmed/rejected/investigation), ground_truth_label, confidence_level."""
    # TODO: create police_review, update devices trust score
    pass


@router.get("/report/{report_id}")
async def get_reviews_for_report(report_id: str):
    """Get all reviews for a specific report."""
    pass
