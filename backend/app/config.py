from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Resolve .env regardless of working directory (Alembic, Render, local dev).
# Priority: backend/.env relative to this file → .env in cwd as last resort.
_HERE = Path(__file__).resolve().parent          # backend/app/
_BACKEND_ENV = _HERE.parent / ".env"             # backend/.env
_ENV_FILE = str(_BACKEND_ENV) if _BACKEND_ENV.exists() else ".env"


class Settings(BaseSettings):
    app_name: str = "TrustBond API"
    debug: bool = False
    database_url: str = "postgresql://neondb_owner:npg_TYSOxwo1lLM6@ep-weathered-snow-ago27130-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    secret_key: str = "change-me-in-production"

    # CORS: comma-separated origins, e.g. "https://dashboard.trustbond.rw". Empty = allow all ("*").
    cors_origins: str = "https://trustbond-dashboard.vercel.app,http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    # Optional regex for dynamic origins (e.g. ngrok): r"https://.*\\.ngrok-free\\.dev"
    cors_origin_regex: Optional[str] = None

    # Optional Cloudinary configuration (pulled from .env if present)
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None

    # Optional SMTP for sending user credentials email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_timeout_seconds: int = 12
    # Base URL of the police dashboard (for login link in email)
    frontend_url: str = "https://trustbond-dashboard.vercel.app"

    # How many hours after submitting a report the user (device) can still add evidence (mobile).
    evidence_add_window_hours: int = 72
    # Max raw upload size per evidence file (MB).
    evidence_max_upload_mb: int = 25
    # Optional semantic description matcher (disabled by default to avoid model downloads/runtime overhead).
    enable_semantic_match: bool = False

    # Device anti-abuse guardrails for report creation.
    duplicate_report_time_window_seconds: int = 120
    duplicate_report_radius_meters: int = 250
    device_activity_window_minutes: int = 30
    impossible_travel_window_seconds: int = 300
    impossible_travel_min_distance_km: float = 20.0
    max_plausible_speed_kmh: float = 250.0

    # Lightweight API throttles (per-client-IP, fixed-window, per minute).
    rate_limit_report_create_per_minute: int = 20
    rate_limit_evidence_upload_per_minute: int = 30
    rate_limit_report_confirm_per_minute: int = 40

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug_value(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return value

    def get_cors_origins_list(self) -> List[str]:
        default_local_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

        if not self.cors_origins or not self.cors_origins.strip():
            return ["*"]

        configured = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "*" in configured:
            return ["*"]

        merged: List[str] = []
        frontend_origin = self.get_frontend_origin()
        origins = configured + ([frontend_origin] if frontend_origin else []) + default_local_origins
        for origin in origins:
            if origin not in merged:
                merged.append(origin)
        return merged

    def get_frontend_origin(self) -> Optional[str]:
        raw = (self.frontend_url or "").strip()
        if not raw:
            return None

        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        if not parsed.scheme or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}"

    def get_cors_origin_regex(self) -> Optional[str]:
        configured = (self.cors_origin_regex or "").strip()
        if configured:
            return configured

        frontend_origin = self.get_frontend_origin()
        if not frontend_origin:
            return None

        parsed = urlparse(frontend_origin)
        hostname = (parsed.hostname or "").lower()
        if not hostname.endswith(".vercel.app"):
            return None

        project_slug = hostname.removesuffix(".vercel.app")
        if not project_slug:
            return None

        # Allow the main Vercel production URL plus preview URLs derived from the same project slug.
        return rf"^https://{project_slug}(?:-[a-z0-9-]+)?\.vercel\.app$"

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"


settings = Settings()
