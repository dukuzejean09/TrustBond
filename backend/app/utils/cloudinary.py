"""Cloudinary upload helper — supports photo and video evidence."""

import cloudinary
import cloudinary.uploader
from app.core.config import settings

_configured = False


def configure_cloudinary():
    """Configure Cloudinary credentials (idempotent)."""
    global _configured
    if _configured:
        return
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    _configured = True


def _detect_resource_type(file_type: str) -> str:
    """Map evidence file_type to Cloudinary resource_type."""
    return "video" if file_type == "video" else "image"


def upload_file(
    file,
    folder: str = "trustbond/evidence",
    file_type: str = "photo",
) -> dict:
    """
    Upload a file to Cloudinary and return metadata.

    Args:
        file: file-like object or path
        folder: Cloudinary folder path
        file_type: "photo" or "video" — determines resource_type

    Returns:
        dict with url, public_id, format, resource_type, bytes
    """
    configure_cloudinary()
    resource_type = _detect_resource_type(file_type)
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type=resource_type,
    )
    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "format": result.get("format"),
        "resource_type": result.get("resource_type"),
        "bytes": result.get("bytes"),
    }


def delete_file(public_id: str, resource_type: str = "image") -> bool:
    """Delete a file from Cloudinary by its public_id."""
    configure_cloudinary()
    result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    return result.get("result") == "ok"


def test_connection() -> dict:
    """Verify Cloudinary credentials are valid. Returns account info."""
    configure_cloudinary()
    try:
        import cloudinary.api
        result = cloudinary.api.ping()
        return {"status": "ok", "response": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
