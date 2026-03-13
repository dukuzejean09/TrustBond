from contextlib import asynccontextmanager
import logging
import traceback
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.config import settings
from app.database import engine, Base
from app.models import (
    Device,
    IncidentType,
    Location,
    Report,
    EvidenceFile,
    MLPrediction,
    PoliceUser,
    PoliceReview,
    Hotspot,
    IncidentGroup,
    ReportAssignment,
    Notification,
    AuditLog,
)
from app.api.v1 import (
    auth,
    devices,
    incident_types,
    police_users,
    reports,
    stats,
    hotspots,
    notifications,
    audit,
    locations,
    incident_groups,
    cases,
    stations,
    system_config,
    public_hotspots,
    public_locations,
)
from app.services.incident_type_importer import import_incident_types
from app.services.admin_seeder import create_default_admin
from scripts.populate_locations import populate_locations as seed_locations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Create PostGIS extension first (required for geometry type)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()

    # 2) Import incident types from data/incident_types.json (upsert)
    with Session(engine) as db:
        summary = import_incident_types(db)
        logger.info("[startup] Incident types import: %s", summary)

    # 3) Create default admin user if it doesn't exist
    with Session(engine) as db:
        admin_result = create_default_admin(db)
        logger.info("[startup] Admin user seeding: %s", admin_result['message'])

    # 4) Seed locations (sectors, cells, villages) if not already populated
    with Session(engine) as db:
        count = db.execute(text("SELECT COUNT(*) FROM locations")).scalar()
        if count == 0:
            logger.info("[startup] Seeding locations from GeoJSON...")
            seed_locations()
            logger.info("[startup] Locations seeded successfully.")
        else:
            logger.info("[startup] Locations already populated (%d rows).", count)

    yield
    # shutdown if needed


app = FastAPI(
    title=settings.app_name,
    description="TrustBond API – Incident reporting and community safety platform for Musanze District.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for evidence uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(incident_types.router, prefix="/api/v1")
app.include_router(police_users.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(hotspots.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(incident_groups.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
app.include_router(stations.router, prefix="/api/v1")
app.include_router(system_config.router, prefix="/api/v1")
app.include_router(public_hotspots.router, prefix="/api/v1")
app.include_router(public_locations.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, "".join(tb))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )