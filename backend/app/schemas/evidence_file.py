from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class EvidenceFileCreate(BaseModel):
    file_type: str = "photo"                      # photo / video
    media_latitude: Optional[Decimal] = None
    media_longitude: Optional[Decimal] = None
    captured_at: Optional[datetime] = None
    is_live_capture: bool = False


class EvidenceFileResponse(BaseModel):
    evidence_id: UUID
    report_id: UUID
    file_url: str
    file_type: str
    media_latitude: Optional[Decimal]
    media_longitude: Optional[Decimal]
    captured_at: Optional[datetime]
    is_live_capture: bool
    uploaded_at: datetime
    perceptual_hash: Optional[str]
    blur_score: Optional[Decimal]
    tamper_score: Optional[Decimal]
    ai_quality_label: Optional[str]
    ai_checked_at: Optional[datetime]

    class Config:
        from_attributes = True
