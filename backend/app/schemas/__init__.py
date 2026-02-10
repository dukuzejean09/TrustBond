"""Pydantic schemas for request/response validation."""

from app.schemas.device import DeviceCreate, DeviceResponse
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeResponse
from app.schemas.report import ReportCreate, ReportResponse, ReportListResponse
from app.schemas.evidence_file import EvidenceFileResponse
from app.schemas.ml_prediction import MLPredictionResponse
from app.schemas.police_user import PoliceUserCreate, PoliceUserResponse, LoginRequest, TokenResponse
from app.schemas.police_review import PoliceReviewCreate, PoliceReviewResponse
from app.schemas.report_assignment import ReportAssignmentCreate, ReportAssignmentResponse
from app.schemas.hotspot import HotspotResponse
from app.schemas.notification import NotificationResponse
from app.schemas.audit_log import AuditLogResponse
