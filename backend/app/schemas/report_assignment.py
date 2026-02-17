from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ReportAssignmentCreate(BaseModel):
    report_id: UUID
    police_user_id: int
    priority: str = "medium"  # low / medium / high / urgent


class ReportAssignmentResponse(BaseModel):
    assignment_id: UUID
    report_id: UUID
    police_user_id: int
    status: str
    priority: str
    assigned_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
