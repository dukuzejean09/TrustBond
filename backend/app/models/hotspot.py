"""
Hotspot Model for Crime Cluster Detection.

Stores detected geographic hotspots from DBSCAN clustering
of trusted reports.
"""

from app import db
from datetime import datetime
import enum


class HotspotSeverity(enum.Enum):
    """Hotspot severity levels based on incident count and recency."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EXTREME = 5


class HotspotStatus(enum.Enum):
    """Hotspot status for tracking."""
    ACTIVE = 'active'
    MONITORING = 'monitoring'
    RESOLVED = 'resolved'
    ARCHIVED = 'archived'


class Hotspot(db.Model):
    """
    Stores detected crime hotspots from DBSCAN clustering.
    
    Each hotspot represents a geographic cluster of trusted
    incident reports, with statistics and metadata.
    """
    __tablename__ = 'hotspots'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Unique identifier for the hotspot
    hotspot_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Geographic center of the cluster
    center_latitude = db.Column(db.Float, nullable=False)
    center_longitude = db.Column(db.Float, nullable=False)
    
    # Cluster boundary (simplified as radius for now)
    radius_meters = db.Column(db.Float, default=500.0)
    
    # Boundary polygon (GeoJSON format) for precise boundaries
    boundary_geojson = db.Column(db.JSON)
    
    # Cluster statistics
    incident_count = db.Column(db.Integer, nullable=False)
    avg_trust_score = db.Column(db.Float)
    
    # Severity assessment
    severity = db.Column(db.Enum(HotspotSeverity), default=HotspotSeverity.LOW)
    severity_score = db.Column(db.Float)  # Numeric severity (1-5)
    
    # Time range of incidents in cluster
    earliest_incident = db.Column(db.DateTime)
    latest_incident = db.Column(db.DateTime)
    
    # Category breakdown (JSON: {"theft": 5, "vandalism": 3, ...})
    category_distribution = db.Column(db.JSON, default=dict)
    
    # Location context
    district = db.Column(db.String(50))
    sector = db.Column(db.String(50))
    location_name = db.Column(db.String(200))  # Human-readable location
    
    # Status tracking
    status = db.Column(db.Enum(HotspotStatus), default=HotspotStatus.ACTIVE)
    
    # Detection metadata
    detection_algorithm = db.Column(db.String(50), default='DBSCAN')
    detection_parameters = db.Column(db.JSON)  # {"eps": 0.01, "min_samples": 3}
    
    # Report IDs in this cluster (for reference)
    report_ids = db.Column(db.JSON, default=list)
    
    # Police response tracking
    response_assigned = db.Column(db.Boolean, default=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    response_notes = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    
    # Timestamps
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # For public display (anonymized)
    is_public = db.Column(db.Boolean, default=True)
    public_after = db.Column(db.DateTime)  # Time delay before showing publicly
    
    # Relationship
    assigned_officer = db.relationship('User', foreign_keys=[assigned_to])
    
    @staticmethod
    def generate_hotspot_id():
        """Generate a unique hotspot ID."""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(chars, k=6))
        return f'HS-{random_part}'
    
    def calculate_severity(self):
        """
        Calculate hotspot severity based on multiple factors.
        
        Factors:
        - Incident count (more incidents = higher severity)
        - Recency (recent incidents = higher severity)
        - Category weights (violent crimes weigh more)
        """
        # Base score from incident count
        if self.incident_count >= 15:
            count_score = 5
        elif self.incident_count >= 10:
            count_score = 4
        elif self.incident_count >= 6:
            count_score = 3
        elif self.incident_count >= 3:
            count_score = 2
        else:
            count_score = 1
        
        # Recency factor
        if self.latest_incident:
            hours_since = (datetime.utcnow() - self.latest_incident).total_seconds() / 3600
            if hours_since < 6:
                recency_factor = 1.5
            elif hours_since < 24:
                recency_factor = 1.2
            elif hours_since < 72:
                recency_factor = 1.0
            else:
                recency_factor = 0.8
        else:
            recency_factor = 1.0
        
        # Category weights
        category_weights = {
            'assault': 1.5,
            'robbery': 1.5,
            'theft': 1.0,
            'vandalism': 0.8,
            'suspicious': 0.7,
            'other': 0.6,
        }
        
        category_factor = 1.0
        if self.category_distribution:
            total = sum(self.category_distribution.values())
            if total > 0:
                weighted_sum = sum(
                    count * category_weights.get(cat, 1.0)
                    for cat, count in self.category_distribution.items()
                )
                category_factor = weighted_sum / total
        
        # Final severity score
        self.severity_score = min(5.0, count_score * recency_factor * category_factor)
        
        # Map to severity level
        if self.severity_score >= 4.5:
            self.severity = HotspotSeverity.EXTREME
        elif self.severity_score >= 3.5:
            self.severity = HotspotSeverity.CRITICAL
        elif self.severity_score >= 2.5:
            self.severity = HotspotSeverity.HIGH
        elif self.severity_score >= 1.5:
            self.severity = HotspotSeverity.MEDIUM
        else:
            self.severity = HotspotSeverity.LOW
        
        return self.severity
    
    def to_dict(self, include_reports=False):
        """Convert to dictionary for API responses."""
        data = {
            'id': self.id,
            'hotspotId': self.hotspot_id,
            'center': {
                'latitude': self.center_latitude,
                'longitude': self.center_longitude,
            },
            'radiusMeters': self.radius_meters,
            'incidentCount': self.incident_count,
            'avgTrustScore': round(self.avg_trust_score, 2) if self.avg_trust_score else None,
            'severity': self.severity.value if self.severity else 1,
            'severityLevel': self.severity.name if self.severity else 'LOW',
            'severityScore': round(self.severity_score, 2) if self.severity_score else None,
            'categoryDistribution': self.category_distribution,
            'district': self.district,
            'sector': self.sector,
            'locationName': self.location_name,
            'status': self.status.value if self.status else 'active',
            'timeRange': {
                'earliest': self.earliest_incident.isoformat() if self.earliest_incident else None,
                'latest': self.latest_incident.isoformat() if self.latest_incident else None,
            },
            'detectedAt': self.detected_at.isoformat() if self.detected_at else None,
            'responseAssigned': self.response_assigned,
        }
        
        if include_reports:
            data['reportIds'] = self.report_ids
        
        return data
    
    def to_public_dict(self):
        """
        Convert to dictionary for public API (anonymized).
        Less detail than internal API.
        """
        return {
            'id': self.hotspot_id,
            'center': {
                'latitude': round(self.center_latitude, 3),  # Reduced precision
                'longitude': round(self.center_longitude, 3),
            },
            'radius': self.radius_meters,
            'incidentCount': self.incident_count,
            'severity': self.severity.value if self.severity else 1,
            'severityLevel': self.severity.name if self.severity else 'LOW',
            'mainCategory': max(self.category_distribution, key=self.category_distribution.get) if self.category_distribution else 'unknown',
            'district': self.district,
            'lastUpdated': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Hotspot {self.hotspot_id} incidents={self.incident_count} severity={self.severity}>'
