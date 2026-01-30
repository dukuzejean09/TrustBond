"""
Notification Model for User Notifications.

Handles push notifications and in-app notifications for:
- Report status updates
- Alert broadcasts
- System messages
"""

from app import db
from datetime import datetime
import enum


class NotificationType(enum.Enum):
    """Types of notifications."""
    REPORT_SUBMITTED = 'report_submitted'
    REPORT_STATUS_CHANGE = 'report_status_change'
    REPORT_ASSIGNED = 'report_assigned'
    REPORT_RESOLVED = 'report_resolved'
    ALERT_NEW = 'alert_new'
    ALERT_UPDATE = 'alert_update'
    SYSTEM_MESSAGE = 'system_message'
    VERIFICATION_COMPLETE = 'verification_complete'


class NotificationPriority(enum.Enum):
    """Notification priority levels."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class Notification(db.Model):
    """
    Stores user notifications for both mobile and dashboard.
    """
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Target user (nullable for broadcast notifications)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Related entities
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'))
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'))
    
    # Additional data (JSON)
    data = db.Column(db.JSON, default=dict)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    
    # For broadcast notifications
    is_broadcast = db.Column(db.Boolean, default=False)
    target_district = db.Column(db.String(50))  # For location-based broadcasts
    target_role = db.Column(db.String(20))  # For role-based broadcasts
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    report = db.relationship('Report', backref='notifications')
    alert = db.relationship('Alert', backref='notifications')
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'userId': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type.value,
            'priority': self.priority.value,
            'reportId': self.report_id,
            'alertId': self.alert_id,
            'data': self.data,
            'isRead': self.is_read,
            'readAt': self.read_at.isoformat() if self.read_at else None,
            'isBroadcast': self.is_broadcast,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.notification_type.value}>'


class NotificationService:
    """Service class for creating and managing notifications."""
    
    @staticmethod
    def notify_report_submitted(report, user_id=None):
        """Create notification when a report is submitted."""
        notification = Notification(
            user_id=user_id,
            title='Report Submitted',
            message=f'Your report #{report.report_number} has been submitted successfully.',
            notification_type=NotificationType.REPORT_SUBMITTED,
            report_id=report.id,
            data={'reportNumber': report.report_number, 'trackingCode': report.tracking_code}
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def notify_status_change(report, old_status, new_status):
        """Create notification when report status changes."""
        if report.reporter_id:
            notification = Notification(
                user_id=report.reporter_id,
                title='Report Status Updated',
                message=f'Your report #{report.report_number} status changed from {old_status} to {new_status}.',
                notification_type=NotificationType.REPORT_STATUS_CHANGE,
                priority=NotificationPriority.HIGH,
                report_id=report.id,
                data={'oldStatus': old_status, 'newStatus': new_status}
            )
            db.session.add(notification)
            return notification
        return None
    
    @staticmethod
    def notify_report_assigned(report, officer):
        """Create notification when report is assigned to an officer."""
        # Notify officer
        officer_notification = Notification(
            user_id=officer.id,
            title='New Case Assigned',
            message=f'You have been assigned to report #{report.report_number}.',
            notification_type=NotificationType.REPORT_ASSIGNED,
            priority=NotificationPriority.HIGH,
            report_id=report.id,
            data={'category': report.category.value, 'district': report.district}
        )
        db.session.add(officer_notification)
        
        # Notify reporter if not anonymous
        if report.reporter_id:
            reporter_notification = Notification(
                user_id=report.reporter_id,
                title='Officer Assigned',
                message=f'An officer has been assigned to investigate your report #{report.report_number}.',
                notification_type=NotificationType.REPORT_ASSIGNED,
                report_id=report.id
            )
            db.session.add(reporter_notification)
        
        return officer_notification
    
    @staticmethod
    def notify_report_resolved(report, resolution_notes=None):
        """Create notification when report is resolved."""
        if report.reporter_id:
            notification = Notification(
                user_id=report.reporter_id,
                title='Report Resolved',
                message=f'Your report #{report.report_number} has been resolved.',
                notification_type=NotificationType.REPORT_RESOLVED,
                priority=NotificationPriority.HIGH,
                report_id=report.id,
                data={'resolutionNotes': resolution_notes}
            )
            db.session.add(notification)
            return notification
        return None
    
    @staticmethod
    def broadcast_alert(alert):
        """Create broadcast notification for a new alert."""
        notification = Notification(
            title=alert.title,
            message=alert.message,
            notification_type=NotificationType.ALERT_NEW,
            priority=NotificationPriority.URGENT if alert.is_nationwide else NotificationPriority.HIGH,
            alert_id=alert.id,
            is_broadcast=True,
            target_district=alert.district if not alert.is_nationwide else None,
            data={'alertType': alert.alert_type.value, 'isNationwide': alert.is_nationwide}
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def notify_verification_complete(report, trust_score):
        """Create notification when verification completes."""
        if report.reporter_id:
            notification = Notification(
                user_id=report.reporter_id,
                title='Verification Complete',
                message=f'Your report #{report.report_number} has been verified.',
                notification_type=NotificationType.VERIFICATION_COMPLETE,
                report_id=report.id,
                data={
                    'classification': trust_score.classification.value,
                    'score': trust_score.final_score
                }
            )
            db.session.add(notification)
            return notification
        return None
