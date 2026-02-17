"""Police review endpoints — ground truth decisions on reports."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.police_user import PoliceUser
from app.models.police_review import PoliceReview
from app.models.report import Report
from app.schemas.police_review import PoliceReviewCreate, PoliceReviewResponse
from app.services.device_service import DeviceService
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/", response_model=PoliceReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: PoliceReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """
    Officer reviews a report.

    After review, the device trust score is recalculated:
    - confirmed  → trusted_reports++
    - rejected   → flagged_reports++
    """
    report = db.query(Report).filter(Report.report_id == data.report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found",
        )

    review = PoliceReview(
        report_id=data.report_id,
        police_user_id=current_user.police_user_id,
        decision=data.decision,
        review_note=data.review_note,
        ground_truth_label=data.ground_truth_label,
        confidence_level=data.confidence_level,
        used_for_training=data.used_for_training,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Update device trust counts based on decision
    if data.decision == "confirmed":
        DeviceService.increment_trusted(db, report.device_id)
    elif data.decision == "rejected":
        DeviceService.increment_flagged(db, report.device_id)

    # Recalculate device trust score
    DeviceService.recalculate_trust(db, report.device_id)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="review",
        entity_type="police_review",
        entity_id=str(review.review_id),
        details={"decision": data.decision, "report_id": str(data.report_id)},
        ip_address=request.client.host if request.client else None,
    )
    return review


@router.get("/report/{report_id}", response_model=List[PoliceReviewResponse])
async def get_reviews_for_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Get all reviews for a specific report."""
    return (
        db.query(PoliceReview)
        .filter(PoliceReview.report_id == report_id)
        .order_by(PoliceReview.reviewed_at.desc())
        .all()
    )
