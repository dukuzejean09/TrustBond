"""Notification service — create and manage alerts."""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.models.notification import Notification


class NotificationService:
    """Business logic for notifications table."""

    @staticmethod
    def create_notification(
        db: Session,
        police_user_id: int,
        title: str,
        message: str,
        notif_type: str,
        entity_type: str = None,
        entity_id: str = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            police_user_id=police_user_id,
            title=title,
            message=message,
            type=notif_type,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def list_for_user(
        db: Session,
        police_user_id: int,
        notif_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Notification]:
        """List notifications for a specific officer."""
        query = db.query(Notification).filter(
            Notification.police_user_id == police_user_id
        )
        if notif_type:
            query = query.filter(Notification.type == notif_type)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_read(db: Session, notification_id: UUID) -> Optional[Notification]:
        """Mark notification as read."""
        notification = db.query(Notification).filter(
            Notification.notification_id == notification_id
        ).first()
        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)
        return notification

    @staticmethod
    def unread_count(db: Session, police_user_id: int) -> int:
        """Return count of unread notifications."""
        return (
            db.query(Notification)
            .filter(
                Notification.police_user_id == police_user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .count()
        )
