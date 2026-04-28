"""
Point-in-polygon lookup: given (lat, lon), find the village (location_type='village')
whose geometry contains the point. Used to set report.village_location_id.

The mobile app uses a forgiving local GeoJSON lookup with a nearest-village fallback.
To avoid false rejections near polygon edges or on slightly invalid geometries,
the backend mirrors that behavior:
- prefer an exact geometry match
- accept boundary points
- fall back to the nearest village centroid within a small tolerance
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.location import Location

_NEAREST_VILLAGE_FALLBACK_METERS = 750


def _nearest_village_location_id(
    db: Session,
    latitude: float,
    longitude: float,
    max_distance_meters: int = _NEAREST_VILLAGE_FALLBACK_METERS,
) -> int | None:
    """
    Return the closest active village by centroid when geometry matching misses.

    This helps when:
    - a device point lands exactly on a polygon boundary
    - stored geometries are slightly invalid or simplified
    - GPS drift places the point just outside the polygon even though the user is
      practically inside the village
    """
    q = text(
        """
        SELECT location_id
        FROM locations
        WHERE location_type = 'village'
          AND is_active = true
          AND centroid_lat IS NOT NULL
          AND centroid_long IS NOT NULL
          AND ST_DWithin(
              geography(ST_SetSRID(ST_MakePoint(centroid_long, centroid_lat), 4326)),
              geography(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)),
              :max_distance_meters
          )
        ORDER BY ST_Distance(
            geography(ST_SetSRID(ST_MakePoint(centroid_long, centroid_lat), 4326)),
            geography(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        )
        LIMIT 1
        """
    )
    row = db.execute(
        q,
        {
            "lat": latitude,
            "lon": longitude,
            "max_distance_meters": max_distance_meters,
        },
    ).fetchone()
    return int(row[0]) if row else None


def get_village_location_id(db: Session, latitude: float, longitude: float) -> int | None:
    """
    Return location_id of the village containing the point (lat, lon), or None if none.
    Uses PostGIS with WGS84 (SRID 4326). ST_MakePoint(longitude, latitude).

    Notes:
    - ST_Covers accepts points on boundaries, unlike ST_Contains.
    - ST_MakeValid reduces failures from imperfect multipolygons.
    - If geometry lookup misses, use the nearest centroid within a modest radius.
    """
    q = text("""
        SELECT location_id
        FROM locations
        WHERE location_type = 'village'
          AND is_active = true
          AND geometry IS NOT NULL
          AND ST_Covers(
              ST_MakeValid(geometry),
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
          )
        LIMIT 1
    """)
    row = db.execute(q, {"lat": latitude, "lon": longitude}).fetchone()
    if row:
        return int(row[0])
    return _nearest_village_location_id(db, latitude, longitude)


def get_village_location_info(db: Session, latitude: float, longitude: float) -> dict | None:
    """
    Return village name and parent hierarchy (cell, sector, district) for the point (lat, lon).
    Returns None if point is not inside any village.
    Returns dict with:
    - village_location_id/location_id, village_name
    - cell_location_id/cell_name (optional)
    - sector_location_id/sector_name (optional)
    - district_location_id/district_name (optional)
    """
    loc_id = get_village_location_id(db, latitude, longitude)
    if loc_id is None:
        return None
    village = db.query(Location).filter(Location.location_id == loc_id).first()
    if not village:
        return None
    out = {
        "location_id": loc_id,
        "village_location_id": loc_id,
        "village_name": village.location_name,
        "cell_location_id": None,
        "cell_name": None,
        "sector_location_id": None,
        "sector_name": None,
        "district_location_id": None,
        "district_name": None,
    }
    if village.parent_location_id:
        parent = db.query(Location).filter(Location.location_id == village.parent_location_id).first()
        if parent:
            if parent.location_type == "cell":
                out["cell_location_id"] = parent.location_id
                out["cell_name"] = parent.location_name
                if parent.parent_location_id:
                    sector = db.query(Location).filter(Location.location_id == parent.parent_location_id).first()
                    if sector:
                        out["sector_location_id"] = sector.location_id
                        out["sector_name"] = sector.location_name
                        if sector.parent_location_id:
                            district = (
                                db.query(Location)
                                .filter(Location.location_id == sector.parent_location_id)
                                .first()
                            )
                            if district:
                                out["district_location_id"] = district.location_id
                                out["district_name"] = district.location_name
            elif parent.location_type == "sector":
                # Some datasets have village directly under sector (no cell level).
                out["sector_location_id"] = parent.location_id
                out["sector_name"] = parent.location_name
                if parent.parent_location_id:
                    district = (
                        db.query(Location)
                        .filter(Location.location_id == parent.parent_location_id)
                        .first()
                    )
                    if district:
                        out["district_location_id"] = district.location_id
                        out["district_name"] = district.location_name
    return out
