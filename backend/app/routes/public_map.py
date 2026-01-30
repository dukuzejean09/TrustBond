"""
Public Map Routes - Public safety map endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import PublicMapService, PoliceService, AuditService

public_map_bp = Blueprint('public_map', __name__)


# ==================== PUBLIC ENDPOINTS (No Auth) ====================
@public_map_bp.route('/data', methods=['GET'])
def get_public_map_data():
    """Get anonymized data for public safety map"""
    district_id = request.args.get('district_id', type=int)
    include_zones = request.args.get('include_zones', 'true').lower() == 'true'
    include_hotspots = request.args.get('include_hotspots', 'true').lower() == 'true'
    
    data = PublicMapService.get_public_map_data(
        district_id=district_id,
        include_zones=include_zones,
        include_hotspots=include_hotspots
    )
    
    return jsonify(data), 200


@public_map_bp.route('/zones', methods=['GET'])
def get_public_zones():
    """Get public safety zones"""
    district_id = request.args.get('district_id', type=int)
    
    zones = PublicMapService.get_all_safety_zones(district_id=district_id)
    
    return jsonify({
        'zones': [PublicMapService.zone_to_public_dict(z) for z in zones]
    }), 200


@public_map_bp.route('/zones/<zone_id>', methods=['GET'])
def get_public_zone(zone_id):
    """Get specific safety zone (public view)"""
    zone = PublicMapService.get_safety_zone_by_id(zone_id)
    
    if not zone or not zone.is_active:
        return jsonify({'error': 'Zone not found'}), 404
    
    return jsonify({
        'zone': PublicMapService.zone_to_public_dict(zone)
    }), 200


# ==================== ADMIN ENDPOINTS ====================
@public_map_bp.route('/admin/zones', methods=['GET'])
@jwt_required()
def get_all_zones_admin():
    """Get all safety zones (admin view)"""
    district_id = request.args.get('district_id', type=int)
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    
    zones = PublicMapService.get_all_safety_zones(
        district_id=district_id,
        active_only=active_only
    )
    
    return jsonify({
        'zones': [PublicMapService.zone_to_dict(z) for z in zones]
    }), 200


@public_map_bp.route('/admin/zones/<zone_id>', methods=['GET'])
@jwt_required()
def get_zone_admin(zone_id):
    """Get zone details (admin view)"""
    zone = PublicMapService.get_safety_zone_by_id(zone_id)
    
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404
    
    return jsonify({
        'zone': PublicMapService.zone_to_dict(zone)
    }), 200


@public_map_bp.route('/admin/zones', methods=['POST'])
@jwt_required()
def create_zone():
    """Create a new safety zone"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('zone_name'):
        return jsonify({'error': 'zone_name is required'}), 400
    
    if not data.get('centroid_latitude') or not data.get('centroid_longitude'):
        return jsonify({'error': 'centroid_latitude and centroid_longitude are required'}), 400
    
    try:
        zone = PublicMapService.create_safety_zone(data, created_by_user_id=user_id)
        
        AuditService.log_activity(
            user_id=user_id,
            activity_type='create',
            description=f"Created safety zone: {zone.zone_name}",
            resource_type='safety_zone',
            resource_id=zone.zone_id
        )
        
        return jsonify({
            'message': 'Safety zone created successfully',
            'zone': PublicMapService.zone_to_dict(zone)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@public_map_bp.route('/admin/zones/<zone_id>', methods=['PUT'])
@jwt_required()
def update_zone(zone_id):
    """Update a safety zone"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    zone = PublicMapService.update_safety_zone(
        zone_id=zone_id,
        update_data=data,
        updated_by_user_id=user_id
    )
    
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Updated safety zone: {zone.zone_name}",
        resource_type='safety_zone',
        resource_id=zone_id
    )
    
    return jsonify({
        'message': 'Safety zone updated successfully',
        'zone': PublicMapService.zone_to_dict(zone)
    }), 200


@public_map_bp.route('/admin/zones/<zone_id>', methods=['DELETE'])
@jwt_required()
def delete_zone(zone_id):
    """Delete/deactivate a safety zone"""
    user_id = get_jwt_identity()
    
    success = PublicMapService.delete_safety_zone(zone_id)
    
    if not success:
        return jsonify({'error': 'Zone not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Deleted safety zone: {zone_id}",
        resource_type='safety_zone',
        resource_id=zone_id
    )
    
    return jsonify({'message': 'Safety zone deleted successfully'}), 200


# ==================== SYNC FROM HOTSPOTS ====================
@public_map_bp.route('/admin/sync', methods=['POST'])
@jwt_required()
def sync_from_hotspots():
    """Sync safety zones from active hotspots"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    min_reports = data.get('min_reports', 5)
    
    synced = PublicMapService.sync_zones_from_hotspots(
        min_reports=min_reports,
        created_by_user_id=user_id
    )
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Synced {len(synced)} safety zones from hotspots",
        resource_type='safety_zone'
    )
    
    return jsonify({
        'message': f'Synced {len(synced)} safety zones',
        'zones': [PublicMapService.zone_to_dict(z) for z in synced]
    }), 200
