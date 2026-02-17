from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class PoliceReviewCreate(BaseModel):
    report_id: UUID
    decision: str  # confirmed / rejected / investigation
    review_note: Optional[str] = None
    ground_truth_label: Optional[str] = None  # real / fake
    confidence_level: Optional[Decimal] = None
    used_for_training: bool = False


class PoliceReviewResponse(BaseModel):
    review_id: UUID
    report_id: UUID
    police_user_id: int
    decision: str
    review_note: Optional[str]
    reviewed_at: datetime
    ground_truth_label: Optional[str]
    confidence_level: Optional[Decimal]
    used_for_training: bool

    class Config:
        from_attributes = True
