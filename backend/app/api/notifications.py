"""Notification endpoints — system alerts for police users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.police_user import PoliceUser
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    notif_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """List notifications for current officer. Filterable by type, is_read."""
    return NotificationService.list_for_user(
        db,
        police_user_id=current_user.police_user_id,
        notif_type=notif_type,
        is_read=is_read,
        limit=limit,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Mark notification as read."""
    notification = NotificationService.mark_read(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    # Ensure the notification belongs to the current user
    if notification.police_user_id != current_user.police_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's notification",
        )
    return notification


@router.get("/unread-count")
async def unread_count(
    db: Session = Depends(get_db),
    current_user: PoliceUser = Depends(get_current_user),
):
    """Return count of unread notifications for current user."""
    count = NotificationService.unread_count(db, current_user.police_user_id)
    return {"unread_count": count}
