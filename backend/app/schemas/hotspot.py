from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class HotspotResponse(BaseModel):
    hotspot_id: int
    center_lat: Decimal
    center_long: Decimal
    radius_meters: Optional[Decimal]
    incident_count: int
    risk_level: str
    time_window_hours: Optional[int]
    detected_at: datetime

    class Config:
        from_attributes = True
