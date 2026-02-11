"""Report endpoints — CRUD for incident reports."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.police_user import PoliceUser
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportDetailResponse,
    ReportListResponse,
)
from app.services.report_service import ReportService
from app.services.device_service import DeviceService
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
):
    """
    Submit a new incident report (anonymous, from mobile app).

    The device is registered/resolved via device_hash (SHA-256).
    """
    # Get or create the anonymous device
    device = DeviceService.get_or_create(db, data.device_hash)
    DeviceService.increment_total(db, device.device_id)

    report = ReportService.create_report(db, device.device_id, data.model_dump())

    AuditService.log(
        db,
        actor_type="system",
        actor_id=None,
        action_type="create",
        entity_type="report",
        entity_id=str(report.report_id),
    )
    return report


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    rule_status: Optional[str] = None,
    incident_type_id: Optional[int] = None,
    is_flagged: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """List/filter reports for dashboard (joins incident_types, devices)."""
    filters = {
        "rule_status": rule_status,
        "incident_type_id": incident_type_id,
        "is_flagged": is_flagged,
        "start_date": start_date,
        "end_date": end_date,
    }
    reports, total = ReportService.list_reports(db, filters, page, per_page)
    return ReportListResponse(
        reports=reports, total=total, page=page, per_page=per_page,
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Single report with evidence_files, ml_predictions, police_reviews, assignments."""
    report = ReportService.get_report_detail(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    data: ReportUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Update rule_status, is_flagged."""
    update_data = data.model_dump(exclude_unset=True)
    report = ReportService.update_report(db, report_id, update_data)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="update",
        entity_type="report",
        entity_id=str(report_id),
        details=update_data,
        ip_address=request.client.host if request.client else None,
    )
    return report
