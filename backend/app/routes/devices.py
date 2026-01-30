"""
Device Routes - Device registration and management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import DeviceService

devices_bp = Blueprint('devices', __name__)


# ==================== MOBILE APP ENDPOINTS ====================
@devices_bp.route('/register', methods=['POST'])
def register_device():
    """Register a new device from mobile app"""
    data = request.get_json()
    
    if not data.get('device_fingerprint'):
        return jsonify({'error': 'device_fingerprint is required'}), 400
    
    try:
        result = DeviceService.register_device(
            device_fingerprint=data['device_fingerprint'],
            device_data={
                'device_model': data.get('device_model'),
                'os_name': data.get('os_name'),
                'os_version': data.get('os_version'),
                'app_version': data.get('app_version'),
                'screen_resolution': data.get('screen_resolution'),
                'language': data.get('language'),
                'timezone': data.get('timezone'),
                'push_token': data.get('push_token'),
                'fcm_token': data.get('fcm_token')
            },
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': 'Device registered successfully',
            'device': DeviceService.device_to_dict(result['device']),
            'is_new': result['is_new']
        }), 201 if result['is_new'] else 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500


@devices_bp.route('/heartbeat', methods=['POST'])
def device_heartbeat():
    """Update device activity (heartbeat)"""
    data = request.get_json()
    
    if not data.get('device_id'):
        return jsonify({'error': 'device_id is required'}), 400
    
    device = DeviceService.update_activity(
        device_id=data['device_id'],
        ip_address=request.remote_addr,
        app_version=data.get('app_version'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'status': 'ok',
        'trust_score': float(device.trust_score) if device.trust_score else None,
        'is_blocked': device.is_blocked
    }), 200


@devices_bp.route('/status/<device_id>', methods=['GET'])
def get_device_status(device_id):
    """Get device status (for mobile app)"""
    device = DeviceService.get_device_by_id(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'device_id': device.device_id,
        'is_verified': device.is_verified,
        'is_blocked': device.is_blocked,
        'trust_score': float(device.trust_score) if device.trust_score else None,
        'trust_level': device.trust_level,
        'total_reports': device.total_reports
    }), 200


# ==================== ADMIN ENDPOINTS ====================
@devices_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_devices():
    """Get all devices (admin)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {}
    if request.args.get('is_blocked'):
        filters['is_blocked'] = request.args.get('is_blocked').lower() == 'true'
    if request.args.get('is_verified'):
        filters['is_verified'] = request.args.get('is_verified').lower() == 'true'
    if request.args.get('trust_level'):
        filters['trust_level'] = request.args.get('trust_level')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    pagination = DeviceService.get_all_devices(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'devices': [DeviceService.device_to_dict(d) for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@devices_bp.route('/<device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """Get device details (admin)"""
    device = DeviceService.get_device_by_id(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'device': DeviceService.device_to_dict(device, include_reports=True)
    }), 200


@devices_bp.route('/<device_id>/block', methods=['POST'])
@jwt_required()
def block_device(device_id):
    """Block a device"""
    data = request.get_json() or {}
    user_id = get_jwt_identity()
    
    device = DeviceService.block_device(
        device_id=device_id,
        reason=data.get('reason'),
        blocked_by_user_id=user_id
    )
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'message': 'Device blocked successfully',
        'device': DeviceService.device_to_dict(device)
    }), 200


@devices_bp.route('/<device_id>/unblock', methods=['POST'])
@jwt_required()
def unblock_device(device_id):
    """Unblock a device"""
    device = DeviceService.unblock_device(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'message': 'Device unblocked successfully',
        'device': DeviceService.device_to_dict(device)
    }), 200


@devices_bp.route('/<device_id>/verify', methods=['POST'])
@jwt_required()
def verify_device(device_id):
    """Verify a device"""
    user_id = get_jwt_identity()
    
    device = DeviceService.verify_device(
        device_id=device_id,
        verified_by_user_id=user_id
    )
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'message': 'Device verified successfully',
        'device': DeviceService.device_to_dict(device)
    }), 200


@devices_bp.route('/<device_id>/trust-history', methods=['GET'])
@jwt_required()
def get_trust_history(device_id):
    """Get device trust score history"""
    limit = request.args.get('limit', 30, type=int)
    
    history = DeviceService.get_trust_history(device_id=device_id, limit=limit)
    
    return jsonify({
        'device_id': device_id,
        'history': [DeviceService.trust_history_to_dict(h) for h in history]
    }), 200


@devices_bp.route('/<device_id>/recalculate-trust', methods=['POST'])
@jwt_required()
def recalculate_trust(device_id):
    """Recalculate device trust score"""
    result = DeviceService.recalculate_trust_score(device_id)
    
    if not result:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'message': 'Trust score recalculated',
        'device_id': device_id,
        'new_trust_score': result['trust_score'],
        'new_trust_level': result['trust_level']
    }), 200


@devices_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_device_statistics():
    """Get device statistics"""
    days = request.args.get('days', 30, type=int)
    
    stats = DeviceService.get_device_statistics(days=days)
    
    return jsonify(stats), 200
