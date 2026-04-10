"""
Audit logging: write actions to audit_logs table.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.core.request_context import get_request_id
from app.models.audit_log import AuditLog


structured_logger = logging.getLogger("app.structured")


def log_action(
    db: Session,
    action_type: str,
    *,
    actor_type: str = "police_user",
    actor_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action_details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
) -> None:
    """Append one entry to the audit log."""
    entry = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        action_details=action_details,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
    )
    db.add(entry)


def structured_log(action: str, entity: str, outcome: str, **tags: Any) -> dict[str, Any]:
    """Emit a structured log event with the current request correlation id."""
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "entity": entity,
        "outcome": outcome,
    }
    request_id = get_request_id()
    if request_id:
        payload["request_id"] = request_id
    if tags:
        payload.update(tags)

    structured_logger.info(json.dumps(payload, default=str))
    return payload
