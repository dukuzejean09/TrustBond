from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class MLPredictionResponse(BaseModel):
    prediction_id: UUID
    report_id: UUID
    trust_score: Optional[Decimal]
    prediction_label: Optional[str]
    model_version: Optional[str]
    evaluated_at: datetime
    confidence: Optional[Decimal]
    explanation: Optional[Any]  # JSONB
    processing_time: Optional[int]
    model_type: Optional[str]
    is_final: bool

    class Config:
        from_attributes = True
