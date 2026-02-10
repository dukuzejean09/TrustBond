"""Audit service — log all state-changing actions."""

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.audit_log import AuditLog


class AuditService:
    """Business logic for audit_logs table."""

    @staticmethod
    def log(
        db: Session,
        actor_type: str,
        actor_id: int | None,
        action_type: str,
        entity_type: str,
        entity_id: str,
        details: dict | None = None,
        ip_address: str | None = None,
        success: bool = True,
    ):
        """Write an audit log entry."""
        entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action_details=details,
            ip_address=ip_address,
            success=success,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()
        return entry
