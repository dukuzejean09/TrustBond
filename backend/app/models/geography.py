from app import db
from datetime import datetime
import json


class Province(db.Model):
    """Rwanda Provinces - Top-level administrative divisions"""
    __tablename__ = 'provinces'
    
    province_id = db.Column(db.Integer, primary_key=True)
    province_name = db.Column(db.String(50), nullable=False, unique=True)
    province_code = db.Column(db.String(2), nullable=False, unique=True)
    boundary_geojson = db.Column(db.JSON)
    centroid_latitude = db.Column(db.Numeric(10, 8))
    centroid_longitude = db.Column(db.Numeric(11, 8))
    population = db.Column(db.Integer)
    area_sq_km = db.Column(db.Numeric(10, 2))
    district_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    districts = db.relationship('District', backref='province', lazy=True, cascade='all, delete-orphan')


class District(db.Model):
    """Rwanda Districts - Primary geographic unit for incidents"""
    __tablename__ = 'districts'
    
    district_id = db.Column(db.Integer, primary_key=True)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.province_id'), nullable=False)
    district_name = db.Column(db.String(100), nullable=False, unique=True)
    district_code = db.Column(db.String(10), nullable=False, unique=True)
    boundary_geojson = db.Column(db.JSON)
    centroid_latitude = db.Column(db.Numeric(10, 8))
    centroid_longitude = db.Column(db.Numeric(11, 8))
    population = db.Column(db.Integer)
    area_sq_km = db.Column(db.Numeric(10, 2))
    sector_count = db.Column(db.Integer, default=0)
    is_pilot_area = db.Column(db.Boolean, default=False)
    pilot_start_date = db.Column(db.Date)
    pilot_end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sectors = db.relationship('Sector', backref='district', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('IncidentReport', backref='district', lazy=True)
    
    __table_args__ = (
        db.Index('idx_district_province_id', 'province_id'),
    )


class Sector(db.Model):
    """Sectors within Districts"""
    __tablename__ = 'sectors'
    
    sector_id = db.Column(db.Integer, primary_key=True)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id'), nullable=False)
    sector_name = db.Column(db.String(100), nullable=False)
    sector_code = db.Column(db.String(20), nullable=False, unique=True)
    boundary_geojson = db.Column(db.JSON)
    centroid_latitude = db.Column(db.Numeric(10, 8))
    centroid_longitude = db.Column(db.Numeric(11, 8))
    population = db.Column(db.Integer)
    area_sq_km = db.Column(db.Numeric(10, 2))
    cell_count = db.Column(db.Integer, default=0)
    police_station_name = db.Column(db.String(100))
    police_station_contact = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cells = db.relationship('Cell', backref='sector', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('IncidentReport', backref='sector', lazy=True)
    
    __table_args__ = (
        db.Index('idx_sector_district_id', 'district_id'),
    )


class Cell(db.Model):
    """Cells within Sectors - Smallest official admin unit"""
    __tablename__ = 'cells'
    
    cell_id = db.Column(db.Integer, primary_key=True)
    sector_id = db.Column(db.Integer, db.ForeignKey('sectors.sector_id'), nullable=False)
    cell_name = db.Column(db.String(100), nullable=False)
    cell_code = db.Column(db.String(30), nullable=False, unique=True)
    boundary_geojson = db.Column(db.JSON)
    centroid_latitude = db.Column(db.Numeric(10, 8))
    centroid_longitude = db.Column(db.Numeric(11, 8))
    population = db.Column(db.Integer)
    area_sq_km = db.Column(db.Numeric(8, 2))
    cell_leader_title = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    villages = db.relationship('Village', backref='cell', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('IncidentReport', backref='cell', lazy=True)
    
    __table_args__ = (
        db.Index('idx_cell_sector_id', 'sector_id'),
    )


class Village(db.Model):
    """Villages within Cells - Fine-grained location detail"""
    __tablename__ = 'villages'
    
    village_id = db.Column(db.Integer, primary_key=True)
    cell_id = db.Column(db.Integer, db.ForeignKey('cells.cell_id'), nullable=False)
    village_name = db.Column(db.String(100), nullable=False)
    village_code = db.Column(db.String(40), nullable=False, unique=True)
    centroid_latitude = db.Column(db.Numeric(10, 8))
    centroid_longitude = db.Column(db.Numeric(11, 8))
    population = db.Column(db.Integer)
    household_count = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('IncidentReport', backref='village', lazy=True)
    
    __table_args__ = (
        db.Index('idx_village_cell_id', 'cell_id'),
    )
