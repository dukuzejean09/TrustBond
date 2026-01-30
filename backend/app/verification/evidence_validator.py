"""
Evidence Validator.

Validates the quality and authenticity of submitted evidence
(photos, videos, audio files).
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class EvidenceValidator:
    """
    Validates evidence files attached to reports.
    
    Checks:
    - Evidence is present
    - File types are valid
    - EXIF metadata consistency (if available)
    - Evidence quantity and quality indicators
    """
    
    # Valid file extensions
    VALID_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic'}
    VALID_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', '3gp'}
    VALID_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'aac'}
    
    # Maximum allowed time difference between evidence capture and report
    MAX_EVIDENCE_AGE_HOURS = 72
    
    def __init__(self):
        pass
    
    def validate_all(self, report_data: Dict) -> Dict:
        """
        Run all evidence validation checks.
        
        Args:
            report_data: Report data including attachments/evidence list
        
        Returns:
            Dictionary with validation results and scores
        """
        evidence = report_data.get('attachments') or report_data.get('evidence') or []
        
        results = {
            'has_evidence': len(evidence) > 0,
            'evidence_count': len(evidence),
            'evidence_types': self.categorize_evidence(evidence),
            'type_scores': {},
            'exif_valid': None,
            'exif_score': 0.5,  # Neutral if no EXIF
            'overall_score': 0.0,
        }
        
        # Calculate score based on evidence presence and quality
        if len(evidence) == 0:
            results['overall_score'] = 0.3  # Penalty for no evidence
            results['reason'] = 'No evidence attached'
            return results
        
        # Score based on evidence count
        count_score = min(1.0, len(evidence) / 3)  # Max score at 3+ pieces
        
        # Score based on evidence types
        type_score = self.calculate_type_score(results['evidence_types'])
        
        # EXIF validation (if metadata available)
        exif_data = report_data.get('exif_data') or report_data.get('evidence_metadata')
        if exif_data:
            exif_result = self.validate_exif(exif_data, report_data)
            results['exif_valid'] = exif_result['valid']
            results['exif_score'] = exif_result['score']
        
        # Calculate overall score
        results['overall_score'] = (
            count_score * 0.3 +
            type_score * 0.3 +
            results['exif_score'] * 0.4
        )
        
        return results
    
    def categorize_evidence(self, evidence: List) -> Dict:
        """
        Categorize evidence by file type.
        
        Returns count of each type: photos, videos, audio, documents
        """
        categories = {
            'photos': 0,
            'videos': 0,
            'audio': 0,
            'documents': 0,
            'unknown': 0,
        }
        
        for item in evidence:
            # Handle both string paths and dict objects
            if isinstance(item, str):
                filename = item
            elif isinstance(item, dict):
                filename = item.get('filename') or item.get('path') or item.get('url', '')
            else:
                categories['unknown'] += 1
                continue
            
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            if ext in self.VALID_IMAGE_EXTENSIONS:
                categories['photos'] += 1
            elif ext in self.VALID_VIDEO_EXTENSIONS:
                categories['videos'] += 1
            elif ext in self.VALID_AUDIO_EXTENSIONS:
                categories['audio'] += 1
            elif ext in {'pdf', 'doc', 'docx', 'txt'}:
                categories['documents'] += 1
            else:
                categories['unknown'] += 1
        
        return categories
    
    def calculate_type_score(self, evidence_types: Dict) -> float:
        """
        Calculate score based on evidence type diversity and quality.
        
        Photos and videos are weighted higher than audio/documents.
        """
        score = 0.0
        
        # Photos are valuable
        if evidence_types['photos'] > 0:
            score += 0.4
            if evidence_types['photos'] >= 2:
                score += 0.1
        
        # Videos are very valuable
        if evidence_types['videos'] > 0:
            score += 0.3
        
        # Audio provides additional context
        if evidence_types['audio'] > 0:
            score += 0.15
        
        # Documents are less common but useful
        if evidence_types['documents'] > 0:
            score += 0.05
        
        return min(1.0, score)
    
    def validate_exif(self, exif_data: Dict, report_data: Dict) -> Dict:
        """
        Validate EXIF metadata against report data.
        
        Checks:
        - GPS in EXIF matches report GPS
        - Capture time is consistent with report time
        - Camera/device info is consistent
        """
        result = {'valid': True, 'score': 0.8, 'issues': []}
        
        if not exif_data:
            result['score'] = 0.5  # Neutral if no EXIF
            return result
        
        # Check GPS consistency
        exif_lat = exif_data.get('gps_latitude') or exif_data.get('GPSLatitude')
        exif_lng = exif_data.get('gps_longitude') or exif_data.get('GPSLongitude')
        report_lat = report_data.get('latitude')
        report_lng = report_data.get('longitude')
        
        if exif_lat and exif_lng and report_lat and report_lng:
            # Allow 1km tolerance
            lat_diff = abs(float(exif_lat) - float(report_lat))
            lng_diff = abs(float(exif_lng) - float(report_lng))
            
            if lat_diff > 0.01 or lng_diff > 0.01:  # ~1km
                result['issues'].append('GPS mismatch between evidence and report')
                result['score'] -= 0.2
        
        # Check timestamp consistency
        exif_time = exif_data.get('datetime') or exif_data.get('DateTimeOriginal')
        report_time = report_data.get('timestamp') or report_data.get('created_at')
        
        if exif_time and report_time:
            try:
                if isinstance(exif_time, str):
                    # EXIF format: "2024:01:28 14:30:00"
                    exif_time = datetime.strptime(exif_time, '%Y:%m:%d %H:%M:%S')
                if isinstance(report_time, str):
                    report_time = datetime.fromisoformat(report_time.replace('Z', '+00:00'))
                
                time_diff = abs((report_time - exif_time).total_seconds()) / 3600
                
                if time_diff > self.MAX_EVIDENCE_AGE_HOURS:
                    result['issues'].append(f'Evidence captured {time_diff:.1f} hours before report')
                    result['score'] -= 0.3
                elif time_diff > 24:
                    result['issues'].append('Evidence may not be from incident')
                    result['score'] -= 0.1
            except:
                pass  # Ignore parsing errors
        
        # Ensure score is within bounds
        result['score'] = max(0.0, min(1.0, result['score']))
        result['valid'] = result['score'] >= 0.5
        
        return result
    
    def check_evidence_authenticity(self, evidence_item: Dict) -> Dict:
        """
        Check if evidence appears to be authentic (not manipulated).
        
        This is a placeholder for more advanced checks like:
        - Error Level Analysis (ELA)
        - Metadata stripping detection
        - Copy-paste detection
        
        Currently returns neutral score as these require specialized libraries.
        """
        return {
            'authentic': True,
            'score': 0.5,
            'method': 'basic_check',
            'note': 'Advanced authenticity analysis not yet implemented'
        }
