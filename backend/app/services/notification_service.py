"""Notification service — create and manage alerts."""

from sqlalchemy.orm import Session


class NotificationService:
    """Business logic for notifications table."""

    @staticmethod
    def create_notification(db: Session, police_user_id: int, title: str, message: str, notif_type: str, entity_type: str = None, entity_id: str = None):
        """Create a new notification."""
        # TODO: implement
        pass

    @staticmethod
    def mark_read(db: Session, notification_id: str):
        """Mark notification as read."""
        # TODO: implement
        pass
