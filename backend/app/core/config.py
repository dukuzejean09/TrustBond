"""Application configuration — loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Project ───────────────────────────────────────────
    PROJECT_NAME: str = "TrustBond"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:trustbond2026@127.0.0.1:5432/trustbond"

    # ── JWT ───────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ──────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Cloudinary ────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Redis / Celery ────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
