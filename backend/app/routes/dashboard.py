from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Report, ReportStatus, ReportPriority, CrimeCategory, User, UserRole, Alert, AlertStatus
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


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


@dashboard_bp.route('/stats', methods=['GET'])
@admin_or_officer_required
def get_stats():
    """Get dashboard statistics"""
    # Total counts
    total_reports = Report.query.count()
    total_users = User.query.count()
    total_officers = User.query.filter(User.role == UserRole.OFFICER).count()
    active_alerts = Alert.query.filter(Alert.status == AlertStatus.ACTIVE).count()
    
    # Reports by status
    pending_reports = Report.query.filter(Report.status == ReportStatus.PENDING).count()
    investigating_reports = Report.query.filter(Report.status == ReportStatus.INVESTIGATING).count()
    resolved_reports = Report.query.filter(Report.status == ReportStatus.RESOLVED).count()
    
    # This week's reports
    week_ago = datetime.utcnow() - timedelta(days=7)
    reports_this_week = Report.query.filter(Report.created_at >= week_ago).count()
    
    # This month's reports
    month_ago = datetime.utcnow() - timedelta(days=30)
    reports_this_month = Report.query.filter(Report.created_at >= month_ago).count()
    
    # Resolution rate
    resolution_rate = (resolved_reports / total_reports * 100) if total_reports > 0 else 0
    
    return jsonify({
        'totalReports': total_reports,
        'totalUsers': total_users,
        'totalOfficers': total_officers,
        'activeAlerts': active_alerts,
        'pendingReports': pending_reports,
        'investigatingReports': investigating_reports,
        'resolvedReports': resolved_reports,
        'reportsThisWeek': reports_this_week,
        'reportsThisMonth': reports_this_month,
        'resolutionRate': round(resolution_rate, 2)
    }), 200


@dashboard_bp.route('/reports-by-category', methods=['GET'])
@admin_or_officer_required
def get_reports_by_category():
    """Get reports grouped by category"""
    results = db.session.query(
        Report.category,
        func.count(Report.id).label('count')
    ).group_by(Report.category).all()
    
    data = [{'category': r.category.value, 'count': r.count} for r in results]
    
    return jsonify({'data': data}), 200


@dashboard_bp.route('/reports-by-status', methods=['GET'])
@admin_or_officer_required
def get_reports_by_status():
    """Get reports grouped by status"""
    results = db.session.query(
        Report.status,
        func.count(Report.id).label('count')
    ).group_by(Report.status).all()
    
    data = [{'status': r.status.value, 'count': r.count} for r in results]
    
    return jsonify({'data': data}), 200


@dashboard_bp.route('/reports-by-district', methods=['GET'])
@admin_or_officer_required
def get_reports_by_district():
    """Get reports grouped by district"""
    results = db.session.query(
        Report.district,
        func.count(Report.id).label('count')
    ).filter(Report.district.isnot(None)).group_by(Report.district).all()
    
    data = [{'district': r.district, 'count': r.count} for r in results]
    
    return jsonify({'data': data}), 200


@dashboard_bp.route('/reports-by-priority', methods=['GET'])
@admin_or_officer_required
def get_reports_by_priority():
    """Get reports grouped by priority"""
    results = db.session.query(
        Report.priority,
        func.count(Report.id).label('count')
    ).group_by(Report.priority).all()
    
    data = [{'priority': r.priority.value, 'count': r.count} for r in results]
    
    return jsonify({'data': data}), 200


@dashboard_bp.route('/reports-trend', methods=['GET'])
@admin_or_officer_required
def get_reports_trend():
    """Get reports trend over the last 30 days"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    results = db.session.query(
        func.date(Report.created_at).label('date'),
        func.count(Report.id).label('count')
    ).filter(
        Report.created_at >= thirty_days_ago
    ).group_by(
        func.date(Report.created_at)
    ).order_by(
        func.date(Report.created_at)
    ).all()
    
    data = [{'date': str(r.date), 'count': r.count} for r in results]
    
    return jsonify({'data': data}), 200


@dashboard_bp.route('/recent-reports', methods=['GET'])
@admin_or_officer_required
def get_recent_reports():
    """Get recent reports"""
    reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    
    # Hide reporter identity for privacy in dashboard view
    return jsonify({
        'reports': [report.to_dict(include_reporter=False) for report in reports]
    }), 200


@dashboard_bp.route('/recent-alerts', methods=['GET'])
@admin_or_officer_required
def get_recent_alerts():
    """Get recent alerts"""
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    
    return jsonify({
        'alerts': [alert.to_dict() for alert in alerts]
    }), 200


@dashboard_bp.route('/officer-performance', methods=['GET'])
@admin_or_officer_required
def get_officer_performance():
    """Get officer performance metrics"""
    results = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        User.badge_number,
        func.count(Report.id).label('assigned_cases'),
        func.sum(
            db.case(
                (Report.status == ReportStatus.RESOLVED, 1),
                else_=0
            )
        ).label('resolved_cases')
    ).join(
        Report, Report.assigned_to == User.id, isouter=True
    ).filter(
        User.role == UserRole.OFFICER
    ).group_by(
        User.id, User.first_name, User.last_name, User.badge_number
    ).all()
    
    data = [{
        'id': r.id,
        'name': f'{r.first_name} {r.last_name}',
        'badgeNumber': r.badge_number,
        'assignedCases': r.assigned_cases or 0,
        'resolvedCases': r.resolved_cases or 0,
        'resolutionRate': round((r.resolved_cases or 0) / r.assigned_cases * 100, 2) if r.assigned_cases else 0
    } for r in results]
    
    return jsonify({'data': data}), 200
