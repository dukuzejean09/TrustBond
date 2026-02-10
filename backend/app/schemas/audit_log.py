from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    log_id: int
    actor_type: str
    actor_id: Optional[int]
    action_type: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    action_details: Optional[Any]
    ip_address: Optional[str]
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True
