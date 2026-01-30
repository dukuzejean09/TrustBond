"""
Geography Routes - Rwanda administrative geography endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services import GeographyService

geography_bp = Blueprint('geography', __name__)


# ==================== PROVINCE ENDPOINTS ====================
@geography_bp.route('/provinces', methods=['GET'])
def get_provinces():
    """Get all provinces"""
    provinces = GeographyService.get_all_provinces()
    
    return jsonify({
        'provinces': [GeographyService.province_to_dict(p) for p in provinces]
    }), 200


@geography_bp.route('/provinces/<int:province_id>', methods=['GET'])
def get_province(province_id):
    """Get province details with districts"""
    province = GeographyService.get_province_by_id(province_id)
    
    if not province:
        return jsonify({'error': 'Province not found'}), 404
    
    return jsonify({
        'province': GeographyService.province_to_dict(province, include_districts=True)
    }), 200


# ==================== DISTRICT ENDPOINTS ====================
@geography_bp.route('/districts', methods=['GET'])
def get_districts():
    """Get all districts or districts by province"""
    province_id = request.args.get('province_id', type=int)
    
    if province_id:
        districts = GeographyService.get_districts_by_province(province_id)
    else:
        districts = GeographyService.get_all_districts()
    
    return jsonify({
        'districts': [GeographyService.district_to_dict(d) for d in districts]
    }), 200


@geography_bp.route('/districts/<int:district_id>', methods=['GET'])
def get_district(district_id):
    """Get district details with sectors"""
    district = GeographyService.get_district_by_id(district_id)
    
    if not district:
        return jsonify({'error': 'District not found'}), 404
    
    return jsonify({
        'district': GeographyService.district_to_dict(district, include_sectors=True)
    }), 200


# ==================== SECTOR ENDPOINTS ====================
@geography_bp.route('/sectors', methods=['GET'])
def get_sectors():
    """Get sectors by district"""
    district_id = request.args.get('district_id', type=int)
    
    if not district_id:
        return jsonify({'error': 'district_id is required'}), 400
    
    sectors = GeographyService.get_sectors_by_district(district_id)
    
    return jsonify({
        'sectors': [GeographyService.sector_to_dict(s) for s in sectors]
    }), 200


@geography_bp.route('/sectors/<int:sector_id>', methods=['GET'])
def get_sector(sector_id):
    """Get sector details with cells"""
    sector = GeographyService.get_sector_by_id(sector_id)
    
    if not sector:
        return jsonify({'error': 'Sector not found'}), 404
    
    return jsonify({
        'sector': GeographyService.sector_to_dict(sector, include_cells=True)
    }), 200


# ==================== CELL ENDPOINTS ====================
@geography_bp.route('/cells', methods=['GET'])
def get_cells():
    """Get cells by sector"""
    sector_id = request.args.get('sector_id', type=int)
    
    if not sector_id:
        return jsonify({'error': 'sector_id is required'}), 400
    
    cells = GeographyService.get_cells_by_sector(sector_id)
    
    return jsonify({
        'cells': [GeographyService.cell_to_dict(c) for c in cells]
    }), 200


@geography_bp.route('/cells/<int:cell_id>', methods=['GET'])
def get_cell(cell_id):
    """Get cell details with villages"""
    cell = GeographyService.get_cell_by_id(cell_id)
    
    if not cell:
        return jsonify({'error': 'Cell not found'}), 404
    
    return jsonify({
        'cell': GeographyService.cell_to_dict(cell, include_villages=True)
    }), 200


# ==================== VILLAGE ENDPOINTS ====================
@geography_bp.route('/villages', methods=['GET'])
def get_villages():
    """Get villages by cell"""
    cell_id = request.args.get('cell_id', type=int)
    
    if not cell_id:
        return jsonify({'error': 'cell_id is required'}), 400
    
    villages = GeographyService.get_villages_by_cell(cell_id)
    
    return jsonify({
        'villages': [GeographyService.village_to_dict(v) for v in villages]
    }), 200


# ==================== LOCATION RESOLUTION ====================
@geography_bp.route('/resolve', methods=['POST'])
def resolve_location():
    """Resolve coordinates to administrative hierarchy"""
    data = request.get_json()
    
    if not data.get('latitude') or not data.get('longitude'):
        return jsonify({'error': 'latitude and longitude are required'}), 400
    
    try:
        location = GeographyService.resolve_location(
            latitude=float(data['latitude']),
            longitude=float(data['longitude'])
        )
        
        if not location:
            return jsonify({'error': 'Location could not be resolved'}), 404
        
        return jsonify({
            'location': location
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400


@geography_bp.route('/validate', methods=['POST'])
def validate_location():
    """Validate if coordinates are within Rwanda"""
    data = request.get_json()
    
    if not data.get('latitude') or not data.get('longitude'):
        return jsonify({'error': 'latitude and longitude are required'}), 400
    
    try:
        is_valid = GeographyService.validate_rwanda_location(
            latitude=float(data['latitude']),
            longitude=float(data['longitude'])
        )
        
        return jsonify({
            'is_valid': is_valid,
            'latitude': float(data['latitude']),
            'longitude': float(data['longitude'])
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400


# ==================== HIERARCHY ENDPOINTS ====================
@geography_bp.route('/hierarchy', methods=['GET'])
def get_hierarchy():
    """Get full administrative hierarchy"""
    hierarchy = GeographyService.get_full_hierarchy()
    
    return jsonify({
        'hierarchy': hierarchy
    }), 200


@geography_bp.route('/hierarchy/<int:district_id>', methods=['GET'])
def get_district_hierarchy(district_id):
    """Get hierarchy for a specific district"""
    hierarchy = GeographyService.get_district_hierarchy(district_id)
    
    if not hierarchy:
        return jsonify({'error': 'District not found'}), 404
    
    return jsonify({
        'hierarchy': hierarchy
    }), 200


# ==================== STATISTICS ====================
@geography_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_geography_statistics():
    """Get geography statistics"""
    stats = GeographyService.get_geography_statistics()
    
    return jsonify(stats), 200
