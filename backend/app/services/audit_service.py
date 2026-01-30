"""
Audit Service - Activity logging and data change tracking
"""
from app import db
from app.models.audit import ActivityLog, DataChangeAudit
from datetime import datetime, timedelta
import uuid
import json


class AuditService:
    """Service for audit logging and tracking"""
    
    # Activity types
    ACTIVITY_TYPES = {
        'LOGIN': 'login',
        'LOGOUT': 'logout',
        'VIEW': 'view',
        'CREATE': 'create',
        'UPDATE': 'update',
        'DELETE': 'delete',
        'VERIFY': 'verify',
        'REJECT': 'reject',
        'ASSIGN': 'assign',
        'EXPORT': 'export',
        'IMPORT': 'import',
        'SEARCH': 'search',
        'DOWNLOAD': 'download'
    }
    
    # Resource types
    RESOURCE_TYPES = {
        'REPORT': 'report',
        'HOTSPOT': 'hotspot',
        'USER': 'user',
        'DEVICE': 'device',
        'NOTIFICATION': 'notification',
        'SETTING': 'setting',
        'ML_MODEL': 'ml_model',
        'EVIDENCE': 'evidence'
    }
    
    # ==================== ACTIVITY LOGGING ====================
    @staticmethod
    def log_activity(
        user_id,
        activity_type,
        description,
        resource_type=None,
        resource_id=None,
        ip_address=None,
        user_agent=None,
        request_path=None,
        request_method=None,
        metadata=None,
        status='success'
    ):
        """Log a user activity"""
        log = ActivityLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            metadata=metadata,
            status=status
        )
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_login(user_id, ip_address, user_agent, success=True):
        """Log login attempt"""
        return AuditService.log_activity(
            user_id=user_id,
            activity_type='login',
            description=f"User {'logged in successfully' if success else 'failed login attempt'}",
            ip_address=ip_address,
            user_agent=user_agent,
            status='success' if success else 'failed'
        )
    
    @staticmethod
    def log_logout(user_id, ip_address=None):
        """Log logout"""
        return AuditService.log_activity(
            user_id=user_id,
            activity_type='logout',
            description="User logged out",
            ip_address=ip_address
        )
    
    @staticmethod
    def log_report_action(user_id, report_id, action, details=None, ip_address=None):
        """Log report-related action"""
        return AuditService.log_activity(
            user_id=user_id,
            activity_type=action,
            description=f"Report {action}: {details}" if details else f"Report {action}",
            resource_type='report',
            resource_id=report_id,
            ip_address=ip_address,
            metadata={'details': details} if details else None
        )
    
    @staticmethod
    def log_verification(user_id, report_id, result, notes=None, ip_address=None):
        """Log report verification"""
        return AuditService.log_activity(
            user_id=user_id,
            activity_type='verify',
            description=f"Report verified as {result}",
            resource_type='report',
            resource_id=report_id,
            ip_address=ip_address,
            metadata={'result': result, 'notes': notes}
        )
    
    @staticmethod
    def log_hotspot_action(user_id, hotspot_id, action, details=None, ip_address=None):
        """Log hotspot-related action"""
        return AuditService.log_activity(
            user_id=user_id,
            activity_type=action,
            description=f"Hotspot {action}: {details}" if details else f"Hotspot {action}",
            resource_type='hotspot',
            resource_id=hotspot_id,
            ip_address=ip_address,
            metadata={'details': details} if details else None
        )
    
    @staticmethod
    def log_user_management(admin_id, target_user_id, action, details=None, ip_address=None):
        """Log user management action"""
        return AuditService.log_activity(
            user_id=admin_id,
            activity_type=action,
            description=f"User {action} for user {target_user_id}: {details}" if details else f"User {action}",
            resource_type='user',
            resource_id=target_user_id,
            ip_address=ip_address,
            metadata={'target_user': target_user_id, 'details': details}
        )
    
    @staticmethod
    def log_export(user_id, export_type, record_count, ip_address=None):
        """Log data export"""
        return AuditService.log_activity(
            user_id=user_id,
            activity_type='export',
            description=f"Exported {record_count} {export_type} records",
            resource_type=export_type,
            ip_address=ip_address,
            metadata={'record_count': record_count}
        )
    
    # ==================== DATA CHANGE TRACKING ====================
    @staticmethod
    def track_change(
        table_name,
        record_id,
        operation,
        old_values=None,
        new_values=None,
        changed_by_user_id=None,
        change_reason=None
    ):
        """Track a data change"""
        # Calculate changed fields
        changed_fields = []
        if old_values and new_values:
            for key in set(list(old_values.keys()) + list(new_values.keys())):
                old_val = old_values.get(key)
                new_val = new_values.get(key)
                if old_val != new_val:
                    changed_fields.append(key)
        elif new_values:
            changed_fields = list(new_values.keys())
        elif old_values:
            changed_fields = list(old_values.keys())
        
        audit = DataChangeAudit(
            audit_id=str(uuid.uuid4()),
            table_name=table_name,
            record_id=str(record_id),
            operation=operation,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            changed_by=changed_by_user_id,
            change_reason=change_reason
        )
        
        db.session.add(audit)
        db.session.commit()
        return audit
    
    @staticmethod
    def track_create(table_name, record_id, new_values, user_id=None, reason=None):
        """Track record creation"""
        return AuditService.track_change(
            table_name=table_name,
            record_id=record_id,
            operation='INSERT',
            new_values=new_values,
            changed_by_user_id=user_id,
            change_reason=reason
        )
    
    @staticmethod
    def track_update(table_name, record_id, old_values, new_values, user_id=None, reason=None):
        """Track record update"""
        return AuditService.track_change(
            table_name=table_name,
            record_id=record_id,
            operation='UPDATE',
            old_values=old_values,
            new_values=new_values,
            changed_by_user_id=user_id,
            change_reason=reason
        )
    
    @staticmethod
    def track_delete(table_name, record_id, old_values, user_id=None, reason=None):
        """Track record deletion"""
        return AuditService.track_change(
            table_name=table_name,
            record_id=record_id,
            operation='DELETE',
            old_values=old_values,
            changed_by_user_id=user_id,
            change_reason=reason
        )
    
    # ==================== RETRIEVAL ====================
    @staticmethod
    def get_activity_logs(filters=None, page=1, per_page=50):
        """Get activity logs with optional filters"""
        query = ActivityLog.query
        
        if filters:
            if filters.get('user_id'):
                query = query.filter_by(user_id=filters['user_id'])
            if filters.get('activity_type'):
                query = query.filter_by(activity_type=filters['activity_type'])
            if filters.get('resource_type'):
                query = query.filter_by(resource_type=filters['resource_type'])
            if filters.get('resource_id'):
                query = query.filter_by(resource_id=filters['resource_id'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('from_date'):
                query = query.filter(ActivityLog.created_at >= filters['from_date'])
            if filters.get('to_date'):
                query = query.filter(ActivityLog.created_at <= filters['to_date'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(ActivityLog.description.ilike(search))
        
        return query.order_by(ActivityLog.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_user_activity(user_id, days=30, limit=100):
        """Get activity for a specific user"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        return ActivityLog.query.filter(
            ActivityLog.user_id == user_id,
            ActivityLog.created_at >= from_date
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_resource_history(resource_type, resource_id):
        """Get all activity for a specific resource"""
        return ActivityLog.query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id
        ).order_by(ActivityLog.created_at.desc()).all()
    
    @staticmethod
    def get_data_changes(filters=None, page=1, per_page=50):
        """Get data change audit records"""
        query = DataChangeAudit.query
        
        if filters:
            if filters.get('table_name'):
                query = query.filter_by(table_name=filters['table_name'])
            if filters.get('record_id'):
                query = query.filter_by(record_id=filters['record_id'])
            if filters.get('operation'):
                query = query.filter_by(operation=filters['operation'])
            if filters.get('changed_by'):
                query = query.filter_by(changed_by=filters['changed_by'])
            if filters.get('from_date'):
                query = query.filter(DataChangeAudit.changed_at >= filters['from_date'])
            if filters.get('to_date'):
                query = query.filter(DataChangeAudit.changed_at <= filters['to_date'])
        
        return query.order_by(DataChangeAudit.changed_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_record_history(table_name, record_id):
        """Get complete change history for a record"""
        return DataChangeAudit.query.filter_by(
            table_name=table_name,
            record_id=str(record_id)
        ).order_by(DataChangeAudit.changed_at.desc()).all()
    
    # ==================== STATISTICS ====================
    @staticmethod
    def get_activity_stats(user_id=None, days=30):
        """Get activity statistics"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = ActivityLog.query.filter(ActivityLog.created_at >= from_date)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        # Total activities
        total = query.count()
        
        # By type
        by_type = db.session.query(
            ActivityLog.activity_type,
            db.func.count(ActivityLog.log_id)
        ).filter(ActivityLog.created_at >= from_date)
        
        if user_id:
            by_type = by_type.filter(ActivityLog.user_id == user_id)
        
        by_type = dict(by_type.group_by(ActivityLog.activity_type).all())
        
        # By status
        by_status = db.session.query(
            ActivityLog.status,
            db.func.count(ActivityLog.log_id)
        ).filter(ActivityLog.created_at >= from_date)
        
        if user_id:
            by_status = by_status.filter(ActivityLog.user_id == user_id)
        
        by_status = dict(by_status.group_by(ActivityLog.status).all())
        
        return {
            'total': total,
            'by_type': by_type,
            'by_status': by_status,
            'period_days': days
        }
    
    @staticmethod
    def get_most_active_users(days=30, limit=10):
        """Get most active users"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            ActivityLog.user_id,
            db.func.count(ActivityLog.log_id).label('activity_count')
        ).filter(
            ActivityLog.created_at >= from_date,
            ActivityLog.user_id.isnot(None)
        ).group_by(ActivityLog.user_id)\
         .order_by(db.func.count(ActivityLog.log_id).desc())\
         .limit(limit).all()
        
        return [{'user_id': r.user_id, 'activity_count': r.activity_count} for r in results]
    
    # ==================== CLEANUP ====================
    @staticmethod
    def cleanup_old_logs(days=365):
        """Delete old activity logs"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deleted = ActivityLog.query.filter(
            ActivityLog.created_at < cutoff
        ).delete()
        
        db.session.commit()
        return deleted
    
    @staticmethod
    def archive_audit_records(days=180):
        """Archive old audit records (placeholder for future implementation)"""
        # In production, this would move records to an archive table
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        count = DataChangeAudit.query.filter(
            DataChangeAudit.changed_at < cutoff
        ).count()
        
        return {'records_to_archive': count}
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def activity_log_to_dict(log):
        """Convert activity log to dictionary"""
        if not log:
            return None
        return {
            'log_id': log.log_id,
            'user_id': log.user_id,
            'activity_type': log.activity_type,
            'description': log.description,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'request_path': log.request_path,
            'request_method': log.request_method,
            'metadata': log.metadata,
            'status': log.status,
            'created_at': log.created_at.isoformat() if log.created_at else None
        }
    
    @staticmethod
    def data_change_to_dict(audit):
        """Convert data change audit to dictionary"""
        if not audit:
            return None
        return {
            'audit_id': audit.audit_id,
            'table_name': audit.table_name,
            'record_id': audit.record_id,
            'operation': audit.operation,
            'old_values': audit.old_values,
            'new_values': audit.new_values,
            'changed_fields': audit.changed_fields,
            'changed_by': audit.changed_by,
            'change_reason': audit.change_reason,
            'changed_at': audit.changed_at.isoformat() if audit.changed_at else None
        }
