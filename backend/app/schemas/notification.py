from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class NotificationResponse(BaseModel):
    notification_id: UUID
    police_user_id: int
    title: str
    message: Optional[str]
    type: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
