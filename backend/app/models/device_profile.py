"""
Device Profile Model for Pseudonymous Device Identification.

This model tracks device reputation without storing personal information.
Each device is identified by a unique fingerprint hash generated from
hardware characteristics (not IMEI or phone number).
"""

from app import db
from datetime import datetime


class DeviceProfile(db.Model):
    """
    Stores pseudonymous device profiles for trust tracking.
    
    The device_fingerprint is a SHA-256 hash of device characteristics,
    ensuring privacy while enabling reputation tracking.
    """
    __tablename__ = 'device_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Pseudonymous identifier (SHA-256 hash of device info)
    device_fingerprint = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Device metadata (non-identifying)
    platform = db.Column(db.String(20))  # 'android' or 'ios'
    app_version = db.Column(db.String(20))
    
    # Trust metrics
    total_reports = db.Column(db.Integer, default=0)
    trusted_reports = db.Column(db.Integer, default=0)
    delayed_reports = db.Column(db.Integer, default=0)
    suspicious_reports = db.Column(db.Integer, default=0)
    
    # Calculated trust score (0.0 to 1.0)
    trust_score = db.Column(db.Float, default=0.5)
    
    # Abuse detection flags
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(200))
    flagged_at = db.Column(db.DateTime)
    
    # Activity tracking
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_report_at = db.Column(db.DateTime)
    
    # Location patterns (for consistency checking)
    typical_latitude = db.Column(db.Float)
    typical_longitude = db.Column(db.Float)
    location_variance = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_trust_score(self):
        """
        Calculate device trust score based on report history.
        
        Score formula:
        - Base score: 0.5 (neutral)
        - +0.1 for each trusted report (max +0.4)
        - -0.1 for each suspicious report
        - Minimum: 0.0, Maximum: 1.0
        """
        if self.total_reports == 0:
            return 0.5
        
        # Calculate ratio-based score
        trusted_ratio = self.trusted_reports / max(self.total_reports, 1)
        suspicious_ratio = self.suspicious_reports / max(self.total_reports, 1)
        
        # Weighted score
        score = 0.5 + (trusted_ratio * 0.4) - (suspicious_ratio * 0.4)
        
        # Clamp between 0 and 1
        self.trust_score = max(0.0, min(1.0, score))
        return self.trust_score
    
    def record_report(self, classification):
        """
        Record a new report and update trust metrics.
        
        Args:
            classification: 'trusted', 'delayed', or 'suspicious'
        """
        self.total_reports += 1
        self.last_report_at = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        
        if classification == 'trusted':
            self.trusted_reports += 1
        elif classification == 'delayed':
            self.delayed_reports += 1
        elif classification == 'suspicious':
            self.suspicious_reports += 1
            
            # Auto-flag if too many suspicious reports
            if self.suspicious_reports >= 3 and self.suspicious_reports > self.trusted_reports:
                self.is_flagged = True
                self.flag_reason = 'Multiple suspicious reports detected'
                self.flagged_at = datetime.utcnow()
        
        self.calculate_trust_score()
    
    def update_location_pattern(self, latitude, longitude):
        """
        Update typical location pattern for the device.
        Uses exponential moving average.
        """
        if self.typical_latitude is None:
            self.typical_latitude = latitude
            self.typical_longitude = longitude
        else:
            # Exponential moving average (alpha = 0.3)
            alpha = 0.3
            self.typical_latitude = alpha * latitude + (1 - alpha) * self.typical_latitude
            self.typical_longitude = alpha * longitude + (1 - alpha) * self.typical_longitude
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'deviceFingerprint': self.device_fingerprint[:8] + '...',  # Partial for privacy
            'platform': self.platform,
            'trustScore': round(self.trust_score, 3),
            'totalReports': self.total_reports,
            'trustedReports': self.trusted_reports,
            'delayedReports': self.delayed_reports,
            'suspiciousReports': self.suspicious_reports,
            'isFlagged': self.is_flagged,
            'flagReason': self.flag_reason,
            'firstSeen': self.first_seen.isoformat() if self.first_seen else None,
            'lastSeen': self.last_seen.isoformat() if self.last_seen else None,
        }
    
    def __repr__(self):
        return f'<DeviceProfile {self.device_fingerprint[:8]}... trust={self.trust_score:.2f}>'
