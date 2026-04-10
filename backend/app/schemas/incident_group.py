from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from decimal import Decimal


class IncidentGroupResponse(BaseModel):
    group_id: UUID
    incident_type_id: int
    center_lat: Decimal
    center_long: Decimal
    start_time: datetime
    end_time: datetime
    report_count: int
    distinct_device_count: int = 0
    radius_meters: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    grouping_method: Optional[str] = None
    is_active: bool = True
    case_id: Optional[UUID] = None
    case_number: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentGroupCreate(BaseModel):
    incident_type_id: int
    center_lat: Decimal
    center_long: Decimal
    start_time: datetime
    end_time: datetime
    report_count: int
