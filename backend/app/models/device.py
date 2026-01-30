from app import db
from datetime import datetime
import enum
import uuid


class Device(db.Model):
    """Anonymous Reporter Devices - Tracks device behavior and trust history"""
    __tablename__ = 'devices'
    
    device_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_fingerprint = db.Column(db.String(255), unique=True, nullable=False)
    platform = db.Column(db.Enum('android', 'ios'), nullable=False)
    app_version = db.Column(db.String(20))
    os_version = db.Column(db.String(30))
    device_language = db.Column(db.String(10), default='en')
    
    # Trust metrics
    current_trust_score = db.Column(db.Numeric(5, 2), default=50.00)
    total_reports = db.Column(db.Integer, default=0)
    trusted_reports = db.Column(db.Integer, default=0)
    suspicious_reports = db.Column(db.Integer, default=0)
    false_reports = db.Column(db.Integer, default=0)
    
    # Blocking
    is_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.Text)
    blocked_at = db.Column(db.DateTime)
    blocked_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    
    # Notifications
    push_token_encrypted = db.Column(db.String(500))
    
    # Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active_at = db.Column(db.DateTime)
    last_report_at = db.Column(db.DateTime)
    
    # Relationships
    trust_history = db.relationship('DeviceTrustHistory', backref='device', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('IncidentReport', backref='device', lazy=True, cascade='all, delete-orphan')


class DeviceTrustHistory(db.Model):
    """Device Trust Score History - Audit trail of trust score changes"""
    __tablename__ = 'device_trust_history'
    
    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(36), db.ForeignKey('devices.device_id'), nullable=False)
    trust_score = db.Column(db.Numeric(5, 2), nullable=False)
    total_reports = db.Column(db.Integer)
    trusted_reports = db.Column(db.Integer)
    suspicious_reports = db.Column(db.Integer)
    false_reports = db.Column(db.Integer)
    score_change = db.Column(db.Numeric(5, 2))
    change_reason = db.Column(db.String(100))
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_device_trust_history_device_id', 'device_id'),
        db.Index('idx_device_trust_history_calculated_at', 'calculated_at'),
    )
