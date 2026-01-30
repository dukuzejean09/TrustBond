from app import db
from datetime import datetime


class APIKey(db.Model):
    """API Authentication Keys"""
    __tablename__ = 'api_keys'
    
    key_id = db.Column(db.Integer, primary_key=True)
    key_name = db.Column(db.String(100), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    key_prefix = db.Column(db.String(10), unique=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'), nullable=False)
    owner_description = db.Column(db.String(255))
    
    permissions = db.Column(db.JSON)
    rate_limit_per_minute = db.Column(db.Integer)
    allowed_ips = db.Column(db.JSON)
    allowed_districts = db.Column(db.JSON)
    
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    total_requests = db.Column(db.BigInteger, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    revoked_reason = db.Column(db.String(255))
    
    # Relationships
    request_logs = db.relationship('APIRequestLog', backref='api_key', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_api_key_owner_user_id', 'owner_user_id'),
    )


class APIRequestLog(db.Model):
    """API Request Logging"""
    __tablename__ = 'api_request_logs'
    
    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.key_id'), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.Enum('GET', 'POST', 'PUT', 'PATCH', 'DELETE'), nullable=False)
    request_params = db.Column(db.JSON)
    response_status = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    had_error = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_api_log_api_key_id', 'api_key_id'),
        db.Index('idx_api_log_requested_at', 'requested_at'),
    )
