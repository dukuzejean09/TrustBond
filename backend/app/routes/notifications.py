"""
Notifications API Routes.

Provides endpoints for:
- Getting user notifications
- Marking notifications as read
- Push notification registration
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    Notification, NotificationType, NotificationPriority,
    User, UserRole
)
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Get notifications for the current user.
    
    Query Parameters:
    - page: Page number (default 1)
    - per_page: Items per page (default 20)
    - unread_only: Only get unread notifications
    - type: Filter by notification type
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    notification_type = request.args.get('type')
    
    # Build query - get user's notifications and relevant broadcasts
    query = Notification.query.filter(
        or_(
            Notification.user_id == user_id,
            and_(
                Notification.is_broadcast == True,
                or_(
                    Notification.target_district.is_(None),
                    Notification.target_district == user.district
                ),
                or_(
                    Notification.target_role.is_(None),
                    Notification.target_role == user.role.value
                )
            )
        )
    )
    
    # Filter out expired notifications
    now = datetime.utcnow()
    query = query.filter(
        or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > now
        )
    )
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    if notification_type:
        query = query.filter(Notification.notification_type == NotificationType(notification_type))
    
    # Order by creation date, newest first
    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Count unread
    unread_count = Notification.query.filter(
        or_(
            Notification.user_id == user_id,
            Notification.is_broadcast == True
        ),
        Notification.is_read == False
    ).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page,
        'unreadCount': unread_count
    }), 200


@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get count of unread notifications."""
    user_id = int(get_jwt_identity())
    
    count = Notification.query.filter(
        or_(
            Notification.user_id == user_id,
            Notification.is_broadcast == True
        ),
        Notification.is_read == False
    ).count()
    
    return jsonify({'unreadCount': count}), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a notification as read."""
    user_id = int(get_jwt_identity())
    
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Check ownership (unless it's a broadcast)
    if notification.user_id and notification.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({
        'message': 'Notification marked as read',
        'notification': notification.to_dict()
    }), 200


@notifications_bp.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read."""
    user_id = int(get_jwt_identity())
    
    now = datetime.utcnow()
    Notification.query.filter(
        or_(
            Notification.user_id == user_id,
            Notification.is_broadcast == True
        ),
        Notification.is_read == False
    ).update({
        'is_read': True,
        'read_at': now
    }, synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'}), 200


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification."""
    user_id = int(get_jwt_identity())
    
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Check ownership
    if notification.user_id and notification.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'}), 200


@notifications_bp.route('/clear-old', methods=['DELETE'])
@jwt_required()
def clear_old_notifications():
    """Clear notifications older than 30 days."""
    user_id = int(get_jwt_identity())
    
    cutoff = datetime.utcnow() - timedelta(days=30)
    
    deleted = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.created_at < cutoff,
        Notification.is_read == True
    ).delete(synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Cleared {deleted} old notifications'
    }), 200


# ==================== Admin Endpoints ====================

@notifications_bp.route('/broadcast', methods=['POST'])
@jwt_required()
def create_broadcast():
    """Create a broadcast notification (admin only)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    if not data.get('title') or not data.get('message'):
        return jsonify({'error': 'Title and message are required'}), 400
    
    notification = Notification(
        title=data['title'],
        message=data['message'],
        notification_type=NotificationType.SYSTEM_MESSAGE,
        priority=NotificationPriority(data.get('priority', 'medium')),
        is_broadcast=True,
        target_district=data.get('district'),
        target_role=data.get('role'),
        data=data.get('data', {}),
        expires_at=datetime.fromisoformat(data['expiresAt']) if data.get('expiresAt') else None
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Broadcast notification created',
        'notification': notification.to_dict()
    }), 201


# ==================== Push Notification Tokens ====================

@notifications_bp.route('/push-token', methods=['POST'])
@jwt_required()
def register_push_token():
    """
    Register a push notification token for the user's device.
    
    Request Body:
    - token: FCM/APNs token
    - platform: 'android' or 'ios'
    - device_id: Device identifier (optional)
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    token = data.get('token')
    platform = data.get('platform')
    
    if not token or not platform:
        return jsonify({'error': 'Token and platform are required'}), 400
    
    # In a full implementation, you would store this in a PushToken model
    # For now, we'll store it in user metadata or a separate table
    # This is a placeholder for the push notification infrastructure
    
    return jsonify({
        'message': 'Push token registered successfully',
        'platform': platform
    }), 200


@notifications_bp.route('/push-token', methods=['DELETE'])
@jwt_required()
def unregister_push_token():
    """Unregister push notification token when logging out."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    token = data.get('token')
    
    # Remove token from storage
    # Placeholder implementation
    
    return jsonify({'message': 'Push token unregistered'}), 200
