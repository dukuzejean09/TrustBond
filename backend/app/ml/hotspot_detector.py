"""
DBSCAN Hotspot Detector.

This module implements spatial clustering of crime reports using DBSCAN
(Density-Based Spatial Clustering of Applications with Noise) to identify
crime hotspots in Musanze District.

Hotspots are used for:
- Patrol resource allocation
- Public safety awareness (anonymized)
- Trend analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

# Graceful import handling
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class HotspotDetector:
    """
    Crime Hotspot Detector using DBSCAN Clustering.
    
    DBSCAN is ideal for crime hotspot detection because:
    1. It doesn't require specifying number of clusters
    2. It can find arbitrarily shaped clusters
    3. It identifies outliers (noise points)
    4. Density-based approach matches crime distribution patterns
    
    Parameters:
    - eps: Maximum distance between two points to be neighbors (in km)
    - min_samples: Minimum points required to form a cluster
    
    The detector processes reports from a configurable time window
    and outputs hotspot polygons with severity ratings.
    """
    
    # DBSCAN parameters
    DEFAULT_EPS_KM = 0.5        # 500 meters neighborhood
    DEFAULT_MIN_SAMPLES = 3     # At least 3 reports to form hotspot
    
    # Time window for analysis
    DEFAULT_WINDOW_DAYS = 30    # Last 30 days
    
    # Earth's radius in km for distance calculations
    EARTH_RADIUS_KM = 6371.0
    
    # Severity thresholds (reports per cluster)
    SEVERITY_THRESHOLDS = {
        1: 3,   # Low: 3-5 reports
        2: 6,   # Moderate: 6-10 reports  
        3: 11,  # High: 11-20 reports
        4: 21,  # Critical: 21-35 reports
        5: 36,  # Severe: 36+ reports
    }
    
    def __init__(
        self,
        eps_km: float = DEFAULT_EPS_KM,
        min_samples: int = DEFAULT_MIN_SAMPLES,
        window_days: int = DEFAULT_WINDOW_DAYS
    ):
        """
        Initialize the Hotspot Detector.
        
        Args:
            eps_km: Neighborhood radius in kilometers
            min_samples: Minimum reports to form a hotspot
            window_days: Time window for analysis
        """
        self.eps_km = eps_km
        self.min_samples = min_samples
        self.window_days = window_days
        
        if SKLEARN_AVAILABLE:
            # Convert eps from km to radians for haversine
            self.eps_rad = eps_km / self.EARTH_RADIUS_KM
            self.model = DBSCAN(
                eps=self.eps_rad,
                min_samples=min_samples,
                metric='haversine',
                algorithm='ball_tree'
            )
        else:
            logger.warning("scikit-learn not available. Hotspot detection disabled.")
            self.model = None
    
    def detect_hotspots(
        self,
        reports: List[Dict],
        incident_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Detect crime hotspots from a list of reports.
        
        Args:
            reports: List of report dictionaries with latitude/longitude
            incident_type: Optional filter for specific incident type
        
        Returns:
            List of hotspot dictionaries with location, severity, and metadata
        """
        if not SKLEARN_AVAILABLE:
            return []
        
        # Filter reports by time window
        cutoff = datetime.utcnow() - timedelta(days=self.window_days)
        filtered_reports = []
        
        for report in reports:
            # Get timestamp
            timestamp = report.get('timestamp') or report.get('created_at')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        dt = datetime.utcnow()
                else:
                    dt = timestamp
                
                if dt < cutoff:
                    continue
            
            # Filter by incident type if specified
            if incident_type:
                if report.get('incident_type', '').lower() != incident_type.lower():
                    continue
            
            # Require GPS coordinates
            lat = report.get('latitude')
            lng = report.get('longitude')
            if lat is not None and lng is not None:
                filtered_reports.append(report)
        
        if len(filtered_reports) < self.min_samples:
            logger.info(f"Not enough reports for hotspot detection: {len(filtered_reports)}")
            return []
        
        # Extract coordinates (convert to radians for haversine)
        coordinates = np.array([
            [np.radians(r['latitude']), np.radians(r['longitude'])]
            for r in filtered_reports
        ])
        
        # Run DBSCAN clustering
        try:
            labels = self.model.fit_predict(coordinates)
        except Exception as e:
            logger.error(f"DBSCAN clustering failed: {e}")
            return []
        
        # Process clusters into hotspots
        hotspots = self._process_clusters(
            labels, 
            filtered_reports, 
            coordinates,
            incident_type
        )
        
        return hotspots
    
    def _process_clusters(
        self,
        labels: np.ndarray,
        reports: List[Dict],
        coordinates: np.ndarray,
        incident_type: Optional[str]
    ) -> List[Dict]:
        """
        Process DBSCAN cluster labels into hotspot objects.
        
        Args:
            labels: Cluster labels from DBSCAN (-1 = noise)
            reports: Original report list
            coordinates: Coordinate array in radians
            incident_type: Incident type filter used
        
        Returns:
            List of hotspot dictionaries
        """
        hotspots = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:
                continue  # Skip noise points
            
            # Get reports in this cluster
            cluster_mask = labels == label
            cluster_reports = [r for r, m in zip(reports, cluster_mask) if m]
            cluster_coords = coordinates[cluster_mask]
            
            # Calculate centroid (convert back to degrees)
            centroid_rad = cluster_coords.mean(axis=0)
            centroid = (np.degrees(centroid_rad[0]), np.degrees(centroid_rad[1]))
            
            # Calculate cluster radius (max distance from centroid)
            distances = self._haversine_distance_vectorized(
                centroid_rad[0], centroid_rad[1],
                cluster_coords[:, 0], cluster_coords[:, 1]
            )
            radius_km = float(distances.max())
            
            # Determine severity
            report_count = len(cluster_reports)
            severity = self._calculate_severity(report_count)
            
            # Get incident types distribution
            type_counts = {}
            for r in cluster_reports:
                t = r.get('incident_type', 'unknown')
                type_counts[t] = type_counts.get(t, 0) + 1
            
            # Find dominant incident type
            dominant_type = max(type_counts.keys(), key=lambda k: type_counts[k])
            
            # Calculate time range
            timestamps = []
            for r in cluster_reports:
                ts = r.get('timestamp') or r.get('created_at')
                if ts:
                    if isinstance(ts, str):
                        try:
                            timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                        except:
                            pass
                    else:
                        timestamps.append(ts)
            
            if timestamps:
                first_report = min(timestamps)
                last_report = max(timestamps)
            else:
                first_report = last_report = datetime.utcnow()
            
            hotspot = {
                'cluster_id': int(label),
                'center_latitude': float(centroid[0]),
                'center_longitude': float(centroid[1]),
                'radius_km': round(radius_km, 3),
                'report_count': report_count,
                'severity': severity,
                'severity_label': self._severity_label(severity),
                'incident_types': type_counts,
                'dominant_type': dominant_type,
                'first_report': first_report.isoformat(),
                'last_report': last_report.isoformat(),
                'analysis_window_days': self.window_days,
                'filtered_by_type': incident_type,
                'created_at': datetime.utcnow().isoformat(),
            }
            
            hotspots.append(hotspot)
        
        # Sort by severity (descending)
        hotspots.sort(key=lambda h: h['severity'], reverse=True)
        
        return hotspots
    
    def _haversine_distance_vectorized(
        self,
        lat1_rad: float,
        lon1_rad: float,
        lat2_rad: np.ndarray,
        lon2_rad: np.ndarray
    ) -> np.ndarray:
        """
        Calculate haversine distance from one point to many (vectorized).
        
        Args:
            lat1_rad, lon1_rad: Reference point in radians
            lat2_rad, lon2_rad: Array of points in radians
        
        Returns:
            Array of distances in kilometers
        """
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat / 2) ** 2 + \
            np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return self.EARTH_RADIUS_KM * c
    
    def _calculate_severity(self, report_count: int) -> int:
        """
        Calculate severity level (1-5) based on report count.
        """
        for severity in [5, 4, 3, 2, 1]:
            if report_count >= self.SEVERITY_THRESHOLDS[severity]:
                return severity
        return 1
    
    def _severity_label(self, severity: int) -> str:
        """Get human-readable severity label."""
        labels = {
            1: 'Low',
            2: 'Moderate',
            3: 'High',
            4: 'Critical',
            5: 'Severe'
        }
        return labels.get(severity, 'Unknown')
    
    def detect_by_type(
        self,
        reports: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Detect hotspots separately for each incident type.
        
        Returns:
            Dictionary mapping incident type to list of hotspots
        """
        # Get all incident types
        types = set()
        for r in reports:
            t = r.get('incident_type')
            if t:
                types.add(t.lower())
        
        # Detect hotspots for each type
        results = {}
        for incident_type in types:
            hotspots = self.detect_hotspots(reports, incident_type)
            if hotspots:
                results[incident_type] = hotspots
        
        return results
    
    def get_public_hotspots(
        self,
        reports: List[Dict],
        anonymize: bool = True
    ) -> List[Dict]:
        """
        Get hotspots suitable for public display.
        
        Applies additional anonymization for community safety map:
        - Reduces coordinate precision
        - Removes detailed timestamps
        - Uses generalized severity labels
        
        Args:
            reports: List of reports
            anonymize: Whether to anonymize data for public
        
        Returns:
            List of anonymized hotspot data
        """
        hotspots = self.detect_hotspots(reports)
        
        if not anonymize:
            return hotspots
        
        public_hotspots = []
        for h in hotspots:
            public = {
                'id': h['cluster_id'],
                # Reduce coordinate precision (3 decimal = ~111m)
                'latitude': round(h['center_latitude'], 3),
                'longitude': round(h['center_longitude'], 3),
                # Generalize radius
                'area_km': round(h['radius_km'] * 2, 1),  # Diameter
                # Use generalized activity level instead of report count
                'activity_level': self._activity_level(h['report_count']),
                'severity': h['severity'],
                'severity_label': h['severity_label'],
                # Only show dominant type
                'incident_type': h['dominant_type'],
                # Generalize time (week of last activity)
                'last_activity': self._generalize_time(h['last_report']),
            }
            public_hotspots.append(public)
        
        return public_hotspots
    
    def _activity_level(self, count: int) -> str:
        """Convert report count to generalized activity level."""
        if count >= 20:
            return 'Very High'
        elif count >= 10:
            return 'High'
        elif count >= 5:
            return 'Moderate'
        else:
            return 'Low'
    
    def _generalize_time(self, iso_timestamp: str) -> str:
        """Generalize timestamp to week for privacy."""
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            # Return start of week
            start_of_week = dt - timedelta(days=dt.weekday())
            return f"Week of {start_of_week.strftime('%b %d, %Y')}"
        except:
            return "Recent"
    
    def get_statistics(self, hotspots: List[Dict]) -> Dict:
        """
        Get summary statistics for detected hotspots.
        
        Returns:
            Dictionary with hotspot statistics
        """
        if not hotspots:
            return {
                'total_hotspots': 0,
                'total_reports_in_hotspots': 0,
                'severity_distribution': {},
                'type_distribution': {},
            }
        
        severity_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        type_dist = {}
        total_reports = 0
        
        for h in hotspots:
            severity_dist[h['severity']] = severity_dist.get(h['severity'], 0) + 1
            type_dist[h['dominant_type']] = type_dist.get(h['dominant_type'], 0) + 1
            total_reports += h['report_count']
        
        return {
            'total_hotspots': len(hotspots),
            'total_reports_in_hotspots': total_reports,
            'severity_distribution': severity_dist,
            'type_distribution': type_dist,
            'average_reports_per_hotspot': round(total_reports / len(hotspots), 1),
        }
    
    def get_config(self) -> Dict:
        """Get current detector configuration."""
        return {
            'sklearn_available': SKLEARN_AVAILABLE,
            'eps_km': self.eps_km,
            'min_samples': self.min_samples,
            'window_days': self.window_days,
            'severity_thresholds': self.SEVERITY_THRESHOLDS,
        }
