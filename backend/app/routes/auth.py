from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, UserRole
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'firstName', 'lastName']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    if data.get('nationalId') and User.query.filter_by(national_id=data['nationalId']).first():
        return jsonify({'error': 'National ID already registered'}), 409
    
    # Create new user
    user = User(
        email=data['email'],
        first_name=data['firstName'],
        last_name=data['lastName'],
        phone=data.get('phone'),
        national_id=data.get('nationalId'),
        province=data.get('province'),
        district=data.get('district'),
        sector=data.get('sector'),
        cell=data.get('cell'),
        role=UserRole.CITIZEN
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Generate token (JWT identity must be a string)
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Registration successful',
        'token': access_token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if user.status.value != 'active':
        return jsonify({'error': 'Account is not active'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate token (JWT identity must be a string)
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not data.get('currentPassword') or not data.get('newPassword'):
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    if not user.check_password(data['currentPassword']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    user.set_password(data['newPassword'])
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin/Officer login for dashboard"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Check if user is admin or officer
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Access denied. Admin or officer account required'}), 403
    
    if user.status.value != 'active':
        return jsonify({'error': 'Account is not active'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate token (JWT identity must be a string)
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': user.to_dict()
    }), 200


# Password Reset Token Storage (in production, use Redis or database)
password_reset_tokens = {}


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset.
    
    In production, this would send an email with a reset link.
    For demo purposes, it returns the token directly.
    """
    import secrets
    
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return jsonify({
            'message': 'If the email exists, a password reset link has been sent'
        }), 200
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token with expiry (in production, store in database)
    password_reset_tokens[reset_token] = {
        'user_id': user.id,
        'email': user.email,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(hours=1)
    }
    
    # In production: Send email with reset link
    # For demo: Return token in response
    
    return jsonify({
        'message': 'If the email exists, a password reset link has been sent',
        'debug_token': reset_token  # Remove in production
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token."""
    data = request.get_json()
    
    token = data.get('token')
    new_password = data.get('newPassword')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400
    
    # Validate token
    token_data = password_reset_tokens.get(token)
    
    if not token_data:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    # Check expiry
    if datetime.utcnow() > token_data['expires_at']:
        del password_reset_tokens[token]
        return jsonify({'error': 'Reset token has expired'}), 400
    
    # Find user
    user = User.query.get(token_data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    # Remove used token
    del password_reset_tokens[token]
    
    return jsonify({'message': 'Password has been reset successfully'}), 200


@auth_bp.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    """Verify if a reset token is valid."""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    
    token_data = password_reset_tokens.get(token)
    
    if not token_data:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 200
    
    if datetime.utcnow() > token_data['expires_at']:
        return jsonify({'valid': False, 'error': 'Token expired'}), 200
    
    return jsonify({
        'valid': True,
        'email': token_data['email']
    }), 200
