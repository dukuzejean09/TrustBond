"""Authentication endpoints — JWT login for police_users."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.police_user import PoliceUser
from app.schemas.police_user import LoginRequest, TokenResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate police officer and return JWT token."""
    user = db.query(PoliceUser).filter(PoliceUser.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        AuditService.log(
            db,
            actor_type="police_user",
            actor_id=None,
            action_type="login_failed",
            entity_type="police_user",
            entity_id=data.email,
            ip_address=request.client.host if request.client else None,
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last_login_at
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        data={"sub": str(user.police_user_id), "role": user.role}
    )

    AuditService.log(
        db,
        actor_type="police_user",
        actor_id=user.police_user_id,
        action_type="login",
        entity_type="police_user",
        entity_id=str(user.police_user_id),
        ip_address=request.client.host if request.client else None,
    )

    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: PoliceUser = Depends(get_current_user),
):
    """Refresh an expiring JWT token."""
    token = create_access_token(
        data={"sub": str(current_user.police_user_id), "role": current_user.role}
    )
    return TokenResponse(access_token=token)
