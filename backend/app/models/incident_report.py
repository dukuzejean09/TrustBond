from app import db
from datetime import datetime
import enum
import uuid
import json


class IncidentReport(db.Model):
    """Core Incident Reports - Main transaction table"""
    __tablename__ = 'incident_reports'
    
    report_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(36), db.ForeignKey('devices.device_id'), nullable=False)
    incident_type_id = db.Column(db.Integer, db.ForeignKey('incident_types.type_id'), nullable=False)
    
    # Basic Information
    title = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=False)
    
    # Location Fields
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    location_accuracy_meters = db.Column(db.Numeric(8, 2))
    altitude_meters = db.Column(db.Numeric(8, 2))
    location_source = db.Column(db.Enum('gps', 'network', 'manual'), default='gps')
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    sector_id = db.Column(db.Integer, db.ForeignKey('sectors.sector_id'))
    cell_id = db.Column(db.Integer, db.ForeignKey('cells.cell_id'))
    village_id = db.Column(db.Integer, db.ForeignKey('villages.village_id'))
    address_description = db.Column(db.String(255))
    
    # Temporal Fields
    reported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    incident_occurred_at = db.Column(db.DateTime, nullable=False)
    incident_time_approximate = db.Column(db.Boolean, default=False)
    
    # Evidence Summary
    photo_count = db.Column(db.Integer, default=0)
    video_count = db.Column(db.Integer, default=0)
    audio_count = db.Column(db.Integer, default=0)
    total_evidence_size_kb = db.Column(db.Integer, default=0)
    
    # Motion Sensor Data (Verification)
    accelerometer_data = db.Column(db.JSON)
    gyroscope_data = db.Column(db.JSON)
    magnetometer_data = db.Column(db.JSON)
    device_motion_score = db.Column(db.Numeric(5, 2))
    device_orientation = db.Column(db.String(20))
    battery_level = db.Column(db.Integer)
    network_type = db.Column(db.String(20))
    
    # Rule-Based Verification (Stage 1)
    rule_check_status = db.Column(db.Enum('pending', 'passed', 'failed', 'partial'), default='pending')
    rule_check_completed_at = db.Column(db.DateTime)
    rules_passed = db.Column(db.Integer, default=0)
    rules_failed = db.Column(db.Integer, default=0)
    rules_total = db.Column(db.Integer, default=0)
    rule_failure_reasons = db.Column(db.JSON)
    is_auto_rejected = db.Column(db.Boolean, default=False)
    
    # ML Trust Scoring (Stage 2)
    ml_model_id = db.Column(db.Integer, db.ForeignKey('ml_models.model_id'))
    ml_trust_score = db.Column(db.Numeric(5, 2))
    ml_confidence = db.Column(db.Numeric(5, 4))
    ml_feature_vector = db.Column(db.JSON)
    ml_scored_at = db.Column(db.DateTime)
    trust_classification = db.Column(db.Enum('Trusted', 'Suspicious', 'False', 'Pending'), default='Pending')
    classification_reason = db.Column(db.String(255))
    
    # Police Verification (Ground Truth)
    police_verified = db.Column(db.Boolean, default=False)
    police_verified_at = db.Column(db.DateTime)
    police_verified_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    police_verification_status = db.Column(db.Enum('pending', 'confirmed', 'false', 'duplicate', 'insufficient_info'), default='pending')
    police_verification_notes = db.Column(db.Text)
    police_priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent'))
    
    # Workflow Status
    report_status = db.Column(db.Enum('submitted', 'rule_checking', 'ml_scoring', 'pending_review', 'investigating', 'resolved', 'rejected'), default='submitted')
    processing_stage = db.Column(db.Enum('received', 'rule_validation', 'ml_scoring', 'clustering', 'ready_for_review', 'in_review', 'completed'), default='received')
    is_duplicate = db.Column(db.Boolean, default=False)
    duplicate_of_report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'))
    duplicate_confidence = db.Column(db.Numeric(5, 2))
    
    # Assignment & Resolution
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    assigned_unit = db.Column(db.String(100))
    assigned_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    resolution_type = db.Column(db.Enum('action_taken', 'no_action_needed', 'referred', 'false_report', 'duplicate'))
    resolution_notes = db.Column(db.Text)
    
    # Hotspot Linkage
    hotspot_id = db.Column(db.Integer, db.ForeignKey('hotspots.hotspot_id'))
    added_to_hotspot_at = db.Column(db.DateTime)
    
    # Metadata
    app_version = db.Column(db.String(20))
    submission_ip_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evidence_files = db.relationship('ReportEvidence', backref='report', lazy=True, cascade='all, delete-orphan')
    rule_executions = db.relationship('RuleExecutionLog', backref='report', lazy=True, cascade='all, delete-orphan')
    ml_prediction = db.relationship('MLPrediction', backref='report', uselist=False, lazy=True, cascade='all, delete-orphan')
    hotspot_links = db.relationship('HotspotReport', backref='report', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_report_device_id', 'device_id'),
        db.Index('idx_report_incident_type_id', 'incident_type_id'),
        db.Index('idx_report_district_id', 'district_id'),
        db.Index('idx_report_reported_at', 'reported_at'),
        db.Index('idx_report_status', 'report_status'),
        db.Index('idx_report_trust_classification', 'trust_classification'),
    )
