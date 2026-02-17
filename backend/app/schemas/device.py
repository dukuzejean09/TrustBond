from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class DeviceCreate(BaseModel):
    device_hash: str


class DeviceResponse(BaseModel):
    device_id: UUID
    device_hash: str
    first_seen_at: datetime
    total_reports: int
    trusted_reports: int
    flagged_reports: int
    device_trust_score: Decimal

    class Config:
        from_attributes = True
