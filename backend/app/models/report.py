from app import db
from datetime import datetime
import enum


class ReportStatus(enum.Enum):
    PENDING = 'pending'
    UNDER_REVIEW = 'under_review'
    INVESTIGATING = 'investigating'
    RESOLVED = 'resolved'
    CLOSED = 'closed'
    REJECTED = 'rejected'


class ReportPriority(enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class CrimeCategory(enum.Enum):
    THEFT = 'theft'
    ASSAULT = 'assault'
    ROBBERY = 'robbery'
    FRAUD = 'fraud'
    VANDALISM = 'vandalism'
    DOMESTIC_VIOLENCE = 'domestic_violence'
    CYBERCRIME = 'cybercrime'
    DRUG_RELATED = 'drug_related'
    TRAFFIC_VIOLATION = 'traffic_violation'
    CORRUPTION = 'corruption'
    MURDER = 'murder'
    KIDNAPPING = 'kidnapping'
    SEXUAL_ASSAULT = 'sexual_assault'
    OTHER = 'other'


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(CrimeCategory), nullable=False)
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    priority = db.Column(db.Enum(ReportPriority), default=ReportPriority.MEDIUM, nullable=False)
    
    # Location details
    province = db.Column(db.String(50))
    district = db.Column(db.String(50))
    sector = db.Column(db.String(50))
    cell = db.Column(db.String(50))
    village = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_description = db.Column(db.Text)
    
    # Incident details
    incident_date = db.Column(db.DateTime)
    incident_time = db.Column(db.String(10))
    
    # Reporter info
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for anonymous reports
    is_anonymous = db.Column(db.Boolean, default=False)
    anonymous_contact = db.Column(db.String(200))  # Optional contact for anonymous follow-up
    tracking_code = db.Column(db.String(20), unique=True, index=True)  # For anonymous report tracking
    
    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    station = db.Column(db.String(100))
    
    # Evidence/Attachments
    attachments = db.Column(db.JSON, default=list)  # List of file URLs
    
    # Resolution
    resolution_notes = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status history
    status_history = db.Column(db.JSON, default=list)
    
    def to_dict(self, include_reporter=True):
        """Convert report to dictionary
        
        Args:
            include_reporter: If False, hides reporter identity for privacy (dashboard view)
        """
        data = {
            'id': self.id,
            'reportNumber': self.report_number,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'province': self.province,
            'district': self.district,
            'sector': self.sector,
            'cell': self.cell,
            'village': self.village,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'locationDescription': self.location_description,
            'incidentDate': self.incident_date.isoformat() if self.incident_date else None,
            'incidentTime': self.incident_time,
            'isAnonymous': self.is_anonymous,
            'assignedTo': self.assigned_to,
            'station': self.station,
            'attachments': self.attachments,
            'resolutionNotes': self.resolution_notes,
            'resolvedAt': self.resolved_at.isoformat() if self.resolved_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'statusHistory': self.status_history,
            'source': 'mobile' if self.reporter_id is None else 'registered'
        }
        
        # Only include reporter info if explicitly requested and not anonymous
        if include_reporter and not self.is_anonymous:
            data['reporterId'] = self.reporter_id
            data['trackingCode'] = self.tracking_code
        else:
            # Hide reporter identity - show as anonymous/mobile submission
            data['reporterId'] = None
            data['trackingCode'] = None
            data['reporterInfo'] = 'Anonymous Mobile User'
        
        return data
    
    @staticmethod
    def generate_report_number():
        """Generate a unique report number like RNP-2026-00001"""
        import random
        year = datetime.utcnow().year
        random_num = random.randint(10000, 99999)
        return f"RNP-{year}-{random_num}"
    
    def __repr__(self):
        return f'<Report {self.report_number}>'
