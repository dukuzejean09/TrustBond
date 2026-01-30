"""
Verification Service - Rule-based verification engine
"""
from app import db
from app.models.verification_rules import VerificationRule, RuleExecutionLog
from app.models.incident_report import IncidentReport
from datetime import datetime, timedelta
from geopy.distance import geodesic
import json


class VerificationService:
    """Service for rule-based report verification"""
    
    # ==================== RULE MANAGEMENT ====================
    @staticmethod
    def get_all_rules(active_only=True):
        """Get all verification rules"""
        query = VerificationRule.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(VerificationRule.execution_order).all()
    
    @staticmethod
    def get_rule_by_id(rule_id):
        """Get rule by ID"""
        return VerificationRule.query.get(rule_id)
    
    @staticmethod
    def get_rule_by_code(rule_code):
        """Get rule by code"""
        return VerificationRule.query.filter_by(rule_code=rule_code).first()
    
    @staticmethod
    def create_rule(data, created_by_user_id):
        """Create a new verification rule"""
        rule = VerificationRule(
            rule_name=data['rule_name'],
            rule_code=data['rule_code'],
            rule_description=data.get('rule_description'),
            rule_category=data['rule_category'],
            rule_parameters=data.get('rule_parameters', {}),
            severity=data.get('severity', 'low'),
            is_blocking=data.get('is_blocking', False),
            failure_score_penalty=data.get('failure_score_penalty', 0),
            execution_order=data.get('execution_order', 999),
            is_active=True,
            applies_to_categories=data.get('applies_to_categories'),
            applies_to_districts=data.get('applies_to_districts'),
            created_by=created_by_user_id
        )
        db.session.add(rule)
        db.session.commit()
        return rule
    
    @staticmethod
    def update_rule(rule_id, data):
        """Update verification rule"""
        rule = VerificationRule.query.get(rule_id)
        if not rule:
            return None
        
        for key, value in data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.utcnow()
        db.session.commit()
        return rule
    
    @staticmethod
    def toggle_rule(rule_id, active):
        """Enable/disable a rule"""
        rule = VerificationRule.query.get(rule_id)
        if rule:
            rule.is_active = active
            rule.updated_at = datetime.utcnow()
            db.session.commit()
        return rule
    
    # ==================== RULE EXECUTION ====================
    @staticmethod
    def execute_rules(report_id):
        """Execute all applicable rules on a report"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        # Update processing stage
        report.report_status = 'rule_checking'
        report.processing_stage = 'rule_validation'
        
        # Get applicable rules
        rules = VerificationRule.query.filter_by(is_active=True)\
            .order_by(VerificationRule.execution_order).all()
        
        results = []
        rules_passed = 0
        rules_failed = 0
        failure_reasons = []
        is_auto_rejected = False
        total_penalty = 0
        
        for rule in rules:
            # Check if rule applies to this report's category/district
            if not VerificationService._rule_applies(rule, report):
                continue
            
            # Execute rule
            start_time = datetime.utcnow()
            passed, input_values, threshold_values, failure_reason = \
                VerificationService._execute_single_rule(rule, report)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log execution
            log = RuleExecutionLog(
                report_id=report_id,
                rule_id=rule.rule_id,
                passed=passed,
                input_values=input_values,
                threshold_values=threshold_values,
                failure_reason=failure_reason,
                execution_time_ms=execution_time
            )
            db.session.add(log)
            
            if passed:
                rules_passed += 1
            else:
                rules_failed += 1
                failure_reasons.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'reason': failure_reason
                })
                total_penalty += float(rule.failure_score_penalty or 0)
                
                if rule.is_blocking:
                    is_auto_rejected = True
            
            results.append({
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'passed': passed,
                'failure_reason': failure_reason
            })
        
        # Update report
        report.rule_check_status = 'passed' if rules_failed == 0 else ('failed' if is_auto_rejected else 'partial')
        report.rule_check_completed_at = datetime.utcnow()
        report.rules_passed = rules_passed
        report.rules_failed = rules_failed
        report.rules_total = rules_passed + rules_failed
        report.rule_failure_reasons = failure_reasons if failure_reasons else None
        report.is_auto_rejected = is_auto_rejected
        
        if is_auto_rejected:
            report.report_status = 'rejected'
            report.processing_stage = 'completed'
            report.trust_classification = 'False'
            report.classification_reason = 'Auto-rejected by blocking rule'
        else:
            report.report_status = 'ml_scoring'
            report.processing_stage = 'ml_scoring'
        
        db.session.commit()
        
        return {
            'report_id': report_id,
            'rules_executed': len(results),
            'rules_passed': rules_passed,
            'rules_failed': rules_failed,
            'is_auto_rejected': is_auto_rejected,
            'total_penalty': total_penalty,
            'results': results
        }
    
    @staticmethod
    def _rule_applies(rule, report):
        """Check if rule applies to this report"""
        # Check category filter
        if rule.applies_to_categories:
            incident_type = report.incident_type
            if incident_type and incident_type.category_id not in rule.applies_to_categories:
                return False
        
        # Check district filter
        if rule.applies_to_districts:
            if report.district_id not in rule.applies_to_districts:
                return False
        
        return True
    
    @staticmethod
    def _execute_single_rule(rule, report):
        """Execute a single rule and return result"""
        params = rule.rule_parameters or {}
        
        # Route to specific rule handler
        rule_handlers = {
            'LOCATION_IN_RWANDA': VerificationService._check_location_in_rwanda,
            'LOCATION_ACCURACY': VerificationService._check_location_accuracy,
            'REPORT_FRESHNESS': VerificationService._check_report_freshness,
            'DESCRIPTION_LENGTH': VerificationService._check_description_length,
            'MOTION_DETECTED': VerificationService._check_motion_detected,
            'DEVICE_TRUST': VerificationService._check_device_trust,
            'DUPLICATE_CHECK': VerificationService._check_duplicate,
            'SPAM_CHECK': VerificationService._check_spam,
            'TIME_CONSISTENCY': VerificationService._check_time_consistency,
            'EVIDENCE_REQUIRED': VerificationService._check_evidence_required
        }
        
        handler = rule_handlers.get(rule.rule_code)
        if handler:
            return handler(report, params)
        
        # Default: pass if no handler
        return True, {}, {}, None
    
    # ==================== RULE IMPLEMENTATIONS ====================
    @staticmethod
    def _check_location_in_rwanda(report, params):
        """Check if location is within Rwanda boundaries"""
        lat = float(report.latitude)
        lon = float(report.longitude)
        
        # Rwanda approximate boundaries
        min_lat = params.get('min_lat', -2.84)
        max_lat = params.get('max_lat', -1.04)
        min_lon = params.get('min_lon', 28.86)
        max_lon = params.get('max_lon', 30.90)
        
        in_bounds = min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
        
        return (
            in_bounds,
            {'latitude': lat, 'longitude': lon},
            {'min_lat': min_lat, 'max_lat': max_lat, 'min_lon': min_lon, 'max_lon': max_lon},
            None if in_bounds else 'Location is outside Rwanda boundaries'
        )
    
    @staticmethod
    def _check_location_accuracy(report, params):
        """Check GPS accuracy"""
        max_accuracy = params.get('max_accuracy_meters', 100)
        accuracy = float(report.location_accuracy_meters or 0)
        
        passed = accuracy <= max_accuracy if accuracy > 0 else True
        
        return (
            passed,
            {'accuracy_meters': accuracy},
            {'max_accuracy_meters': max_accuracy},
            None if passed else f'GPS accuracy {accuracy}m exceeds {max_accuracy}m threshold'
        )
    
    @staticmethod
    def _check_report_freshness(report, params):
        """Check if incident is not too old"""
        max_age_hours = params.get('max_age_hours', 72)
        
        if report.incident_occurred_at:
            age = (datetime.utcnow() - report.incident_occurred_at).total_seconds() / 3600
            passed = age <= max_age_hours
        else:
            passed = True
            age = 0
        
        return (
            passed,
            {'incident_age_hours': age},
            {'max_age_hours': max_age_hours},
            None if passed else f'Incident is {age:.1f} hours old, exceeds {max_age_hours}h limit'
        )
    
    @staticmethod
    def _check_description_length(report, params):
        """Check description meets minimum length"""
        min_length = params.get('min_length', 20)
        description_length = len(report.description or '')
        
        passed = description_length >= min_length
        
        return (
            passed,
            {'description_length': description_length},
            {'min_length': min_length},
            None if passed else f'Description ({description_length} chars) is shorter than {min_length} required'
        )
    
    @staticmethod
    def _check_motion_detected(report, params):
        """Check if device motion indicates genuine reporting"""
        min_score = params.get('min_motion_score', 10)
        motion_score = float(report.device_motion_score or 0)
        
        # Skip if no motion data
        if not report.accelerometer_data:
            return True, {'motion_data': 'not_available'}, {}, None
        
        passed = motion_score >= min_score
        
        return (
            passed,
            {'motion_score': motion_score},
            {'min_motion_score': min_score},
            None if passed else f'Motion score {motion_score} below {min_score} threshold (possible fake report)'
        )
    
    @staticmethod
    def _check_device_trust(report, params):
        """Check device trust score"""
        min_trust = params.get('min_trust_score', 20)
        
        device = report.device
        if not device:
            return True, {'device': 'not_found'}, {}, None
        
        trust_score = float(device.current_trust_score or 50)
        passed = trust_score >= min_trust
        
        return (
            passed,
            {'device_trust_score': trust_score},
            {'min_trust_score': min_trust},
            None if passed else f'Device trust score {trust_score} below {min_trust} threshold'
        )
    
    @staticmethod
    def _check_duplicate(report, params):
        """Check for duplicate reports"""
        time_window_hours = params.get('time_window_hours', 24)
        distance_meters = params.get('distance_meters', 100)
        
        # Look for similar reports in time window
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        similar = IncidentReport.query.filter(
            IncidentReport.report_id != report.report_id,
            IncidentReport.device_id == report.device_id,
            IncidentReport.incident_type_id == report.incident_type_id,
            IncidentReport.reported_at >= time_threshold
        ).all()
        
        for other in similar:
            dist = geodesic(
                (float(report.latitude), float(report.longitude)),
                (float(other.latitude), float(other.longitude))
            ).meters
            if dist <= distance_meters:
                return (
                    False,
                    {'similar_report_id': other.report_id, 'distance_meters': dist},
                    {'time_window_hours': time_window_hours, 'distance_meters': distance_meters},
                    f'Possible duplicate of report {other.report_id} ({dist:.0f}m away)'
                )
        
        return (
            True,
            {'similar_reports_found': len(similar)},
            {'time_window_hours': time_window_hours, 'distance_meters': distance_meters},
            None
        )
    
    @staticmethod
    def _check_spam(report, params):
        """Check for spam patterns"""
        max_reports_per_hour = params.get('max_reports_per_hour', 5)
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = IncidentReport.query.filter(
            IncidentReport.device_id == report.device_id,
            IncidentReport.reported_at >= one_hour_ago
        ).count()
        
        passed = recent_count <= max_reports_per_hour
        
        return (
            passed,
            {'reports_last_hour': recent_count},
            {'max_reports_per_hour': max_reports_per_hour},
            None if passed else f'Device submitted {recent_count} reports in last hour (max {max_reports_per_hour})'
        )
    
    @staticmethod
    def _check_time_consistency(report, params):
        """Check if report time is consistent"""
        max_future_minutes = params.get('max_future_minutes', 5)
        
        if report.incident_occurred_at:
            time_diff = (report.incident_occurred_at - datetime.utcnow()).total_seconds() / 60
            passed = time_diff <= max_future_minutes
        else:
            passed = True
            time_diff = 0
        
        return (
            passed,
            {'future_minutes': time_diff},
            {'max_future_minutes': max_future_minutes},
            None if passed else f'Incident time is {time_diff:.1f} minutes in the future'
        )
    
    @staticmethod
    def _check_evidence_required(report, params):
        """Check if required evidence is present"""
        incident_type = report.incident_type
        if not incident_type:
            return True, {}, {}, None
        
        evidence_count = (report.photo_count or 0) + (report.video_count or 0) + (report.audio_count or 0)
        
        if incident_type.requires_photo and (report.photo_count or 0) == 0:
            return (
                False,
                {'photo_count': report.photo_count or 0},
                {'requires_photo': True},
                'Photo evidence required for this incident type'
            )
        
        if incident_type.requires_video and (report.video_count or 0) == 0:
            return (
                False,
                {'video_count': report.video_count or 0},
                {'requires_video': True},
                'Video evidence required for this incident type'
            )
        
        return (
            True,
            {'evidence_count': evidence_count},
            {},
            None
        )
    
    # ==================== RULE EXECUTION HISTORY ====================
    @staticmethod
    def get_execution_logs(report_id=None, rule_id=None, limit=100):
        """Get rule execution logs"""
        query = RuleExecutionLog.query
        
        if report_id:
            query = query.filter_by(report_id=report_id)
        if rule_id:
            query = query.filter_by(rule_id=rule_id)
        
        return query.order_by(RuleExecutionLog.executed_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_rule_statistics(rule_id):
        """Get statistics for a rule"""
        total = RuleExecutionLog.query.filter_by(rule_id=rule_id).count()
        passed = RuleExecutionLog.query.filter_by(rule_id=rule_id, passed=True).count()
        failed = RuleExecutionLog.query.filter_by(rule_id=rule_id, passed=False).count()
        
        avg_time = db.session.query(db.func.avg(RuleExecutionLog.execution_time_ms))\
            .filter_by(rule_id=rule_id).scalar() or 0
        
        return {
            'rule_id': rule_id,
            'total_executions': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'avg_execution_time_ms': float(avg_time)
        }
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def rule_to_dict(rule):
        """Convert rule to dictionary"""
        if not rule:
            return None
        return {
            'rule_id': rule.rule_id,
            'rule_name': rule.rule_name,
            'rule_code': rule.rule_code,
            'rule_description': rule.rule_description,
            'rule_category': rule.rule_category,
            'rule_parameters': rule.rule_parameters,
            'severity': rule.severity,
            'is_blocking': rule.is_blocking,
            'failure_score_penalty': float(rule.failure_score_penalty) if rule.failure_score_penalty else 0,
            'execution_order': rule.execution_order,
            'is_active': rule.is_active,
            'applies_to_categories': rule.applies_to_categories,
            'applies_to_districts': rule.applies_to_districts,
            'created_at': rule.created_at.isoformat() if rule.created_at else None,
            'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
        }
    
    @staticmethod
    def execution_log_to_dict(log):
        """Convert execution log to dictionary"""
        if not log:
            return None
        return {
            'execution_id': log.execution_id,
            'report_id': log.report_id,
            'rule_id': log.rule_id,
            'passed': log.passed,
            'input_values': log.input_values,
            'threshold_values': log.threshold_values,
            'failure_reason': log.failure_reason,
            'execution_time_ms': float(log.execution_time_ms) if log.execution_time_ms else None,
            'executed_at': log.executed_at.isoformat() if log.executed_at else None
        }
