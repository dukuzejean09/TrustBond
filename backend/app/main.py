from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TrustBond — Anonymous Community Incident Reporting & Verification Platform",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ──────────────────────────────────────────────
from app.api import (
    auth,
    devices,
    reports,
    evidence,
    incident_types,
    locations,
    police_users,
    police_reviews,
    report_assignments,
    incident_groups,
    hotspots,
    notifications,
    audit_logs,
    ml,
    analytics,
)

app.include_router(auth.router,               prefix=f"{settings.API_V1_PREFIX}/auth",               tags=["Authentication"])
app.include_router(devices.router,             prefix=f"{settings.API_V1_PREFIX}/devices",             tags=["Devices"])
app.include_router(reports.router,             prefix=f"{settings.API_V1_PREFIX}/reports",             tags=["Reports"])
app.include_router(evidence.router,            prefix=f"{settings.API_V1_PREFIX}/evidence",            tags=["Evidence"])
app.include_router(incident_types.router,      prefix=f"{settings.API_V1_PREFIX}/incident-types",      tags=["Incident Types"])
app.include_router(locations.router,           prefix=f"{settings.API_V1_PREFIX}/locations",           tags=["Locations"])
app.include_router(police_users.router,        prefix=f"{settings.API_V1_PREFIX}/police-users",        tags=["Police Users"])
app.include_router(police_reviews.router,      prefix=f"{settings.API_V1_PREFIX}/police-reviews",      tags=["Police Reviews"])
app.include_router(report_assignments.router,  prefix=f"{settings.API_V1_PREFIX}/report-assignments",  tags=["Report Assignments"])
app.include_router(incident_groups.router,     prefix=f"{settings.API_V1_PREFIX}/incident-groups",     tags=["Incident Groups"])
app.include_router(hotspots.router,            prefix=f"{settings.API_V1_PREFIX}/hotspots",            tags=["Hotspots"])
app.include_router(notifications.router,       prefix=f"{settings.API_V1_PREFIX}/notifications",       tags=["Notifications"])
app.include_router(audit_logs.router,          prefix=f"{settings.API_V1_PREFIX}/audit-logs",          tags=["Audit Logs"])
app.include_router(ml.router,                  prefix=f"{settings.API_V1_PREFIX}/ml",                  tags=["ML Predictions"])
app.include_router(analytics.router,           prefix=f"{settings.API_V1_PREFIX}/analytics",           tags=["Analytics"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}
