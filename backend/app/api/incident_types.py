"""Incident type endpoints — CRUD for incident categories."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import require_role
from app.models.incident_type import IncidentType
from app.schemas.incident_type import (
    IncidentTypeCreate,
    IncidentTypeUpdate,
    IncidentTypeResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=List[IncidentTypeResponse])
async def list_incident_types(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List incident categories. Defaults to active only."""
    query = db.query(IncidentType)
    if active_only:
        query = query.filter(IncidentType.is_active == True)  # noqa: E712
    return query.order_by(IncidentType.type_name).all()


@router.post("/", response_model=IncidentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_incident_type(
    data: IncidentTypeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Admin creates new incident type (type_name, severity_weight)."""
    existing = db.query(IncidentType).filter(
        IncidentType.type_name == data.type_name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident type already exists",
        )

    incident_type = IncidentType(
        type_name=data.type_name,
        description=data.description,
        severity_weight=data.severity_weight,
        is_active=data.is_active,
    )
    db.add(incident_type)
    db.commit()
    db.refresh(incident_type)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="create",
        entity_type="incident_type",
        entity_id=str(incident_type.incident_type_id),
        ip_address=request.client.host if request.client else None,
    )
    return incident_type


@router.patch("/{incident_type_id}", response_model=IncidentTypeResponse)
async def update_incident_type(
    incident_type_id: int,
    data: IncidentTypeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """Update incident type details or toggle is_active."""
    incident_type = db.query(IncidentType).filter(
        IncidentType.incident_type_id == incident_type_id
    ).first()
    if not incident_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident type not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(incident_type, key, value)

    db.commit()
    db.refresh(incident_type)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="update",
        entity_type="incident_type",
        entity_id=str(incident_type.incident_type_id),
        details=update_data,
        ip_address=request.client.host if request.client else None,
    )
    return incident_type
