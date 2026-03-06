"""
Point-in-polygon lookup: given (lat, lon), find the village (location_type='village')
whose geometry contains the point. Used to set report.village_location_id.

Falls back to nearest-village lookup (within ~500 m) when the point lands in a
gap between village polygon boundaries (roads, rivers, boundary edges).
A final district-level bounding-box check prevents truly out-of-area reports.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.location import Location

# Musanze District approximate bounding box (generous padding)
_MUSANZE_LAT_MIN = -1.70
_MUSANZE_LAT_MAX = -1.35
_MUSANZE_LON_MIN = 29.35
_MUSANZE_LON_MAX = 29.75


def _is_inside_musanze_bbox(latitude: float, longitude: float) -> bool:
    """Quick bounding-box check — is the point roughly inside Musanze District?"""
    return (
        _MUSANZE_LAT_MIN <= latitude <= _MUSANZE_LAT_MAX
        and _MUSANZE_LON_MIN <= longitude <= _MUSANZE_LON_MAX
    )


def get_village_location_id(db: Session, latitude: float, longitude: float) -> int | None:
    """
    Return location_id of the village for the point (lat, lon), or None if the
    point is outside Musanze District.

    Strategy:
      1. Exact ST_Contains — point is inside a village polygon.
      2. Nearest village within ~500 m (ST_DWithin) — covers gaps between polygons.
      3. District bounding-box fallback — if inside the box, assign the nearest
         village regardless of distance so the report is not rejected.
    """
    # --- Step 1: exact polygon match ---
    q_exact = text("""
        SELECT location_id
        FROM locations
        WHERE location_type = 'village'
          AND is_active = true
          AND geometry IS NOT NULL
          AND ST_Contains(
              geometry,
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
          )
        LIMIT 1
    """)
    row = db.execute(q_exact, {"lat": latitude, "lon": longitude}).fetchone()
    if row:
        return int(row[0])

    # --- Step 2: nearest village within ~500 m buffer ---
    # 0.005 degrees ≈ 500 m at the equator; close enough for Rwanda (~1.5° S).
    q_near = text("""
        SELECT location_id,
               ST_Distance(
                   geometry::geography,
                   ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
               ) AS dist_m
        FROM locations
        WHERE location_type = 'village'
          AND is_active = true
          AND geometry IS NOT NULL
          AND ST_DWithin(
              geometry::geography,
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
              500
          )
        ORDER BY dist_m
        LIMIT 1
    """)
    row = db.execute(q_near, {"lat": latitude, "lon": longitude}).fetchone()
    if row:
        return int(row[0])

    # --- Step 3: bounding-box fallback — assign nearest village in entire district ---
    if _is_inside_musanze_bbox(latitude, longitude):
        q_fallback = text("""
            SELECT location_id,
                   ST_Distance(
                       geometry::geography,
                       ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                   ) AS dist_m
            FROM locations
            WHERE location_type = 'village'
              AND is_active = true
              AND geometry IS NOT NULL
            ORDER BY dist_m
            LIMIT 1
        """)
        row = db.execute(q_fallback, {"lat": latitude, "lon": longitude}).fetchone()
        if row:
            return int(row[0])

    return None


def get_village_location_info(db: Session, latitude: float, longitude: float) -> dict | None:
    """
    Return village name and parent hierarchy (cell, sector) for the point (lat, lon).
    Returns None if point is not inside any village.
    Returns dict with: location_id, village_name, cell_name (optional), sector_name (optional).
    """
    loc_id = get_village_location_id(db, latitude, longitude)
    if loc_id is None:
        return None
    village = db.query(Location).filter(Location.location_id == loc_id).first()
    if not village:
        return None
    out = {
        "location_id": loc_id,
        "village_name": village.location_name,
        "cell_name": None,
        "sector_name": None,
    }
    if village.parent_location_id:
        cell = db.query(Location).filter(Location.location_id == village.parent_location_id).first()
        if cell:
            out["cell_name"] = cell.location_name
            if cell.parent_location_id:
                sector = db.query(Location).filter(Location.location_id == cell.parent_location_id).first()
                if sector:
                    out["sector_name"] = sector.location_name
    return out
