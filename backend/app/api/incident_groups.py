"""Incident group endpoints — duplicate incident grouping."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.police_user import PoliceUser
from app.models.incident_group import IncidentGroup
from app.schemas.incident_group import IncidentGroupResponse

router = APIRouter()


@router.get("/", response_model=List[IncidentGroupResponse])
async def list_incident_groups(
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """List grouped duplicate reports."""
    return (
        db.query(IncidentGroup)
        .order_by(IncidentGroup.created_at.desc())
        .all()
    )


@router.get("/{group_id}", response_model=IncidentGroupResponse)
async def get_incident_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Get group detail."""
    group = db.query(IncidentGroup).filter(
        IncidentGroup.group_id == group_id
    ).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident group not found",
        )
    return group
