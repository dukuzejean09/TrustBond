from app import db
from datetime import datetime


class DailyStatistic(db.Model):
    """Aggregated Daily Metrics"""
    __tablename__ = 'daily_statistics'
    
    stat_id = db.Column(db.Integer, primary_key=True)
    stat_date = db.Column(db.Date, nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    sector_id = db.Column(db.Integer, db.ForeignKey('sectors.sector_id'))
    
    # Report Metrics
    total_reports = db.Column(db.Integer, default=0)
    trusted_reports = db.Column(db.Integer, default=0)
    suspicious_reports = db.Column(db.Integer, default=0)
    false_reports = db.Column(db.Integer, default=0)
    pending_reports = db.Column(db.Integer, default=0)
    avg_trust_score = db.Column(db.Numeric(5, 2))
    median_trust_score = db.Column(db.Numeric(5, 2))
    
    # Evidence Metrics
    reports_with_photo = db.Column(db.Integer, default=0)
    reports_with_video = db.Column(db.Integer, default=0)
    
    # Verification Metrics
    reports_police_verified = db.Column(db.Integer, default=0)
    reports_confirmed = db.Column(db.Integer, default=0)
    reports_rejected = db.Column(db.Integer, default=0)
    verification_rate = db.Column(db.Numeric(5, 2))
    avg_verification_time_hours = db.Column(db.Numeric(8, 2))
    
    # Hotspot Metrics
    active_hotspots = db.Column(db.Integer, default=0)
    new_hotspots = db.Column(db.Integer, default=0)
    resolved_hotspots = db.Column(db.Integer, default=0)
    critical_hotspots = db.Column(db.Integer, default=0)
    
    # Device Metrics
    unique_reporting_devices = db.Column(db.Integer, default=0)
    new_devices = db.Column(db.Integer, default=0)
    blocked_devices = db.Column(db.Integer, default=0)
    avg_device_trust_score = db.Column(db.Numeric(5, 2))
    
    # Response Metrics
    reports_assigned = db.Column(db.Integer, default=0)
    reports_resolved = db.Column(db.Integer, default=0)
    avg_resolution_time_hours = db.Column(db.Numeric(8, 2))
    
    # Incident Analysis
    incident_type_counts = db.Column(db.JSON)
    top_incident_type_id = db.Column(db.Integer, db.ForeignKey('incident_types.type_id'))
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_daily_stat_stat_date', 'stat_date'),
        db.Index('idx_daily_stat_district_id', 'district_id'),
    )


class IncidentTypeTrend(db.Model):
    """Weekly Trends by Incident Type"""
    __tablename__ = 'incident_type_trends'
    
    trend_id = db.Column(db.Integer, primary_key=True)
    incident_type_id = db.Column(db.Integer, db.ForeignKey('incident_types.type_id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    week_start_date = db.Column(db.Date, nullable=False)
    week_end_date = db.Column(db.Date, nullable=False)
    year_week = db.Column(db.String(7), nullable=False)
    
    report_count = db.Column(db.Integer)
    trusted_count = db.Column(db.Integer)
    suspicious_count = db.Column(db.Integer)
    false_count = db.Column(db.Integer)
    avg_trust_score = db.Column(db.Numeric(5, 2))
    police_verified_count = db.Column(db.Integer)
    
    prev_week_count = db.Column(db.Integer)
    count_change = db.Column(db.Integer)
    count_change_pct = db.Column(db.Numeric(6, 2))
    trend_direction = db.Column(db.Enum('increasing', 'stable', 'decreasing'))
    associated_hotspots = db.Column(db.Integer)
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_trend_incident_type_id', 'incident_type_id'),
        db.Index('idx_trend_week_start_date', 'week_start_date'),
    )
