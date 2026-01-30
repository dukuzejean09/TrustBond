"""
Incident Routes - Incident report endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import IncidentService, DeviceService, VerificationService, MLService, AuditService

incidents_bp = Blueprint('incidents', __name__)


# ==================== MOBILE APP ENDPOINTS ====================
@incidents_bp.route('/submit', methods=['POST'])
def submit_report():
    """Submit a new incident report (mobile app)"""
    data = request.get_json()
    
    # Validate required fields
    required = ['device_id', 'latitude', 'longitude', 'incident_type_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check device
    device = DeviceService.get_device_by_id(data['device_id'])
    if not device:
        return jsonify({'error': 'Device not registered'}), 404
    
    if device.is_blocked:
        return jsonify({'error': 'Device is blocked from submitting reports'}), 403
    
    try:
        # Create report
        report = IncidentService.create_report({
            'device_id': data['device_id'],
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'location_accuracy': data.get('location_accuracy'),
            'incident_type_id': data['incident_type_id'],
            'incident_category_id': data.get('incident_category_id'),
            'description': data.get('description'),
            'incident_occurred_at': data.get('incident_occurred_at'),
            'anonymous_id': data.get('anonymous_id'),
            'motion_detected': data.get('motion_detected'),
            'motion_confidence': data.get('motion_confidence'),
            'sensor_data': data.get('sensor_data'),
            'network_type': data.get('network_type'),
            'submission_duration_seconds': data.get('submission_duration_seconds')
        })
        
        # Run verification rules
        verification_result = VerificationService.run_verification(report.report_id)
        
        # Calculate ML trust score
        ml_result = MLService.score_report(report.report_id)
        
        # Update device statistics
        DeviceService.update_report_count(data['device_id'])
        
        return jsonify({
            'message': 'Report submitted successfully',
            'report_id': report.report_id,
            'tracking_code': report.tracking_code,
            'trust_score': float(report.ml_trust_score) if report.ml_trust_score else None,
            'trust_classification': report.trust_classification,
            'is_auto_rejected': report.is_auto_rejected
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to submit report'}), 500


@incidents_bp.route('/track/<tracking_code>', methods=['GET'])
def track_report(tracking_code):
    """Track report status by tracking code (mobile app)"""
    report = IncidentService.get_report_by_tracking_code(tracking_code)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    return jsonify({
        'report_id': report.report_id,
        'tracking_code': report.tracking_code,
        'status': report.status,
        'trust_classification': report.trust_classification,
        'police_verified': report.police_verified,
        'verification_result': report.verification_result,
        'submitted_at': report.reported_at.isoformat() if report.reported_at else None
    }), 200


@incidents_bp.route('/<report_id>/evidence', methods=['POST'])
def add_evidence(report_id):
    """Add evidence to a report (mobile app)"""
    data = request.get_json()
    
    report = IncidentService.get_report_by_id(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    try:
        evidence = IncidentService.add_evidence(
            report_id=report_id,
            evidence_type=data.get('evidence_type', 'image'),
            file_path=data.get('file_path'),
            file_hash=data.get('file_hash'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            captured_at=data.get('captured_at'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        
        return jsonify({
            'message': 'Evidence added successfully',
            'evidence': IncidentService.evidence_to_dict(evidence)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ==================== ADMIN/DASHBOARD ENDPOINTS ====================
@incidents_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_reports():
    """Get all incident reports with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('trust_classification'):
        filters['trust_classification'] = request.args.get('trust_classification')
    if request.args.get('district_id'):
        filters['district_id'] = request.args.get('district_id', type=int)
    if request.args.get('incident_type_id'):
        filters['incident_type_id'] = request.args.get('incident_type_id', type=int)
    if request.args.get('police_verified'):
        filters['police_verified'] = request.args.get('police_verified').lower() == 'true'
    if request.args.get('from_date'):
        filters['from_date'] = request.args.get('from_date')
    if request.args.get('to_date'):
        filters['to_date'] = request.args.get('to_date')
    
    pagination = IncidentService.get_all_reports(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'reports': [IncidentService.report_to_dict(r) for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@incidents_bp.route('/<report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """Get report details"""
    report = IncidentService.get_report_by_id(report_id)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    return jsonify({
        'report': IncidentService.report_to_dict(report, include_evidence=True, include_verification=True)
    }), 200


@incidents_bp.route('/<report_id>/verify', methods=['POST'])
@jwt_required()
def verify_report(report_id):
    """Verify a report"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    report = IncidentService.verify_report(
        report_id=report_id,
        verified_by_user_id=user_id,
        verification_result=data.get('result', 'valid'),
        verification_notes=data.get('notes')
    )
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Log the action
    AuditService.log_verification(user_id, report_id, data.get('result', 'valid'), data.get('notes'))
    
    return jsonify({
        'message': 'Report verified successfully',
        'report': IncidentService.report_to_dict(report)
    }), 200


@incidents_bp.route('/<report_id>/status', methods=['PUT'])
@jwt_required()
def update_report_status(report_id):
    """Update report status"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('status'):
        return jsonify({'error': 'status is required'}), 400
    
    report = IncidentService.update_report_status(
        report_id=report_id,
        status=data['status'],
        updated_by_user_id=user_id
    )
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Log the action
    AuditService.log_report_action(user_id, report_id, 'update', f"Status changed to {data['status']}")
    
    return jsonify({
        'message': 'Status updated successfully',
        'report': IncidentService.report_to_dict(report)
    }), 200


@incidents_bp.route('/<report_id>/assign', methods=['POST'])
@jwt_required()
def assign_report(report_id):
    """Assign report to an officer"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('officer_id'):
        return jsonify({'error': 'officer_id is required'}), 400
    
    report = IncidentService.assign_report(
        report_id=report_id,
        officer_id=data['officer_id'],
        assigned_by_user_id=user_id
    )
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Log the action
    AuditService.log_report_action(user_id, report_id, 'assign', f"Assigned to officer {data['officer_id']}")
    
    return jsonify({
        'message': 'Report assigned successfully',
        'report': IncidentService.report_to_dict(report)
    }), 200


@incidents_bp.route('/<report_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_report(report_id):
    """Resolve a report"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    report = IncidentService.resolve_report(
        report_id=report_id,
        resolution_notes=data.get('resolution_notes'),
        resolved_by_user_id=user_id
    )
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Log the action
    AuditService.log_report_action(user_id, report_id, 'resolve', data.get('resolution_notes'))
    
    return jsonify({
        'message': 'Report resolved successfully',
        'report': IncidentService.report_to_dict(report)
    }), 200


# ==================== INCIDENT TYPES/CATEGORIES ====================
@incidents_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all incident categories"""
    categories = IncidentService.get_all_categories()
    
    return jsonify({
        'categories': [IncidentService.category_to_dict(c, include_types=True) for c in categories]
    }), 200


@incidents_bp.route('/types', methods=['GET'])
def get_types():
    """Get all incident types"""
    category_id = request.args.get('category_id', type=int)
    
    types = IncidentService.get_types_by_category(category_id) if category_id else IncidentService.get_all_types()
    
    return jsonify({
        'types': [IncidentService.type_to_dict(t) for t in types]
    }), 200


@incidents_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Create a new incident category"""
    data = request.get_json()
    
    if not data.get('category_name'):
        return jsonify({'error': 'category_name is required'}), 400
    
    try:
        category = IncidentService.create_category(
            category_name=data['category_name'],
            category_name_kinyarwanda=data.get('category_name_kinyarwanda'),
            description=data.get('description'),
            icon=data.get('icon'),
            color=data.get('color'),
            severity_weight=data.get('severity_weight')
        )
        
        return jsonify({
            'message': 'Category created successfully',
            'category': IncidentService.category_to_dict(category)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@incidents_bp.route('/types', methods=['POST'])
@jwt_required()
def create_type():
    """Create a new incident type"""
    data = request.get_json()
    
    if not data.get('type_name') or not data.get('category_id'):
        return jsonify({'error': 'type_name and category_id are required'}), 400
    
    try:
        incident_type = IncidentService.create_type(
            category_id=data['category_id'],
            type_name=data['type_name'],
            type_name_kinyarwanda=data.get('type_name_kinyarwanda'),
            description=data.get('description'),
            severity_level=data.get('severity_level'),
            requires_evidence=data.get('requires_evidence'),
            auto_notify_police=data.get('auto_notify_police')
        )
        
        return jsonify({
            'message': 'Incident type created successfully',
            'type': IncidentService.type_to_dict(incident_type)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ==================== REPORT STATISTICS ====================
@incidents_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_report_statistics():
    """Get report statistics"""
    district_id = request.args.get('district_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    stats = IncidentService.get_report_statistics(district_id=district_id, days=days)
    
    return jsonify(stats), 200
