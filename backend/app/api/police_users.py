"""Police user endpoints — officer management with role-based access."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import hash_password
from app.models.police_user import PoliceUser
from app.schemas.police_user import (
    PoliceUserCreate,
    PoliceUserUpdate,
    PoliceUserResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/exists")
async def police_users_exist(db: Session = Depends(get_db)):
    """Public endpoint — return whether any police users exist (used for bootstrap UI)."""
    exists = db.query(PoliceUser).first() is not None
    return {"exists": exists}


@router.post("/bootstrap", response_model=PoliceUserResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_police_user(
    data: PoliceUserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create the first admin account if the `police_users` table is empty.

    - This endpoint is intentionally public but only allowed when no users exist.
    - The first user must have role=`admin`.
    """
    # Prevent bootstrap if users already exist
    if db.query(PoliceUser).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Police users already exist; bootstrap disabled.",
        )

    # Enforce admin role for the first account
    if (data.role or "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First user must have role 'admin'",
        )

    # Basic duplicate checks (unlikely when empty, but safe)
    if db.query(PoliceUser).filter(PoliceUser.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered",
        )

    user = PoliceUser(
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        email=data.email,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password),
        badge_number=data.badge_number,
        role="admin",
        assigned_location_id=data.assigned_location_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    AuditService.log(
        db,
        actor_type="system",
        actor_id=None,
        action_type="bootstrap_create",
        entity_type="police_user",
        entity_id=str(user.police_user_id),
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.get("/", response_model=List[PoliceUserResponse])
async def list_police_users(
    role: Optional[str] = None,
    assigned_location_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """List officers, filterable by role and assigned_location_id."""
    query = db.query(PoliceUser)
    if role:
        query = query.filter(PoliceUser.role == role)
    if assigned_location_id is not None:
        query = query.filter(PoliceUser.assigned_location_id == assigned_location_id)
    if is_active is not None:
        query = query.filter(PoliceUser.is_active == is_active)
    return query.order_by(PoliceUser.last_name, PoliceUser.first_name).all()


@router.post("/", response_model=PoliceUserResponse, status_code=status.HTTP_201_CREATED)
async def create_police_user(
    data: PoliceUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(require_role("admin")),
):
    """Admin creates officer (first_name, last_name, email, etc.)."""
    # Check duplicate email
    if db.query(PoliceUser).filter(PoliceUser.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered",
        )

    # Check duplicate badge number
    if data.badge_number:
        if db.query(PoliceUser).filter(PoliceUser.badge_number == data.badge_number).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Badge number already in use",
            )

    user = PoliceUser(
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        email=data.email,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password),
        badge_number=data.badge_number,
        role=data.role,
        assigned_location_id=data.assigned_location_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="create",
        entity_type="police_user",
        entity_id=str(user.police_user_id),
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.get("/{police_user_id}", response_model=PoliceUserResponse)
async def get_police_user(
    police_user_id: int,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Get single officer detail."""
    user = db.query(PoliceUser).filter(
        PoliceUser.police_user_id == police_user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found",
        )
    return user


@router.patch("/{police_user_id}", response_model=PoliceUserResponse)
async def update_police_user(
    police_user_id: int,
    data: PoliceUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(require_role("admin", "supervisor")),
):
    """Update officer details, toggle is_active."""
    user = db.query(PoliceUser).filter(
        PoliceUser.police_user_id == police_user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Uniqueness check if email is changing
    if "email" in update_data:
        dup = db.query(PoliceUser).filter(
            PoliceUser.email == update_data["email"],
            PoliceUser.police_user_id != police_user_id,
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use",
            )

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=current_user.police_user_id,
        action_type="update",
        entity_type="police_user",
        entity_id=str(police_user_id),
        details=update_data,
        ip_address=request.client.host if request.client else None,
    )
    return user
