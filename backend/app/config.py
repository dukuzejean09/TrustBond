from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TrustBond API"
    debug: bool = False
    database_url: str = "postgresql://postgres:postgres@localhost:5432/trustbond"
    secret_key: str = "change-me-in-production"

    # CORS: comma-separated origins, e.g. "https://dashboard.trustbond.rw".
    # Empty = allow all ("*") — NOT recommended for production.
    cors_origins: str = ""

    # Minimum password length for police user passwords
    min_password_length: int = 8

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
    # Base URL of the police dashboard (for login link in email)
    frontend_url: str = "http://localhost:5173"

    # How many hours after submitting a report the user (device) can still add evidence (mobile).
    evidence_add_window_hours: int = 72

    def get_cors_origins_list(self) -> List[str]:
        if not self.cors_origins or not self.cors_origins.strip():
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_secret_key(self) -> None:
        """Warn if the default insecure secret key is still in use."""
        if self.secret_key == "change-me-in-production" and not self.debug:
            import warnings
            warnings.warn(
                "\n⚠️  SECRET_KEY is still the default! Set a strong SECRET_KEY in your .env file.\n"
                "   JWTs signed with the default key are insecure.\n",
                stacklevel=2,
            )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
settings.validate_secret_key()
