"""
Activity Log Model for Audit Trail.

Tracks all significant actions in the system for:
- Security auditing
- Compliance reporting
- User activity monitoring
"""

from app import db
from datetime import datetime
import enum
import json


class ActivityType(enum.Enum):
    """Types of logged activities."""
    # Authentication
    LOGIN = 'login'
    LOGOUT = 'logout'
    LOGIN_FAILED = 'login_failed'
    PASSWORD_CHANGED = 'password_changed'
    PASSWORD_RESET = 'password_reset'
    
    # User Management
    USER_CREATED = 'user_created'
    USER_UPDATED = 'user_updated'
    USER_DELETED = 'user_deleted'
    USER_SUSPENDED = 'user_suspended'
    USER_ACTIVATED = 'user_activated'
    
    # Report Operations
    REPORT_CREATED = 'report_created'
    REPORT_UPDATED = 'report_updated'
    REPORT_VIEWED = 'report_viewed'
    REPORT_ASSIGNED = 'report_assigned'
    REPORT_STATUS_CHANGED = 'report_status_changed'
    REPORT_RESOLVED = 'report_resolved'
    REPORT_DELETED = 'report_deleted'
    
    # Alert Operations
    ALERT_CREATED = 'alert_created'
    ALERT_UPDATED = 'alert_updated'
    ALERT_CANCELLED = 'alert_cancelled'
    ALERT_DELETED = 'alert_deleted'
    
    # Verification
    VERIFICATION_RUN = 'verification_run'
    POLICE_VALIDATION = 'police_validation'
    
    # System Operations
    EXPORT_DATA = 'export_data'
    IMPORT_DATA = 'import_data'
    SETTINGS_CHANGED = 'settings_changed'
    
    # ML Operations
    MODEL_TRAINED = 'model_trained'
    HOTSPOT_DETECTED = 'hotspot_detected'


class ActivityLog(db.Model):
    """
    Stores activity log entries for auditing.
    """
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Actor information
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    user_email = db.Column(db.String(120))  # Denormalized for fast queries
    user_role = db.Column(db.String(20))
    
    # Activity details
    activity_type = db.Column(db.Enum(ActivityType), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    
    # Target entity
    entity_type = db.Column(db.String(50))  # 'report', 'user', 'alert', etc.
    entity_id = db.Column(db.Integer)
    
    # Additional data
    old_value = db.Column(db.JSON)  # Previous state for updates
    new_value = db.Column(db.JSON)  # New state for updates
    extra_data = db.Column(db.JSON, default=dict)  # Additional context (renamed from metadata)
    
    # Request information
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(500))
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic'))
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'userId': self.user_id,
            'userEmail': self.user_email,
            'userRole': self.user_role,
            'activityType': self.activity_type.value,
            'description': self.description,
            'entityType': self.entity_type,
            'entityId': self.entity_id,
            'oldValue': self.old_value,
            'newValue': self.new_value,
            'metadata': self.extra_data,
            'ipAddress': self.ip_address,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ActivityLog {self.id}: {self.activity_type.value}>'


class ActivityLogger:
    """Service class for logging activities."""
    
    @staticmethod
    def log(activity_type, description, user=None, entity_type=None, entity_id=None,
            old_value=None, new_value=None, metadata=None, request=None):
        """
        Log an activity.
        
        Args:
            activity_type: ActivityType enum value
            description: Human-readable description
            user: User object performing the action
            entity_type: Type of entity affected (e.g., 'report', 'user')
            entity_id: ID of affected entity
            old_value: Previous state (for updates)
            new_value: New state (for updates)
            metadata: Additional context dictionary
            request: Flask request object for IP and user agent
        """
        log_entry = ActivityLog(
            activity_type=activity_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            extra_data=metadata or {}
        )
        
        if user:
            log_entry.user_id = user.id
            log_entry.user_email = user.email
            log_entry.user_role = user.role.value if user.role else None
        
        if request:
            log_entry.ip_address = request.remote_addr
            log_entry.user_agent = request.user_agent.string[:500] if request.user_agent else None
        
        db.session.add(log_entry)
        return log_entry
    
    @staticmethod
    def log_login(user, success=True, request=None):
        """Log login attempt."""
        activity_type = ActivityType.LOGIN if success else ActivityType.LOGIN_FAILED
        return ActivityLogger.log(
            activity_type=activity_type,
            description=f"{'Successful' if success else 'Failed'} login attempt for {user.email}",
            user=user if success else None,
            entity_type='user',
            entity_id=user.id,
            request=request
        )
    
    @staticmethod
    def log_report_created(report, user=None, request=None):
        """Log report creation."""
        return ActivityLogger.log(
            activity_type=ActivityType.REPORT_CREATED,
            description=f"Report #{report.report_number} created - {report.category.value}",
            user=user,
            entity_type='report',
            entity_id=report.id,
            new_value={'category': report.category.value, 'district': report.district},
            request=request
        )
    
    @staticmethod
    def log_report_status_change(report, old_status, new_status, user=None, request=None):
        """Log report status change."""
        return ActivityLogger.log(
            activity_type=ActivityType.REPORT_STATUS_CHANGED,
            description=f"Report #{report.report_number} status changed: {old_status} -> {new_status}",
            user=user,
            entity_type='report',
            entity_id=report.id,
            old_value={'status': old_status},
            new_value={'status': new_status},
            request=request
        )
    
    @staticmethod
    def log_report_assigned(report, officer, user=None, request=None):
        """Log report assignment."""
        return ActivityLogger.log(
            activity_type=ActivityType.REPORT_ASSIGNED,
            description=f"Report #{report.report_number} assigned to {officer.first_name} {officer.last_name}",
            user=user,
            entity_type='report',
            entity_id=report.id,
            new_value={'assignedTo': officer.id, 'officerName': f"{officer.first_name} {officer.last_name}"},
            request=request
        )
    
    @staticmethod
    def log_alert_created(alert, user=None, request=None):
        """Log alert creation."""
        return ActivityLogger.log(
            activity_type=ActivityType.ALERT_CREATED,
            description=f"Alert created: {alert.title}",
            user=user,
            entity_type='alert',
            entity_id=alert.id,
            new_value={'alertType': alert.alert_type.value, 'isNationwide': alert.is_nationwide},
            request=request
        )
    
    @staticmethod
    def log_verification(report, trust_score, user=None, request=None):
        """Log verification run."""
        return ActivityLogger.log(
            activity_type=ActivityType.VERIFICATION_RUN,
            description=f"Verification run for report #{report.report_number}: {trust_score.classification.value}",
            user=user,
            entity_type='report',
            entity_id=report.id,
            new_value={
                'classification': trust_score.classification.value,
                'score': trust_score.final_score
            },
            request=request
        )
    
    @staticmethod
    def log_police_validation(report, is_credible, user=None, request=None):
        """Log police validation."""
        return ActivityLogger.log(
            activity_type=ActivityType.POLICE_VALIDATION,
            description=f"Police validation for report #{report.report_number}: {'credible' if is_credible else 'not credible'}",
            user=user,
            entity_type='report',
            entity_id=report.id,
            new_value={'isCredible': is_credible},
            request=request
        )
    
    @staticmethod
    def log_user_created(new_user, admin_user=None, request=None):
        """Log user creation."""
        return ActivityLogger.log(
            activity_type=ActivityType.USER_CREATED,
            description=f"User created: {new_user.email} ({new_user.role.value})",
            user=admin_user,
            entity_type='user',
            entity_id=new_user.id,
            new_value={'email': new_user.email, 'role': new_user.role.value},
            request=request
        )
    
    @staticmethod
    def log_export(export_type, user=None, request=None, metadata=None):
        """Log data export."""
        return ActivityLogger.log(
            activity_type=ActivityType.EXPORT_DATA,
            description=f"Data export: {export_type}",
            user=user,
            metadata=metadata,
            request=request
        )
