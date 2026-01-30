"""
Rule-Based Verification Engine.

Orchestrates all verification checks and produces a final trust classification
for incoming reports. This is the main entry point for the verification system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .spatial_temporal import SpatialTemporalChecker
from .evidence_validator import EvidenceValidator


class TrustClassification(Enum):
    """Trust classification levels for reports."""
    TRUSTED = "trusted"       # High confidence, immediate alert
    DELAYED = "delayed"       # Medium confidence, needs review
    SUSPICIOUS = "suspicious" # Low confidence, flagged for investigation


class RuleBasedVerifier:
    """
    Rule-based verification engine for anonymous reports.
    
    This engine applies multiple verification rules to assess report credibility
    WITHOUT compromising reporter anonymity. It produces a trust classification
    that determines how reports are processed:
    
    - TRUSTED: Passes all checks, triggers immediate police alert
    - DELAYED: Some concerns, sent to review queue
    - SUSPICIOUS: Multiple red flags, flagged for investigation
    
    Verification Rules:
    1. GPS Validity: Coordinates within Rwanda/Musanze bounds
    2. Timestamp Validity: Report time is reasonable
    3. Location Consistency: GPS matches stated district
    4. Travel Feasibility: Speed between reports is physically possible
    5. Evidence Quality: Evidence is present and consistent
    6. Report Pattern: Device history indicates reliability
    """
    
    # Thresholds for classification
    TRUSTED_THRESHOLD = 0.75
    DELAYED_THRESHOLD = 0.45
    # Below DELAYED_THRESHOLD = SUSPICIOUS
    
    # Weight configuration for each rule
    RULE_WEIGHTS = {
        'gps_valid': 0.20,
        'timestamp_valid': 0.10,
        'location_consistent': 0.15,
        'travel_feasible': 0.15,
        'evidence_quality': 0.20,
        'device_history': 0.20,
    }
    
    def __init__(self):
        """Initialize verification components."""
        self.spatial_checker = SpatialTemporalChecker()
        self.evidence_validator = EvidenceValidator()
    
    def verify_report(
        self,
        report_data: Dict,
        device_fingerprint: Optional[str] = None,
        device_history: Optional[Dict] = None
    ) -> Dict:
        """
        Run full verification pipeline on a report.
        
        Args:
            report_data: The incoming report data with all fields
            device_fingerprint: Pseudonymous device identifier
            device_history: Previous reports and trust scores for this device
        
        Returns:
            Verification result with classification and detailed breakdown
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'classification': None,
            'overall_score': 0.0,
            'rule_results': {},
            'passed_rules': [],
            'failed_rules': [],
            'recommendations': [],
        }
        
        # Rule 1: GPS Validity
        gps_result = self._check_gps(report_data)
        results['rule_results']['gps_valid'] = gps_result
        
        # Rule 2: Timestamp Validity
        timestamp_result = self._check_timestamp(report_data)
        results['rule_results']['timestamp_valid'] = timestamp_result
        
        # Rule 3: Location Consistency
        location_result = self._check_location_consistency(report_data)
        results['rule_results']['location_consistent'] = location_result
        
        # Rule 4: Travel Feasibility (if device has history)
        travel_result = self._check_travel_feasibility(report_data, device_history)
        results['rule_results']['travel_feasible'] = travel_result
        
        # Rule 5: Evidence Quality
        evidence_result = self._check_evidence(report_data)
        results['rule_results']['evidence_quality'] = evidence_result
        
        # Rule 6: Device History Score
        history_result = self._check_device_history(device_history)
        results['rule_results']['device_history'] = history_result
        
        # Calculate overall weighted score
        total_weight = 0.0
        weighted_score = 0.0
        
        for rule_name, weight in self.RULE_WEIGHTS.items():
            rule_result = results['rule_results'].get(rule_name, {})
            score = rule_result.get('score', 0.5)  # Neutral if missing
            
            weighted_score += score * weight
            total_weight += weight
            
            # Track passed/failed
            if score >= 0.6:
                results['passed_rules'].append(rule_name)
            elif score < 0.4:
                results['failed_rules'].append(rule_name)
        
        # Normalize score
        results['overall_score'] = weighted_score / total_weight if total_weight > 0 else 0.5
        
        # Classify based on score
        results['classification'] = self._classify(results['overall_score'], results)
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _check_gps(self, report_data: Dict) -> Dict:
        """Check GPS validity using spatial checker."""
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        
        if lat is None or lng is None:
            return {
                'passed': False,
                'score': 0.2,
                'reason': 'No GPS coordinates provided'
            }
        
        is_valid, reason = self.spatial_checker.check_gps_valid(lat, lng)
        
        if is_valid:
            return {
                'passed': True,
                'score': 1.0,
                'reason': 'GPS coordinates valid for Musanze'
            }
        else:
            return {
                'passed': False,
                'score': 0.0,
                'reason': reason
            }
    
    def _check_timestamp(self, report_data: Dict) -> Dict:
        """Check timestamp validity."""
        timestamp = report_data.get('timestamp') or report_data.get('created_at')
        
        if not timestamp:
            return {
                'passed': True,
                'score': 0.5,
                'reason': 'No timestamp provided (will use server time)'
            }
        
        is_valid, reason = self.spatial_checker.check_timestamp_valid(timestamp)
        
        return {
            'passed': is_valid,
            'score': 1.0 if is_valid else 0.2,
            'reason': reason
        }
    
    def _check_location_consistency(self, report_data: Dict) -> Dict:
        """Check if GPS matches stated district."""
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        district = report_data.get('district') or report_data.get('location')
        
        if not all([lat, lng, district]):
            return {
                'passed': True,
                'score': 0.5,
                'reason': 'Insufficient data for location consistency check'
            }
        
        is_consistent, reason = self.spatial_checker.check_district_match(lat, lng, district)
        
        return {
            'passed': is_consistent,
            'score': 1.0 if is_consistent else 0.3,
            'reason': reason
        }
    
    def _check_travel_feasibility(
        self,
        report_data: Dict,
        device_history: Optional[Dict]
    ) -> Dict:
        """Check if travel between reports is physically possible."""
        if not device_history or not device_history.get('last_report'):
            return {
                'passed': True,
                'score': 0.6,
                'reason': 'First report from device - no travel history'
            }
        
        last_report = device_history['last_report']
        
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        timestamp = report_data.get('timestamp') or datetime.utcnow().isoformat()
        
        last_lat = last_report.get('latitude')
        last_lng = last_report.get('longitude')
        last_time = last_report.get('timestamp')
        
        if not all([lat, lng, last_lat, last_lng, last_time]):
            return {
                'passed': True,
                'score': 0.5,
                'reason': 'Insufficient data for travel check'
            }
        
        is_feasible, reason = self.spatial_checker.check_travel_speed(
            lat, lng, timestamp,
            last_lat, last_lng, last_time
        )
        
        return {
            'passed': is_feasible,
            'score': 1.0 if is_feasible else 0.0,
            'reason': reason
        }
    
    def _check_evidence(self, report_data: Dict) -> Dict:
        """Validate evidence quality."""
        evidence_result = self.evidence_validator.validate_all(report_data)
        
        return {
            'passed': evidence_result['overall_score'] >= 0.5,
            'score': evidence_result['overall_score'],
            'reason': evidence_result.get('reason', 'Evidence validation complete'),
            'details': {
                'has_evidence': evidence_result['has_evidence'],
                'evidence_count': evidence_result['evidence_count'],
                'evidence_types': evidence_result['evidence_types']
            }
        }
    
    def _check_device_history(self, device_history: Optional[Dict]) -> Dict:
        """Check device's historical trustworthiness."""
        if not device_history:
            return {
                'passed': True,
                'score': 0.5,
                'reason': 'New device - no history available'
            }
        
        trust_score = device_history.get('trust_score', 0.5)
        total_reports = device_history.get('total_reports', 0)
        verified_reports = device_history.get('verified_reports', 0)
        false_reports = device_history.get('false_reports', 0)
        
        # Calculate history-based score
        if total_reports == 0:
            score = 0.5
            reason = 'New device - no history'
        elif total_reports < 3:
            score = 0.5 + (trust_score - 0.5) * 0.3  # Reduced impact for new devices
            reason = f'Limited history ({total_reports} reports)'
        else:
            # Full history impact
            score = trust_score
            accuracy = verified_reports / total_reports if total_reports > 0 else 0
            
            if false_reports > 0:
                penalty = min(0.3, false_reports * 0.1)
                score -= penalty
                reason = f'{false_reports} false reports detected, score reduced'
            elif accuracy > 0.8:
                reason = f'High accuracy history ({accuracy:.0%} verified)'
            else:
                reason = f'Moderate history ({total_reports} reports, {accuracy:.0%} verified)'
        
        return {
            'passed': score >= 0.4,
            'score': max(0.0, min(1.0, score)),
            'reason': reason,
            'details': {
                'total_reports': total_reports,
                'verified_reports': verified_reports,
                'false_reports': false_reports
            }
        }
    
    def _classify(self, score: float, results: Dict) -> TrustClassification:
        """
        Determine trust classification based on score and rule results.
        
        Special rules:
        - GPS failure forces DELAYED at minimum
        - Evidence + GPS failure forces SUSPICIOUS
        """
        # Check for critical failures
        gps_failed = 'gps_valid' in results['failed_rules']
        evidence_failed = 'evidence_quality' in results['failed_rules']
        travel_failed = 'travel_feasible' in results['failed_rules']
        
        # Critical: GPS failure with other issues -> SUSPICIOUS
        if gps_failed and (evidence_failed or travel_failed):
            return TrustClassification.SUSPICIOUS
        
        # Critical: Impossible travel -> SUSPICIOUS
        if travel_failed:
            return TrustClassification.SUSPICIOUS
        
        # Score-based classification
        if score >= self.TRUSTED_THRESHOLD:
            return TrustClassification.TRUSTED
        elif score >= self.DELAYED_THRESHOLD:
            return TrustClassification.DELAYED
        else:
            return TrustClassification.SUSPICIOUS
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate actionable recommendations based on verification results."""
        recommendations = []
        classification = results['classification']
        
        if classification == TrustClassification.TRUSTED:
            recommendations.append('Send immediate alert to patrol officers')
            recommendations.append('Add to hotspot analysis')
        
        elif classification == TrustClassification.DELAYED:
            recommendations.append('Queue for manual review within 30 minutes')
            if 'gps_valid' in results['failed_rules']:
                recommendations.append('Verify location through call-back if needed')
            if 'evidence_quality' in results['failed_rules']:
                recommendations.append('Request additional evidence if possible')
        
        else:  # SUSPICIOUS
            recommendations.append('Flag for investigation')
            recommendations.append('Do not include in statistics until verified')
            if 'travel_feasible' in results['failed_rules']:
                recommendations.append('Investigate potential location spoofing')
        
        return recommendations
    
    def get_verification_summary(self, results: Dict) -> str:
        """Get human-readable verification summary."""
        classification = results['classification']
        score = results['overall_score']
        passed = len(results['passed_rules'])
        failed = len(results['failed_rules'])
        
        return (
            f"Classification: {classification.value.upper()}\n"
            f"Trust Score: {score:.2f}\n"
            f"Rules Passed: {passed}/{passed + failed}\n"
            f"Recommendations:\n" +
            "\n".join(f"  - {r}" for r in results['recommendations'])
        )
