from app import db
from datetime import datetime


class SystemSetting(db.Model):
    """Application Configuration"""
    __tablename__ = 'system_settings'
    
    setting_id = db.Column(db.Integer, primary_key=True)
    setting_category = db.Column(db.Enum('general', 'ml', 'verification', 'hotspot', 'notification', 
                                         'security', 'privacy', 'display'), nullable=False)
    setting_key = db.Column(db.String(100), nullable=False, unique=True, index=True)
    setting_value = db.Column(db.JSON)
    value_type = db.Column(db.Enum('string', 'number', 'boolean', 'json', 'array'), default='string')
    display_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    validation_rules = db.Column(db.JSON)
    default_value = db.Column(db.JSON)
    requires_admin = db.Column(db.Boolean, default=False)
    is_sensitive = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
