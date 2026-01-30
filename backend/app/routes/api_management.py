"""
API Management Routes - API key and request management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import APIService, PoliceService, AuditService
from functools import wraps
import time

api_management_bp = Blueprint('api_management', __name__)


# ==================== API KEY MANAGEMENT ====================
@api_management_bp.route('/keys', methods=['GET'])
@jwt_required()
def get_all_api_keys():
    """Get all API keys"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {}
    if request.args.get('is_active'):
        filters['is_active'] = request.args.get('is_active').lower() == 'true'
    if request.args.get('client_name'):
        filters['client_name'] = request.args.get('client_name')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    pagination = APIService.get_all_api_keys(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'api_keys': [APIService.api_key_to_dict(k) for k in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@api_management_bp.route('/keys/<key_id>', methods=['GET'])
@jwt_required()
def get_api_key(key_id):
    """Get API key details"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    api_key = APIService.get_api_key_by_id(key_id)
    
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404
    
    return jsonify({
        'api_key': APIService.api_key_to_dict(api_key, include_sensitive=True)
    }), 200


@api_management_bp.route('/keys', methods=['POST'])
@jwt_required()
def create_api_key():
    """Create a new API key"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if not data.get('name') or not data.get('client_name'):
        return jsonify({'error': 'name and client_name are required'}), 400
    
    try:
        result = APIService.create_api_key(data, created_by_user_id=user_id)
        
        AuditService.log_activity(
            user_id=user_id,
            activity_type='create',
            description=f"Created API key: {data['name']}",
            resource_type='api_key',
            resource_id=result['api_key'].key_id
        )
        
        return jsonify({
            'message': result['message'],
            'api_key': APIService.api_key_to_dict(result['api_key']),
            'raw_key': result['raw_key']  # Only returned once!
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_management_bp.route('/keys/<key_id>', methods=['PUT'])
@jwt_required()
def update_api_key(key_id):
    """Update API key settings"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    api_key = APIService.update_api_key(key_id, data, updated_by_user_id=user_id)
    
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Updated API key: {api_key.name}",
        resource_type='api_key',
        resource_id=key_id
    )
    
    return jsonify({
        'message': 'API key updated successfully',
        'api_key': APIService.api_key_to_dict(api_key)
    }), 200


@api_management_bp.route('/keys/<key_id>/revoke', methods=['POST'])
@jwt_required()
def revoke_api_key(key_id):
    """Revoke an API key"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    
    api_key = APIService.revoke_api_key(
        key_id=key_id,
        reason=data.get('reason'),
        revoked_by_user_id=user_id
    )
    
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Revoked API key: {api_key.name}",
        resource_type='api_key',
        resource_id=key_id
    )
    
    return jsonify({
        'message': 'API key revoked successfully',
        'api_key': APIService.api_key_to_dict(api_key)
    }), 200


@api_management_bp.route('/keys/<key_id>/regenerate', methods=['POST'])
@jwt_required()
def regenerate_api_key(key_id):
    """Regenerate an API key"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    result = APIService.regenerate_api_key(key_id, regenerated_by_user_id=user_id)
    
    if not result:
        return jsonify({'error': 'API key not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Regenerated API key: {result['api_key'].name}",
        resource_type='api_key',
        resource_id=key_id
    )
    
    return jsonify({
        'message': result['message'],
        'api_key': APIService.api_key_to_dict(result['api_key']),
        'raw_key': result['raw_key']  # Only returned once!
    }), 200


# ==================== REQUEST LOGS ====================
@api_management_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_request_logs():
    """Get API request logs"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    if request.args.get('api_key_id'):
        filters['api_key_id'] = request.args.get('api_key_id')
    if request.args.get('endpoint'):
        filters['endpoint'] = request.args.get('endpoint')
    if request.args.get('method'):
        filters['method'] = request.args.get('method')
    if request.args.get('status'):
        filters['status'] = request.args.get('status', type=int)
    if request.args.get('has_error'):
        filters['has_error'] = request.args.get('has_error').lower() == 'true'
    
    pagination = APIService.get_request_logs(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'logs': [APIService.request_log_to_dict(l) for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@api_management_bp.route('/logs/key/<key_id>', methods=['GET'])
@jwt_required()
def get_key_request_logs(key_id):
    """Get request logs for a specific API key"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    pagination = APIService.get_request_logs(api_key_id=key_id, page=page, per_page=per_page)
    
    return jsonify({
        'api_key_id': key_id,
        'logs': [APIService.request_log_to_dict(l) for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


# ==================== STATISTICS ====================
@api_management_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_api_statistics():
    """Get overall API usage statistics"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    stats = APIService.get_overall_api_stats(days=days)
    
    return jsonify(stats), 200


@api_management_bp.route('/statistics/key/<key_id>', methods=['GET'])
@jwt_required()
def get_key_statistics(key_id):
    """Get statistics for a specific API key"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    stats = APIService.get_api_key_stats(key_id, days=days)
    
    if not stats:
        return jsonify({'error': 'API key not found'}), 404
    
    return jsonify(stats), 200


# ==================== SCOPES INFO ====================
@api_management_bp.route('/scopes', methods=['GET'])
@jwt_required()
def get_available_scopes():
    """Get list of available API scopes"""
    return jsonify({
        'scopes': APIService.SCOPES
    }), 200


@api_management_bp.route('/rate-limits', methods=['GET'])
@jwt_required()
def get_rate_limit_tiers():
    """Get available rate limit tiers"""
    return jsonify({
        'rate_limits': APIService.RATE_LIMITS
    }), 200


# ==================== CLEANUP ====================
@api_management_bp.route('/logs/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_logs():
    """Delete old request logs"""
    user_id = get_jwt_identity()
    
    user = PoliceService.get_user_by_id(user_id)
    if not user or user.role != 'superadmin':
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    days = data.get('days', 90)
    
    deleted = APIService.cleanup_old_logs(days=days)
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Cleaned up {deleted} old API request logs",
        resource_type='api_logs'
    )
    
    return jsonify({
        'message': f'Deleted {deleted} old logs',
        'days_threshold': days
    }), 200


# ==================== API KEY VALIDATION (for external use) ====================
@api_management_bp.route('/validate', methods=['POST'])
def validate_api_key():
    """Validate an API key (for external services)"""
    data = request.get_json()
    
    if not data.get('api_key'):
        return jsonify({'error': 'api_key is required'}), 400
    
    api_key, message = APIService.validate_api_key(data['api_key'])
    
    if not api_key:
        return jsonify({'valid': False, 'error': message}), 401
    
    # Check rate limit
    is_allowed, limit_message = APIService.check_rate_limit(api_key)
    
    return jsonify({
        'valid': True,
        'rate_limit_ok': is_allowed,
        'rate_limit_message': limit_message if not is_allowed else None,
        'scopes': api_key.scopes,
        'client_name': api_key.client_name
    }), 200
