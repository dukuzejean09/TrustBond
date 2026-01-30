from app import db
from datetime import datetime


class Notification(db.Model):
    """Police Alerts and Notifications"""
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'), nullable=False)
    notification_type = db.Column(db.Enum('new_report', 'high_trust_report', 'suspicious_report', 'hotspot_detected', 
                                          'hotspot_escalated', 'assignment', 'verification_needed', 'system_alert', 
                                          'model_update', 'weekly_summary'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'))
    hotspot_id = db.Column(db.Integer, db.ForeignKey('hotspots.hotspot_id'))
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent'), default='normal')
    delivery_channels = db.Column(db.JSON)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    is_dismissed = db.Column(db.Boolean, default=False)
    dismissed_at = db.Column(db.DateTime)
    action_taken = db.Column(db.String(100))
    action_taken_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.Index('idx_notification_recipient_user_id', 'recipient_user_id'),
        db.Index('idx_notification_created_at', 'created_at'),
    )
