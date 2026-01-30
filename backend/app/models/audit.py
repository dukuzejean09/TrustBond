from app import db
from datetime import datetime
import enum


class ActivityLog(db.Model):
    """User Activity Audit Trail"""
    __tablename__ = 'activity_logs'
    
    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    user_type = db.Column(db.Enum('police', 'system', 'api'), default='police')
    action_type = db.Column(db.String(50), nullable=False)
    action_category = db.Column(db.Enum('auth', 'report', 'hotspot', 'user_management', 'settings', 
                                        'ml', 'data_export', 'system'), default='system')
    action_description = db.Column(db.String(500))
    
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'))
    hotspot_id = db.Column(db.Integer, db.ForeignKey('hotspots.hotspot_id'))
    affected_user_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    affected_table = db.Column(db.String(100))
    affected_record_id = db.Column(db.String(100))
    
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    session_id = db.Column(db.String(36))
    
    was_successful = db.Column(db.Boolean, default=True)
    failure_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_activity_log_user_id', 'user_id'),
        db.Index('idx_activity_log_created_at', 'created_at'),
        db.Index('idx_activity_log_action_category', 'action_category'),
    )


class DataChangeAudit(db.Model):
    """Data Change Tracking - INSERT, UPDATE, DELETE"""
    __tablename__ = 'data_change_audit'
    
    audit_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.String(100), nullable=False)
    operation = db.Column(db.Enum('INSERT', 'UPDATE', 'DELETE'), nullable=False)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    changed_columns = db.Column(db.JSON)
    changed_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    changed_by_type = db.Column(db.Enum('police', 'system', 'api', 'trigger'), default='system')
    ip_address = db.Column(db.String(45))
    application_context = db.Column(db.String(100))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_audit_table_name', 'table_name'),
        db.Index('idx_audit_changed_at', 'changed_at'),
    )
