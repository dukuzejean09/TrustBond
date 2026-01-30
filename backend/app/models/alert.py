from app import db
from datetime import datetime
import enum


class AlertType(enum.Enum):
    EMERGENCY = 'emergency'
    WARNING = 'warning'
    INFO = 'info'
    SECURITY = 'security'
    WEATHER = 'weather'
    TRAFFIC = 'traffic'
    COMMUNITY = 'community'


class AlertStatus(enum.Enum):
    ACTIVE = 'active'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.Enum(AlertType), nullable=False)
    status = db.Column(db.Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False)
    
    # Target area
    province = db.Column(db.String(50))
    district = db.Column(db.String(50))
    sector = db.Column(db.String(50))
    is_nationwide = db.Column(db.Boolean, default=False)
    
    # Validity
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    # Creator
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    creator = db.relationship('User', backref='alerts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'alertType': self.alert_type.value,
            'status': self.status.value,
            'province': self.province,
            'district': self.district,
            'sector': self.sector,
            'isNationwide': self.is_nationwide,
            'validFrom': self.valid_from.isoformat() if self.valid_from else None,
            'validUntil': self.valid_until.isoformat() if self.valid_until else None,
            'createdBy': self.created_by,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Alert {self.title}>'
