"""
Analytics Routes - Dashboard analytics and statistics endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import AnalyticsService, PoliceService, AuditService
from datetime import datetime

analytics_bp = Blueprint('analytics', __name__)


# ==================== DASHBOARD ====================
@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    district_id = request.args.get('district_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    stats = AnalyticsService.get_dashboard_stats(
        district_id=district_id,
        days=days
    )
    
    return jsonify({
        'stats': stats
    }), 200


@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """Get quick overview statistics"""
    stats = AnalyticsService.get_overview_stats()
    
    return jsonify({
        'overview': stats
    }), 200


# ==================== TIME SERIES ====================
@analytics_bp.route('/time-series/incidents', methods=['GET'])
@jwt_required()
def get_incident_time_series():
    """Get incident count time series"""
    district_id = request.args.get('district_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    interval = request.args.get('interval', 'day')  # day, week, month
    
    # Parse dates
    if start_date:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    data = AnalyticsService.get_incidents_time_series(
        district_id=district_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    return jsonify({
        'time_series': data
    }), 200


# ==================== GEOGRAPHIC ANALYSIS ====================
@analytics_bp.route('/geographic/distribution', methods=['GET'])
@jwt_required()
def get_geographic_distribution():
    """Get incident distribution by geography"""
    level = request.args.get('level', 'district')  # province, district, sector
    parent_id = request.args.get('parent_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    data = AnalyticsService.get_geographic_distribution(
        level=level,
        parent_id=parent_id,
        days=days
    )
    
    return jsonify({
        'distribution': data
    }), 200


@analytics_bp.route('/geographic/heatmap', methods=['GET'])
@jwt_required()
def get_heatmap_data():
    """Get heatmap data for geographic visualization"""
    district_id = request.args.get('district_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    data = AnalyticsService.get_heatmap_data(
        district_id=district_id,
        days=days
    )
    
    return jsonify({
        'heatmap': data
    }), 200


# ==================== TRENDS ====================
@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """Get incident type trends"""
    district_id = request.args.get('district_id', type=int)
    weeks = request.args.get('weeks', 12, type=int)
    
    data = AnalyticsService.get_incident_trends(
        district_id=district_id,
        weeks=weeks
    )
    
    return jsonify({
        'trends': data
    }), 200


@analytics_bp.route('/trends/categories', methods=['GET'])
@jwt_required()
def get_category_trends():
    """Get trends by incident category"""
    days = request.args.get('days', 30, type=int)
    
    data = AnalyticsService.get_category_trends(days=days)
    
    return jsonify({
        'trends': data
    }), 200


# ==================== COMPARISONS ====================
@analytics_bp.route('/compare/districts', methods=['GET'])
@jwt_required()
def compare_districts():
    """Compare statistics across districts"""
    district_ids = request.args.get('district_ids', '')
    days = request.args.get('days', 30, type=int)
    
    ids = [int(x) for x in district_ids.split(',') if x.strip()]
    
    if not ids:
        return jsonify({'error': 'district_ids parameter required'}), 400
    
    data = AnalyticsService.compare_districts(
        district_ids=ids,
        days=days
    )
    
    return jsonify({
        'comparison': data
    }), 200


@analytics_bp.route('/compare/periods', methods=['GET'])
@jwt_required()
def compare_periods():
    """Compare statistics between two time periods"""
    period1_start = request.args.get('period1_start')
    period1_end = request.args.get('period1_end')
    period2_start = request.args.get('period2_start')
    period2_end = request.args.get('period2_end')
    district_id = request.args.get('district_id', type=int)
    
    if not all([period1_start, period1_end, period2_start, period2_end]):
        return jsonify({'error': 'All period dates required'}), 400
    
    data = AnalyticsService.compare_time_periods(
        period1_start=datetime.fromisoformat(period1_start.replace('Z', '+00:00')),
        period1_end=datetime.fromisoformat(period1_end.replace('Z', '+00:00')),
        period2_start=datetime.fromisoformat(period2_start.replace('Z', '+00:00')),
        period2_end=datetime.fromisoformat(period2_end.replace('Z', '+00:00')),
        district_id=district_id
    )
    
    return jsonify({
        'comparison': data
    }), 200


# ==================== VERIFICATION STATS ====================
@analytics_bp.route('/verification', methods=['GET'])
@jwt_required()
def get_verification_stats():
    """Get verification statistics"""
    days = request.args.get('days', 30, type=int)
    
    data = AnalyticsService.get_verification_stats(days=days)
    
    return jsonify({
        'verification': data
    }), 200


# ==================== DEVICE STATS ====================
@analytics_bp.route('/devices', methods=['GET'])
@jwt_required()
def get_device_stats():
    """Get device registration statistics"""
    days = request.args.get('days', 30, type=int)
    
    data = AnalyticsService.get_device_stats(days=days)
    
    return jsonify({
        'devices': data
    }), 200


# ==================== HOTSPOT STATS ====================
@analytics_bp.route('/hotspots', methods=['GET'])
@jwt_required()
def get_hotspot_stats():
    """Get hotspot statistics"""
    district_id = request.args.get('district_id', type=int)
    
    data = AnalyticsService.get_hotspot_stats(district_id=district_id)
    
    return jsonify({
        'hotspots': data
    }), 200


# ==================== RESPONSE TIME ====================
@analytics_bp.route('/response-time', methods=['GET'])
@jwt_required()
def get_response_time_stats():
    """Get response time statistics"""
    days = request.args.get('days', 30, type=int)
    district_id = request.args.get('district_id', type=int)
    
    data = AnalyticsService.get_response_time_stats(
        days=days,
        district_id=district_id
    )
    
    return jsonify({
        'response_time': data
    }), 200


# ==================== DAILY STATISTICS ====================
@analytics_bp.route('/daily', methods=['GET'])
@jwt_required()
def get_daily_statistics():
    """Get daily statistics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    district_id = request.args.get('district_id', type=int)
    
    if start_date:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
    if end_date:
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
    
    data = AnalyticsService.get_daily_statistics(
        start_date=start_date,
        end_date=end_date,
        district_id=district_id
    )
    
    return jsonify({
        'daily_statistics': data
    }), 200


@analytics_bp.route('/daily/generate', methods=['POST'])
@jwt_required()
def generate_daily_stats():
    """Generate daily statistics for a date range"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    # Check permission
    if not PoliceService.has_permission(user_id, 'manage_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if start_date:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
    if end_date:
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
    
    count = AnalyticsService.generate_daily_statistics(
        start_date=start_date,
        end_date=end_date
    )
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='create',
        description=f"Generated {count} daily statistics records",
        resource_type='daily_statistic'
    )
    
    return jsonify({
        'message': f'Generated {count} daily statistics records'
    }), 200


# ==================== EXPORT ====================
@analytics_bp.route('/export', methods=['POST'])
@jwt_required()
def export_analytics():
    """Export analytics data"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    report_type = data.get('report_type', 'summary')  # summary, detailed, geographic
    format_type = data.get('format', 'json')  # json, csv
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    district_id = data.get('district_id')
    
    if start_date:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    export_data = AnalyticsService.export_analytics(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        district_id=district_id
    )
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='read',
        description=f"Exported {report_type} analytics report",
        resource_type='analytics'
    )
    
    return jsonify({
        'export': export_data
    }), 200
