"""
ML and Verification API Routes.

Provides endpoints for:
- Report verification and trust scoring
- Hotspot detection and visualization
- ML model status and training
- Public safety map data
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app import db
from app.models import Report, User, UserRole, DeviceProfile, TrustScore, Hotspot
from app.models.trust_score import TrustClassification, VerificationStatus
from app.models.hotspot import HotspotSeverity
from app.verification import RuleBasedVerifier, TrustClassification as VerifyClassification
from app.ml import MLTrustScorer, HotspotDetector

ml_bp = Blueprint('ml', __name__)

# Initialize ML components
verifier = RuleBasedVerifier()
trust_scorer = MLTrustScorer()
hotspot_detector = HotspotDetector()


# ============================================================================
# VERIFICATION ENDPOINTS
# ============================================================================

@ml_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_report():
    """
    Verify a report using rule-based and ML systems.
    
    Request Body:
    - report_data: Report information to verify
    - device_fingerprint: Optional device identifier
    
    Returns verification results with trust classification.
    """
    data = request.get_json()
    report_data = data.get('report_data', {})
    device_fingerprint = data.get('device_fingerprint')
    
    # Get device history if fingerprint provided
    device_history = None
    if device_fingerprint:
        device = DeviceProfile.query.filter_by(fingerprint=device_fingerprint).first()
        if device:
            device_history = device.get_history()
    
    # Run rule-based verification
    rule_result = verifier.verify_report(
        report_data,
        device_fingerprint,
        device_history
    )
    
    # Run ML scoring
    ml_result = trust_scorer.predict_trust(
        report_data,
        rule_result,
        device_history
    )
    
    # Get combined score
    combined_score, classification = trust_scorer.get_combined_score(
        report_data,
        rule_result,
        device_history
    )
    
    return jsonify({
        'verification': {
            'classification': classification,
            'combined_score': round(combined_score, 3),
            'rule_based_score': round(rule_result['overall_score'], 3),
            'ml_score': round(ml_result['ml_score'], 3) if ml_result['ml_score'] else None,
            'ml_confidence': round(ml_result['confidence'], 3),
            'ml_method': ml_result['method'],
        },
        'rule_results': rule_result['rule_results'],
        'passed_rules': rule_result['passed_rules'],
        'failed_rules': rule_result['failed_rules'],
        'recommendations': rule_result['recommendations'],
        'timestamp': datetime.utcnow().isoformat(),
    }), 200


@ml_bp.route('/verify/<int:report_id>', methods=['POST'])
@jwt_required()
def verify_existing_report(report_id):
    """
    Run verification on an existing report in the database.
    
    Stores the verification result in TrustScore table.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Only admins and officers can verify existing reports
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Build report data from database record
    report_data = {
        'latitude': report.latitude,
        'longitude': report.longitude,
        'district': report.district,
        'timestamp': report.created_at.isoformat() if report.created_at else None,
        'incident_type': report.category.value if report.category else None,
        'attachments': report.attachments or [],
    }
    
    # Get device history (from DeviceProfile if available)
    device_history = None
    # In a full implementation, we'd link reports to device profiles
    
    # Run verification
    rule_result = verifier.verify_report(report_data, None, device_history)
    ml_result = trust_scorer.predict_trust(report_data, rule_result, device_history)
    combined_score, classification = trust_scorer.get_combined_score(
        report_data, rule_result, device_history
    )
    
    # Store/update TrustScore
    trust_score = TrustScore.query.filter_by(report_id=report_id).first()
    if not trust_score:
        trust_score = TrustScore(report_id=report_id, final_score=combined_score)
        db.session.add(trust_score)
    
    # Update scores
    trust_score.final_score = combined_score
    trust_score.ml_score = ml_result['ml_score']
    trust_score.ml_confidence = ml_result['confidence']
    trust_score.classification = TrustClassification(classification.upper())
    trust_score.verification_status = VerificationStatus.VERIFIED
    
    # Store rule details
    trust_score.gps_score = rule_result['rule_results'].get('gps_valid', {}).get('score', 0.5)
    trust_score.timestamp_score = rule_result['rule_results'].get('timestamp_valid', {}).get('score', 0.5)
    trust_score.spatial_temporal_score = rule_result['rule_results'].get('location_consistent', {}).get('score', 0.5)
    trust_score.evidence_score = rule_result['rule_results'].get('evidence_quality', {}).get('score', 0.5)
    trust_score.device_trust_score = rule_result['rule_results'].get('device_history', {}).get('score', 0.5)
    
    trust_score.verified_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Report verified successfully',
        'report_id': report_id,
        'verification': trust_score.to_dict(),
    }), 200


@ml_bp.route('/trust-score/<int:report_id>', methods=['GET'])
@jwt_required()
def get_trust_score(report_id):
    """Get the trust score for a specific report."""
    trust_score = TrustScore.query.filter_by(report_id=report_id).first()
    
    if not trust_score:
        return jsonify({'error': 'No verification data found for this report'}), 404
    
    return jsonify({'trust_score': trust_score.to_dict()}), 200


# ============================================================================
# HOTSPOT ENDPOINTS
# ============================================================================

@ml_bp.route('/hotspots', methods=['GET'])
@jwt_required()
def get_hotspots():
    """
    Get detected crime hotspots.
    
    Query Parameters:
    - incident_type: Filter by incident type
    - days: Analysis window (default 30)
    - refresh: Force recalculation (default false)
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Only admins and officers can view detailed hotspots
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident_type = request.args.get('incident_type')
    days = request.args.get('days', 30, type=int)
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    # Check if we have recent cached hotspots
    cache_cutoff = datetime.utcnow() - timedelta(hours=6)
    
    if not refresh:
        # Try to get from database
        query = Hotspot.query.filter(Hotspot.created_at > cache_cutoff)
        if incident_type:
            query = query.filter(Hotspot.dominant_type == incident_type)
        
        cached = query.order_by(Hotspot.severity.desc()).all()
        if cached:
            return jsonify({
                'hotspots': [h.to_dict() for h in cached],
                'source': 'cache',
                'cached_at': cached[0].created_at.isoformat(),
            }), 200
    
    # Calculate fresh hotspots
    cutoff = datetime.utcnow() - timedelta(days=days)
    reports = Report.query.filter(Report.created_at > cutoff).all()
    
    report_data = [
        {
            'latitude': r.latitude,
            'longitude': r.longitude,
            'incident_type': r.category.value if r.category else 'unknown',
            'timestamp': r.created_at.isoformat(),
        }
        for r in reports if r.latitude and r.longitude
    ]
    
    # Detect hotspots
    hotspot_detector.window_days = days
    hotspots = hotspot_detector.detect_hotspots(report_data, incident_type)
    
    # Store in database
    for h in hotspots:
        db_hotspot = Hotspot(
            center_latitude=h['center_latitude'],
            center_longitude=h['center_longitude'],
            radius_km=h['radius_km'],
            report_count=h['report_count'],
            severity=HotspotSeverity(h['severity']),
            dominant_type=h['dominant_type'],
            incident_types=h['incident_types'],
            first_report=datetime.fromisoformat(h['first_report'].replace('Z', '+00:00')),
            last_report=datetime.fromisoformat(h['last_report'].replace('Z', '+00:00')),
            analysis_window_days=h['analysis_window_days'],
        )
        db.session.add(db_hotspot)
    
    db.session.commit()
    
    # Get statistics
    stats = hotspot_detector.get_statistics(hotspots)
    
    return jsonify({
        'hotspots': hotspots,
        'statistics': stats,
        'source': 'calculated',
        'parameters': {
            'window_days': days,
            'incident_type': incident_type,
            'total_reports_analyzed': len(report_data),
        }
    }), 200


@ml_bp.route('/hotspots/by-type', methods=['GET'])
@jwt_required()
def get_hotspots_by_type():
    """Get hotspots grouped by incident type."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    reports = Report.query.filter(Report.created_at > cutoff).all()
    
    report_data = [
        {
            'latitude': r.latitude,
            'longitude': r.longitude,
            'incident_type': r.category.value if r.category else 'unknown',
            'timestamp': r.created_at.isoformat(),
        }
        for r in reports if r.latitude and r.longitude
    ]
    
    hotspot_detector.window_days = days
    results = hotspot_detector.detect_by_type(report_data)
    
    return jsonify({
        'hotspots_by_type': results,
        'incident_types': list(results.keys()),
        'window_days': days,
    }), 200


# ============================================================================
# PUBLIC SAFETY MAP ENDPOINTS
# ============================================================================

@ml_bp.route('/public/safety-map', methods=['GET'])
def get_public_safety_map():
    """
    Get anonymized hotspot data for public community safety map.
    
    This endpoint is PUBLIC (no authentication required).
    Data is anonymized to protect privacy while informing community.
    """
    days = request.args.get('days', 30, type=int)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    reports = Report.query.filter(Report.created_at > cutoff).all()
    
    report_data = [
        {
            'latitude': r.latitude,
            'longitude': r.longitude,
            'incident_type': r.category.value if r.category else 'unknown',
            'timestamp': r.created_at.isoformat(),
        }
        for r in reports if r.latitude and r.longitude
    ]
    
    # Get anonymized public hotspots
    hotspot_detector.window_days = days
    public_hotspots = hotspot_detector.get_public_hotspots(report_data, anonymize=True)
    
    # Get general statistics (no sensitive data)
    total_hotspots = len(public_hotspots)
    severity_counts = {}
    for h in public_hotspots:
        sev = h['severity_label']
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    return jsonify({
        'hotspots': public_hotspots,
        'statistics': {
            'total_areas': total_hotspots,
            'severity_distribution': severity_counts,
        },
        'metadata': {
            'analysis_period': f'Last {days} days',
            'last_updated': datetime.utcnow().isoformat(),
            'disclaimer': 'Data is anonymized and generalized for community safety awareness.',
        }
    }), 200


@ml_bp.route('/public/safety-tips', methods=['GET'])
def get_safety_tips():
    """
    Get safety tips based on current hotspot data.
    
    This endpoint is PUBLIC (no authentication required).
    """
    # Get current hotspots
    days = 30
    cutoff = datetime.utcnow() - timedelta(days=days)
    reports = Report.query.filter(Report.created_at > cutoff).all()
    
    report_data = [
        {
            'latitude': r.latitude,
            'longitude': r.longitude,
            'incident_type': r.category.value if r.category else 'unknown',
            'timestamp': r.created_at.isoformat(),
        }
        for r in reports if r.latitude and r.longitude
    ]
    
    hotspots = hotspot_detector.detect_hotspots(report_data)
    
    # Generate tips based on prevalent crime types
    type_counts = {}
    for h in hotspots:
        for t, count in h.get('incident_types', {}).items():
            type_counts[t] = type_counts.get(t, 0) + count
    
    # Safety tips by crime type
    tips_db = {
        'theft': [
            'Keep valuables out of sight in vehicles',
            'Be aware of your surroundings when using phones in public',
            'Secure homes and businesses with proper locks',
        ],
        'burglary': [
            'Install adequate lighting around your property',
            'Consider community watch programs',
            'Report suspicious activity immediately',
        ],
        'assault': [
            'Avoid isolated areas, especially at night',
            'Travel in groups when possible',
            'Keep emergency contacts readily available',
        ],
        'robbery': [
            'Avoid displaying expensive items in public',
            'Use well-lit and populated routes',
            'If confronted, prioritize personal safety over possessions',
        ],
        'fraud': [
            'Never share personal banking information',
            'Verify identity of callers claiming to be officials',
            'Report suspicious financial requests',
        ],
    }
    
    # Select relevant tips
    relevant_tips = []
    for crime_type, count in sorted(type_counts.items(), key=lambda x: -x[1])[:3]:
        if crime_type in tips_db:
            relevant_tips.extend([
                {'category': crime_type, 'tip': tip}
                for tip in tips_db[crime_type]
            ])
    
    # Add general tips
    general_tips = [
        {'category': 'general', 'tip': 'Report incidents promptly to help keep your community safe'},
        {'category': 'general', 'tip': 'Stay informed about safety updates in your area'},
        {'category': 'general', 'tip': 'Know the emergency contact numbers: Police 112'},
    ]
    
    return jsonify({
        'tips': relevant_tips[:9] + general_tips,
        'based_on_analysis': True,
        'last_updated': datetime.utcnow().isoformat(),
    }), 200


# ============================================================================
# ML MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@ml_bp.route('/model/status', methods=['GET'])
@jwt_required()
def get_model_status():
    """Get the status of ML models."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'trust_scorer': trust_scorer.get_model_info(),
        'hotspot_detector': hotspot_detector.get_config(),
        'verifier': {
            'thresholds': {
                'trusted': verifier.TRUSTED_THRESHOLD,
                'delayed': verifier.DELAYED_THRESHOLD,
            },
            'rule_weights': verifier.RULE_WEIGHTS,
        }
    }), 200


@ml_bp.route('/model/validate', methods=['POST'])
@jwt_required()
def validate_report_manually():
    """
    Police validation of a report (used to train ML model).
    
    Request Body:
    - report_id: ID of the report
    - is_credible: boolean - was the report accurate?
    - notes: Optional validation notes
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    report_id = data.get('report_id')
    is_credible = data.get('is_credible')
    notes = data.get('notes', '')
    
    if report_id is None or is_credible is None:
        return jsonify({'error': 'report_id and is_credible are required'}), 400
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Update TrustScore with police validation
    trust_score = TrustScore.query.filter_by(report_id=report_id).first()
    if not trust_score:
        trust_score = TrustScore(report_id=report_id)
        db.session.add(trust_score)
    
    # Store validation
    trust_score.police_validated = True
    trust_score.police_validation_result = is_credible
    trust_score.validation_notes = notes
    trust_score.validated_by = user_id
    trust_score.validation_timestamp = datetime.utcnow()
    trust_score.verification_status = VerificationStatus.POLICE_VERIFIED
    
    db.session.commit()
    
    # Add to ML training data
    report_data = {
        'latitude': report.latitude,
        'longitude': report.longitude,
        'district': report.district,
        'timestamp': report.created_at.isoformat() if report.created_at else None,
        'incident_type': report.category.value if report.category else None,
        'attachments': report.attachments or [],
    }
    
    rule_result = verifier.verify_report(report_data, None, None)
    trust_scorer.add_training_sample(report_data, rule_result, None, is_credible)
    
    return jsonify({
        'message': 'Validation recorded successfully',
        'report_id': report_id,
        'is_credible': is_credible,
        'used_for_training': True,
    }), 200


@ml_bp.route('/model/feature-importance', methods=['GET'])
@jwt_required()
def get_feature_importance():
    """Get feature importance from trained ML model."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    importance = trust_scorer.get_feature_importance()
    
    if not importance:
        return jsonify({
            'error': 'Model not trained yet or feature importance unavailable'
        }), 400
    
    return jsonify({
        'feature_importance': importance,
        'model_info': trust_scorer.get_model_info(),
    }), 200


# ============================================================================
# DEVICE PROFILE ENDPOINTS
# ============================================================================

@ml_bp.route('/device/profile', methods=['POST'])
def register_device():
    """
    Register or update a device profile.
    
    Request Body:
    - fingerprint: Device fingerprint hash
    - device_info: Optional device metadata (will be hashed)
    
    Returns device trust score.
    """
    data = request.get_json()
    fingerprint = data.get('fingerprint')
    
    if not fingerprint:
        return jsonify({'error': 'Device fingerprint required'}), 400
    
    # Get or create device profile
    device = DeviceProfile.query.filter_by(fingerprint=fingerprint).first()
    
    if not device:
        device = DeviceProfile(fingerprint=fingerprint)
        db.session.add(device)
        db.session.commit()
    
    return jsonify({
        'device_id': device.id,
        'trust_score': device.trust_score,
        'total_reports': device.total_reports,
        'verified_reports': device.verified_reports,
        'first_seen': device.first_seen.isoformat(),
        'last_seen': device.last_seen.isoformat(),
    }), 200


@ml_bp.route('/device/trust', methods=['GET'])
def get_device_trust():
    """
    Get trust score for a device.
    
    Query Parameters:
    - fingerprint: Device fingerprint
    """
    fingerprint = request.args.get('fingerprint')
    
    if not fingerprint:
        return jsonify({'error': 'Device fingerprint required'}), 400
    
    device = DeviceProfile.query.filter_by(fingerprint=fingerprint).first()
    
    if not device:
        return jsonify({
            'is_new_device': True,
            'trust_score': 0.5,
            'message': 'Device not found - will use neutral trust score'
        }), 200
    
    return jsonify({
        'is_new_device': False,
        'trust_score': device.calculate_trust_score(),
        'total_reports': device.total_reports,
        'verified_reports': device.verified_reports,
        'false_reports': device.false_reports,
    }), 200
