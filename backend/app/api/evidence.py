"""Evidence endpoints — upload and retrieve report evidence files."""

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Form, Request,
)
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.models.report import Report
from app.schemas.evidence_file import EvidenceFileResponse
from app.services.evidence_service import EvidenceService
from app.services.audit_service import AuditService

router = APIRouter()


@router.post(
    "/{report_id}/evidence",
    response_model=EvidenceFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    report_id: UUID,
    file: UploadFile = File(...),
    file_type: str = Form("photo"),
    media_latitude: Optional[Decimal] = Form(None),
    media_longitude: Optional[Decimal] = Form(None),
    captured_at: Optional[datetime] = Form(None),
    is_live_capture: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Upload evidence to Cloudinary, store metadata in evidence_files."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    metadata = {
        "file_type": file_type,
        "media_latitude": media_latitude,
        "media_longitude": media_longitude,
        "captured_at": captured_at,
        "is_live_capture": is_live_capture,
    }

    evidence = EvidenceService.upload_evidence(db, report_id, file.file, metadata)

    AuditService.log(
        db,
        actor_type="system",
        actor_id=None,
        action_type="upload",
        entity_type="evidence_file",
        entity_id=str(evidence.evidence_id),
    )
    return evidence


@router.get("/{report_id}/evidence", response_model=List[EvidenceFileResponse])
async def get_report_evidence(
    report_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve all evidence files for a report."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return EvidenceService.get_evidence_for_report(db, report_id)
