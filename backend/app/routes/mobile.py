"""
Mobile-specific API endpoints for TrustBond mobile app.
These endpoints are optimized for mobile usage and include public endpoints.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from app import db
from app.models import Report, ReportStatus, ReportPriority, CrimeCategory, User, Alert, AlertStatus, AlertType
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import math

mobile_bp = Blueprint('mobile', __name__)


# ==================== Public Endpoints (No Auth Required) ====================

@mobile_bp.route('/stats', methods=['GET'])
def get_public_stats():
    """Get public statistics for the mobile app home screen"""
    # Total reports
    total_reports = Report.query.count()
    
    # Resolved reports
    resolved_reports = Report.query.filter(Report.status == ReportStatus.RESOLVED).count()
    
    # Active alerts
    now = datetime.utcnow()
    active_alerts = Alert.query.filter(
        Alert.status == AlertStatus.ACTIVE,
        or_(Alert.valid_until.is_(None), Alert.valid_until > now)
    ).count()
    
    # Reports this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    reports_this_month = Report.query.filter(Report.created_at >= month_ago).count()
    
    # Resolution rate
    resolution_rate = (resolved_reports / total_reports * 100) if total_reports > 0 else 0
    
    # Average response time (in hours) - simplified calculation
    avg_response_time = 24  # Default 24 hours
    
    return jsonify({
        'success': True,
        'stats': {
            'totalReports': total_reports,
            'resolvedReports': resolved_reports,
            'activeAlerts': active_alerts,
            'reportsThisMonth': reports_this_month,
            'resolutionRate': round(resolution_rate, 1),
            'avgResponseTime': avg_response_time
        }
    }), 200


@mobile_bp.route('/emergency-contacts', methods=['GET'])
def get_emergency_contacts():
    """Get emergency contact numbers for Rwanda"""
    contacts = [
        {
            'id': '1',
            'name': 'Police Emergency',
            'number': '112',
            'description': 'Rwanda National Police Emergency Line',
            'icon': 'police',
            'isPrimary': True
        },
        {
            'id': '2',
            'name': 'Ambulance',
            'number': '912',
            'description': 'Emergency Medical Services',
            'icon': 'medical',
            'isPrimary': True
        },
        {
            'id': '3',
            'name': 'Fire Brigade',
            'number': '112',
            'description': 'Fire Emergency Services',
            'icon': 'fire',
            'isPrimary': True
        },
        {
            'id': '4',
            'name': 'Traffic Police',
            'number': '113',
            'description': 'Traffic Incident Reporting',
            'icon': 'traffic',
            'isPrimary': False
        },
        {
            'id': '5',
            'name': 'Gender-Based Violence',
            'number': '3512',
            'description': 'GBV Hotline - Free & Confidential',
            'icon': 'support',
            'isPrimary': False
        },
        {
            'id': '6',
            'name': 'Child Helpline',
            'number': '116',
            'description': 'Child Protection Services',
            'icon': 'child',
            'isPrimary': False
        },
        {
            'id': '7',
            'name': 'RIB (Investigation)',
            'number': '9191',
            'description': 'Rwanda Investigation Bureau',
            'icon': 'investigation',
            'isPrimary': False
        },
        {
            'id': '8',
            'name': 'Anti-Corruption',
            'number': '997',
            'description': 'Report Corruption',
            'icon': 'corruption',
            'isPrimary': False
        }
    ]
    
    return jsonify({
        'success': True,
        'contacts': contacts
    }), 200


@mobile_bp.route('/nearby-reports', methods=['GET'])
def get_nearby_reports():
    """Get anonymous summary of nearby reports (public, no details)"""
    lat = request.args.get('latitude', type=float)
    lng = request.args.get('longitude', type=float)
    radius_km = request.args.get('radius', 5, type=float)  # Default 5km
    
    if lat is None or lng is None:
        return jsonify({
            'success': False,
            'error': 'Latitude and longitude are required'
        }), 400
    
    # Calculate bounding box for initial filtering
    lat_range = radius_km / 111  # ~111km per degree latitude
    lng_range = radius_km / (111 * math.cos(math.radians(lat)))
    
    # Get reports within bounding box from last 30 days
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    reports = Report.query.filter(
        and_(
            Report.latitude.isnot(None),
            Report.longitude.isnot(None),
            Report.latitude.between(lat - lat_range, lat + lat_range),
            Report.longitude.between(lng - lng_range, lng + lng_range),
            Report.created_at >= month_ago
        )
    ).all()
    
    # Calculate actual distance and filter
    nearby_summary = {}
    for report in reports:
        distance = _haversine_distance(lat, lng, report.latitude, report.longitude)
        if distance <= radius_km:
            category = report.category.value
            if category not in nearby_summary:
                nearby_summary[category] = {'count': 0, 'recent': []}
            nearby_summary[category]['count'] += 1
            
            # Keep only last 3 for each category (anonymized)
            if len(nearby_summary[category]['recent']) < 3:
                nearby_summary[category]['recent'].append({
                    'date': report.created_at.strftime('%Y-%m-%d'),
                    'distance': round(distance, 1),
                    'status': report.status.value
                })
    
    return jsonify({
        'success': True,
        'radius': radius_km,
        'summary': nearby_summary,
        'totalNearby': sum(cat['count'] for cat in nearby_summary.values())
    }), 200


@mobile_bp.route('/crime-categories', methods=['GET'])
def get_crime_categories():
    """Get all available crime categories with descriptions"""
    categories = [
        {
            'id': 'theft',
            'name': 'Theft',
            'description': 'Stealing property without force',
            'icon': 'theft',
            'priority': 'medium'
        },
        {
            'id': 'assault',
            'name': 'Assault',
            'description': 'Physical attack or threat of attack',
            'icon': 'assault',
            'priority': 'high'
        },
        {
            'id': 'robbery',
            'name': 'Robbery',
            'description': 'Theft using force or intimidation',
            'icon': 'robbery',
            'priority': 'high'
        },
        {
            'id': 'fraud',
            'name': 'Fraud',
            'description': 'Deception for financial gain',
            'icon': 'fraud',
            'priority': 'medium'
        },
        {
            'id': 'vandalism',
            'name': 'Vandalism',
            'description': 'Deliberate destruction of property',
            'icon': 'vandalism',
            'priority': 'low'
        },
        {
            'id': 'domestic_violence',
            'name': 'Domestic Violence',
            'description': 'Violence within household or family',
            'icon': 'domestic',
            'priority': 'critical'
        },
        {
            'id': 'cybercrime',
            'name': 'Cybercrime',
            'description': 'Online fraud, hacking, or scams',
            'icon': 'cyber',
            'priority': 'medium'
        },
        {
            'id': 'drug_related',
            'name': 'Drug Related',
            'description': 'Drug trafficking or abuse',
            'icon': 'drugs',
            'priority': 'high'
        },
        {
            'id': 'traffic_violation',
            'name': 'Traffic Violation',
            'description': 'Dangerous driving or accidents',
            'icon': 'traffic',
            'priority': 'medium'
        },
        {
            'id': 'corruption',
            'name': 'Corruption',
            'description': 'Bribery or abuse of power',
            'icon': 'corruption',
            'priority': 'high'
        },
        {
            'id': 'other',
            'name': 'Other',
            'description': 'Other incidents not listed',
            'icon': 'other',
            'priority': 'medium'
        }
    ]
    
    return jsonify({
        'success': True,
        'categories': categories
    }), 200


@mobile_bp.route('/districts', methods=['GET'])
def get_districts():
    """Get all Rwanda districts organized by province"""
    provinces = {
        'Kigali City': ['Gasabo', 'Kicukiro', 'Nyarugenge'],
        'Eastern Province': ['Bugesera', 'Gatsibo', 'Kayonza', 'Kirehe', 'Ngoma', 'Nyagatare', 'Rwamagana'],
        'Western Province': ['Karongi', 'Ngororero', 'Nyabihu', 'Nyamasheke', 'Rubavu', 'Rusizi', 'Rutsiro'],
        'Northern Province': ['Burera', 'Gakenke', 'Gicumbi', 'Musanze', 'Rulindo'],
        'Southern Province': ['Gisagara', 'Huye', 'Kamonyi', 'Muhanga', 'Nyamagabe', 'Nyanza', 'Nyaruguru', 'Ruhango']
    }
    
    return jsonify({
        'success': True,
        'provinces': provinces
    }), 200


@mobile_bp.route('/app-config', methods=['GET'])
def get_app_config():
    """Get app configuration for mobile client"""
    return jsonify({
        'success': True,
        'config': {
            'appName': 'TrustBond',
            'version': '1.0.0',
            'minVersion': '1.0.0',
            'maintenanceMode': False,
            'features': {
                'anonymousReporting': True,
                'locationTracking': True,
                'offlineMode': True,
                'pushNotifications': True,
                'evidenceUpload': True
            },
            'limits': {
                'maxDescriptionLength': 1000,
                'maxEvidenceFiles': 10,
                'maxFileSizeMB': 10,
                'maxVideoSeconds': 60,
                'maxAudioSeconds': 120
            },
            'supportEmail': 'support@trustbond.rw',
            'privacyPolicyUrl': 'https://trustbond.rw/privacy',
            'termsUrl': 'https://trustbond.rw/terms'
        }
    }), 200


@mobile_bp.route('/report-tips', methods=['GET'])
def get_report_tips():
    """Get tips for effective crime reporting"""
    tips = [
        {
            'id': '1',
            'title': 'Be Specific',
            'description': 'Provide as much detail as possible about what happened, when, and where.',
            'icon': 'detail'
        },
        {
            'id': '2',
            'title': 'Include Location',
            'description': 'Enable GPS or describe the location clearly with landmarks.',
            'icon': 'location'
        },
        {
            'id': '3',
            'title': 'Add Evidence',
            'description': 'Photos, videos, or audio recordings can help with investigation.',
            'icon': 'evidence'
        },
        {
            'id': '4',
            'title': 'Note Time',
            'description': 'Record the exact or approximate time the incident occurred.',
            'icon': 'time'
        },
        {
            'id': '5',
            'title': 'Stay Safe',
            'description': 'Your safety is priority. Report from a safe location.',
            'icon': 'safety'
        },
        {
            'id': '6',
            'title': 'Save Tracking Code',
            'description': 'Keep your tracking code to check the status of your report.',
            'icon': 'tracking'
        }
    ]
    
    return jsonify({
        'success': True,
        'tips': tips
    }), 200


@mobile_bp.route('/faqs', methods=['GET'])
def get_faqs():
    """Get frequently asked questions"""
    faqs = [
        {
            'id': '1',
            'question': 'Is my report anonymous?',
            'answer': 'Yes, you can submit reports without creating an account. Your identity will not be linked to the report unless you choose to provide contact information.',
            'category': 'privacy'
        },
        {
            'id': '2',
            'question': 'How do I track my report?',
            'answer': 'After submitting an anonymous report, you will receive a tracking code. Use this code in the "Track Report" section to check your report status.',
            'category': 'tracking'
        },
        {
            'id': '3',
            'question': 'What types of incidents can I report?',
            'answer': 'You can report various crimes including theft, assault, fraud, domestic violence, drug-related activities, traffic violations, and more.',
            'category': 'reporting'
        },
        {
            'id': '4',
            'question': 'How long does it take to process a report?',
            'answer': 'Reports are typically reviewed within 24-48 hours. Critical incidents are prioritized for immediate attention.',
            'category': 'process'
        },
        {
            'id': '5',
            'question': 'Can I add evidence after submitting?',
            'answer': 'Currently, you cannot add evidence to an existing anonymous report. Make sure to include all evidence at the time of submission.',
            'category': 'evidence'
        },
        {
            'id': '6',
            'question': 'Is the app available offline?',
            'answer': 'Yes, you can draft reports offline. They will be submitted automatically when you regain internet connection.',
            'category': 'features'
        },
        {
            'id': '7',
            'question': 'What should I do in an emergency?',
            'answer': 'For immediate emergencies, call 112 (Police) or 912 (Ambulance) directly. The app is for reporting incidents, not emergency response.',
            'category': 'emergency'
        }
    ]
    
    return jsonify({
        'success': True,
        'faqs': faqs
    }), 200


# ==================== Helper Functions ====================

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c
