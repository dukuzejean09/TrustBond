"""
Spatial-Temporal Consistency Checker.

Verifies that report GPS coordinates, timestamps, and location claims
are logically consistent and physically possible.
"""

from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Optional, Tuple


class SpatialTemporalChecker:
    """
    Checks spatial-temporal consistency of reports.
    
    Validates:
    - GPS coordinates are within Rwanda
    - Timestamp is reasonable (not future, not too old)
    - Location matches claimed district/sector
    - Travel speed between reports is physically possible
    """
    
    # Rwanda geographic boundaries (approximate)
    RWANDA_BOUNDS = {
        'min_lat': -2.84,
        'max_lat': -1.05,
        'min_lng': 28.86,
        'max_lng': 30.90
    }
    
    # Musanze District boundaries (approximate)
    MUSANZE_BOUNDS = {
        'min_lat': -1.70,
        'max_lat': -1.45,
        'min_lng': 29.40,
        'max_lng': 29.70
    }
    
    # District center coordinates for distance checking
    DISTRICT_CENTERS = {
        'musanze': (-1.4997, 29.6350),
        'kigali': (-1.9403, 29.8739),
        'rubavu': (-1.6847, 29.3150),
        'nyagatare': (-1.2967, 30.3275),
        'huye': (-2.5967, 29.7394),
    }
    
    # Maximum reasonable speed (km/h) for travel between reports
    MAX_TRAVEL_SPEED = 120  # km/h
    
    def __init__(self):
        pass
    
    def check_all(self, report_data: Dict, previous_report: Optional[Dict] = None) -> Dict:
        """
        Run all spatial-temporal checks on a report.
        
        Args:
            report_data: Report data including lat, lng, timestamp, district
            previous_report: Previous report from same device (if any)
        
        Returns:
            Dictionary with individual scores and overall score
        """
        results = {
            'gps_valid': self.check_gps_valid(report_data),
            'gps_in_rwanda': self.check_gps_in_rwanda(report_data),
            'timestamp_valid': self.check_timestamp_valid(report_data),
            'district_match': self.check_district_match(report_data),
            'travel_speed_valid': True,
            'travel_speed_score': 1.0,
        }
        
        # Check travel speed if previous report exists
        if previous_report:
            speed_check = self.check_travel_speed(report_data, previous_report)
            results['travel_speed_valid'] = speed_check['valid']
            results['travel_speed_score'] = speed_check['score']
        
        # Calculate overall spatial-temporal score
        scores = [
            1.0 if results['gps_valid'] else 0.0,
            1.0 if results['gps_in_rwanda'] else 0.2,
            results['timestamp_valid']['score'],
            results['district_match']['score'],
            results['travel_speed_score'],
        ]
        
        results['overall_score'] = sum(scores) / len(scores)
        results['passed'] = results['overall_score'] >= 0.5
        
        return results
    
    def check_gps_valid(self, report_data: Dict) -> bool:
        """Check if GPS coordinates are present and valid."""
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        
        if lat is None or lng is None:
            return False
        
        # Check valid range
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return False
        
        # Check for null island (0, 0)
        if lat == 0 and lng == 0:
            return False
        
        return True
    
    def check_gps_in_rwanda(self, report_data: Dict) -> bool:
        """Check if GPS coordinates are within Rwanda."""
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        
        if lat is None or lng is None:
            return False
        
        bounds = self.RWANDA_BOUNDS
        return (
            bounds['min_lat'] <= lat <= bounds['max_lat'] and
            bounds['min_lng'] <= lng <= bounds['max_lng']
        )
    
    def check_timestamp_valid(self, report_data: Dict) -> Dict:
        """
        Check if timestamp is valid and reasonable.
        
        Returns score based on:
        - Not in the future
        - Not too old (> 30 days)
        - Reasonable submission delay
        """
        timestamp = report_data.get('timestamp') or report_data.get('created_at')
        incident_date = report_data.get('incident_date')
        
        result = {'valid': False, 'score': 0.0, 'reason': ''}
        
        if timestamp is None:
            result['reason'] = 'No timestamp'
            return result
        
        # Parse timestamp if string
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                result['reason'] = 'Invalid timestamp format'
                return result
        
        now = datetime.utcnow()
        
        # Check not in future
        if timestamp > now + timedelta(minutes=5):  # Allow 5 min clock skew
            result['reason'] = 'Timestamp in future'
            result['score'] = 0.0
            return result
        
        # Check not too old
        age_days = (now - timestamp).days
        if age_days > 30:
            result['reason'] = 'Report too old'
            result['score'] = 0.3
            result['valid'] = True
            return result
        
        # Score based on age
        if age_days <= 1:
            score = 1.0
        elif age_days <= 7:
            score = 0.8
        elif age_days <= 14:
            score = 0.6
        else:
            score = 0.4
        
        # Check incident date vs submission date
        if incident_date:
            if isinstance(incident_date, str):
                try:
                    incident_date = datetime.fromisoformat(incident_date.replace('Z', '+00:00'))
                except:
                    pass
            
            if isinstance(incident_date, datetime):
                # Incident should be before or same as submission
                if incident_date > timestamp:
                    score *= 0.5
                    result['reason'] = 'Incident date after submission'
        
        result['valid'] = True
        result['score'] = score
        return result
    
    def check_district_match(self, report_data: Dict) -> Dict:
        """
        Check if GPS coordinates match the claimed district.
        
        Returns score based on distance from district center.
        """
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        district = report_data.get('district', '').lower()
        
        result = {'match': False, 'score': 0.5, 'distance_km': None}
        
        if not lat or not lng:
            result['score'] = 0.3
            return result
        
        if not district or district not in self.DISTRICT_CENTERS:
            # No district specified or unknown, give neutral score
            result['score'] = 0.5
            return result
        
        # Calculate distance to district center
        center_lat, center_lng = self.DISTRICT_CENTERS[district]
        distance = self.haversine_distance(lat, lng, center_lat, center_lng)
        result['distance_km'] = round(distance, 2)
        
        # Score based on distance
        if distance <= 10:
            result['score'] = 1.0
            result['match'] = True
        elif distance <= 25:
            result['score'] = 0.8
            result['match'] = True
        elif distance <= 50:
            result['score'] = 0.5
        else:
            result['score'] = 0.2
        
        return result
    
    def check_travel_speed(self, current_report: Dict, previous_report: Dict) -> Dict:
        """
        Check if travel speed between reports is physically possible.
        
        If a device submits two reports from locations that would require
        unrealistic travel speed, flag as suspicious.
        """
        result = {'valid': True, 'score': 1.0, 'speed_kmh': None}
        
        # Get coordinates
        lat1 = previous_report.get('latitude')
        lng1 = previous_report.get('longitude')
        lat2 = current_report.get('latitude')
        lng2 = current_report.get('longitude')
        
        if not all([lat1, lng1, lat2, lng2]):
            return result
        
        # Get timestamps
        time1 = previous_report.get('timestamp') or previous_report.get('created_at')
        time2 = current_report.get('timestamp') or current_report.get('created_at')
        
        if not time1 or not time2:
            return result
        
        # Parse timestamps
        if isinstance(time1, str):
            time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
        if isinstance(time2, str):
            time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
        
        # Calculate time difference in hours
        time_diff = abs((time2 - time1).total_seconds()) / 3600
        
        if time_diff < 0.01:  # Less than 36 seconds
            time_diff = 0.01
        
        # Calculate distance
        distance = self.haversine_distance(lat1, lng1, lat2, lng2)
        
        # Calculate speed
        speed = distance / time_diff
        result['speed_kmh'] = round(speed, 1)
        
        # Check if speed is reasonable
        if speed <= self.MAX_TRAVEL_SPEED:
            result['score'] = 1.0
        elif speed <= self.MAX_TRAVEL_SPEED * 1.5:
            result['score'] = 0.7
        elif speed <= self.MAX_TRAVEL_SPEED * 2:
            result['score'] = 0.4
            result['valid'] = False
        else:
            result['score'] = 0.1
            result['valid'] = False
        
        return result
    
    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate the great-circle distance between two points on Earth.
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
