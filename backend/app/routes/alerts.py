from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Alert, AlertType, AlertStatus, User, UserRole
from datetime import datetime

alerts_bp = Blueprint('alerts', __name__)


def admin_or_officer_required(f):
    """Decorator to require admin or officer role"""
    from functools import wraps
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]:
            return jsonify({'error': 'Admin or officer access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@alerts_bp.route('', methods=['GET'])
def get_alerts():
    """Get all active alerts (public endpoint)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    alert_type = request.args.get('type')
    district = request.args.get('district')
    
    query = Alert.query.filter(Alert.status == AlertStatus.ACTIVE)
    
    # Filter by validity
    now = datetime.utcnow()
    query = query.filter(
        db.or_(
            Alert.valid_until.is_(None),
            Alert.valid_until > now
        )
    )
    
    if alert_type:
        query = query.filter(Alert.alert_type == AlertType(alert_type))
    
    if district:
        query = query.filter(
            db.or_(
                Alert.district == district,
                Alert.is_nationwide == True
            )
        )
    
    pagination = query.order_by(Alert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'alerts': [alert.to_dict() for alert in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@alerts_bp.route('/all', methods=['GET'])
@admin_or_officer_required
def get_all_alerts():
    """Get all alerts including expired/cancelled (admin/officer only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Alert.query
    
    if status:
        query = query.filter(Alert.status == AlertStatus(status))
    
    pagination = query.order_by(Alert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'alerts': [alert.to_dict() for alert in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@alerts_bp.route('/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    return jsonify({'alert': alert.to_dict()}), 200


@alerts_bp.route('', methods=['POST'])
@admin_or_officer_required
def create_alert():
    """Create a new alert"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    required_fields = ['title', 'message', 'alertType']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        alert_type = AlertType(data['alertType'])
    except ValueError:
        return jsonify({'error': 'Invalid alert type'}), 400
    
    alert = Alert(
        title=data['title'],
        message=data['message'],
        alert_type=alert_type,
        province=data.get('province'),
        district=data.get('district'),
        sector=data.get('sector'),
        is_nationwide=data.get('isNationwide', False),
        valid_from=datetime.fromisoformat(data['validFrom']) if data.get('validFrom') else datetime.utcnow(),
        valid_until=datetime.fromisoformat(data['validUntil']) if data.get('validUntil') else None,
        created_by=user_id
    )
    
    db.session.add(alert)
    db.session.commit()
    
    return jsonify({
        'message': 'Alert created successfully',
        'alert': alert.to_dict()
    }), 201


@alerts_bp.route('/<int:alert_id>', methods=['PUT'])
@admin_or_officer_required
def update_alert(alert_id):
    """Update an alert"""
    data = request.get_json()
    
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    # Update fields
    if 'title' in data:
        alert.title = data['title']
    if 'message' in data:
        alert.message = data['message']
    if 'alertType' in data:
        alert.alert_type = AlertType(data['alertType'])
    if 'status' in data:
        alert.status = AlertStatus(data['status'])
    if 'province' in data:
        alert.province = data['province']
    if 'district' in data:
        alert.district = data['district']
    if 'sector' in data:
        alert.sector = data['sector']
    if 'isNationwide' in data:
        alert.is_nationwide = data['isNationwide']
    if 'validUntil' in data:
        alert.valid_until = datetime.fromisoformat(data['validUntil']) if data['validUntil'] else None
    
    db.session.commit()
    
    return jsonify({
        'message': 'Alert updated successfully',
        'alert': alert.to_dict()
    }), 200


@alerts_bp.route('/<int:alert_id>', methods=['DELETE'])
@admin_or_officer_required
def delete_alert(alert_id):
    """Delete an alert"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    db.session.delete(alert)
    db.session.commit()
    
    return jsonify({'message': 'Alert deleted successfully'}), 200


@alerts_bp.route('/<int:alert_id>/cancel', methods=['POST'])
@admin_or_officer_required
def cancel_alert(alert_id):
    """Cancel an alert"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    alert.status = AlertStatus.CANCELLED
    db.session.commit()
    
    return jsonify({
        'message': 'Alert cancelled successfully',
        'alert': alert.to_dict()
    }), 200
