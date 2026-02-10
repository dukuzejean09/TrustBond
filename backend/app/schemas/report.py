from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ReportCreate(BaseModel):
    device_hash: str
    incident_type_id: int
    description: Optional[str] = None
    latitude: Decimal
    longitude: Decimal
    gps_accuracy: Optional[Decimal] = None
    motion_level: Optional[str] = None  # low / medium / high
    movement_speed: Optional[Decimal] = None
    was_stationary: Optional[bool] = None


class ReportResponse(BaseModel):
    report_id: UUID
    device_id: UUID
    incident_type_id: int
    description: Optional[str]
    latitude: Decimal
    longitude: Decimal
    gps_accuracy: Optional[Decimal]
    motion_level: Optional[str]
    movement_speed: Optional[Decimal]
    was_stationary: Optional[bool]
    village_location_id: Optional[int]
    reported_at: datetime
    rule_status: str
    is_flagged: bool
    ai_ready: bool

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int
    per_page: int
