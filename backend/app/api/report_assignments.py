"""Report assignment endpoints — case handling workflow."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.police_user import PoliceUser
from app.models.report import Report
from app.models.report_assignment import ReportAssignment
from app.schemas.report_assignment import (
    ReportAssignmentCreate,
    ReportAssignmentResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/", response_model=ReportAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: ReportAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(require_role("admin", "supervisor")),
):
    """Assign report to officer with priority (low/medium/high/urgent)."""
    # Verify report exists
    report = db.query(Report).filter(Report.report_id == data.report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Verify officer exists
    officer = db.query(PoliceUser).filter(PoliceUser.police_user_id == data.police_user_id).first()
    if not officer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")

    assignment = ReportAssignment(
        report_id=data.report_id,
        police_user_id=data.police_user_id,
        priority=data.priority,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="assign",
        entity_type="report_assignment",
        entity_id=str(assignment.assignment_id),
        details={"report_id": str(data.report_id), "officer_id": data.police_user_id},
        ip_address=request.client.host if request.client else None,
    )
    return assignment


@router.get("/", response_model=List[ReportAssignmentResponse])
async def list_assignments(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    police_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """List assignments filterable by status, priority, officer."""
    query = db.query(ReportAssignment)
    if status_filter:
        query = query.filter(ReportAssignment.status == status_filter)
    if priority:
        query = query.filter(ReportAssignment.priority == priority)
    if police_user_id is not None:
        query = query.filter(ReportAssignment.police_user_id == police_user_id)
    return query.order_by(ReportAssignment.assigned_at.desc()).all()


@router.patch("/{assignment_id}", response_model=ReportAssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    status_value: Optional[str] = None,
    priority: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Update assignment status: assigned → investigating → resolved → closed."""
    assignment = db.query(ReportAssignment).filter(
        ReportAssignment.assignment_id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    changes = {}
    if status_value:
        assignment.status = status_value
        changes["status"] = status_value
        if status_value in ("resolved", "closed"):
            from datetime import datetime, timezone
            assignment.completed_at = datetime.now(timezone.utc)
    if priority:
        assignment.priority = priority
        changes["priority"] = priority

    db.commit()
    db.refresh(assignment)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="update",
        entity_type="report_assignment",
        entity_id=str(assignment_id),
        details=changes,
        ip_address=request.client.host if request and request.client else None,
    )
    return assignment
