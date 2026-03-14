from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.report import Report
from app.schemas.report import PublicMapIncidentResponse

router = APIRouter(prefix="/public/map", tags=["public"])

MAP_ELIGIBLE_STATUSES = ("classified", "passed", "confirmed", "verified")


def _normalize_status(status: Optional[str]) -> str:
    value = (status or "").strip().lower()
    if value in ("classified", "passed", "confirmed", "verified"):
        return "classified"
    return value or "unknown"


@router.get("/incidents", response_model=List[PublicMapIncidentResponse])
def list_public_map_incidents(
    db: Session = Depends(get_db),
    incident_type_id: Optional[int] = Query(None, description="Filter by incident type id"),
    from_date: Optional[datetime] = Query(None, description="Return incidents on or after this date"),
    to_date: Optional[datetime] = Query(None, description="Return incidents on or before this date"),
    limit: int = Query(1000, ge=1, le=5000),
):
    """
    Public (no-auth) map incidents endpoint.

    Returns only map-eligible incidents (classified and legacy aliases),
    with normalized rule_status="classified" for consistent frontend filtering.
    """
    query = (
        db.query(Report)
        .options(joinedload(Report.incident_type), joinedload(Report.village_location))
        .filter(
            Report.rule_status.in_(MAP_ELIGIBLE_STATUSES),
            Report.latitude.isnot(None),
            Report.longitude.isnot(None),
        )
    )

    if incident_type_id is not None:
        query = query.filter(Report.incident_type_id == incident_type_id)
    if from_date is not None:
        query = query.filter(Report.reported_at >= from_date)
    if to_date is not None:
        query = query.filter(Report.reported_at <= to_date)

    incidents = query.order_by(Report.reported_at.desc()).limit(limit).all()

    return [
        PublicMapIncidentResponse(
            report_id=r.report_id,
            incident_type_id=r.incident_type_id,
            incident_type_name=r.incident_type.type_name if r.incident_type else None,
            description=r.description,
            latitude=r.latitude,
            longitude=r.longitude,
            reported_at=r.reported_at,
            rule_status=_normalize_status(r.rule_status),
            village_name=r.village_location.location_name if r.village_location else None,
        )
        for r in incidents
    ]
