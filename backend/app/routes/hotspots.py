"""
Hotspot Routes - Crime hotspot detection and management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import HotspotService, NotificationService, AuditService

hotspots_bp = Blueprint('hotspots', __name__)


# ==================== HOTSPOT RETRIEVAL ====================
@hotspots_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_hotspots():
    """Get all hotspots with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {}
    if request.args.get('district_id'):
        filters['district_id'] = request.args.get('district_id', type=int)
    if request.args.get('sector_id'):
        filters['sector_id'] = request.args.get('sector_id', type=int)
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('risk_level'):
        filters['risk_level'] = request.args.get('risk_level')
    if request.args.get('is_active'):
        filters['is_active'] = request.args.get('is_active').lower() == 'true'
    
    pagination = HotspotService.get_all_hotspots(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'hotspots': [HotspotService.hotspot_to_dict(h) for h in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@hotspots_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_hotspots():
    """Get all active hotspots"""
    district_id = request.args.get('district_id', type=int)
    
    hotspots = HotspotService.get_active_hotspots(district_id=district_id)
    
    return jsonify({
        'hotspots': [HotspotService.hotspot_to_dict(h) for h in hotspots]
    }), 200


@hotspots_bp.route('/<hotspot_id>', methods=['GET'])
@jwt_required()
def get_hotspot(hotspot_id):
    """Get hotspot details"""
    include_reports = request.args.get('include_reports', 'false').lower() == 'true'
    
    hotspot = HotspotService.get_hotspot_by_id(hotspot_id)
    
    if not hotspot:
        return jsonify({'error': 'Hotspot not found'}), 404
    
    return jsonify({
        'hotspot': HotspotService.hotspot_to_dict(hotspot, include_reports=include_reports)
    }), 200


# ==================== CLUSTERING ====================
@hotspots_bp.route('/detect', methods=['POST'])
@jwt_required()
def run_detection():
    """Run hotspot detection (DBSCAN clustering)"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    try:
        result = HotspotService.run_clustering(
            district_id=data.get('district_id'),
            epsilon_meters=data.get('epsilon_meters', 500),
            min_samples=data.get('min_samples', 3),
            trust_weight_enabled=data.get('trust_weight_enabled', True),
            min_trust_score=data.get('min_trust_score', 30),
            days_back=data.get('days_back', 30),
            triggered_by_user_id=user_id
        )
        
        # Log the action
        AuditService.log_activity(
            user_id=user_id,
            activity_type='create',
            description=f"Ran hotspot detection - found {result['clusters_found']} clusters",
            resource_type='hotspot',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': 'Hotspot detection completed',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hotspots_bp.route('/runs', methods=['GET'])
@jwt_required()
def get_clustering_runs():
    """Get clustering run history"""
    limit = request.args.get('limit', 20, type=int)
    
    runs = HotspotService.get_clustering_runs(limit=limit)
    
    return jsonify({
        'runs': [HotspotService.clustering_run_to_dict(r) for r in runs]
    }), 200


@hotspots_bp.route('/runs/<run_id>', methods=['GET'])
@jwt_required()
def get_clustering_run(run_id):
    """Get clustering run details"""
    run = HotspotService.get_clustering_run(run_id)
    
    if not run:
        return jsonify({'error': 'Clustering run not found'}), 404
    
    return jsonify({
        'run': HotspotService.clustering_run_to_dict(run)
    }), 200


# ==================== HOTSPOT MANAGEMENT ====================
@hotspots_bp.route('/<hotspot_id>/assign', methods=['POST'])
@jwt_required()
def assign_hotspot(hotspot_id):
    """Assign hotspot to an officer"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('officer_id'):
        return jsonify({'error': 'officer_id is required'}), 400
    
    hotspot = HotspotService.assign_hotspot(
        hotspot_id=hotspot_id,
        officer_id=data['officer_id'],
        unit=data.get('unit')
    )
    
    if not hotspot:
        return jsonify({'error': 'Hotspot not found'}), 404
    
    # Send notification to assigned officer
    from app.services import PoliceService
    officer = PoliceService.get_user_by_id(data['officer_id'])
    if officer:
        NotificationService.notify_hotspot_assigned(hotspot, officer)
    
    # Log the action
    AuditService.log_hotspot_action(
        user_id, hotspot_id, 'assign', 
        f"Assigned to officer {data['officer_id']}"
    )
    
    return jsonify({
        'message': 'Hotspot assigned successfully',
        'hotspot': HotspotService.hotspot_to_dict(hotspot)
    }), 200


@hotspots_bp.route('/<hotspot_id>/status', methods=['PUT'])
@jwt_required()
def update_hotspot_status(hotspot_id):
    """Update hotspot status"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('status'):
        return jsonify({'error': 'status is required'}), 400
    
    hotspot = HotspotService.update_hotspot_status(
        hotspot_id=hotspot_id,
        status=data['status']
    )
    
    if not hotspot:
        return jsonify({'error': 'Hotspot not found'}), 404
    
    # Log the action
    AuditService.log_hotspot_action(
        user_id, hotspot_id, 'update',
        f"Status changed to {data['status']}"
    )
    
    return jsonify({
        'message': 'Hotspot status updated',
        'hotspot': HotspotService.hotspot_to_dict(hotspot)
    }), 200


@hotspots_bp.route('/<hotspot_id>/address', methods=['POST'])
@jwt_required()
def address_hotspot(hotspot_id):
    """Mark hotspot as addressed"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    hotspot = HotspotService.address_hotspot(
        hotspot_id=hotspot_id,
        resolution_notes=data.get('resolution_notes'),
        addressed_by_user_id=user_id
    )
    
    if not hotspot:
        return jsonify({'error': 'Hotspot not found'}), 404
    
    # Log the action
    AuditService.log_hotspot_action(
        user_id, hotspot_id, 'resolve',
        data.get('resolution_notes')
    )
    
    return jsonify({
        'message': 'Hotspot marked as addressed',
        'hotspot': HotspotService.hotspot_to_dict(hotspot)
    }), 200


@hotspots_bp.route('/<hotspot_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_hotspot(hotspot_id):
    """Deactivate a hotspot"""
    user_id = get_jwt_identity()
    
    hotspot = HotspotService.deactivate_hotspot(hotspot_id)
    
    if not hotspot:
        return jsonify({'error': 'Hotspot not found'}), 404
    
    # Log the action
    AuditService.log_hotspot_action(user_id, hotspot_id, 'delete', 'Deactivated')
    
    return jsonify({
        'message': 'Hotspot deactivated',
        'hotspot': HotspotService.hotspot_to_dict(hotspot)
    }), 200


# ==================== HOTSPOT HISTORY ====================
@hotspots_bp.route('/<hotspot_id>/history', methods=['GET'])
@jwt_required()
def get_hotspot_history(hotspot_id):
    """Get hotspot history"""
    limit = request.args.get('limit', 30, type=int)
    
    history = HotspotService.get_hotspot_history(hotspot_id, limit=limit)
    
    return jsonify({
        'hotspot_id': hotspot_id,
        'history': [{
            'snapshot_date': h.snapshot_date.isoformat() if h.snapshot_date else None,
            'report_count': h.report_count,
            'avg_trust_score': float(h.avg_trust_score) if h.avg_trust_score else None,
            'risk_level': h.risk_level,
            'priority_score': float(h.priority_score) if h.priority_score else None,
            'report_count_change': h.report_count_change,
            'trend_direction': h.trend_direction
        } for h in history]
    }), 200


@hotspots_bp.route('/<hotspot_id>/snapshot', methods=['POST'])
@jwt_required()
def create_snapshot(hotspot_id):
    """Create a history snapshot"""
    history = HotspotService.create_history_snapshot(hotspot_id)
    
    if not history:
        return jsonify({'error': 'Hotspot not found'}), 404
    
    return jsonify({
        'message': 'Snapshot created',
        'snapshot_date': history.snapshot_date.isoformat()
    }), 201


# ==================== PUBLIC SAFETY MAP ====================
@hotspots_bp.route('/public', methods=['GET'])
def get_public_hotspots():
    """Get anonymized hotspots for public safety map (no auth required)"""
    district_id = request.args.get('district_id', type=int)
    min_reports = request.args.get('min_reports', 3, type=int)
    
    hotspots = HotspotService.get_public_hotspots(
        district_id=district_id,
        min_reports=min_reports
    )
    
    return jsonify({
        'hotspots': hotspots,
        'generated_at': __import__('datetime').datetime.utcnow().isoformat()
    }), 200
