"""
Public Map Service - Public safety zone and map data management
"""
from app import db
from app.models.public_map import PublicSafetyZone
from app.models.hotspots import Hotspot
from datetime import datetime, timedelta
import uuid


class PublicMapService:
    """Service for public safety map data"""
    
    # ==================== SAFETY ZONES ====================
    @staticmethod
    def get_all_safety_zones(district_id=None, active_only=True):
        """Get all public safety zones"""
        query = PublicSafetyZone.query
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        if district_id:
            query = query.filter_by(district_id=district_id)
        
        return query.order_by(PublicSafetyZone.priority_order).all()
    
    @staticmethod
    def get_safety_zone_by_id(zone_id):
        """Get safety zone by ID"""
        return PublicSafetyZone.query.get(zone_id)
    
    @staticmethod
    def create_safety_zone(zone_data, created_by_user_id=None):
        """Create a new safety zone"""
        zone = PublicSafetyZone(
            zone_id=str(uuid.uuid4()),
            zone_name=zone_data.get('zone_name'),
            zone_type=zone_data.get('zone_type', 'caution'),
            description=zone_data.get('description'),
            safety_advice=zone_data.get('safety_advice'),
            centroid_latitude=zone_data.get('centroid_latitude'),
            centroid_longitude=zone_data.get('centroid_longitude'),
            radius_meters=zone_data.get('radius_meters', 500),
            boundary_polygon=zone_data.get('boundary_polygon'),
            district_id=zone_data.get('district_id'),
            sector_id=zone_data.get('sector_id'),
            incident_count=zone_data.get('incident_count', 0),
            risk_level=zone_data.get('risk_level', 'low'),
            hotspot_id=zone_data.get('hotspot_id'),
            valid_from=zone_data.get('valid_from', datetime.utcnow()),
            valid_until=zone_data.get('valid_until'),
            priority_order=zone_data.get('priority_order', 0),
            is_active=True,
            created_by=created_by_user_id
        )
        
        db.session.add(zone)
        db.session.commit()
        return zone
    
    @staticmethod
    def update_safety_zone(zone_id, update_data, updated_by_user_id=None):
        """Update a safety zone"""
        zone = PublicSafetyZone.query.get(zone_id)
        if not zone:
            return None
        
        allowed_fields = [
            'zone_name', 'zone_type', 'description', 'safety_advice',
            'centroid_latitude', 'centroid_longitude', 'radius_meters',
            'boundary_polygon', 'district_id', 'sector_id', 'incident_count',
            'risk_level', 'valid_from', 'valid_until', 'priority_order', 'is_active'
        ]
        
        for field in allowed_fields:
            if field in update_data:
                setattr(zone, field, update_data[field])
        
        zone.updated_at = datetime.utcnow()
        db.session.commit()
        return zone
    
    @staticmethod
    def delete_safety_zone(zone_id):
        """Delete/deactivate a safety zone"""
        zone = PublicSafetyZone.query.get(zone_id)
        if zone:
            zone.is_active = False
            zone.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    # ==================== PUBLIC MAP DATA ====================
    @staticmethod
    def get_public_map_data(district_id=None, include_zones=True, include_hotspots=True):
        """Get anonymized data for public safety map"""
        data = {
            'generated_at': datetime.utcnow().isoformat(),
            'zones': [],
            'hotspots': []
        }
        
        # Get safety zones
        if include_zones:
            zones = PublicMapService.get_all_safety_zones(district_id=district_id)
            data['zones'] = [PublicMapService.zone_to_public_dict(z) for z in zones]
        
        # Get hotspots (anonymized)
        if include_hotspots:
            hotspot_query = Hotspot.query.filter_by(is_active=True)
            if district_id:
                hotspot_query = hotspot_query.filter_by(district_id=district_id)
            
            hotspots = hotspot_query.filter(Hotspot.report_count >= 3).all()
            data['hotspots'] = [PublicMapService.hotspot_to_public_dict(h) for h in hotspots]
        
        return data
    
    @staticmethod
    def zone_to_public_dict(zone):
        """Convert zone to public dictionary (no sensitive data)"""
        if not zone:
            return None
        return {
            'zone_id': zone.zone_id,
            'zone_name': zone.zone_name,
            'zone_type': zone.zone_type,
            'description': zone.description,
            'safety_advice': zone.safety_advice,
            'latitude': float(zone.centroid_latitude) if zone.centroid_latitude else None,
            'longitude': float(zone.centroid_longitude) if zone.centroid_longitude else None,
            'radius_meters': float(zone.radius_meters) if zone.radius_meters else None,
            'risk_level': zone.risk_level,
            'incident_count': zone.incident_count,
            'valid_from': zone.valid_from.isoformat() if zone.valid_from else None,
            'valid_until': zone.valid_until.isoformat() if zone.valid_until else None
        }
    
    @staticmethod
    def hotspot_to_public_dict(hotspot):
        """Convert hotspot to public dictionary (anonymized)"""
        if not hotspot:
            return None
        
        # Get safety advice based on risk level
        advice_map = {
            'critical': 'High incident area. Exercise extreme caution and avoid if possible.',
            'high': 'Elevated risk area. Stay alert and avoid traveling alone.',
            'medium': 'Moderate activity area. Be aware of your surroundings.',
            'low': 'Generally safe area. Standard precautions recommended.'
        }
        
        return {
            'latitude': float(hotspot.centroid_latitude) if hotspot.centroid_latitude else None,
            'longitude': float(hotspot.centroid_longitude) if hotspot.centroid_longitude else None,
            'radius_meters': float(hotspot.radius_meters) if hotspot.radius_meters else 500,
            'risk_level': hotspot.risk_level,
            'incident_count': hotspot.report_count,
            'safety_advice': advice_map.get(hotspot.risk_level, advice_map['low'])
        }
    
    # ==================== SYNC FROM HOTSPOTS ====================
    @staticmethod
    def sync_zones_from_hotspots(min_reports=5, created_by_user_id=None):
        """Create/update safety zones from active hotspots"""
        hotspots = Hotspot.query.filter(
            Hotspot.is_active == True,
            Hotspot.report_count >= min_reports
        ).all()
        
        synced = []
        for hotspot in hotspots:
            # Check if zone already exists for this hotspot
            existing = PublicSafetyZone.query.filter_by(hotspot_id=hotspot.hotspot_id).first()
            
            if existing:
                # Update existing zone
                existing.incident_count = hotspot.report_count
                existing.risk_level = hotspot.risk_level
                existing.centroid_latitude = hotspot.centroid_latitude
                existing.centroid_longitude = hotspot.centroid_longitude
                existing.radius_meters = hotspot.radius_meters
                existing.updated_at = datetime.utcnow()
                synced.append(existing)
            else:
                # Create new zone
                zone = PublicMapService.create_safety_zone({
                    'zone_name': f'Safety Alert Zone {hotspot.hotspot_id[:8]}',
                    'zone_type': 'hotspot',
                    'description': f'Area with elevated incident activity',
                    'centroid_latitude': hotspot.centroid_latitude,
                    'centroid_longitude': hotspot.centroid_longitude,
                    'radius_meters': hotspot.radius_meters or 500,
                    'district_id': hotspot.district_id,
                    'sector_id': hotspot.sector_id,
                    'incident_count': hotspot.report_count,
                    'risk_level': hotspot.risk_level,
                    'hotspot_id': hotspot.hotspot_id
                }, created_by_user_id)
                synced.append(zone)
        
        db.session.commit()
        return synced
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def zone_to_dict(zone):
        """Convert zone to full dictionary"""
        if not zone:
            return None
        return {
            'zone_id': zone.zone_id,
            'zone_name': zone.zone_name,
            'zone_type': zone.zone_type,
            'description': zone.description,
            'safety_advice': zone.safety_advice,
            'centroid_latitude': float(zone.centroid_latitude) if zone.centroid_latitude else None,
            'centroid_longitude': float(zone.centroid_longitude) if zone.centroid_longitude else None,
            'radius_meters': float(zone.radius_meters) if zone.radius_meters else None,
            'boundary_polygon': zone.boundary_polygon,
            'district_id': zone.district_id,
            'sector_id': zone.sector_id,
            'incident_count': zone.incident_count,
            'risk_level': zone.risk_level,
            'hotspot_id': zone.hotspot_id,
            'valid_from': zone.valid_from.isoformat() if zone.valid_from else None,
            'valid_until': zone.valid_until.isoformat() if zone.valid_until else None,
            'priority_order': zone.priority_order,
            'is_active': zone.is_active,
            'created_at': zone.created_at.isoformat() if zone.created_at else None,
            'updated_at': zone.updated_at.isoformat() if zone.updated_at else None
        }
