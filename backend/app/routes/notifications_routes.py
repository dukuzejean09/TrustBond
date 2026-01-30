"""
Notifications Routes - Notification management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import NotificationService, PoliceService, AuditService

notifications_bp = Blueprint('notifications', __name__)


# ==================== GET NOTIFICATIONS ====================
@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for current user"""
    user_id = get_jwt_identity()
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    notifications, total = NotificationService.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'notifications': [NotificationService.notification_to_dict(n) for n in notifications],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get unread notification count for current user"""
    user_id = get_jwt_identity()
    
    count = NotificationService.get_unread_count(user_id)
    
    return jsonify({
        'unread_count': count
    }), 200


@notifications_bp.route('/<notification_id>', methods=['GET'])
@jwt_required()
def get_notification(notification_id):
    """Get a specific notification"""
    user_id = get_jwt_identity()
    
    notification = NotificationService.get_notification_by_id(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Check ownership
    if notification.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'notification': NotificationService.notification_to_dict(notification)
    }), 200


# ==================== UPDATE NOTIFICATIONS ====================
@notifications_bp.route('/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark notification as read"""
    user_id = get_jwt_identity()
    
    notification = NotificationService.get_notification_by_id(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Check ownership
    if notification.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    success = NotificationService.mark_as_read(notification_id)
    
    return jsonify({
        'message': 'Notification marked as read',
        'success': success
    }), 200


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read for current user"""
    user_id = get_jwt_identity()
    
    count = NotificationService.mark_all_as_read(user_id)
    
    return jsonify({
        'message': f'Marked {count} notifications as read',
        'count': count
    }), 200


@notifications_bp.route('/read-multiple', methods=['PUT'])
@jwt_required()
def mark_multiple_as_read():
    """Mark multiple notifications as read"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    notification_ids = data.get('notification_ids', [])
    
    if not notification_ids:
        return jsonify({'error': 'notification_ids array required'}), 400
    
    count = NotificationService.mark_multiple_as_read(
        notification_ids=notification_ids,
        user_id=user_id
    )
    
    return jsonify({
        'message': f'Marked {count} notifications as read',
        'count': count
    }), 200


@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification"""
    user_id = get_jwt_identity()
    
    notification = NotificationService.get_notification_by_id(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Check ownership
    if notification.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    success = NotificationService.delete_notification(notification_id)
    
    return jsonify({
        'message': 'Notification deleted',
        'success': success
    }), 200


# ==================== ADMIN - SEND NOTIFICATIONS ====================
@notifications_bp.route('/send', methods=['POST'])
@jwt_required()
def send_notification():
    """Send a notification to a user (admin)"""
    sender_id = get_jwt_identity()
    data = request.get_json()
    
    # Check permission
    if not PoliceService.has_permission(sender_id, 'send_notifications'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if not data.get('user_id'):
        return jsonify({'error': 'user_id is required'}), 400
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400
    
    notification = NotificationService.create_notification(
        user_id=data['user_id'],
        title=data['title'],
        message=data.get('message'),
        notification_type=data.get('notification_type', 'system'),
        reference_type=data.get('reference_type'),
        reference_id=data.get('reference_id'),
        priority=data.get('priority', 'normal')
    )
    
    AuditService.log_activity(
        user_id=sender_id,
        activity_type='create',
        description=f"Sent notification to user {data['user_id']}: {data['title']}",
        resource_type='notification',
        resource_id=notification.notification_id
    )
    
    return jsonify({
        'message': 'Notification sent',
        'notification': NotificationService.notification_to_dict(notification)
    }), 201


@notifications_bp.route('/broadcast', methods=['POST'])
@jwt_required()
def broadcast_notification():
    """Broadcast notification to multiple users (admin)"""
    sender_id = get_jwt_identity()
    data = request.get_json()
    
    # Check permission
    if not PoliceService.has_permission(sender_id, 'send_notifications'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if not data.get('user_ids') and not data.get('all_users'):
        return jsonify({'error': 'user_ids array or all_users flag required'}), 400
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400
    
    # Get target users
    if data.get('all_users'):
        users = PoliceService.get_all_active_users()
        user_ids = [u.user_id for u in users]
    else:
        user_ids = data['user_ids']
    
    notifications = NotificationService.create_bulk_notifications(
        user_ids=user_ids,
        title=data['title'],
        message=data.get('message'),
        notification_type=data.get('notification_type', 'system'),
        priority=data.get('priority', 'normal')
    )
    
    AuditService.log_activity(
        user_id=sender_id,
        activity_type='create',
        description=f"Broadcast notification to {len(notifications)} users: {data['title']}",
        resource_type='notification'
    )
    
    return jsonify({
        'message': f'Notification sent to {len(notifications)} users',
        'count': len(notifications)
    }), 201


# ==================== ADMIN - MANAGE NOTIFICATIONS ====================
@notifications_bp.route('/admin/all', methods=['GET'])
@jwt_required()
def get_all_notifications_admin():
    """Get all notifications (admin)"""
    user_id = get_jwt_identity()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'view_notifications'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    notification_type = request.args.get('type')
    
    notifications, total = NotificationService.get_all_notifications(
        page=page,
        per_page=per_page,
        notification_type=notification_type
    )
    
    return jsonify({
        'notifications': [NotificationService.notification_to_dict(n) for n in notifications],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@notifications_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_notification_stats():
    """Get notification statistics (admin)"""
    user_id = get_jwt_identity()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'view_notifications'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    stats = NotificationService.get_notification_stats(days=days)
    
    return jsonify({
        'stats': stats
    }), 200


@notifications_bp.route('/admin/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_notifications():
    """Cleanup old notifications (admin)"""
    user_id = get_jwt_identity()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_notifications'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    days = data.get('days_old', 90)
    
    count = NotificationService.cleanup_old_notifications(days_old=days)
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Cleaned up {count} old notifications (older than {days} days)",
        resource_type='notification'
    )
    
    return jsonify({
        'message': f'Cleaned up {count} old notifications',
        'count': count
    }), 200
