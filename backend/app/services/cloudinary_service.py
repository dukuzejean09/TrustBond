"""
Cloudinary evidence service for TrustBond.

Handles:
- Upload to Cloudinary with metadata extraction
- EXIF-based evidence validation (time, GPS, device, screenshot detection)
- Duplicate detection via perceptual hashing
- Evidence freshness validation (24-hour rule)
"""
import io
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

CLOUDINARY_ENABLED = bool(settings.cloudinary_cloud_name and settings.cloudinary_api_key)

# Evidence freshness window (hours) — reject media older than this
EVIDENCE_MAX_AGE_HOURS = 24


def upload_to_cloudinary(
    content: bytes, filename: str, is_image: bool
) -> dict:
    """Upload file bytes to Cloudinary and return the result dict."""
    upload_opts = {"folder": "trustbond/evidence"}
    if not is_image:
        upload_opts["resource_type"] = "video"

    file_obj = io.BytesIO(content)
    file_obj.name = filename or f"{uuid4()}.bin"
    result = cloudinary.uploader.upload(file_obj, **upload_opts)
    return result


def extract_exif_metadata(image_bytes: bytes) -> dict:
    """
    Extract EXIF metadata from image bytes.

    Returns dict with keys:
    - gps_latitude, gps_longitude: float or None
    - captured_at: datetime or None
    - camera_model: str or None
    - software: str or None
    - has_camera_metadata: bool
    """
    result = {
        "gps_latitude": None,
        "gps_longitude": None,
        "captured_at": None,
        "camera_model": None,
        "software": None,
        "has_camera_metadata": False,
    }
    try:
        image = Image.open(io.BytesIO(image_bytes))
        exif_data = getattr(image, "getexif", lambda: None)()
        if not exif_data:
            exif_data = getattr(image, "_getexif", lambda: None)()
        if not exif_data:
            return result

        exif = {TAGS.get(k, k): v for k, v in exif_data.items()}

        # Camera model and software
        result["camera_model"] = exif.get("Model") or exif.get("Make")
        result["software"] = exif.get("Software")
        result["has_camera_metadata"] = result["camera_model"] is not None

        # Capture datetime
        dt_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if dt_str:
            try:
                result["captured_at"] = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                pass

        # GPS info
        gps_info = None
        if hasattr(exif_data, "get_ifd"):
            try:
                gps_ifd = exif_data.get_ifd(34853)
                if gps_ifd:
                    gps_info = gps_ifd
            except Exception:
                pass

        if gps_info is None:
            raw_gps = exif_data.get(34853) or exif.get("GPSInfo")
            if isinstance(raw_gps, dict):
                gps_info = raw_gps
            elif isinstance(raw_gps, int) and hasattr(exif_data, "get_ifd"):
                try:
                    gps_info = exif_data.get_ifd(raw_gps)
                except Exception:
                    pass

        if gps_info:
            gps_parsed = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}

            def _to_deg(value, ref):
                try:
                    if isinstance(value[0], (tuple, list)):
                        d = value[0][0] / value[0][1]
                        m = value[1][0] / value[1][1]
                        s = value[2][0] / value[2][1]
                    else:
                        d, m, s = value
                    deg = d + (m / 60.0) + (s / 3600.0)
                    if ref in ["S", "W"]:
                        deg = -deg
                    return float(deg)
                except Exception:
                    return None

            lat_val = gps_parsed.get("GPSLatitude")
            lat_ref = gps_parsed.get("GPSLatitudeRef")
            lon_val = gps_parsed.get("GPSLongitude")
            lon_ref = gps_parsed.get("GPSLongitudeRef")

            if lat_val and lat_ref:
                result["gps_latitude"] = _to_deg(lat_val, lat_ref)
            if lon_val and lon_ref:
                result["gps_longitude"] = _to_deg(lon_val, lon_ref)

    except Exception as e:
        logger.debug("EXIF extraction failed: %s", e)

    return result


def compute_image_hash(image_bytes: bytes) -> Optional[str]:
    """
    Compute a perceptual hash for duplicate detection.
    Uses average hash (aHash) - resize to 8x8, convert to grayscale,
    compare each pixel to the mean.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
        pixels = list(image.getdata())
        avg = sum(pixels) / len(pixels)
        bits = "".join("1" if p >= avg else "0" for p in pixels)
        # Convert to hex string
        return hex(int(bits, 2))[2:].zfill(16)
    except Exception as e:
        logger.debug("Image hash computation failed: %s", e)
        return None


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of raw file bytes for exact duplicate detection."""
    return hashlib.sha256(content).hexdigest()


def detect_screenshot_by_metadata(exif_meta: dict) -> bool:
    """
    Detect if image is a screenshot based on EXIF metadata.
    Screenshots typically lack camera metadata and may have software indicators.
    """
    # No camera model = likely screenshot
    if not exif_meta.get("has_camera_metadata"):
        software = (exif_meta.get("software") or "").lower()
        screenshot_software = [
            "screenshot", "screencap", "android system",
            "screen capture", "snipping", "gyazo", "shareware",
        ]
        if any(kw in software for kw in screenshot_software):
            return True
        # No camera and no software = ambiguous, but flag as suspicious
        if not exif_meta.get("software"):
            return True
    return False


def validate_evidence_freshness(
    captured_at: Optional[datetime],
    max_age_hours: int = EVIDENCE_MAX_AGE_HOURS,
) -> dict:
    """
    Validate that evidence was captured within the allowed time window.

    Returns dict with:
    - is_fresh: bool (True if within window or no timestamp)
    - age_hours: float or None
    - message: str
    """
    if captured_at is None:
        return {
            "is_fresh": True,
            "age_hours": None,
            "message": "No capture timestamp available",
        }

    now = datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)

    age = now - captured_at
    age_hours = age.total_seconds() / 3600

    if age_hours > max_age_hours:
        return {
            "is_fresh": False,
            "age_hours": round(age_hours, 1),
            "message": f"Evidence is {round(age_hours, 1)} hours old (max {max_age_hours}h allowed)",
        }

    if age_hours < -1:  # Allow 1 hour clock drift
        return {
            "is_fresh": False,
            "age_hours": round(age_hours, 1),
            "message": "Evidence capture time is in the future (possible tampering)",
        }

    return {
        "is_fresh": True,
        "age_hours": round(age_hours, 1),
        "message": "Evidence is fresh",
    }


def validate_timestamp_order(
    captured_at: Optional[datetime],
    uploaded_at: datetime,
    reported_at: Optional[datetime],
) -> dict:
    """
    Validate that timestamps follow the correct order:
    captured_at <= uploaded_at <= reported_at (approximately)

    Returns dict with:
    - is_valid: bool
    - message: str
    """
    if captured_at is None:
        return {"is_valid": True, "message": "No capture timestamp to validate"}

    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    if uploaded_at.tzinfo is None:
        uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)

    # Allow 1-hour tolerance for clock differences
    tolerance = timedelta(hours=1)

    if captured_at > uploaded_at + tolerance:
        return {
            "is_valid": False,
            "message": "Capture time is after upload time (suspicious)",
        }

    if reported_at:
        if reported_at.tzinfo is None:
            reported_at = reported_at.replace(tzinfo=timezone.utc)
        if captured_at > reported_at + tolerance:
            return {
                "is_valid": False,
                "message": "Capture time is after report submission time (suspicious)",
            }

    return {"is_valid": True, "message": "Timestamps are consistent"}


def run_evidence_verification(
    content: bytes,
    filename: str,
    is_image: bool,
    report_reported_at: Optional[datetime] = None,
) -> dict:
    """
    Run the full evidence verification pipeline on uploaded content.

    Returns a verification result dict with:
    - exif: extracted metadata
    - freshness: freshness validation result
    - timestamp_order: timestamp order validation
    - is_screenshot: bool
    - is_duplicate_hash: str (perceptual hash for images, file hash otherwise)
    - verification_status: 'accepted' | 'rejected' | 'flagged'
    - rejection_reason: str or None
    """
    now = datetime.now(timezone.utc)

    # 1. Extract EXIF metadata (images only)
    exif_meta = extract_exif_metadata(content) if is_image else {
        "gps_latitude": None,
        "gps_longitude": None,
        "captured_at": None,
        "camera_model": None,
        "software": None,
        "has_camera_metadata": False,
    }

    captured_at = exif_meta.get("captured_at")

    # 2. Freshness check
    freshness = validate_evidence_freshness(captured_at)

    # 3. Timestamp order
    timestamp_order = validate_timestamp_order(captured_at, now, report_reported_at)

    # 4. Screenshot detection (metadata-based, for images)
    is_screenshot = False
    if is_image:
        is_screenshot = detect_screenshot_by_metadata(exif_meta)

    # 5. Compute hashes for duplicate detection
    perceptual_hash = compute_image_hash(content) if is_image else None
    file_hash = compute_file_hash(content)

    # 6. Determine verification status
    verification_status = "accepted"
    rejection_reason = None

    if not freshness["is_fresh"]:
        verification_status = "rejected"
        rejection_reason = freshness["message"]
    elif not timestamp_order["is_valid"]:
        verification_status = "flagged"
        rejection_reason = timestamp_order["message"]
    elif is_screenshot:
        verification_status = "rejected"
        rejection_reason = "Evidence appears to be a screenshot (no camera metadata detected)"

    return {
        "exif": exif_meta,
        "freshness": freshness,
        "timestamp_order": timestamp_order,
        "is_screenshot": is_screenshot,
        "perceptual_hash": perceptual_hash,
        "file_hash": file_hash,
        "verification_status": verification_status,
        "rejection_reason": rejection_reason,
    }
