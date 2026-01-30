from app import db
from datetime import datetime


class AppFeedback(db.Model):
    """Anonymous App Feedback"""
    __tablename__ = 'app_feedback'
    
    feedback_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(36), db.ForeignKey('devices.device_id'))
    feedback_type = db.Column(db.Enum('bug_report', 'feature_request', 'usability_issue', 'performance_issue', 
                                      'content_issue', 'compliment', 'other'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5
    
    app_version = db.Column(db.String(20))
    platform = db.Column(db.Enum('android', 'ios'))
    os_version = db.Column(db.String(30))
    screen_name = db.Column(db.String(100))
    
    related_report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'))
    attachment_count = db.Column(db.Integer, default=0)
    
    is_reviewed = db.Column(db.Boolean, default=False)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    review_notes = db.Column(db.Text)
    review_status = db.Column(db.Enum('new', 'acknowledged', 'investigating', 'resolved', 'wont_fix'), default='new')
    
    requires_followup = db.Column(db.Boolean, default=False)
    followup_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attachments = db.relationship('FeedbackAttachment', backref='feedback', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_feedback_device_id', 'device_id'),
        db.Index('idx_feedback_created_at', 'created_at'),
    )


class FeedbackAttachment(db.Model):
    """Feedback Screenshots and Files"""
    __tablename__ = 'feedback_attachments'
    
    attachment_id = db.Column(db.Integer, primary_key=True)
    feedback_id = db.Column(db.Integer, db.ForeignKey('app_feedback.feedback_id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_attachment_feedback_id', 'feedback_id'),
    )
