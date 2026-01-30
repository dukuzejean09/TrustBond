from app import db
from datetime import datetime
import uuid


class ReportEvidence(db.Model):
    """Evidence Files - Photos, videos, and audio"""
    __tablename__ = 'report_evidence'
    
    evidence_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'), nullable=False)
    evidence_type = db.Column(db.Enum('photo', 'video', 'audio'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    duration_seconds = db.Column(db.Integer)
    width_pixels = db.Column(db.Integer)
    height_pixels = db.Column(db.Integer)
    file_hash_sha256 = db.Column(db.String(64), unique=True)
    file_hash_perceptual = db.Column(db.String(64))
    captured_at = db.Column(db.DateTime)
    capture_latitude = db.Column(db.Numeric(10, 8))
    capture_longitude = db.Column(db.Numeric(11, 8))
    camera_metadata = db.Column(db.JSON)
    blur_score = db.Column(db.Numeric(5, 2))
    brightness_score = db.Column(db.Numeric(5, 2))
    is_low_quality = db.Column(db.Boolean, default=False)
    quality_issues = db.Column(db.JSON)
    content_moderation_status = db.Column(db.Enum('pending', 'approved', 'flagged', 'rejected'), default='pending')
    has_inappropriate_content = db.Column(db.Boolean, default=False)
    moderation_flags = db.Column(db.JSON)
    moderated_at = db.Column(db.DateTime)
    moderated_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    is_processed = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)
    deletion_reason = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_evidence_report_id', 'report_id'),
        db.Index('idx_evidence_evidence_type', 'evidence_type'),
    )
