"""Import Musanze locations (sectors, cells, villages) from the provided GeoJSON.

- Reads ML_model/Village level boundary/Musanze_Villages.geojson
- Inserts missing sectors/cells/villages into `locations` with geometry (villages)
- Sets centroid_lat/centroid_long from feature properties when available

Run: python backend/scripts/import_musanze_locations.py
"""
import json
import os
from pathlib import Path
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.location import Location

BASE = Path(__file__).resolve().parents[1]  # backend/
GEOJSON_PATH = (BASE.parent / 'ML_model' / 'Village level boundary' / 'Musanze_Villages.geojson')
if not GEOJSON_PATH.exists():
    raise SystemExit(f"GeoJSON not found: {GEOJSON_PATH}")

session = SessionLocal()
try:
    with GEOJSON_PATH.open('r', encoding='utf-8') as fh:
        data = json.load(fh)

    features = data.get('features', [])
    print(f"Found {len(features)} features in {GEOJSON_PATH.name}")

    sectors = {}
    cells = {}
    villages = 0

    for f in features:
        props = f.get('properties', {})
        geom = f.get('geometry')

        sector_name = props.get('NAME_3') or props.get('NAME_2')
        cell_name = props.get('NAME_4')
        village_name = props.get('NAME_5')
        centroid_lat = props.get('latitude')
        centroid_long = props.get('longitude')

        # --- sector ---
        sector_id = None
        if sector_name:
            sector = (
                session.execute(
                    select(Location).where(
                        Location.location_type == 'sector',
                        Location.location_name == sector_name,
                    )
                ).scalars().first()
            )
            if not sector:
                sector = Location(
                    location_type='sector',
                    location_name=sector_name,
                    parent_location_id=None,
                    geometry=None,
                    centroid_lat=None,
                    centroid_long=None,
                )
                session.add(sector)
                session.flush()
                print(f"Inserted sector: {sector_name} (id={sector.location_id})")
            sector_id = sector.location_id
            sectors[sector_name] = sector_id

        # --- cell ---
        cell_id = None
        if cell_name:
            cell = (
                session.execute(
                    select(Location).where(
                        Location.location_type == 'cell',
                        Location.location_name == cell_name,
                        Location.parent_location_id == sector_id,
                    )
                ).scalars().first()
            )
            if not cell:
                cell = Location(
                    location_type='cell',
                    location_name=cell_name,
                    parent_location_id=sector_id,
                    geometry=None,
                    centroid_lat=None,
                    centroid_long=None,
                )
                session.add(cell)
                session.flush()
                print(f"Inserted cell: {cell_name} (id={cell.location_id}) parent_sector={sector_name}")
            cell_id = cell.location_id
            cells[(cell_name, sector_id)] = cell_id

        # --- village ---
        if village_name:
            # avoid duplicates by name+parent
            existing = (
                session.execute(
                    select(Location).where(
                        Location.location_type == 'village',
                        Location.location_name == village_name,
                        Location.parent_location_id == cell_id,
                    )
                ).scalars().first()
            )
            if existing:
                continue

            # Insert with geometry using ST_GeomFromGeoJSON; geometry may be None for some features
            geom_json = json.dumps(geom) if geom else None

            loc = Location(
                location_type='village',
                location_name=village_name,
                parent_location_id=cell_id,
                centroid_lat=float(centroid_lat) if centroid_lat is not None else None,
                centroid_long=float(centroid_long) if centroid_long is not None else None,
            )
            session.add(loc)
            session.flush()  # get location_id

            if geom_json:
                # set geometry via raw SQL to ensure SRID is set correctly
                session.execute(
                    "UPDATE locations SET geometry = ST_SetSRID(ST_GeomFromGeoJSON(:geo), 4326) WHERE location_id = :id",
                    {"geo": geom_json, "id": loc.location_id},
                )

            villages += 1

    session.commit()
    print(f"Import complete — sectors: {len(sectors)}, cells: {len(cells)}, villages inserted: {villages}")
finally:
    session.close()
