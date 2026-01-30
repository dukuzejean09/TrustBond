from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Report, ReportStatus, ReportPriority, CrimeCategory, User, UserRole
from datetime import datetime

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('', methods=['GET'])
@jwt_required()
def get_reports():
    """Get reports with filtering and pagination"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    category = request.args.get('category')
    priority = request.args.get('priority')
    district = request.args.get('district')
    search = request.args.get('search')
    
    query = Report.query
    
    # Citizens can only see their own reports
    if user.role == UserRole.CITIZEN:
        query = query.filter(Report.reporter_id == user_id)
    # Officers see reports assigned to them or in their station
    elif user.role == UserRole.OFFICER:
        query = query.filter(
            db.or_(
                Report.assigned_to == user_id,
                Report.station == user.station
            )
        )
    # Admins see all reports
    
    if status:
        query = query.filter(Report.status == ReportStatus(status))
    
    if category:
        query = query.filter(Report.category == CrimeCategory(category))
    
    if priority:
        query = query.filter(Report.priority == ReportPriority(priority))
    
    if district:
        query = query.filter(Report.district == district)
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Report.title.ilike(search_term),
                Report.description.ilike(search_term),
                Report.report_number.ilike(search_term)
            )
        )
    
    pagination = query.order_by(Report.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # For dashboard views (admins/officers), hide reporter identity for privacy
    # Citizens viewing their own reports can see their info
    hide_reporter = user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OFFICER]
    
    return jsonify({
        'reports': [report.to_dict(include_reporter=not hide_reporter) for report in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@reports_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """Get a specific report"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Check access permissions
    if user.role == UserRole.CITIZEN and report.reporter_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # For dashboard views (admins/officers), hide reporter identity for privacy
    hide_reporter = user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OFFICER]
    
    return jsonify({'report': report.to_dict(include_reporter=not hide_reporter)}), 200


@reports_bp.route('', methods=['POST'])
@jwt_required()
def create_report():
    """Create a new crime report (authenticated users)"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    required_fields = ['title', 'description', 'category']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        category = CrimeCategory(data['category'])
    except ValueError:
        return jsonify({'error': 'Invalid category'}), 400
    
    report = Report(
        report_number=Report.generate_report_number(),
        title=data['title'],
        description=data['description'],
        category=category,
        priority=ReportPriority(data.get('priority', 'medium')),
        province=data.get('province'),
        district=data.get('district'),
        sector=data.get('sector'),
        cell=data.get('cell'),
        village=data.get('village'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        location_description=data.get('locationDescription'),
        incident_date=datetime.fromisoformat(data['incidentDate']) if data.get('incidentDate') else None,
        incident_time=data.get('incidentTime'),
        reporter_id=user_id,
        is_anonymous=data.get('isAnonymous', False),
        attachments=data.get('attachments', []),
        status_history=[{
            'status': 'pending',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Report submitted'
        }]
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({
        'message': 'Report submitted successfully',
        'report': report.to_dict()
    }), 201


@reports_bp.route('/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_report(report_id):
    """Update a report"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Citizens can only update their own pending reports
    if user.role == UserRole.CITIZEN:
        if report.reporter_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        if report.status != ReportStatus.PENDING:
            return jsonify({'error': 'Cannot update report after it has been reviewed'}), 400
    
    # Update fields
    updateable_fields = ['title', 'description', 'locationDescription', 'attachments']
    field_mapping = {'locationDescription': 'location_description'}
    
    for field in updateable_fields:
        if field in data:
            attr_name = field_mapping.get(field, field)
            setattr(report, attr_name, data[field])
    
    # Admin/Officer only updates
    if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]:
        if 'status' in data:
            new_status = ReportStatus(data['status'])
            if new_status != report.status:
                history = report.status_history or []
                history.append({
                    'status': new_status.value,
                    'timestamp': datetime.utcnow().isoformat(),
                    'updatedBy': user_id,
                    'note': data.get('statusNote', '')
                })
                report.status_history = history
                report.status = new_status
                
                if new_status == ReportStatus.RESOLVED:
                    report.resolved_at = datetime.utcnow()
        
        if 'priority' in data:
            report.priority = ReportPriority(data['priority'])
        
        if 'assignedTo' in data:
            report.assigned_to = data['assignedTo']
        
        if 'station' in data:
            report.station = data['station']
        
        if 'resolutionNotes' in data:
            report.resolution_notes = data['resolutionNotes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Report updated successfully',
        'report': report.to_dict()
    }), 200


@reports_bp.route('/<int:report_id>/assign', methods=['POST'])
@jwt_required()
def assign_report(report_id):
    """Assign a report to an officer"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Admin access required'}), 403
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    officer_id = data.get('officerId')
    officer = User.query.get(officer_id)
    
    if not officer or officer.role != UserRole.OFFICER:
        return jsonify({'error': 'Invalid officer'}), 400
    
    report.assigned_to = officer_id
    report.station = officer.station
    
    if report.status == ReportStatus.PENDING:
        report.status = ReportStatus.UNDER_REVIEW
        history = report.status_history or []
        history.append({
            'status': 'under_review',
            'timestamp': datetime.utcnow().isoformat(),
            'updatedBy': user_id,
            'note': f'Assigned to officer {officer.first_name} {officer.last_name}'
        })
        report.status_history = history
    
    db.session.commit()
    
    return jsonify({
        'message': 'Report assigned successfully',
        'report': report.to_dict()
    }), 200


@reports_bp.route('/my-reports', methods=['GET'])
@jwt_required()
def get_my_reports():
    """Get current user's reports"""
    user_id = int(get_jwt_identity())
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Report.query.filter_by(reporter_id=user_id).order_by(
        Report.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'reports': [report.to_dict() for report in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@reports_bp.route('/anonymous', methods=['POST'])
def create_anonymous_report():
    """Create an anonymous crime report (no authentication required)"""
    data = request.get_json()
    
    required_fields = ['title', 'description', 'category']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        category = CrimeCategory(data['category'])
    except ValueError:
        return jsonify({'error': 'Invalid category'}), 400
    
    # Generate a tracking code for anonymous reports
    import secrets
    tracking_code = f"ANON-{secrets.token_hex(4).upper()}"
    
    report = Report(
        report_number=Report.generate_report_number(),
        title=data['title'],
        description=data['description'],
        category=category,
        priority=ReportPriority(data.get('priority', 'medium')),
        province=data.get('province'),
        district=data.get('district'),
        sector=data.get('sector'),
        cell=data.get('cell'),
        village=data.get('village'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        location_description=data.get('locationDescription'),
        incident_date=datetime.fromisoformat(data['incidentDate']) if data.get('incidentDate') else None,
        incident_time=data.get('incidentTime'),
        reporter_id=None,  # Anonymous - no user linked
        is_anonymous=True,
        anonymous_contact=data.get('anonymousContact'),  # Optional contact for follow-up
        tracking_code=tracking_code,
        attachments=data.get('attachments', []),
        status_history=[{
            'status': 'pending',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Anonymous report submitted'
        }]
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({
        'message': 'Anonymous report submitted successfully',
        'trackingCode': tracking_code,
        'report': report.to_dict()
    }), 201


@reports_bp.route('/track/<tracking_code>', methods=['GET'])
def track_anonymous_report(tracking_code):
    """Track an anonymous report by tracking code"""
    report = Report.query.filter_by(tracking_code=tracking_code).first()
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Return limited info for anonymous tracking
    return jsonify({
        'trackingCode': tracking_code,
        'reportNumber': report.report_number,
        'status': report.status.value,
        'category': report.category.value,
        'createdAt': report.created_at.isoformat() if report.created_at else None,
        'statusHistory': report.status_history or [],
        'resolutionNotes': report.resolution_notes if report.status == ReportStatus.RESOLVED else None
    }), 200


# ==================== BATCH OPERATIONS ====================

@reports_bp.route('/batch/status', methods=['POST'])
@jwt_required()
def batch_update_status():
    """
    Update status of multiple reports at once.
    
    Request Body:
    - report_ids: List of report IDs
    - status: New status
    - note: Optional status change note
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Staff access required'}), 403
    
    data = request.get_json()
    report_ids = data.get('report_ids', [])
    new_status_str = data.get('status')
    note = data.get('note', '')
    
    if not report_ids or not new_status_str:
        return jsonify({'error': 'report_ids and status are required'}), 400
    
    try:
        new_status = ReportStatus(new_status_str)
    except ValueError:
        return jsonify({'error': 'Invalid status'}), 400
    
    updated = []
    failed = []
    
    for report_id in report_ids:
        report = Report.query.get(report_id)
        if not report:
            failed.append({'id': report_id, 'reason': 'Report not found'})
            continue
        
        old_status = report.status.value
        report.status = new_status
        
        # Update status history
        history = report.status_history or []
        history.append({
            'status': new_status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'updatedBy': user_id,
            'note': note
        })
        report.status_history = history
        
        if new_status == ReportStatus.RESOLVED:
            report.resolved_at = datetime.utcnow()
        
        updated.append({
            'id': report_id,
            'reportNumber': report.report_number,
            'oldStatus': old_status,
            'newStatus': new_status.value
        })
    
    db.session.commit()
    
    return jsonify({
        'message': f'Updated {len(updated)} reports',
        'updated': updated,
        'failed': failed
    }), 200


@reports_bp.route('/batch/assign', methods=['POST'])
@jwt_required()
def batch_assign_reports():
    """
    Assign multiple reports to an officer.
    
    Request Body:
    - report_ids: List of report IDs
    - officer_id: ID of officer to assign
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    report_ids = data.get('report_ids', [])
    officer_id = data.get('officer_id')
    
    if not report_ids or not officer_id:
        return jsonify({'error': 'report_ids and officer_id are required'}), 400
    
    officer = User.query.get(officer_id)
    if not officer or officer.role != UserRole.OFFICER:
        return jsonify({'error': 'Invalid officer'}), 400
    
    updated = []
    failed = []
    
    for report_id in report_ids:
        report = Report.query.get(report_id)
        if not report:
            failed.append({'id': report_id, 'reason': 'Report not found'})
            continue
        
        report.assigned_to = officer_id
        report.station = officer.station
        
        # Update status if pending
        if report.status == ReportStatus.PENDING:
            report.status = ReportStatus.UNDER_REVIEW
            history = report.status_history or []
            history.append({
                'status': 'under_review',
                'timestamp': datetime.utcnow().isoformat(),
                'updatedBy': user_id,
                'note': f'Assigned to officer {officer.first_name} {officer.last_name}'
            })
            report.status_history = history
        
        updated.append({
            'id': report_id,
            'reportNumber': report.report_number,
            'assignedTo': officer_id
        })
    
    db.session.commit()
    
    return jsonify({
        'message': f'Assigned {len(updated)} reports to {officer.first_name} {officer.last_name}',
        'updated': updated,
        'failed': failed
    }), 200


@reports_bp.route('/batch/priority', methods=['POST'])
@jwt_required()
def batch_update_priority():
    """
    Update priority of multiple reports.
    
    Request Body:
    - report_ids: List of report IDs
    - priority: New priority (low, medium, high, critical)
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Staff access required'}), 403
    
    data = request.get_json()
    report_ids = data.get('report_ids', [])
    new_priority_str = data.get('priority')
    
    if not report_ids or not new_priority_str:
        return jsonify({'error': 'report_ids and priority are required'}), 400
    
    try:
        new_priority = ReportPriority(new_priority_str)
    except ValueError:
        return jsonify({'error': 'Invalid priority'}), 400
    
    updated = []
    failed = []
    
    for report_id in report_ids:
        report = Report.query.get(report_id)
        if not report:
            failed.append({'id': report_id, 'reason': 'Report not found'})
            continue
        
        old_priority = report.priority.value
        report.priority = new_priority
        
        updated.append({
            'id': report_id,
            'reportNumber': report.report_number,
            'oldPriority': old_priority,
            'newPriority': new_priority.value
        })
    
    db.session.commit()
    
    return jsonify({
        'message': f'Updated priority for {len(updated)} reports',
        'updated': updated,
        'failed': failed
    }), 200


@reports_bp.route('/batch/delete', methods=['DELETE'])
@jwt_required()
def batch_delete_reports():
    """
    Delete multiple reports (admin only).
    
    Query Parameter:
    - ids: Comma-separated list of report IDs
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != UserRole.SUPER_ADMIN:
        return jsonify({'error': 'Super admin access required'}), 403
    
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return jsonify({'error': 'Report IDs are required'}), 400
    
    try:
        report_ids = [int(id.strip()) for id in ids_param.split(',')]
    except ValueError:
        return jsonify({'error': 'Invalid report IDs format'}), 400
    
    deleted = []
    failed = []
    
    for report_id in report_ids:
        report = Report.query.get(report_id)
        if not report:
            failed.append({'id': report_id, 'reason': 'Report not found'})
            continue
        
        deleted.append({
            'id': report_id,
            'reportNumber': report.report_number
        })
        db.session.delete(report)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Deleted {len(deleted)} reports',
        'deleted': deleted,
        'failed': failed
    }), 200
