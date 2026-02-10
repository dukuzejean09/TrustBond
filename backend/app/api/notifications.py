"""Notification endpoints — system alerts for police users."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_notifications():
    """List notifications for current officer. Filterable by type, is_read."""
    pass


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark notification as read."""
    pass


@router.get("/unread-count")
async def unread_count():
    """Return count of unread notifications for current user."""
    pass
