"""
Analytics and Statistics API Routes.

Provides endpoints for:
- Detailed analytics reports
- Data exports (CSV, JSON)
- Trend analysis
- Performance metrics
"""

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    Report, ReportStatus, ReportPriority, CrimeCategory,
    User, UserRole, Alert, AlertStatus,
    TrustScore, Hotspot, ActivityLog, ActivityType, ActivityLogger
)
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import json
import csv
import io

analytics_bp = Blueprint('analytics', __name__)


def admin_required(f):
    """Decorator to require admin role."""
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


# ============================================================================
# COMPREHENSIVE ANALYTICS
# ============================================================================

@analytics_bp.route('/overview', methods=['GET'])
@admin_required
def get_analytics_overview():
    """Get comprehensive analytics overview."""
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Overall statistics
    total_reports = Report.query.count()
    reports_in_period = Report.query.filter(Report.created_at >= cutoff).count()
    
    # Status distribution
    status_counts = dict(db.session.query(
        Report.status, func.count(Report.id)
    ).group_by(Report.status).all())
    
    # Category distribution
    category_counts = dict(db.session.query(
        Report.category, func.count(Report.id)
    ).group_by(Report.category).all())
    
    # Priority distribution
    priority_counts = dict(db.session.query(
        Report.priority, func.count(Report.id)
    ).group_by(Report.priority).all())
    
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter(User.last_login >= cutoff).count()
    new_users = User.query.filter(User.created_at >= cutoff).count()
    
    # Resolution metrics
    resolved_reports = Report.query.filter(Report.status == ReportStatus.RESOLVED).count()
    resolution_rate = (resolved_reports / total_reports * 100) if total_reports > 0 else 0
    
    # Average resolution time
    resolved_with_time = db.session.query(
        func.avg(func.extract('epoch', Report.resolved_at - Report.created_at))
    ).filter(
        Report.resolved_at.isnot(None),
        Report.created_at.isnot(None)
    ).scalar()
    
    avg_resolution_hours = round(resolved_with_time / 3600, 1) if resolved_with_time else None
    
    # Anonymous vs registered reports
    anonymous_reports = Report.query.filter(Report.is_anonymous == True).count()
    registered_reports = Report.query.filter(Report.is_anonymous == False).count()
    
    # Trust score distribution
    trust_scores = db.session.query(
        TrustScore.classification, func.count(TrustScore.id)
    ).group_by(TrustScore.classification).all()
    
    return jsonify({
        'period': {
            'days': days,
            'startDate': cutoff.isoformat(),
            'endDate': datetime.utcnow().isoformat()
        },
        'reports': {
            'total': total_reports,
            'inPeriod': reports_in_period,
            'byStatus': {k.value: v for k, v in status_counts.items()},
            'byCategory': {k.value: v for k, v in category_counts.items()},
            'byPriority': {k.value: v for k, v in priority_counts.items()},
            'anonymous': anonymous_reports,
            'registered': registered_reports
        },
        'users': {
            'total': total_users,
            'active': active_users,
            'newInPeriod': new_users
        },
        'performance': {
            'resolutionRate': round(resolution_rate, 2),
            'avgResolutionHours': avg_resolution_hours
        },
        'verification': {
            'trustDistribution': {k.value: v for k, v in trust_scores} if trust_scores else {}
        }
    }), 200


@analytics_bp.route('/trends', methods=['GET'])
@admin_required
def get_trends():
    """Get trend data over time."""
    days = request.args.get('days', 30, type=int)
    interval = request.args.get('interval', 'day')  # 'day', 'week', 'month'
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    if interval == 'day':
        date_trunc = func.date(Report.created_at)
    elif interval == 'week':
        date_trunc = func.date_trunc('week', Report.created_at)
    else:
        date_trunc = func.date_trunc('month', Report.created_at)
    
    # Reports over time
    report_trends = db.session.query(
        date_trunc.label('period'),
        func.count(Report.id).label('count')
    ).filter(
        Report.created_at >= cutoff
    ).group_by(date_trunc).order_by(date_trunc).all()
    
    # Resolved reports over time
    resolution_trends = db.session.query(
        func.date(Report.resolved_at).label('period'),
        func.count(Report.id).label('count')
    ).filter(
        Report.resolved_at >= cutoff
    ).group_by(func.date(Report.resolved_at)).order_by(func.date(Report.resolved_at)).all()
    
    # Category trends
    category_trends = db.session.query(
        date_trunc.label('period'),
        Report.category,
        func.count(Report.id).label('count')
    ).filter(
        Report.created_at >= cutoff
    ).group_by(date_trunc, Report.category).order_by(date_trunc).all()
    
    # Format category trends
    category_data = {}
    for row in category_trends:
        period_str = str(row.period)
        if period_str not in category_data:
            category_data[period_str] = {}
        category_data[period_str][row.category.value] = row.count
    
    return jsonify({
        'reportTrends': [
            {'period': str(r.period), 'count': r.count} for r in report_trends
        ],
        'resolutionTrends': [
            {'period': str(r.period), 'count': r.count} for r in resolution_trends
        ],
        'categoryTrends': category_data,
        'interval': interval,
        'days': days
    }), 200


@analytics_bp.route('/geographic', methods=['GET'])
@admin_required
def get_geographic_analytics():
    """Get geographic distribution of reports."""
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # By district
    by_district = db.session.query(
        Report.district,
        func.count(Report.id).label('count'),
        func.avg(
            db.case(
                (Report.status == ReportStatus.RESOLVED, 1),
                else_=0
            )
        ).label('resolution_rate')
    ).filter(
        Report.created_at >= cutoff,
        Report.district.isnot(None)
    ).group_by(Report.district).all()
    
    # By province
    by_province = db.session.query(
        Report.province,
        func.count(Report.id).label('count')
    ).filter(
        Report.created_at >= cutoff,
        Report.province.isnot(None)
    ).group_by(Report.province).all()
    
    # Hotspot areas (based on GPS coordinates)
    hotspot_query = db.session.query(
        func.round(Report.latitude, 2).label('lat'),
        func.round(Report.longitude, 2).label('lng'),
        func.count(Report.id).label('count')
    ).filter(
        Report.created_at >= cutoff,
        Report.latitude.isnot(None),
        Report.longitude.isnot(None)
    ).group_by(
        func.round(Report.latitude, 2),
        func.round(Report.longitude, 2)
    ).having(func.count(Report.id) > 2).all()
    
    return jsonify({
        'byDistrict': [
            {
                'district': r.district,
                'count': r.count,
                'resolutionRate': round(float(r.resolution_rate or 0) * 100, 1)
            } for r in by_district
        ],
        'byProvince': [
            {'province': r.province, 'count': r.count} for r in by_province
        ],
        'hotspots': [
            {'latitude': float(r.lat), 'longitude': float(r.lng), 'count': r.count}
            for r in hotspot_query
        ],
        'days': days
    }), 200


@analytics_bp.route('/officer-performance', methods=['GET'])
@admin_required
def get_officer_performance():
    """Get detailed officer performance metrics."""
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    officers = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        User.badge_number,
        User.station,
        func.count(Report.id).label('total_assigned'),
        func.sum(db.case((Report.status == ReportStatus.RESOLVED, 1), else_=0)).label('resolved'),
        func.sum(db.case((Report.status == ReportStatus.INVESTIGATING, 1), else_=0)).label('investigating'),
        func.avg(
            db.case(
                (Report.resolved_at.isnot(None),
                 func.extract('epoch', Report.resolved_at - Report.created_at) / 3600),
                else_=None
            )
        ).label('avg_resolution_hours')
    ).outerjoin(
        Report, Report.assigned_to == User.id
    ).filter(
        User.role == UserRole.OFFICER
    ).group_by(
        User.id, User.first_name, User.last_name, User.badge_number, User.station
    ).all()
    
    return jsonify({
        'officers': [
            {
                'id': o.id,
                'name': f'{o.first_name} {o.last_name}',
                'badgeNumber': o.badge_number,
                'station': o.station,
                'totalAssigned': o.total_assigned or 0,
                'resolved': o.resolved or 0,
                'investigating': o.investigating or 0,
                'resolutionRate': round((o.resolved or 0) / max(o.total_assigned or 1, 1) * 100, 1),
                'avgResolutionHours': round(float(o.avg_resolution_hours or 0), 1)
            } for o in officers
        ],
        'days': days
    }), 200


# ============================================================================
# DATA EXPORT
# ============================================================================

@analytics_bp.route('/export/reports', methods=['GET'])
@admin_required
def export_reports():
    """Export reports data to CSV or JSON."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    format_type = request.args.get('format', 'csv')  # 'csv' or 'json'
    days = request.args.get('days', 30, type=int)
    status = request.args.get('status')
    category = request.args.get('category')
    district = request.args.get('district')
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = Report.query.filter(Report.created_at >= cutoff)
    
    if status:
        query = query.filter(Report.status == ReportStatus(status))
    if category:
        query = query.filter(Report.category == CrimeCategory(category))
    if district:
        query = query.filter(Report.district == district)
    
    reports = query.order_by(Report.created_at.desc()).all()
    
    # Log the export
    ActivityLogger.log_export(
        f'reports_{format_type}',
        user=user,
        request=request,
        metadata={'days': days, 'count': len(reports)}
    )
    db.session.commit()
    
    if format_type == 'json':
        export_data = []
        for r in reports:
            export_data.append({
                'reportNumber': r.report_number,
                'title': r.title,
                'category': r.category.value,
                'status': r.status.value,
                'priority': r.priority.value,
                'district': r.district,
                'sector': r.sector,
                'createdAt': r.created_at.isoformat() if r.created_at else None,
                'resolvedAt': r.resolved_at.isoformat() if r.resolved_at else None,
                'isAnonymous': r.is_anonymous
            })
        
        return jsonify({
            'exportedAt': datetime.utcnow().isoformat(),
            'count': len(export_data),
            'data': export_data
        }), 200
    
    else:  # CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Report Number', 'Title', 'Category', 'Status', 'Priority',
            'District', 'Sector', 'Created At', 'Resolved At', 'Is Anonymous'
        ])
        
        # Data rows
        for r in reports:
            writer.writerow([
                r.report_number,
                r.title,
                r.category.value,
                r.status.value,
                r.priority.value,
                r.district,
                r.sector,
                r.created_at.isoformat() if r.created_at else '',
                r.resolved_at.isoformat() if r.resolved_at else '',
                'Yes' if r.is_anonymous else 'No'
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=reports_export_{datetime.utcnow().strftime("%Y%m%d")}.csv'
            }
        )


@analytics_bp.route('/export/statistics', methods=['GET'])
@admin_required
def export_statistics():
    """Export summary statistics."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Gather comprehensive statistics
    stats = {
        'exportedAt': datetime.utcnow().isoformat(),
        'period': {
            'days': days,
            'start': cutoff.isoformat(),
            'end': datetime.utcnow().isoformat()
        },
        'summary': {
            'totalReports': Report.query.count(),
            'reportsInPeriod': Report.query.filter(Report.created_at >= cutoff).count(),
            'pendingReports': Report.query.filter(Report.status == ReportStatus.PENDING).count(),
            'resolvedReports': Report.query.filter(Report.status == ReportStatus.RESOLVED).count(),
            'totalUsers': User.query.count(),
            'activeOfficers': User.query.filter(
                User.role == UserRole.OFFICER,
                User.last_login >= cutoff
            ).count()
        },
        'byCategory': {},
        'byDistrict': {},
        'byStatus': {}
    }
    
    # Category breakdown
    categories = db.session.query(
        Report.category, func.count(Report.id)
    ).filter(Report.created_at >= cutoff).group_by(Report.category).all()
    stats['byCategory'] = {c.value: count for c, count in categories}
    
    # District breakdown
    districts = db.session.query(
        Report.district, func.count(Report.id)
    ).filter(
        Report.created_at >= cutoff,
        Report.district.isnot(None)
    ).group_by(Report.district).all()
    stats['byDistrict'] = {d: count for d, count in districts}
    
    # Status breakdown
    statuses = db.session.query(
        Report.status, func.count(Report.id)
    ).group_by(Report.status).all()
    stats['byStatus'] = {s.value: count for s, count in statuses}
    
    # Log export
    ActivityLogger.log_export(
        'statistics_json',
        user=user,
        request=request,
        metadata={'days': days}
    )
    db.session.commit()
    
    return jsonify(stats), 200


# ============================================================================
# ACTIVITY LOGS
# ============================================================================

@analytics_bp.route('/activity-logs', methods=['GET'])
@admin_required
def get_activity_logs():
    """Get activity logs for auditing."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    activity_type = request.args.get('type')
    user_id_filter = request.args.get('user_id', type=int)
    entity_type = request.args.get('entity_type')
    days = request.args.get('days', 7, type=int)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = ActivityLog.query.filter(ActivityLog.created_at >= cutoff)
    
    if activity_type:
        query = query.filter(ActivityLog.activity_type == ActivityType(activity_type))
    if user_id_filter:
        query = query.filter(ActivityLog.user_id == user_id_filter)
    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
    
    pagination = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@analytics_bp.route('/activity-summary', methods=['GET'])
@admin_required
def get_activity_summary():
    """Get summary of recent activity."""
    days = request.args.get('days', 7, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Count by activity type
    by_type = db.session.query(
        ActivityLog.activity_type,
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.created_at >= cutoff
    ).group_by(ActivityLog.activity_type).all()
    
    # Most active users
    active_users = db.session.query(
        ActivityLog.user_email,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= cutoff,
        ActivityLog.user_email.isnot(None)
    ).group_by(ActivityLog.user_email).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'byType': {t.value: count for t, count in by_type},
        'mostActiveUsers': [
            {'email': email, 'actionCount': count}
            for email, count in active_users
        ],
        'totalActions': sum(count for _, count in by_type),
        'days': days
    }), 200
