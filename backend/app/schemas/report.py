from pydantic import BaseModel
from typing import Optional, List, Any
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
    village_location_id: Optional[int] = None


class ReportUpdate(BaseModel):
    rule_status: Optional[str] = None     # passed / flagged / rejected
    is_flagged: Optional[bool] = None


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


# ── Nested response schemas (imported inline to avoid circular deps) ──

class _EvidenceFileBrief(BaseModel):
    evidence_id: UUID
    file_url: str
    file_type: str
    media_latitude: Optional[Decimal] = None
    media_longitude: Optional[Decimal] = None
    is_live_capture: bool = False
    uploaded_at: datetime
    blur_score: Optional[Decimal] = None
    tamper_score: Optional[Decimal] = None
    ai_quality_label: Optional[str] = None
    class Config:
        from_attributes = True


class _MLPredictionBrief(BaseModel):
    prediction_id: UUID
    trust_score: Optional[Decimal] = None
    prediction_label: Optional[str] = None
    confidence: Optional[Decimal] = None
    explanation: Optional[Any] = None
    model_type: Optional[str] = None
    is_final: bool = False
    evaluated_at: datetime
    class Config:
        from_attributes = True


class _PoliceReviewBrief(BaseModel):
    review_id: UUID
    police_user_id: int
    decision: str
    review_note: Optional[str] = None
    ground_truth_label: Optional[str] = None
    confidence_level: Optional[Decimal] = None
    reviewed_at: datetime
    class Config:
        from_attributes = True


class _AssignmentBrief(BaseModel):
    assignment_id: UUID
    police_user_id: int
    status: str
    priority: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class _IncidentTypeBrief(BaseModel):
    incident_type_id: int
    type_name: str
    severity_weight: Decimal
    class Config:
        from_attributes = True


class _DeviceBrief(BaseModel):
    device_id: UUID
    device_hash: str
    device_trust_score: Decimal
    total_reports: int
    trusted_reports: int
    flagged_reports: int
    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    evidence_files: List[_EvidenceFileBrief] = []
    ml_predictions: List[_MLPredictionBrief] = []
    police_reviews: List[_PoliceReviewBrief] = []
    assignments: List[_AssignmentBrief] = []
    incident_type: Optional[_IncidentTypeBrief] = None
    device: Optional[_DeviceBrief] = None


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int
    per_page: int
