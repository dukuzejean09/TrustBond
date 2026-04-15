from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.incident_group import IncidentGroup
from app.models.police_user import PoliceUser
from app.core.incident_grouping import (
    summarize_group,
    sync_incident_groups,
)

router = APIRouter(prefix="/incident-groups", tags=["incident-groups"])


class IncidentGroupReportPreviewResponse(BaseModel):
    report_id: UUID
    report_number: Optional[str] = None
    device_id: Optional[UUID] = None
    incident_type_id: int
    incident_type_name: Optional[str] = None
    reported_at: datetime
    latitude: Decimal
    longitude: Decimal
    verification_status: Optional[str] = None
    rule_status: Optional[str] = None
    village_name: Optional[str] = None
    trust_score: Optional[Decimal] = None


class IncidentGroupDetailResponse(BaseModel):
    group_id: UUID
    incident_type_id: int
    incident_type_name: Optional[str] = None
    center_lat: Decimal
    center_long: Decimal
    start_time: datetime
    end_time: datetime
    report_count: int
    created_at: Optional[datetime] = None
    location_name: Optional[str] = None
    device_count: int = 0
    average_trust_score: Optional[Decimal] = None
    time_span_hours: Optional[Decimal] = None
    report_ids: List[UUID] = Field(default_factory=list)
    sample_reports: List[IncidentGroupReportPreviewResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class IncidentGroupSyncResponse(BaseModel):
    created: int
    updated: int
    matched: int
    cluster_count: int
    groups: List[IncidentGroupDetailResponse] = Field(default_factory=list)


@router.get("/", response_model=List[IncidentGroupDetailResponse])
def list_incident_groups(
    db: Session = Depends(get_db),
    _: Annotated[PoliceUser, Depends(get_current_user)] = None,
    incident_type_id: Optional[int] = Query(None, description="Filter by incident type"),
    preview_limit: int = Query(5, ge=1, le=20, description="How many matching reports to preview per group"),
    limit: int = Query(50, ge=1, le=200),
):
    """List incident groups with live cluster metadata and report previews. Auth required."""
    query = db.query(IncidentGroup).order_by(IncidentGroup.created_at.desc())
    if incident_type_id is not None:
        query = query.filter(IncidentGroup.incident_type_id == incident_type_id)

    groups = query.limit(limit).all()
    return [IncidentGroupDetailResponse(**summarize_group(db, group, preview_limit=preview_limit)) for group in groups]


@router.get("/{group_id}", response_model=IncidentGroupDetailResponse)
def get_incident_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    _: Annotated[PoliceUser, Depends(get_current_user)] = None,
    preview_limit: int = Query(10, ge=1, le=20),
):
    group = db.query(IncidentGroup).filter(IncidentGroup.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Incident group not found")
    return IncidentGroupDetailResponse(**summarize_group(db, group, preview_limit=preview_limit))


@router.post("/sync", response_model=IncidentGroupSyncResponse)
def sync_incident_groups_from_verified_reports(
    db: Session = Depends(get_db),
    _: Annotated[PoliceUser, Depends(get_current_user)] = None,
    incident_type_id: Optional[int] = Query(None, description="Optional incident type filter"),
    lookback_hours: int = Query(72, ge=1, le=720, description="How far back to scan verified reports"),
    radius_meters: float = Query(500.0, ge=50.0, le=5000.0, description="Clustering radius in meters"),
    time_window_hours: int = Query(24, ge=1, le=168, description="Maximum report-to-report time gap inside a cluster"),
):
    """Rebuild materialized incident groups from verified reports."""
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    result = sync_incident_groups(
        db,
        incident_type_id=incident_type_id,
        since=since,
        radius_meters=radius_meters,
        time_window_hours=time_window_hours,
    )

    return IncidentGroupSyncResponse(
        created=result["created"],
        updated=result["updated"],
        matched=result["matched"],
        cluster_count=result["cluster_count"],
        groups=[
            IncidentGroupDetailResponse(
                **summarize_group(db, group)
            )
            for group in result["groups"]
        ],
    )
