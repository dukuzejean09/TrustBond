"""Pydantic schemas for incident_groups (duplicate grouping)."""

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class IncidentGroupResponse(BaseModel):
    group_id: UUID
    incident_type_id: int
    center_lat: Optional[Decimal] = None
    center_long: Optional[Decimal] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    report_count: int
    created_at: datetime

    class Config:
        from_attributes = True
