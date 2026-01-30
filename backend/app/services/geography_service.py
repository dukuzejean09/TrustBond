"""
Geography Service - Rwanda Administrative Geography Management
"""
from app import db
from app.models.geography import Province, District, Sector, Cell, Village
from geopy.distance import geodesic


class GeographyService:
    """Service for managing Rwanda administrative geography"""
    
    # ==================== PROVINCES ====================
    @staticmethod
    def get_all_provinces():
        """Get all provinces"""
        return Province.query.order_by(Province.province_name).all()
    
    @staticmethod
    def get_province_by_id(province_id):
        """Get province by ID"""
        return Province.query.get(province_id)
    
    @staticmethod
    def create_province(data):
        """Create a new province"""
        province = Province(
            province_id=data.get('province_id'),
            province_name=data['province_name'],
            province_code=data['province_code'],
            boundary_geojson=data.get('boundary_geojson'),
            centroid_latitude=data.get('centroid_latitude'),
            centroid_longitude=data.get('centroid_longitude'),
            population=data.get('population'),
            area_sq_km=data.get('area_sq_km'),
            district_count=data.get('district_count', 0)
        )
        db.session.add(province)
        db.session.commit()
        return province
    
    # ==================== DISTRICTS ====================
    @staticmethod
    def get_all_districts(province_id=None):
        """Get all districts, optionally filtered by province"""
        query = District.query
        if province_id:
            query = query.filter_by(province_id=province_id)
        return query.filter_by(is_active=True).order_by(District.district_name).all()
    
    @staticmethod
    def get_district_by_id(district_id):
        """Get district by ID"""
        return District.query.get(district_id)
    
    @staticmethod
    def get_district_by_code(district_code):
        """Get district by code"""
        return District.query.filter_by(district_code=district_code).first()
    
    @staticmethod
    def create_district(data):
        """Create a new district"""
        district = District(
            district_id=data.get('district_id'),
            province_id=data['province_id'],
            district_name=data['district_name'],
            district_code=data['district_code'],
            boundary_geojson=data.get('boundary_geojson'),
            centroid_latitude=data.get('centroid_latitude'),
            centroid_longitude=data.get('centroid_longitude'),
            population=data.get('population'),
            area_sq_km=data.get('area_sq_km'),
            sector_count=data.get('sector_count', 0),
            is_pilot_area=data.get('is_pilot_area', False),
            pilot_start_date=data.get('pilot_start_date'),
            pilot_end_date=data.get('pilot_end_date'),
            is_active=True
        )
        db.session.add(district)
        db.session.commit()
        return district
    
    @staticmethod
    def get_pilot_districts():
        """Get districts marked as pilot areas"""
        return District.query.filter_by(is_pilot_area=True, is_active=True).all()
    
    # ==================== SECTORS ====================
    @staticmethod
    def get_all_sectors(district_id=None):
        """Get all sectors, optionally filtered by district"""
        query = Sector.query
        if district_id:
            query = query.filter_by(district_id=district_id)
        return query.filter_by(is_active=True).order_by(Sector.sector_name).all()
    
    @staticmethod
    def get_sector_by_id(sector_id):
        """Get sector by ID"""
        return Sector.query.get(sector_id)
    
    @staticmethod
    def get_sector_by_code(sector_code):
        """Get sector by code"""
        return Sector.query.filter_by(sector_code=sector_code).first()
    
    @staticmethod
    def create_sector(data):
        """Create a new sector"""
        sector = Sector(
            sector_id=data.get('sector_id'),
            district_id=data['district_id'],
            sector_name=data['sector_name'],
            sector_code=data['sector_code'],
            boundary_geojson=data.get('boundary_geojson'),
            centroid_latitude=data.get('centroid_latitude'),
            centroid_longitude=data.get('centroid_longitude'),
            population=data.get('population'),
            area_sq_km=data.get('area_sq_km'),
            cell_count=data.get('cell_count', 0),
            police_station_name=data.get('police_station_name'),
            police_station_contact=data.get('police_station_contact'),
            is_active=True
        )
        db.session.add(sector)
        db.session.commit()
        return sector
    
    # ==================== CELLS ====================
    @staticmethod
    def get_all_cells(sector_id=None):
        """Get all cells, optionally filtered by sector"""
        query = Cell.query
        if sector_id:
            query = query.filter_by(sector_id=sector_id)
        return query.filter_by(is_active=True).order_by(Cell.cell_name).all()
    
    @staticmethod
    def get_cell_by_id(cell_id):
        """Get cell by ID"""
        return Cell.query.get(cell_id)
    
    @staticmethod
    def get_cell_by_code(cell_code):
        """Get cell by code"""
        return Cell.query.filter_by(cell_code=cell_code).first()
    
    @staticmethod
    def create_cell(data):
        """Create a new cell"""
        cell = Cell(
            cell_id=data.get('cell_id'),
            sector_id=data['sector_id'],
            cell_name=data['cell_name'],
            cell_code=data['cell_code'],
            boundary_geojson=data.get('boundary_geojson'),
            centroid_latitude=data.get('centroid_latitude'),
            centroid_longitude=data.get('centroid_longitude'),
            population=data.get('population'),
            area_sq_km=data.get('area_sq_km'),
            cell_leader_title=data.get('cell_leader_title'),
            is_active=True
        )
        db.session.add(cell)
        db.session.commit()
        return cell
    
    # ==================== VILLAGES ====================
    @staticmethod
    def get_all_villages(cell_id=None):
        """Get all villages, optionally filtered by cell"""
        query = Village.query
        if cell_id:
            query = query.filter_by(cell_id=cell_id)
        return query.filter_by(is_active=True).order_by(Village.village_name).all()
    
    @staticmethod
    def get_village_by_id(village_id):
        """Get village by ID"""
        return Village.query.get(village_id)
    
    @staticmethod
    def create_village(data):
        """Create a new village"""
        village = Village(
            cell_id=data['cell_id'],
            village_name=data['village_name'],
            village_code=data['village_code'],
            centroid_latitude=data.get('centroid_latitude'),
            centroid_longitude=data.get('centroid_longitude'),
            population=data.get('population'),
            household_count=data.get('household_count'),
            is_active=True
        )
        db.session.add(village)
        db.session.commit()
        return village
    
    # ==================== LOCATION RESOLUTION ====================
    @staticmethod
    def resolve_location(latitude, longitude):
        """
        Resolve geographic coordinates to administrative units
        Returns dict with district_id, sector_id, cell_id, village_id
        """
        # Find nearest district
        districts = District.query.filter_by(is_active=True).all()
        nearest_district = None
        min_distance = float('inf')
        
        for district in districts:
            if district.centroid_latitude and district.centroid_longitude:
                dist = geodesic(
                    (latitude, longitude),
                    (float(district.centroid_latitude), float(district.centroid_longitude))
                ).meters
                if dist < min_distance:
                    min_distance = dist
                    nearest_district = district
        
        result = {
            'district_id': nearest_district.district_id if nearest_district else None,
            'district_name': nearest_district.district_name if nearest_district else None,
            'sector_id': None,
            'sector_name': None,
            'cell_id': None,
            'cell_name': None,
            'village_id': None,
            'village_name': None
        }
        
        if not nearest_district:
            return result
        
        # Find nearest sector within district
        sectors = Sector.query.filter_by(district_id=nearest_district.district_id, is_active=True).all()
        nearest_sector = None
        min_distance = float('inf')
        
        for sector in sectors:
            if sector.centroid_latitude and sector.centroid_longitude:
                dist = geodesic(
                    (latitude, longitude),
                    (float(sector.centroid_latitude), float(sector.centroid_longitude))
                ).meters
                if dist < min_distance:
                    min_distance = dist
                    nearest_sector = sector
        
        if nearest_sector:
            result['sector_id'] = nearest_sector.sector_id
            result['sector_name'] = nearest_sector.sector_name
            
            # Find nearest cell within sector
            cells = Cell.query.filter_by(sector_id=nearest_sector.sector_id, is_active=True).all()
            nearest_cell = None
            min_distance = float('inf')
            
            for cell in cells:
                if cell.centroid_latitude and cell.centroid_longitude:
                    dist = geodesic(
                        (latitude, longitude),
                        (float(cell.centroid_latitude), float(cell.centroid_longitude))
                    ).meters
                    if dist < min_distance:
                        min_distance = dist
                        nearest_cell = cell
            
            if nearest_cell:
                result['cell_id'] = nearest_cell.cell_id
                result['cell_name'] = nearest_cell.cell_name
                
                # Find nearest village within cell
                villages = Village.query.filter_by(cell_id=nearest_cell.cell_id, is_active=True).all()
                nearest_village = None
                min_distance = float('inf')
                
                for village in villages:
                    if village.centroid_latitude and village.centroid_longitude:
                        dist = geodesic(
                            (latitude, longitude),
                            (float(village.centroid_latitude), float(village.centroid_longitude))
                        ).meters
                        if dist < min_distance:
                            min_distance = dist
                            nearest_village = village
                
                if nearest_village:
                    result['village_id'] = nearest_village.village_id
                    result['village_name'] = nearest_village.village_name
        
        return result
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def province_to_dict(province):
        """Convert province to dictionary"""
        if not province:
            return None
        return {
            'province_id': province.province_id,
            'province_name': province.province_name,
            'province_code': province.province_code,
            'centroid_latitude': float(province.centroid_latitude) if province.centroid_latitude else None,
            'centroid_longitude': float(province.centroid_longitude) if province.centroid_longitude else None,
            'population': province.population,
            'area_sq_km': float(province.area_sq_km) if province.area_sq_km else None,
            'district_count': province.district_count
        }
    
    @staticmethod
    def district_to_dict(district, include_sectors=False):
        """Convert district to dictionary"""
        if not district:
            return None
        result = {
            'district_id': district.district_id,
            'province_id': district.province_id,
            'district_name': district.district_name,
            'district_code': district.district_code,
            'centroid_latitude': float(district.centroid_latitude) if district.centroid_latitude else None,
            'centroid_longitude': float(district.centroid_longitude) if district.centroid_longitude else None,
            'population': district.population,
            'area_sq_km': float(district.area_sq_km) if district.area_sq_km else None,
            'sector_count': district.sector_count,
            'is_pilot_area': district.is_pilot_area,
            'is_active': district.is_active
        }
        if include_sectors:
            result['sectors'] = [GeographyService.sector_to_dict(s) for s in district.sectors]
        return result
    
    @staticmethod
    def sector_to_dict(sector, include_cells=False):
        """Convert sector to dictionary"""
        if not sector:
            return None
        result = {
            'sector_id': sector.sector_id,
            'district_id': sector.district_id,
            'sector_name': sector.sector_name,
            'sector_code': sector.sector_code,
            'centroid_latitude': float(sector.centroid_latitude) if sector.centroid_latitude else None,
            'centroid_longitude': float(sector.centroid_longitude) if sector.centroid_longitude else None,
            'population': sector.population,
            'area_sq_km': float(sector.area_sq_km) if sector.area_sq_km else None,
            'cell_count': sector.cell_count,
            'police_station_name': sector.police_station_name,
            'police_station_contact': sector.police_station_contact,
            'is_active': sector.is_active
        }
        if include_cells:
            result['cells'] = [GeographyService.cell_to_dict(c) for c in sector.cells]
        return result
    
    @staticmethod
    def cell_to_dict(cell, include_villages=False):
        """Convert cell to dictionary"""
        if not cell:
            return None
        result = {
            'cell_id': cell.cell_id,
            'sector_id': cell.sector_id,
            'cell_name': cell.cell_name,
            'cell_code': cell.cell_code,
            'centroid_latitude': float(cell.centroid_latitude) if cell.centroid_latitude else None,
            'centroid_longitude': float(cell.centroid_longitude) if cell.centroid_longitude else None,
            'population': cell.population,
            'area_sq_km': float(cell.area_sq_km) if cell.area_sq_km else None,
            'cell_leader_title': cell.cell_leader_title,
            'is_active': cell.is_active
        }
        if include_villages:
            result['villages'] = [GeographyService.village_to_dict(v) for v in cell.villages]
        return result
    
    @staticmethod
    def village_to_dict(village):
        """Convert village to dictionary"""
        if not village:
            return None
        return {
            'village_id': village.village_id,
            'cell_id': village.cell_id,
            'village_name': village.village_name,
            'village_code': village.village_code,
            'centroid_latitude': float(village.centroid_latitude) if village.centroid_latitude else None,
            'centroid_longitude': float(village.centroid_longitude) if village.centroid_longitude else None,
            'population': village.population,
            'household_count': village.household_count,
            'is_active': village.is_active
        }
    
    @staticmethod
    def get_full_hierarchy():
        """Get complete geographic hierarchy"""
        provinces = Province.query.order_by(Province.province_name).all()
        result = []
        
        for province in provinces:
            prov_data = GeographyService.province_to_dict(province)
            prov_data['districts'] = []
            
            for district in District.query.filter_by(province_id=province.province_id, is_active=True).all():
                dist_data = GeographyService.district_to_dict(district)
                dist_data['sectors'] = []
                
                for sector in Sector.query.filter_by(district_id=district.district_id, is_active=True).all():
                    sect_data = GeographyService.sector_to_dict(sector)
                    sect_data['cells'] = []
                    
                    for cell in Cell.query.filter_by(sector_id=sector.sector_id, is_active=True).all():
                        cell_data = GeographyService.cell_to_dict(cell)
                        cell_data['villages'] = [
                            GeographyService.village_to_dict(v) 
                            for v in Village.query.filter_by(cell_id=cell.cell_id, is_active=True).all()
                        ]
                        sect_data['cells'].append(cell_data)
                    
                    dist_data['sectors'].append(sect_data)
                
                prov_data['districts'].append(dist_data)
            
            result.append(prov_data)
        
        return result
