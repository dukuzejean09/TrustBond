from __future__ import annotations

from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Optional

import io
from PIL import Image, ImageStat
from PIL.ExifTags import GPSTAGS, TAGS


def _load_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))


def _coerce_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _gps_value_to_float(value: Any) -> Optional[float]:
    try:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            denominator = float(value.denominator or 1)
            return float(value.numerator) / denominator
        if isinstance(value, (tuple, list)) and len(value) == 2:
            denominator = float(value[1] or 1)
            return float(value[0]) / denominator
        return float(value)
    except Exception:
        return None


def _gps_to_decimal(coords: Any, ref: Any) -> Optional[float]:
    if not isinstance(coords, (tuple, list)) or len(coords) != 3:
        return None

    parts = [_gps_value_to_float(part) for part in coords]
    if any(part is None for part in parts):
        return None

    degrees, minutes, seconds = parts  # type: ignore[misc]
    decimal = float(degrees) + (float(minutes) / 60.0) + (float(seconds) / 3600.0)
    ref_value = str(ref).strip().upper()
    if ref_value in {"S", "W"}:
        decimal *= -1.0
    return round(decimal, 7)


def average_hash(image_bytes: bytes, *, hash_size: int = 8) -> Optional[str]:
    """Compute a compact perceptual hash using an average-hash strategy."""
    try:
        image = _load_image(image_bytes).convert("L").resize((hash_size, hash_size))
        pixels = list(image.getdata())
        avg = sum(pixels) / max(1, len(pixels))
        bits = "".join("1" if px >= avg else "0" for px in pixels)
        width = max(1, len(bits) // 4)
        return f"{int(bits, 2):0{width}x}"
    except Exception:
        return None


def hamming_distance(hash_a: Optional[str], hash_b: Optional[str]) -> Optional[int]:
    if not hash_a or not hash_b:
        return None
    try:
        a_bits = bin(int(hash_a, 16))[2:].zfill(len(hash_a) * 4)
        b_bits = bin(int(hash_b, 16))[2:].zfill(len(hash_b) * 4)
        if len(a_bits) != len(b_bits):
            return None
        return sum(1 for abit, bbit in zip(a_bits, b_bits) if abit != bbit)
    except Exception:
        return None


def similarity_score(hash_a: Optional[str], hash_b: Optional[str]) -> Optional[float]:
    distance = hamming_distance(hash_a, hash_b)
    if distance is None or not hash_a:
        return None
    max_distance = len(hash_a) * 4
    if max_distance <= 0:
        return None
    return round(max(0.0, 1.0 - (distance / max_distance)), 4)


def brightness_score(image_bytes: bytes) -> Optional[float]:
    try:
        image = _load_image(image_bytes).convert("L")
        stat = ImageStat.Stat(image)
        return float(stat.mean[0])
    except Exception:
        return None


def contrast_score(image_bytes: bytes) -> Optional[float]:
    try:
        image = _load_image(image_bytes).convert("L")
        stat = ImageStat.Stat(image)
        return float(stat.stddev[0])
    except Exception:
        return None


def blur_score(image_bytes: bytes) -> Optional[float]:
    """
    Approximate blur using local pixel-difference variance.
    Higher values mean sharper images.
    """
    try:
        image = _load_image(image_bytes).convert("L").resize((96, 96))
        pixels = list(image.getdata())
        width, height = image.size
        if width < 2 or height < 2:
            return None

        diffs: list[float] = []
        for y in range(height - 1):
            row_offset = y * width
            next_row_offset = (y + 1) * width
            for x in range(width - 1):
                current = pixels[row_offset + x]
                right = pixels[row_offset + x + 1]
                down = pixels[next_row_offset + x]
                diffs.append(abs(float(current) - float(right)))
                diffs.append(abs(float(current) - float(down)))

        if not diffs:
            return None

        mean = sum(diffs) / len(diffs)
        variance = sum((d - mean) ** 2 for d in diffs) / len(diffs)
        return round(sqrt(variance), 3)
    except Exception:
        return None


def quality_label_from_scores(*, blur: Optional[float], brightness: Optional[float]) -> Optional[str]:
    if blur is None and brightness is None:
        return None

    blur_value = blur if blur is not None else 0.0
    brightness_value = brightness if brightness is not None else 128.0

    if blur_value < 8 or brightness_value < 35 or brightness_value > 220:
        return "poor"
    if blur_value < 16 or brightness_value < 55 or brightness_value > 200:
        return "fair"
    return "good"


def estimate_tamper_score(
    *,
    blur: Optional[float],
    brightness: Optional[float],
    contrast: Optional[float],
    gps_consistent: Optional[bool] = None,
    time_consistent: Optional[bool] = None,
) -> Optional[float]:
    """
    Heuristic 0..1 tamper suspicion score.
    This is intentionally lightweight and should be treated as a hint, not proof.
    """
    if blur is None and brightness is None and contrast is None:
        return None

    suspicion = 0.0
    if blur is not None and blur < 8:
        suspicion += 0.35
    elif blur is not None and blur < 16:
        suspicion += 0.15

    if brightness is not None and (brightness < 30 or brightness > 225):
        suspicion += 0.2
    elif brightness is not None and (brightness < 45 or brightness > 210):
        suspicion += 0.1

    if contrast is not None and contrast < 18:
        suspicion += 0.2

    if gps_consistent is False:
        suspicion += 0.15
    if time_consistent is False:
        suspicion += 0.1

    return round(min(1.0, suspicion), 4)


def analyze_image_evidence(image_bytes: bytes) -> dict[str, Any]:
    blur = blur_score(image_bytes)
    brightness = brightness_score(image_bytes)
    contrast = contrast_score(image_bytes)
    return {
        "perceptual_hash": average_hash(image_bytes),
        "blur_score": blur,
        "brightness": brightness,
        "contrast": contrast,
        "quality_label": quality_label_from_scores(blur=blur, brightness=brightness),
        "analyzed_at": datetime.now(timezone.utc),
    }


def extract_exif_metadata(image_bytes: bytes) -> dict[str, Any]:
    """
    Extract practical EXIF fields needed by the upload flow without tying the
    parsing code to the API route.
    """
    try:
        image = _load_image(image_bytes)
        exif_data = getattr(image, "getexif", lambda: None)()
        if not exif_data:
            exif_data = getattr(image, "_getexif", lambda: None)()
        if not exif_data:
            return {
                "has_exif": False,
                "latitude": None,
                "longitude": None,
                "captured_at": None,
                "camera_make": None,
                "camera_model": None,
            }

        exif_map = {TAGS.get(key, key): value for key, value in exif_data.items()}
        gps_info = None
        if hasattr(exif_data, "get_ifd"):
            try:
                gps_info = exif_data.get_ifd(34853)
            except Exception:
                gps_info = None

        if gps_info is None:
            raw_gps = exif_data.get(34853) or exif_map.get("GPSInfo")
            if isinstance(raw_gps, dict):
                gps_info = raw_gps
            elif isinstance(raw_gps, int) and hasattr(exif_data, "get_ifd"):
                try:
                    gps_info = exif_data.get_ifd(raw_gps)
                except Exception:
                    gps_info = None

        gps_map = {GPSTAGS.get(key, key): value for key, value in (gps_info or {}).items()}
        lat = _gps_to_decimal(gps_map.get("GPSLatitude"), gps_map.get("GPSLatitudeRef"))
        lon = _gps_to_decimal(gps_map.get("GPSLongitude"), gps_map.get("GPSLongitudeRef"))

        captured_at = None
        raw_dt = exif_map.get("DateTimeOriginal") or exif_map.get("DateTime")
        if raw_dt:
            try:
                captured_at = datetime.strptime(str(raw_dt), "%Y:%m:%d %H:%M:%S")
            except Exception:
                captured_at = None

        return {
            "has_exif": True,
            "latitude": lat,
            "longitude": lon,
            "captured_at": captured_at,
            "camera_make": exif_map.get("Make"),
            "camera_model": exif_map.get("Model"),
        }
    except Exception:
        return {
            "has_exif": False,
            "latitude": None,
            "longitude": None,
            "captured_at": None,
            "camera_make": None,
            "camera_model": None,
        }


def gps_match_score(
    submitted_lat: Optional[float],
    submitted_lon: Optional[float],
    exif_lat: Optional[float],
    exif_lon: Optional[float],
    *,
    tolerance_meters: float = 150.0,
) -> Optional[float]:
    if None in {submitted_lat, submitted_lon, exif_lat, exif_lon}:
        return None

    r = 6371000.0
    dlat = radians(float(exif_lat) - float(submitted_lat))
    dlon = radians(float(exif_lon) - float(submitted_lon))
    a = sin(dlat / 2) ** 2 + cos(radians(float(submitted_lat))) * cos(radians(float(exif_lat))) * sin(dlon / 2) ** 2
    distance = r * 2 * atan2(sqrt(a), sqrt(1 - a))

    if distance >= tolerance_meters:
        return 0.0
    return round(max(0.0, 1.0 - (distance / tolerance_meters)), 4)


def metadata_consistency_summary(
    *,
    submitted_lat: Optional[float],
    submitted_lon: Optional[float],
    exif_lat: Optional[float],
    exif_lon: Optional[float],
    submitted_captured_at: Optional[datetime],
    exif_captured_at: Optional[datetime],
) -> dict[str, Any]:
    gps_score = gps_match_score(submitted_lat, submitted_lon, exif_lat, exif_lon)
    time_delta_seconds = None
    if submitted_captured_at is not None and exif_captured_at is not None:
        sub = _coerce_utc(submitted_captured_at)
        exif = _coerce_utc(exif_captured_at)
        time_delta_seconds = int(abs((sub - exif).total_seconds()))

    gps_consistent = gps_score is None or gps_score > 0.5
    time_consistent = time_delta_seconds is None or time_delta_seconds <= 900
    metadata_consistent = gps_consistent and time_consistent

    return {
        "gps_match_score": gps_score,
        "gps_consistent": gps_consistent,
        "time_delta_seconds": time_delta_seconds,
        "time_consistent": time_consistent,
        "metadata_consistent": metadata_consistent,
    }


def analyze_image_with_metadata(
    image_bytes: bytes,
    *,
    submitted_lat: Optional[float] = None,
    submitted_lon: Optional[float] = None,
    submitted_captured_at: Optional[datetime] = None,
) -> dict[str, Any]:
    image_metrics = analyze_image_evidence(image_bytes)
    exif = extract_exif_metadata(image_bytes)
    consistency = metadata_consistency_summary(
        submitted_lat=submitted_lat,
        submitted_lon=submitted_lon,
        exif_lat=exif.get("latitude"),
        exif_lon=exif.get("longitude"),
        submitted_captured_at=submitted_captured_at,
        exif_captured_at=exif.get("captured_at"),
    )
    image_metrics["tamper_score"] = estimate_tamper_score(
        blur=image_metrics.get("blur_score"),
        brightness=image_metrics.get("brightness"),
        contrast=image_metrics.get("contrast"),
        gps_consistent=consistency.get("gps_consistent"),
        time_consistent=consistency.get("time_consistent"),
    )
    image_metrics["exif"] = exif
    image_metrics["metadata_consistency"] = consistency
    return image_metrics


def evidence_metadata_summary(
    *,
    image_bytes: bytes,
    submitted_lat: Optional[float] = None,
    submitted_lon: Optional[float] = None,
    submitted_captured_at: Optional[datetime] = None,
    existing_perceptual_hash: Optional[str] = None,
) -> dict[str, Any]:
    analysis = analyze_image_with_metadata(
        image_bytes,
        submitted_lat=submitted_lat,
        submitted_lon=submitted_lon,
        submitted_captured_at=submitted_captured_at,
    )
    analysis["hash_similarity_score"] = similarity_score(
        analysis.get("perceptual_hash"),
        existing_perceptual_hash,
    )
    return analysis
