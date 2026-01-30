from app import db
from datetime import datetime
import enum


class IncidentCategory(db.Model):
    """Main Incident Categories"""
    __tablename__ = 'incident_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon_name = db.Column(db.String(50))
    color_hex = db.Column(db.String(7))
    display_order = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    requires_evidence = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    types = db.relationship('IncidentType', backref='category', lazy=True, cascade='all, delete-orphan')


class IncidentType(db.Model):
    """Specific Incident Types within Categories"""
    __tablename__ = 'incident_types'
    
    type_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('incident_categories.category_id'), nullable=False)
    type_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    severity_level = db.Column(db.Integer)  # 1=Minor, 2=Low, 3=Medium, 4=High, 5=Critical
    response_priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent'), default='normal')
    requires_photo = db.Column(db.Boolean, default=False)
    requires_video = db.Column(db.Boolean, default=False)
    min_description_length = db.Column(db.Integer, default=20)
    icon_name = db.Column(db.String(50))
    display_order = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('IncidentReport', backref='incident_type', lazy=True)
    
    __table_args__ = (
        db.Index('idx_incident_type_category_id', 'category_id'),
    )
