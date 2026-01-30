from app import db
from datetime import datetime
import uuid


class Hotspot(db.Model):
    """Detected Incident Clusters via DBSCAN"""
    __tablename__ = 'hotspots'
    
    hotspot_id = db.Column(db.Integer, primary_key=True)
    cluster_label = db.Column(db.Integer, nullable=False)
    cluster_run_id = db.Column(db.String(36), db.ForeignKey('clustering_runs.run_id'))
    
    # Spatial Data
    centroid_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    centroid_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    boundary_geojson = db.Column(db.JSON)
    radius_meters = db.Column(db.Numeric(10, 2))
    area_sq_meters = db.Column(db.Numeric(12, 2))
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    sector_id = db.Column(db.Integer, db.ForeignKey('sectors.sector_id'))
    cell_id = db.Column(db.Integer, db.ForeignKey('cells.cell_id'))
    village_id = db.Column(db.Integer, db.ForeignKey('villages.village_id'))
    
    # Cluster Statistics
    report_count = db.Column(db.Integer, default=0)
    unique_devices = db.Column(db.Integer, default=0)
    avg_trust_score = db.Column(db.Numeric(5, 2))
    min_trust_score = db.Column(db.Numeric(5, 2))
    max_trust_score = db.Column(db.Numeric(5, 2))
    std_trust_score = db.Column(db.Numeric(5, 2))
    weighted_trust_density = db.Column(db.Numeric(10, 4))
    trusted_report_count = db.Column(db.Integer, default=0)
    suspicious_report_count = db.Column(db.Integer, default=0)
    false_report_count = db.Column(db.Integer, default=0)
    police_verified_count = db.Column(db.Integer, default=0)
    
    # Temporal Data
    earliest_incident_at = db.Column(db.DateTime)
    latest_incident_at = db.Column(db.DateTime)
    time_span_hours = db.Column(db.Integer)
    peak_hour = db.Column(db.Integer)
    peak_day_of_week = db.Column(db.Integer)
    
    # Incident Analysis
    incident_type_distribution = db.Column(db.JSON)
    dominant_incident_type_id = db.Column(db.Integer, db.ForeignKey('incident_types.type_id'))
    dominant_incident_pct = db.Column(db.Numeric(5, 2))
    
    # Risk Assessment
    risk_level = db.Column(db.Enum('low', 'medium', 'high', 'critical'), default='low')
    priority_score = db.Column(db.Numeric(5, 2))
    risk_factors = db.Column(db.JSON)
    
    # DBSCAN Parameters
    dbscan_epsilon_meters = db.Column(db.Numeric(10, 2))
    dbscan_min_samples = db.Column(db.Integer)
    trust_weight_enabled = db.Column(db.Boolean, default=False)
    
    # Status & Response
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum('new', 'monitoring', 'responding', 'addressed', 'recurring'), default='new')
    is_assigned = db.Column(db.Boolean, default=False)
    assigned_to_officer_id = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    assigned_to_unit = db.Column(db.String(100))
    assigned_at = db.Column(db.DateTime)
    is_addressed = db.Column(db.Boolean, default=False)
    addressed_at = db.Column(db.DateTime)
    addressed_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    resolution_notes = db.Column(db.Text)
    
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_report_added_at = db.Column(db.DateTime)
    
    # Relationships
    reports = db.relationship('HotspotReport', backref='hotspot', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('HotspotHistory', backref='hotspot', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_hotspot_district_id', 'district_id'),
        db.Index('idx_hotspot_status', 'status'),
        db.Index('idx_hotspot_risk_level', 'risk_level'),
    )


class HotspotReport(db.Model):
    """Bridge Table - Links reports to hotspot clusters"""
    __tablename__ = 'hotspot_reports'
    
    hotspot_id = db.Column(db.Integer, db.ForeignKey('hotspots.hotspot_id'), primary_key=True)
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'), primary_key=True)
    trust_weight = db.Column(db.Numeric(5, 4))
    distance_to_centroid_meters = db.Column(db.Numeric(10, 2))
    is_core_point = db.Column(db.Boolean, default=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_hotspot_report_hotspot_id', 'hotspot_id'),
    )


class HotspotHistory(db.Model):
    """Hotspot Trends - Historical snapshots"""
    __tablename__ = 'hotspot_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    hotspot_id = db.Column(db.Integer, db.ForeignKey('hotspots.hotspot_id'), nullable=False)
    snapshot_date = db.Column(db.Date, nullable=False)
    report_count = db.Column(db.Integer)
    avg_trust_score = db.Column(db.Numeric(5, 2))
    risk_level = db.Column(db.Enum('low', 'medium', 'high', 'critical'))
    priority_score = db.Column(db.Numeric(5, 2))
    report_count_change = db.Column(db.Integer)
    trust_score_change = db.Column(db.Numeric(5, 2))
    risk_level_changed = db.Column(db.Boolean)
    trend_direction = db.Column(db.Enum('improving', 'stable', 'worsening'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_hotspot_history_hotspot_id', 'hotspot_id'),
    )


class ClusteringRun(db.Model):
    """Clustering Execution Logs"""
    __tablename__ = 'clustering_runs'
    
    run_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'))
    epsilon_meters = db.Column(db.Numeric(10, 2), nullable=False)
    min_samples = db.Column(db.Integer, nullable=False)
    trust_weight_enabled = db.Column(db.Boolean, default=False)
    min_trust_score_threshold = db.Column(db.Numeric(5, 2))
    total_reports_processed = db.Column(db.Integer)
    reports_after_filtering = db.Column(db.Integer)
    date_range_start = db.Column(db.DateTime)
    date_range_end = db.Column(db.DateTime)
    clusters_found = db.Column(db.Integer)
    noise_points = db.Column(db.Integer)
    avg_cluster_size = db.Column(db.Numeric(8, 2))
    execution_time_seconds = db.Column(db.Numeric(10, 2))
    status = db.Column(db.Enum('running', 'completed', 'failed'), default='running')
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    triggered_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    
    # Relationships
    hotspots = db.relationship('Hotspot', backref='clustering_run', lazy=True)
    
    __table_args__ = (
        db.Index('idx_clustering_run_district_id', 'district_id'),
    )
