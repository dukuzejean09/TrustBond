from app import db
from datetime import datetime
import json


class PoliceUser(db.Model):
    """Police and Admin User Accounts"""
    __tablename__ = 'police_users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(200), nullable=False)
    badge_number = db.Column(db.String(50), unique=True)
    rank = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    profile_photo_path = db.Column(db.String(500))
    
    # Role & Permissions
    role = db.Column(db.Enum('super_admin', 'admin', 'commander', 'officer', 'analyst', 'viewer'), default='officer')
    permissions = db.Column(db.JSON)
    
    # Assignment & Jurisdiction
    assigned_district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    assigned_sector_id = db.Column(db.Integer, db.ForeignKey('sectors.sector_id'))
    assigned_unit = db.Column(db.String(100))
    jurisdiction_district_ids = db.Column(db.JSON)
    can_access_all_districts = db.Column(db.Boolean, default=False)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    
    # Security
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(100))
    two_factor_backup_codes = db.Column(db.JSON)
    password_changed_at = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    last_failed_login_at = db.Column(db.DateTime)
    
    # Activity
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer, default=0)
    
    # Preferences
    preferred_language = db.Column(db.String(10), default='en')
    notification_preferences = db.Column(db.JSON)
    dashboard_settings = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    
    # Relationships
    sessions = db.relationship('PoliceSession', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='owner', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_police_user_assigned_district_id', 'assigned_district_id'),
    )


class PoliceSession(db.Model):
    """Active Login Sessions"""
    __tablename__ = 'police_sessions'
    
    session_id = db.Column(db.String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().__str__)
    user_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    refresh_token_hash = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    device_info = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    revoked_reason = db.Column(db.String(100))
    
    __table_args__ = (
        db.Index('idx_session_user_id', 'user_id'),
    )
