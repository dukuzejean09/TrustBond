"""
Police Routes - Police user management and authentication endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services import PoliceService, AuditService

police_bp = Blueprint('police', __name__)


# ==================== AUTHENTICATION ====================
@police_bp.route('/login', methods=['POST'])
def login():
    """Police user login"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    result, message = PoliceService.authenticate(
        username=data['username'],
        password=data['password'],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    if not result:
        # Log failed attempt
        AuditService.log_login(None, request.remote_addr, request.user_agent.string, success=False)
        return jsonify({'error': message}), 401
    
    # Log successful login
    AuditService.log_login(result['user'].user_id, request.remote_addr, request.user_agent.string, success=True)
    
    # Generate JWT token
    access_token = create_access_token(identity=str(result['user'].user_id))
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'session_id': result['session'].session_id,
        'user': PoliceService.user_to_dict(result['user']),
        'must_change_password': result['must_change_password']
    }), 200


@police_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Police user logout"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    if data.get('session_id'):
        PoliceService.logout(data['session_id'])
    
    AuditService.log_logout(user_id, request.remote_addr)
    
    return jsonify({'message': 'Logout successful'}), 200


@police_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    user = PoliceService.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': PoliceService.user_to_dict(user, include_sensitive=True)
    }), 200


@police_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password are required'}), 400
    
    success, message = PoliceService.change_password(
        user_id=user_id,
        old_password=data['current_password'],
        new_password=data['new_password']
    )
    
    if not success:
        return jsonify({'error': message}), 400
    
    return jsonify({'message': message}), 200


# ==================== USER MANAGEMENT ====================
@police_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all police users"""
    user_id = get_jwt_identity()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {}
    if request.args.get('role'):
        filters['role'] = request.args.get('role')
    if request.args.get('is_active'):
        filters['is_active'] = request.args.get('is_active').lower() == 'true'
    if request.args.get('district_id'):
        filters['district_id'] = request.args.get('district_id', type=int)
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    pagination = PoliceService.get_all_users(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'users': [PoliceService.user_to_dict(u) for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@police_bp.route('/users/<target_user_id>', methods=['GET'])
@jwt_required()
def get_user(target_user_id):
    """Get user details"""
    user_id = get_jwt_identity()
    
    # Users can view their own profile, admins can view all
    if target_user_id != user_id and not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    user = PoliceService.get_user_by_id(target_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': PoliceService.user_to_dict(user, include_sensitive=True)
    }), 200


@police_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new police user"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    try:
        user = PoliceService.create_user(data, created_by_user_id=user_id)
        
        AuditService.log_user_management(
            user_id, user.user_id, 'create',
            f"Created user {user.username}"
        )
        
        return jsonify({
            'message': 'User created successfully',
            'user': PoliceService.user_to_dict(user)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@police_bp.route('/users/<target_user_id>', methods=['PUT'])
@jwt_required()
def update_user(target_user_id):
    """Update a police user"""
    user_id = get_jwt_identity()
    
    # Users can update their own profile (limited fields), admins can update all
    if target_user_id != user_id and not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Restrict fields for non-admins
    if not PoliceService.has_permission(user_id, 'manage_users'):
        allowed = ['full_name', 'email', 'phone', 'profile_picture']
        data = {k: v for k, v in data.items() if k in allowed}
    
    try:
        user = PoliceService.update_user(target_user_id, data, updated_by_user_id=user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        AuditService.log_user_management(
            user_id, target_user_id, 'update',
            f"Updated user {user.username}"
        )
        
        return jsonify({
            'message': 'User updated successfully',
            'user': PoliceService.user_to_dict(user)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@police_bp.route('/users/<target_user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(target_user_id):
    """Deactivate a police user"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if target_user_id == user_id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    success = PoliceService.delete_user(target_user_id)
    
    if not success:
        return jsonify({'error': 'User not found'}), 404
    
    AuditService.log_user_management(user_id, target_user_id, 'delete', 'Deactivated user')
    
    return jsonify({'message': 'User deactivated successfully'}), 200


@police_bp.route('/users/<target_user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(target_user_id):
    """Admin reset user password"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if not data.get('new_password'):
        return jsonify({'error': 'new_password is required'}), 400
    
    success, message = PoliceService.reset_password(
        user_id=target_user_id,
        new_password=data['new_password'],
        admin_user_id=user_id
    )
    
    if not success:
        return jsonify({'error': message}), 400
    
    AuditService.log_user_management(user_id, target_user_id, 'update', 'Password reset by admin')
    
    return jsonify({'message': message}), 200


# ==================== PERMISSIONS ====================
@police_bp.route('/users/<target_user_id>/permissions', methods=['GET'])
@jwt_required()
def get_user_permissions(target_user_id):
    """Get user permissions"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    user = PoliceService.get_user_by_id(target_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user_id': target_user_id,
        'role': user.role,
        'permissions': user.permissions or {}
    }), 200


@police_bp.route('/users/<target_user_id>/permissions', methods=['PUT'])
@jwt_required()
def update_user_permissions(target_user_id):
    """Update user permissions"""
    user_id = get_jwt_identity()
    
    if not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    user = PoliceService.update_permissions(
        user_id=target_user_id,
        permissions=data.get('permissions', {}),
        admin_user_id=user_id
    )
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    AuditService.log_user_management(user_id, target_user_id, 'update', 'Updated permissions')
    
    return jsonify({
        'message': 'Permissions updated',
        'permissions': user.permissions
    }), 200


# ==================== SESSIONS ====================
@police_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_my_sessions():
    """Get current user's active sessions"""
    user_id = get_jwt_identity()
    
    sessions = PoliceService.get_active_sessions(user_id)
    
    return jsonify({
        'sessions': [PoliceService.session_to_dict(s) for s in sessions]
    }), 200


@police_bp.route('/sessions/invalidate-all', methods=['POST'])
@jwt_required()
def invalidate_all_sessions():
    """Invalidate all sessions for current user"""
    user_id = get_jwt_identity()
    
    PoliceService.invalidate_all_sessions(user_id)
    
    return jsonify({'message': 'All sessions invalidated'}), 200


# ==================== ACTIVITY ====================
@police_bp.route('/users/<target_user_id>/activity', methods=['GET'])
@jwt_required()
def get_user_activity(target_user_id):
    """Get user activity summary"""
    user_id = get_jwt_identity()
    
    if target_user_id != user_id and not PoliceService.has_permission(user_id, 'manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    summary = PoliceService.get_user_activity_summary(target_user_id, days=days)
    
    if not summary:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(summary), 200
