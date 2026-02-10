"""Cloudinary upload helper."""

import cloudinary
import cloudinary.uploader
from app.core.config import settings


def configure_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_file(file, folder: str = "trustbond/evidence") -> dict:
    """Upload a file to Cloudinary and return the result dict."""
    configure_cloudinary()
    result = cloudinary.uploader.upload(file, folder=folder)
    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "format": result.get("format"),
    }
