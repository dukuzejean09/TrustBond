from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, UserRole, UserStatus

users_bp = Blueprint('users', __name__)


def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@users_bp.route('', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = User.query
    
    if role:
        query = query.filter(User.role == UserRole(role))
    
    if status:
        query = query.filter(User.status == UserStatus(status))
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.phone.ilike(search_term)
            )
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [user.to_dict() for user in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get a specific user"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    # Users can view their own profile, admins can view any profile
    if current_user_id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    data = request.get_json()
    
    # Users can update their own profile, admins can update any profile
    if current_user_id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update allowed fields
    allowed_fields = ['firstName', 'lastName', 'phone', 'province', 'district', 'sector', 'cell', 'profileImage']
    field_mapping = {
        'firstName': 'first_name',
        'lastName': 'last_name',
        'profileImage': 'profile_image'
    }
    
    for field in allowed_fields:
        if field in data:
            attr_name = field_mapping.get(field, field)
            setattr(user, attr_name, data[field])
    
    # Admin-only fields
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if 'role' in data:
            user.role = UserRole(data['role'])
        if 'status' in data:
            user.status = UserStatus(data['status'])
        if 'badgeNumber' in data:
            user.badge_number = data['badgeNumber']
        if 'station' in data:
            user.station = data['station']
        if 'rank' in data:
            user.rank = data['rank']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200


@users_bp.route('/officers', methods=['GET'])
@jwt_required()
def get_officers():
    """Get all officers"""
    officers = User.query.filter(User.role == UserRole.OFFICER).all()
    return jsonify({
        'officers': [officer.to_dict() for officer in officers]
    }), 200


@users_bp.route('/create-officer', methods=['POST'])
@admin_required
def create_officer():
    """Create a new officer account (admin only)"""
    data = request.get_json()
    
    required_fields = ['email', 'password', 'firstName', 'lastName', 'badgeNumber']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    if User.query.filter_by(badge_number=data['badgeNumber']).first():
        return jsonify({'error': 'Badge number already registered'}), 409
    
    officer = User(
        email=data['email'],
        first_name=data['firstName'],
        last_name=data['lastName'],
        phone=data.get('phone'),
        badge_number=data['badgeNumber'],
        station=data.get('station'),
        rank=data.get('rank'),
        role=UserRole.OFFICER
    )
    officer.set_password(data['password'])
    
    db.session.add(officer)
    db.session.commit()
    
    return jsonify({
        'message': 'Officer created successfully',
        'user': officer.to_dict()
    }), 201
