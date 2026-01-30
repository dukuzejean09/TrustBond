from app import db
from datetime import datetime


class PublicSafetyZone(db.Model):
    """Anonymized Public Safety Data"""
    __tablename__ = 'public_safety_zones'
    
    zone_id = db.Column(db.Integer, primary_key=True)
    zone_type = db.Column(db.Enum('grid', 'sector', 'cell', 'custom'), nullable=False)
    zone_geometry = db.Column(db.JSON)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    sector_id = db.Column(db.Integer, db.ForeignKey('sectors.sector_id'))
    cell_id = db.Column(db.Integer, db.ForeignKey('cells.cell_id'))
    grid_row = db.Column(db.Integer)
    grid_col = db.Column(db.Integer)
    grid_size_meters = db.Column(db.Integer)
    
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.Enum('daily', 'weekly', 'monthly'), nullable=False)
    
    incident_count = db.Column(db.Integer)
    safety_score = db.Column(db.Numeric(5, 2))
    safety_level = db.Column(db.Enum('safe', 'moderate', 'elevated', 'high_risk'))
    incident_breakdown = db.Column(db.JSON)
    top_concern = db.Column(db.String(100))
    trend_vs_prev_period = db.Column(db.Enum('improving', 'stable', 'worsening'))
    
    display_color = db.Column(db.String(7))
    is_visible = db.Column(db.Boolean, default=True)
    min_display_threshold = db.Column(db.Integer, default=3)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_public_zone_period', 'period_start', 'period_end'),
    )
