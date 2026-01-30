"""
Audit Routes - Activity logging and audit trail endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import AuditService, PoliceService
from datetime import datetime

audit_bp = Blueprint('audit', __name__)


# ==================== ACTIVITY LOGS ====================
@audit_bp.route('/activities', methods=['GET'])
@jwt_required()
def get_activity_logs():
    """Get activity logs"""
    user_id = get_jwt_identity()
    
    # Check permission for viewing all logs
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    if request.args.get('user_id'):
        filters['user_id'] = request.args.get('user_id')
    if request.args.get('activity_type'):
        filters['activity_type'] = request.args.get('activity_type')
    if request.args.get('resource_type'):
        filters['resource_type'] = request.args.get('resource_type')
    if request.args.get('resource_id'):
        filters['resource_id'] = request.args.get('resource_id')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('from_date'):
        filters['from_date'] = datetime.fromisoformat(request.args.get('from_date'))
    if request.args.get('to_date'):
        filters['to_date'] = datetime.fromisoformat(request.args.get('to_date'))
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    pagination = AuditService.get_activity_logs(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'logs': [AuditService.activity_log_to_dict(l) for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@audit_bp.route('/activities/my', methods=['GET'])
@jwt_required()
def get_my_activity():
    """Get current user's activity"""
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    activities = AuditService.get_user_activity(user_id, days=days, limit=limit)
    
    return jsonify({
        'activities': [AuditService.activity_log_to_dict(a) for a in activities]
    }), 200


@audit_bp.route('/activities/user/<target_user_id>', methods=['GET'])
@jwt_required()
def get_user_activity(target_user_id):
    """Get activity for a specific user"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    activities = AuditService.get_user_activity(target_user_id, days=days, limit=limit)
    
    return jsonify({
        'user_id': target_user_id,
        'activities': [AuditService.activity_log_to_dict(a) for a in activities]
    }), 200


@audit_bp.route('/activities/resource/<resource_type>/<resource_id>', methods=['GET'])
@jwt_required()
def get_resource_history(resource_type, resource_id):
    """Get activity history for a specific resource"""
    activities = AuditService.get_resource_history(resource_type, resource_id)
    
    return jsonify({
        'resource_type': resource_type,
        'resource_id': resource_id,
        'activities': [AuditService.activity_log_to_dict(a) for a in activities]
    }), 200


# ==================== DATA CHANGES ====================
@audit_bp.route('/changes', methods=['GET'])
@jwt_required()
def get_data_changes():
    """Get data change audit records"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    if request.args.get('table_name'):
        filters['table_name'] = request.args.get('table_name')
    if request.args.get('record_id'):
        filters['record_id'] = request.args.get('record_id')
    if request.args.get('operation'):
        filters['operation'] = request.args.get('operation')
    if request.args.get('changed_by'):
        filters['changed_by'] = request.args.get('changed_by')
    if request.args.get('from_date'):
        filters['from_date'] = datetime.fromisoformat(request.args.get('from_date'))
    if request.args.get('to_date'):
        filters['to_date'] = datetime.fromisoformat(request.args.get('to_date'))
    
    pagination = AuditService.get_data_changes(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'changes': [AuditService.data_change_to_dict(c) for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@audit_bp.route('/changes/<table_name>/<record_id>', methods=['GET'])
@jwt_required()
def get_record_history(table_name, record_id):
    """Get complete change history for a record"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    history = AuditService.get_record_history(table_name, record_id)
    
    return jsonify({
        'table_name': table_name,
        'record_id': record_id,
        'history': [AuditService.data_change_to_dict(h) for h in history]
    }), 200


# ==================== STATISTICS ====================
@audit_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_audit_statistics():
    """Get audit statistics"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    target_user_id = request.args.get('user_id')
    
    stats = AuditService.get_activity_stats(user_id=target_user_id, days=days)
    
    return jsonify(stats), 200


@audit_bp.route('/statistics/active-users', methods=['GET'])
@jwt_required()
def get_most_active_users():
    """Get most active users"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    users = AuditService.get_most_active_users(days=days, limit=limit)
    
    return jsonify({
        'most_active_users': users
    }), 200


# ==================== CLEANUP ====================
@audit_bp.route('/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_logs():
    """Delete old activity logs (admin only)"""
    user_id = get_jwt_identity()
    
    # Only superadmin can cleanup logs
    user = PoliceService.get_user_by_id(user_id)
    if not user or user.role != 'superadmin':
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    days = data.get('days', 365)
    
    deleted = AuditService.cleanup_old_logs(days=days)
    
    # Log the cleanup action
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Cleaned up {deleted} old activity logs (older than {days} days)",
        resource_type='system'
    )
    
    return jsonify({
        'message': f'Deleted {deleted} old logs',
        'days_threshold': days
    }), 200


# ==================== EXPORT ====================
@audit_bp.route('/export', methods=['POST'])
@jwt_required()
def export_audit_logs():
    """Export audit logs (placeholder)"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    
    # Log the export request
    AuditService.log_export(
        user_id=user_id,
        export_type='audit_logs',
        record_count=0,  # Would be actual count
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'message': 'Export initiated',
        'status': 'pending',
        'note': 'Export will be sent to your email when ready'
    }), 202
