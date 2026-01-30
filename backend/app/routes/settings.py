"""
Settings Routes - System settings management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import SettingsService, PoliceService, AuditService

settings_bp = Blueprint('settings', __name__)


# ==================== GET SETTINGS ====================
@settings_bp.route('', methods=['GET'])
@jwt_required()
def get_all_settings():
    """Get all system settings"""
    category = request.args.get('category')
    
    settings = SettingsService.get_all_settings(category=category)
    
    return jsonify({
        'settings': settings
    }), 200


@settings_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get available setting categories"""
    categories = SettingsService.get_setting_categories()
    
    return jsonify({
        'categories': categories
    }), 200


@settings_bp.route('/<setting_key>', methods=['GET'])
@jwt_required()
def get_setting(setting_key):
    """Get a specific setting value"""
    typed = request.args.get('typed', 'true').lower() == 'true'
    
    if typed:
        value = SettingsService.get_setting_typed(setting_key)
    else:
        value = SettingsService.get_setting(setting_key)
    
    if value is None:
        return jsonify({'error': 'Setting not found'}), 404
    
    return jsonify({
        'key': setting_key,
        'value': value
    }), 200


# ==================== UPDATE SETTINGS ====================
@settings_bp.route('/<setting_key>', methods=['PUT'])
@jwt_required()
def update_setting(setting_key):
    """Update a setting value"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'value' not in data:
        return jsonify({'error': 'value is required'}), 400
    
    setting = SettingsService.set_setting(
        setting_key=setting_key,
        value=data['value'],
        updated_by_user_id=user_id
    )
    
    if not setting:
        return jsonify({'error': 'Failed to update setting'}), 500
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Updated setting: {setting_key}",
        resource_type='system_setting',
        resource_id=setting_key
    )
    
    return jsonify({
        'message': 'Setting updated successfully',
        'setting': SettingsService.setting_to_dict(setting)
    }), 200


@settings_bp.route('', methods=['PUT'])
@jwt_required()
def update_multiple_settings():
    """Update multiple settings at once"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if not data.get('settings') or not isinstance(data['settings'], dict):
        return jsonify({'error': 'settings dict is required'}), 400
    
    updated = SettingsService.set_multiple_settings(
        settings_dict=data['settings'],
        updated_by_user_id=user_id
    )
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Updated {len(updated)} settings",
        resource_type='system_setting'
    )
    
    return jsonify({
        'message': f'Updated {len(updated)} settings',
        'settings': [SettingsService.setting_to_dict(s) for s in updated]
    }), 200


# ==================== CREATE SETTINGS ====================
@settings_bp.route('', methods=['POST'])
@jwt_required()
def create_setting():
    """Create a new setting"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if not data.get('setting_key'):
        return jsonify({'error': 'setting_key is required'}), 400
    
    try:
        setting = SettingsService.create_setting(data, created_by_user_id=user_id)
        
        AuditService.log_activity(
            user_id=user_id,
            activity_type='create',
            description=f"Created setting: {data['setting_key']}",
            resource_type='system_setting',
            resource_id=setting.setting_key
        )
        
        return jsonify({
            'message': 'Setting created successfully',
            'setting': SettingsService.setting_to_dict(setting)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@settings_bp.route('/<setting_key>', methods=['DELETE'])
@jwt_required()
def delete_setting(setting_key):
    """Delete a setting"""
    user_id = get_jwt_identity()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    success = SettingsService.delete_setting(setting_key)
    
    if not success:
        return jsonify({'error': 'Setting not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Deleted setting: {setting_key}",
        resource_type='system_setting',
        resource_id=setting_key
    )
    
    return jsonify({'message': 'Setting deleted successfully'}), 200


# ==================== INITIALIZE DEFAULTS ====================
@settings_bp.route('/initialize', methods=['POST'])
@jwt_required()
def initialize_defaults():
    """Initialize default settings"""
    user_id = get_jwt_identity()
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_settings'):
        return jsonify({'error': 'Permission denied'}), 403
    
    created = SettingsService.initialize_default_settings(created_by_user_id=user_id)
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='create',
        description=f"Initialized {len(created)} default settings",
        resource_type='system_setting'
    )
    
    return jsonify({
        'message': f'Initialized {len(created)} default settings',
        'settings': [SettingsService.setting_to_dict(s) for s in created]
    }), 200
