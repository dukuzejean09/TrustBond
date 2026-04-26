from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.rate_limit import RouteRateLimitMiddleware
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
    public_locations,
    public_hotspots,
    public_alerts,
    ws,
    geographic_intelligence,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create PostGIS extension first (required for geometry type)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    yield
    # shutdown if needed


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)
app.add_middleware(
    RouteRateLimitMiddleware,
    report_create_per_minute=settings.rate_limit_report_create_per_minute,
    evidence_upload_per_minute=settings.rate_limit_evidence_upload_per_minute,
    report_confirm_per_minute=settings.rate_limit_report_confirm_per_minute,
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
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
app.include_router(public_locations.router, prefix="/api/v1")
app.include_router(public_hotspots.router, prefix="/api/v1")
app.include_router(public_alerts.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")
app.include_router(geographic_intelligence.router, prefix="/api/v1/geographic-intelligence")

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
@app.get("")
def home():
    return {""}