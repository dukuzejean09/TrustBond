import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = (
    str(BACKEND_ROOT / ".env"),
    ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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
    # Semantic description matcher is enabled by default so the production
    # verification pipeline uses embedding-based incident alignment.
    enable_semantic_match: bool = True

    # Device anti-abuse guardrails for report creation.
    duplicate_report_time_window_seconds: int = 1200
    duplicate_report_radius_meters: int = 400
    device_activity_window_minutes: int = 30
    impossible_travel_window_seconds: int = 300
    impossible_travel_min_distance_km: float = 20.0
    max_plausible_speed_kmh: float = 250.0

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug_flag(cls, value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, (int, float)):
            return bool(value)

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "dev", "development", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "prod", "production", "release", "staging"}:
                return False

        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        raw = (value or "").strip()
        if not raw:
            return "postgresql://postgres:postgres@localhost:5432/trustbond"

        # Hosted Postgres providers such as Render typically require SSL.
        # Add sslmode=require automatically when the URL targets a remote host
        # and no explicit sslmode has been provided.
        try:
            parts = urlsplit(raw)
            host = (parts.hostname or "").lower()
            is_local_host = host in {"", "localhost", "127.0.0.1", "::1", "db"}
            query = dict(parse_qsl(parts.query, keep_blank_values=True))
            if host and not is_local_host and "sslmode" not in query:
                query["sslmode"] = "require"
                raw = urlunsplit(
                    (
                        parts.scheme,
                        parts.netloc,
                        parts.path,
                        urlencode(query),
                        parts.fragment,
                    )
                )
        except Exception:
            # If parsing fails, keep the original value and let SQLAlchemy
            # raise a more specific DSN error later.
            pass

        return raw

    @field_validator("database_url")
    @classmethod
    def reject_localhost_in_render(cls, value: str) -> str:
        hosted_render = any(
            os.getenv(name)
            for name in ("RENDER", "RENDER_SERVICE_ID", "RENDER_INSTANCE_ID")
        )
        if not hosted_render:
            return value

        parts = urlsplit(value)
        host = (parts.hostname or "").lower()
        if host in {"", "localhost", "127.0.0.1", "::1"}:
            raise ValueError(
                "DATABASE_URL resolved to a localhost fallback in a Render deployment. "
                "Set the real Postgres connection string in the service environment variables."
            )
        return value

    def get_cors_origins_list(self) -> List[str]:
        default_local_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

        # Auto-detect frontend URL from frontend_url setting
        auto_detected_origins = []
        if self.frontend_url and self.frontend_url.strip():
            frontend_url = self.frontend_url.strip()
            # Add both http and https variants for the frontend URL
            if frontend_url.startswith("http://"):
                auto_detected_origins.append(frontend_url)
                auto_detected_origins.append(frontend_url.replace("http://", "https://"))
            elif frontend_url.startswith("https://"):
                auto_detected_origins.append(frontend_url)
                auto_detected_origins.append(frontend_url.replace("https://", "http://"))

        if not self.cors_origins or not self.cors_origins.strip():
            # If no explicit CORS origins, use auto-detected + defaults
            all_origins = auto_detected_origins + default_local_origins
            return list(set(all_origins)) if all_origins else ["*"]

        configured = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "*" in configured:
            return ["*"]

        # Merge configured origins with auto-detected and defaults
        merged: List[str] = []
        for origin in configured + auto_detected_origins + default_local_origins:
            if origin not in merged:
                merged.append(origin)
        return merged

settings = Settings()
