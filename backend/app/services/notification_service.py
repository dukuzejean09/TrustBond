"""
Notification Service - Notification management for police users
"""
from app import db
from app.models.notifications import Notification
from datetime import datetime, timedelta
import uuid


class NotificationService:
    """Service for notification management"""
    
    # Notification types
    TYPES = {
        'NEW_REPORT': 'new_report',
        'REPORT_UPDATED': 'report_updated',
        'REPORT_VERIFIED': 'report_verified',
        'HOTSPOT_DETECTED': 'hotspot_detected',
        'HOTSPOT_CRITICAL': 'hotspot_critical',
        'HOTSPOT_ASSIGNED': 'hotspot_assigned',
        'SYSTEM_ALERT': 'system_alert',
        'USER_MENTION': 'user_mention',
        'CASE_UPDATE': 'case_update',
        'REMINDER': 'reminder'
    }
    
    # Priority levels
    PRIORITIES = {
        'LOW': 'low',
        'NORMAL': 'normal',
        'HIGH': 'high',
        'URGENT': 'urgent'
    }
    
    # ==================== NOTIFICATION RETRIEVAL ====================
    @staticmethod
    def get_user_notifications(user_id, filters=None, page=1, per_page=20):
        """Get notifications for a user with optional filters"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if filters:
            if filters.get('is_read') is not None:
                query = query.filter_by(is_read=filters['is_read'])
            if filters.get('notification_type'):
                query = query.filter_by(notification_type=filters['notification_type'])
            if filters.get('priority'):
                query = query.filter_by(priority=filters['priority'])
            if filters.get('category'):
                query = query.filter_by(category=filters['category'])
        
        return query.order_by(Notification.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_notification_by_id(notification_id):
        """Get notification by ID"""
        return Notification.query.get(notification_id)
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        return Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).count()
    
    @staticmethod
    def get_urgent_notifications(user_id):
        """Get urgent unread notifications"""
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False,
            priority='urgent'
        ).order_by(Notification.created_at.desc()).all()
    
    # ==================== NOTIFICATION CREATION ====================
    @staticmethod
    def create_notification(
        user_id,
        title,
        message,
        notification_type='system_alert',
        priority='normal',
        category=None,
        reference_type=None,
        reference_id=None,
        action_url=None,
        action_text=None,
        metadata=None,
        expires_at=None
    ):
        """Create a new notification"""
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            category=category,
            reference_type=reference_type,
            reference_id=reference_id,
            action_url=action_url,
            action_text=action_text,
            metadata=metadata,
            expires_at=expires_at
        )
        
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def create_bulk_notifications(user_ids, title, message, **kwargs):
        """Create notifications for multiple users"""
        notifications = []
        for user_id in user_ids:
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                message=message,
                notification_type=kwargs.get('notification_type', 'system_alert'),
                priority=kwargs.get('priority', 'normal'),
                category=kwargs.get('category'),
                reference_type=kwargs.get('reference_type'),
                reference_id=kwargs.get('reference_id'),
                action_url=kwargs.get('action_url'),
                action_text=kwargs.get('action_text'),
                metadata=kwargs.get('metadata'),
                expires_at=kwargs.get('expires_at')
            )
            notifications.append(notification)
        
        db.session.bulk_save_objects(notifications)
        db.session.commit()
        return notifications
    
    # ==================== SPECIALIZED NOTIFICATIONS ====================
    @staticmethod
    def notify_new_report(report, officers):
        """Notify officers about a new report"""
        for officer in officers:
            NotificationService.create_notification(
                user_id=officer.user_id,
                title='New Incident Report',
                message=f'A new incident has been reported in your area',
                notification_type='new_report',
                priority='normal',
                category='reports',
                reference_type='report',
                reference_id=report.report_id,
                action_url=f'/reports/{report.report_id}',
                action_text='View Report'
            )
    
    @staticmethod
    def notify_hotspot_detected(hotspot, officers, is_critical=False):
        """Notify officers about a detected hotspot"""
        priority = 'urgent' if is_critical else 'high'
        notification_type = 'hotspot_critical' if is_critical else 'hotspot_detected'
        
        for officer in officers:
            NotificationService.create_notification(
                user_id=officer.user_id,
                title='Crime Hotspot Detected' if not is_critical else 'CRITICAL: Crime Hotspot Alert',
                message=f'A {"critical " if is_critical else ""}hotspot with {hotspot.report_count} reports has been detected',
                notification_type=notification_type,
                priority=priority,
                category='hotspots',
                reference_type='hotspot',
                reference_id=hotspot.hotspot_id,
                action_url=f'/hotspots/{hotspot.hotspot_id}',
                action_text='View Hotspot',
                metadata={'risk_level': hotspot.risk_level, 'report_count': hotspot.report_count}
            )
    
    @staticmethod
    def notify_hotspot_assigned(hotspot, officer):
        """Notify officer about hotspot assignment"""
        return NotificationService.create_notification(
            user_id=officer.user_id,
            title='Hotspot Assigned to You',
            message=f'You have been assigned to respond to a {hotspot.risk_level} risk hotspot',
            notification_type='hotspot_assigned',
            priority='high',
            category='hotspots',
            reference_type='hotspot',
            reference_id=hotspot.hotspot_id,
            action_url=f'/hotspots/{hotspot.hotspot_id}',
            action_text='View Assignment'
        )
    
    @staticmethod
    def notify_report_verified(report, submitted_by_device=None):
        """Notify about report verification (for future app notifications)"""
        # This would be used for push notifications to the mobile app
        # Currently just creates a log entry
        pass
    
    @staticmethod
    def send_system_alert(user_ids, title, message, priority='normal'):
        """Send system alert to multiple users"""
        return NotificationService.create_bulk_notifications(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='system_alert',
            priority=priority,
            category='system'
        )
    
    @staticmethod
    def send_reminder(user_id, title, message, due_at=None):
        """Send a reminder notification"""
        return NotificationService.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type='reminder',
            priority='normal',
            category='reminders',
            metadata={'due_at': due_at.isoformat() if due_at else None}
        )
    
    # ==================== NOTIFICATION ACTIONS ====================
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark notification as read"""
        notification = Notification.query.filter_by(
            notification_id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            return notification
        return None
    
    @staticmethod
    def mark_all_as_read(user_id, category=None):
        """Mark all notifications as read for a user"""
        query = Notification.query.filter_by(user_id=user_id, is_read=False)
        
        if category:
            query = query.filter_by(category=category)
        
        count = query.update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        return count
    
    @staticmethod
    def mark_as_actioned(notification_id, user_id):
        """Mark notification as actioned"""
        notification = Notification.query.filter_by(
            notification_id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_actioned = True
            notification.actioned_at = datetime.utcnow()
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
            db.session.commit()
            return notification
        return None
    
    @staticmethod
    def dismiss_notification(notification_id, user_id):
        """Dismiss (soft delete) a notification"""
        notification = Notification.query.filter_by(
            notification_id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_dismissed = True
            notification.dismissed_at = datetime.utcnow()
            db.session.commit()
            return notification
        return None
    
    @staticmethod
    def delete_notification(notification_id, user_id):
        """Delete a notification"""
        notification = Notification.query.filter_by(
            notification_id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False
    
    # ==================== CLEANUP ====================
    @staticmethod
    def cleanup_old_notifications(days=90):
        """Delete old read notifications"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deleted = Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff
        ).delete()
        
        db.session.commit()
        return deleted
    
    @staticmethod
    def cleanup_expired_notifications():
        """Delete expired notifications"""
        now = datetime.utcnow()
        
        deleted = Notification.query.filter(
            Notification.expires_at.isnot(None),
            Notification.expires_at < now
        ).delete()
        
        db.session.commit()
        return deleted
    
    # ==================== STATISTICS ====================
    @staticmethod
    def get_notification_stats(user_id):
        """Get notification statistics for a user"""
        total = Notification.query.filter_by(user_id=user_id).count()
        unread = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        urgent = Notification.query.filter_by(user_id=user_id, is_read=False, priority='urgent').count()
        
        # Get by type
        by_type = db.session.query(
            Notification.notification_type,
            db.func.count(Notification.notification_id)
        ).filter_by(user_id=user_id, is_read=False)\
         .group_by(Notification.notification_type).all()
        
        return {
            'total': total,
            'unread': unread,
            'urgent': urgent,
            'by_type': dict(by_type)
        }
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def notification_to_dict(notification):
        """Convert notification to dictionary"""
        if not notification:
            return None
        
        return {
            'notification_id': notification.notification_id,
            'user_id': notification.user_id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'priority': notification.priority,
            'category': notification.category,
            'reference_type': notification.reference_type,
            'reference_id': notification.reference_id,
            'action_url': notification.action_url,
            'action_text': notification.action_text,
            'metadata': notification.metadata,
            'is_read': notification.is_read,
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'is_actioned': notification.is_actioned,
            'actioned_at': notification.actioned_at.isoformat() if notification.actioned_at else None,
            'is_dismissed': notification.is_dismissed,
            'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
            'created_at': notification.created_at.isoformat() if notification.created_at else None
        }
