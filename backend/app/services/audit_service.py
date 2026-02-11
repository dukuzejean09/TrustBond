"""Audit service — log all state-changing actions."""

import json
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.audit_log import AuditLog


class _SafeEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal, UUID, datetime, etc."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def _sanitise_details(details: dict | None) -> dict | None:
    """Round-trip through JSON so column accepts the value on any backend."""
    if details is None:
        return None
    return json.loads(json.dumps(details, cls=_SafeEncoder))


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
            action_details=_sanitise_details(details),
            ip_address=ip_address,
            success=success,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()
        return entry
