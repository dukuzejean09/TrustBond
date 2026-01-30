"""
Feedback Service - App feedback and user suggestions management
"""
from app import db
from app.models.feedback import AppFeedback, FeedbackAttachment
from datetime import datetime, timedelta
import uuid
import os


class FeedbackService:
    """Service for managing app feedback"""
    
    # Feedback types
    TYPES = {
        'BUG': 'bug',
        'FEATURE': 'feature',
        'IMPROVEMENT': 'improvement',
        'COMPLAINT': 'complaint',
        'PRAISE': 'praise',
        'OTHER': 'other'
    }
    
    # Status values
    STATUSES = {
        'NEW': 'new',
        'REVIEWED': 'reviewed',
        'IN_PROGRESS': 'in_progress',
        'RESOLVED': 'resolved',
        'CLOSED': 'closed',
        'WONT_FIX': 'wont_fix'
    }
    
    # Priority values
    PRIORITIES = {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'CRITICAL': 'critical'
    }
    
    # ==================== FEEDBACK RETRIEVAL ====================
    @staticmethod
    def get_all_feedback(filters=None, page=1, per_page=20):
        """Get all feedback with optional filters"""
        query = AppFeedback.query
        
        if filters:
            if filters.get('feedback_type'):
                query = query.filter_by(feedback_type=filters['feedback_type'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('priority'):
                query = query.filter_by(priority=filters['priority'])
            if filters.get('device_id'):
                query = query.filter_by(device_id=filters['device_id'])
            if filters.get('app_version'):
                query = query.filter_by(app_version=filters['app_version'])
            if filters.get('platform'):
                query = query.filter_by(platform=filters['platform'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        AppFeedback.subject.ilike(search),
                        AppFeedback.content.ilike(search)
                    )
                )
            if filters.get('from_date'):
                query = query.filter(AppFeedback.submitted_at >= filters['from_date'])
            if filters.get('to_date'):
                query = query.filter(AppFeedback.submitted_at <= filters['to_date'])
        
        return query.order_by(AppFeedback.submitted_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_feedback_by_id(feedback_id):
        """Get feedback by ID"""
        return AppFeedback.query.get(feedback_id)
    
    @staticmethod
    def get_device_feedback(device_id, limit=50):
        """Get feedback from a specific device"""
        return AppFeedback.query.filter_by(device_id=device_id)\
            .order_by(AppFeedback.submitted_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_unresolved_feedback():
        """Get all unresolved feedback"""
        return AppFeedback.query.filter(
            AppFeedback.status.in_(['new', 'reviewed', 'in_progress'])
        ).order_by(
            AppFeedback.priority.desc(),
            AppFeedback.submitted_at.asc()
        ).all()
    
    @staticmethod
    def get_high_priority_feedback():
        """Get high/critical priority unresolved feedback"""
        return AppFeedback.query.filter(
            AppFeedback.status.in_(['new', 'reviewed', 'in_progress']),
            AppFeedback.priority.in_(['high', 'critical'])
        ).order_by(AppFeedback.submitted_at.asc()).all()
    
    # ==================== FEEDBACK CREATION ====================
    @staticmethod
    def create_feedback(feedback_data):
        """Create new feedback from mobile app"""
        feedback = AppFeedback(
            feedback_id=str(uuid.uuid4()),
            device_id=feedback_data.get('device_id'),
            feedback_type=feedback_data.get('feedback_type', 'other'),
            subject=feedback_data.get('subject'),
            content=feedback_data.get('content'),
            contact_email=feedback_data.get('contact_email'),
            contact_phone=feedback_data.get('contact_phone'),
            contact_consent=feedback_data.get('contact_consent', False),
            app_version=feedback_data.get('app_version'),
            os_version=feedback_data.get('os_version'),
            device_model=feedback_data.get('device_model'),
            platform=feedback_data.get('platform'),
            screen_name=feedback_data.get('screen_name'),
            error_logs=feedback_data.get('error_logs'),
            steps_to_reproduce=feedback_data.get('steps_to_reproduce'),
            rating=feedback_data.get('rating'),
            metadata=feedback_data.get('metadata'),
            status='new'
        )
        
        db.session.add(feedback)
        db.session.commit()
        return feedback
    
    @staticmethod
    def add_attachment(feedback_id, file_path, file_name, file_type, file_size):
        """Add attachment to feedback"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        attachment = FeedbackAttachment(
            attachment_id=str(uuid.uuid4()),
            feedback_id=feedback_id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size
        )
        
        db.session.add(attachment)
        db.session.commit()
        return attachment
    
    # ==================== FEEDBACK MANAGEMENT ====================
    @staticmethod
    def update_feedback(feedback_id, update_data, updated_by_user_id=None):
        """Update feedback record"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        allowed_fields = [
            'status', 'priority', 'assigned_to', 'admin_notes',
            'resolution_notes', 'feedback_type'
        ]
        
        for field in allowed_fields:
            if field in update_data:
                setattr(feedback, field, update_data[field])
        
        # Track status changes
        if update_data.get('status') == 'reviewed' and not feedback.reviewed_at:
            feedback.reviewed_at = datetime.utcnow()
            feedback.reviewed_by = updated_by_user_id
        
        if update_data.get('status') == 'resolved':
            feedback.resolved_at = datetime.utcnow()
            feedback.resolved_by = updated_by_user_id
        
        feedback.updated_at = datetime.utcnow()
        db.session.commit()
        return feedback
    
    @staticmethod
    def assign_feedback(feedback_id, user_id, assigned_by_user_id=None):
        """Assign feedback to a user"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        feedback.assigned_to = user_id
        feedback.status = 'in_progress' if feedback.status in ['new', 'reviewed'] else feedback.status
        feedback.updated_at = datetime.utcnow()
        
        db.session.commit()
        return feedback
    
    @staticmethod
    def resolve_feedback(feedback_id, resolution_notes, resolved_by_user_id):
        """Mark feedback as resolved"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        feedback.status = 'resolved'
        feedback.resolution_notes = resolution_notes
        feedback.resolved_at = datetime.utcnow()
        feedback.resolved_by = resolved_by_user_id
        feedback.updated_at = datetime.utcnow()
        
        db.session.commit()
        return feedback
    
    @staticmethod
    def close_feedback(feedback_id, reason=None, closed_by_user_id=None):
        """Close feedback without resolution"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        feedback.status = 'closed'
        feedback.admin_notes = (feedback.admin_notes or '') + f"\nClosed: {reason}" if reason else feedback.admin_notes
        feedback.updated_at = datetime.utcnow()
        
        db.session.commit()
        return feedback
    
    @staticmethod
    def mark_wont_fix(feedback_id, reason, marked_by_user_id):
        """Mark feedback as won't fix"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        feedback.status = 'wont_fix'
        feedback.resolution_notes = reason
        feedback.resolved_at = datetime.utcnow()
        feedback.resolved_by = marked_by_user_id
        feedback.updated_at = datetime.utcnow()
        
        db.session.commit()
        return feedback
    
    @staticmethod
    def set_priority(feedback_id, priority, set_by_user_id=None):
        """Set feedback priority"""
        feedback = AppFeedback.query.get(feedback_id)
        if not feedback:
            return None
        
        feedback.priority = priority
        feedback.updated_at = datetime.utcnow()
        
        db.session.commit()
        return feedback
    
    # ==================== STATISTICS ====================
    @staticmethod
    def get_feedback_stats(days=30):
        """Get feedback statistics"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = AppFeedback.query.filter(AppFeedback.submitted_at >= from_date)
        
        total = query.count()
        
        # By status
        by_status = db.session.query(
            AppFeedback.status,
            db.func.count(AppFeedback.feedback_id)
        ).filter(AppFeedback.submitted_at >= from_date)\
         .group_by(AppFeedback.status).all()
        
        # By type
        by_type = db.session.query(
            AppFeedback.feedback_type,
            db.func.count(AppFeedback.feedback_id)
        ).filter(AppFeedback.submitted_at >= from_date)\
         .group_by(AppFeedback.feedback_type).all()
        
        # By priority
        by_priority = db.session.query(
            AppFeedback.priority,
            db.func.count(AppFeedback.feedback_id)
        ).filter(AppFeedback.submitted_at >= from_date)\
         .group_by(AppFeedback.priority).all()
        
        # Average rating
        avg_rating = db.session.query(db.func.avg(AppFeedback.rating))\
            .filter(
                AppFeedback.submitted_at >= from_date,
                AppFeedback.rating.isnot(None)
            ).scalar()
        
        # Resolution time
        resolved = AppFeedback.query.filter(
            AppFeedback.submitted_at >= from_date,
            AppFeedback.resolved_at.isnot(None)
        ).all()
        
        if resolved:
            resolution_times = [
                (f.resolved_at - f.submitted_at).total_seconds() / 3600
                for f in resolved
            ]
            avg_resolution_hours = sum(resolution_times) / len(resolution_times)
        else:
            avg_resolution_hours = None
        
        return {
            'total': total,
            'by_status': dict(by_status),
            'by_type': dict(by_type),
            'by_priority': dict(by_priority),
            'avg_rating': round(float(avg_rating), 2) if avg_rating else None,
            'avg_resolution_hours': round(avg_resolution_hours, 2) if avg_resolution_hours else None,
            'period_days': days
        }
    
    @staticmethod
    def get_app_version_stats(days=30):
        """Get feedback breakdown by app version"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            AppFeedback.app_version,
            db.func.count(AppFeedback.feedback_id).label('count'),
            db.func.avg(AppFeedback.rating).label('avg_rating')
        ).filter(
            AppFeedback.submitted_at >= from_date,
            AppFeedback.app_version.isnot(None)
        ).group_by(AppFeedback.app_version)\
         .order_by(db.func.count(AppFeedback.feedback_id).desc()).all()
        
        return [{
            'app_version': r.app_version,
            'count': r.count,
            'avg_rating': round(float(r.avg_rating), 2) if r.avg_rating else None
        } for r in results]
    
    @staticmethod
    def get_platform_stats(days=30):
        """Get feedback breakdown by platform"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            AppFeedback.platform,
            db.func.count(AppFeedback.feedback_id).label('count')
        ).filter(
            AppFeedback.submitted_at >= from_date,
            AppFeedback.platform.isnot(None)
        ).group_by(AppFeedback.platform).all()
        
        return [{
            'platform': r.platform,
            'count': r.count
        } for r in results]
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def feedback_to_dict(feedback, include_attachments=True):
        """Convert feedback to dictionary"""
        if not feedback:
            return None
        
        result = {
            'feedback_id': feedback.feedback_id,
            'device_id': feedback.device_id,
            'feedback_type': feedback.feedback_type,
            'subject': feedback.subject,
            'content': feedback.content,
            'contact_email': feedback.contact_email,
            'contact_consent': feedback.contact_consent,
            'app_version': feedback.app_version,
            'os_version': feedback.os_version,
            'device_model': feedback.device_model,
            'platform': feedback.platform,
            'screen_name': feedback.screen_name,
            'rating': feedback.rating,
            'status': feedback.status,
            'priority': feedback.priority,
            'assigned_to': feedback.assigned_to,
            'admin_notes': feedback.admin_notes,
            'resolution_notes': feedback.resolution_notes,
            'submitted_at': feedback.submitted_at.isoformat() if feedback.submitted_at else None,
            'reviewed_at': feedback.reviewed_at.isoformat() if feedback.reviewed_at else None,
            'resolved_at': feedback.resolved_at.isoformat() if feedback.resolved_at else None,
            'updated_at': feedback.updated_at.isoformat() if feedback.updated_at else None
        }
        
        if include_attachments and feedback.attachments:
            result['attachments'] = [
                FeedbackService.attachment_to_dict(a) for a in feedback.attachments
            ]
        
        return result
    
    @staticmethod
    def attachment_to_dict(attachment):
        """Convert attachment to dictionary"""
        if not attachment:
            return None
        return {
            'attachment_id': attachment.attachment_id,
            'file_name': attachment.file_name,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'uploaded_at': attachment.uploaded_at.isoformat() if attachment.uploaded_at else None
        }
