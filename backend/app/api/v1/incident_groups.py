from typing import Annotated, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.v1.auth import get_current_admin_or_supervisor, get_current_user
from app.core.auto_case_grouping import auto_group_verified_report
from app.database import get_db
from app.models.incident_group import IncidentGroup
from app.models.police_user import PoliceUser
from app.models.report import Report
from app.schemas.incident_group import IncidentGroupResponse

router = APIRouter(prefix="/incident-groups", tags=["incident-groups"])


@router.get("/", response_model=List[IncidentGroupResponse])
def list_incident_groups(
    db: Session = Depends(get_db),
    _: Annotated[PoliceUser, Depends(get_current_user)] = None,
    incident_type_id: Optional[int] = Query(None, description="Filter by incident type"),
    active_only: bool = Query(False, description="Only return currently active groups"),
    limit: int = Query(50, ge=1, le=200),
):
    """List incident groups (spatial-temporal clusters). Auth required."""
    query = (
        db.query(IncidentGroup)
        .options(joinedload(IncidentGroup.case))
        .order_by(IncidentGroup.created_at.desc())
    )
    if incident_type_id is not None:
        query = query.filter(IncidentGroup.incident_type_id == incident_type_id)
    if active_only:
        query = query.filter(IncidentGroup.is_active == True)
    return query.limit(limit).all()


@router.get("/{group_id}", response_model=IncidentGroupResponse)
def get_incident_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    _: Annotated[PoliceUser, Depends(get_current_user)] = None,
):
    """Get a specific incident group by ID. Auth required."""
    group = (
        db.query(IncidentGroup)
        .options(joinedload(IncidentGroup.case))
        .filter(IncidentGroup.group_id == group_id)
        .first()
    )
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident group not found")
    return group


@router.post("/trigger-grouping/{report_id}", response_model=Dict)
def trigger_grouping_for_report(
    report_id: UUID,
    current_user: Annotated[PoliceUser, Depends(get_current_admin_or_supervisor)],
    db: Session = Depends(get_db),
):
    """Manually trigger the automatic grouping algorithm for a verified report.

    This is useful when the background auto-grouping did not fire or when
    a report is re-verified after manual review.  Only admin/supervisor can
    trigger this.
    """
    report = (
        db.query(Report)
        .options(
            selectinload(Report.device),
            selectinload(Report.ml_predictions),
            selectinload(Report.case_reports),
        )
        .filter(Report.report_id == report_id)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    result = auto_group_verified_report(db, report)
    db.commit()

    if result.incident_group is not None:
        db.refresh(result.incident_group)

    return {
        "grouped": result.incident_group is not None,
        "group_id": str(result.incident_group.group_id) if result.incident_group else None,
        "case_id": str(result.case.case_id) if result.case else None,
        "case_number": result.case.case_number if result.case else None,
        "grouped_report_count": len(result.grouped_reports),
        "distinct_device_count": result.distinct_device_count,
    }
