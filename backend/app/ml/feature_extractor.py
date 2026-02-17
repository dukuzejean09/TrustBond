"""Feature extraction — build feature_vector from report + device + evidence data."""

from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

from app.models.report import Report
from app.models.evidence_file import EvidenceFile
from app.models.device import Device


def _haversine(lat1, lon1, lat2, lon2):
    # return distance in meters
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371000 * c


class FeatureExtractor:
    """Extracts ML features from reports and stores in reports.feature_vector (JSONB)."""

    @staticmethod
    def extract(db: Session, report_id: str) -> dict:
        """
        Build a feature vector that matches the training CSV columns used by the
        Random Forest training script and store it on the Report.feature_vector.

        This function attempts to use available DB fields and falls back to sane
        defaults where a column isn't available in the DB schema.
        """
        rpt = (
            db.query(Report)
            .options(joinedload(Report.device), joinedload(Report.evidence_files))
            .filter(Report.report_id == report_id)
            .one_or_none()
        )
        if rpt is None:
            raise ValueError(f"report not found: {report_id}")

        device = rpt.device
        evidences = rpt.evidence_files or []

        # Report-level
        description_length = len((rpt.description or "").strip())
        has_evidence = 1 if len(evidences) > 0 else 0
        evidence_count = len(evidences)
        gps_accuracy = float(rpt.gps_accuracy or 0.0)
        gps_speed_check = float(rpt.movement_speed or 0.0)

        # Evidence-level aggregates (use averages or defaults)
        blur_scores = [float(e.blur_score) for e in evidences if e.blur_score is not None]
        image_blur_score = float(sum(blur_scores) / len(blur_scores)) if blur_scores else 0.0

        # image_quality_score in training data is 0..1 — approximate from ai_quality_label / blur
        if evidences:
            # prefer ai_quality_label if present
            labels = [e.ai_quality_label for e in evidences if e.ai_quality_label]
            if labels:
                # map labels to a 0..1 score
                mapping = {"good": 0.9, "poor": 0.25, "suspicious": 0.5}
                image_quality_score = float(sum(mapping.get(l, 0.5) for l in labels) / len(labels))
            else:
                image_quality_score = max(0.0, min(1.0, 1.0 - image_blur_score / 1000.0))
        else:
            image_quality_score = 0.0

        metadata_gps_match = 0
        hash_similarity_score = 0.0
        perceptual_hash = ""
        image_brightness = 0.0
        is_duplicate_media = 0
        image_metadata_valid = 0

        for e in evidences:
            if e.perceptual_hash:
                perceptual_hash = e.perceptual_hash
            if e.blur_score:
                pass
            if e.media_latitude and e.media_longitude:
                # compare media coords to report coords
                try:
                    dist = _haversine(float(rpt.latitude), float(rpt.longitude), float(e.media_latitude), float(e.media_longitude))
                    if dist <= 50:  # within 50m
                        metadata_gps_match = 1
                except Exception:
                    pass
            if e.ai_quality_label:
                image_metadata_valid = image_metadata_valid or 1

        # Duplicate check: simple DB lookup of perceptual_hash
        if perceptual_hash:
            dup_count = (
                db.query(EvidenceFile).filter(EvidenceFile.perceptual_hash == perceptual_hash).count()
            )
            is_duplicate_media = 1 if dup_count > 1 else 0
            # for now, keep hash_similarity_score as 0/1 indicator
            hash_similarity_score = 0.0 if dup_count <= 1 else 10.0

        # Device-level
        device_trust_score = float(device.device_trust_score) if device else 50.0
        total_reports_submitted = int(device.total_reports) if device else 0
        trusted_reports = int(device.trusted_reports) if device else 0
        flagged_reports = int(device.flagged_reports) if device else 0
        confirmed_reports = trusted_reports
        rejected_reports = flagged_reports
        confirmation_rate = (trusted_reports / total_reports_submitted) if total_reports_submitted > 0 else 0.0
        reporting_frequency = 0.0
        unique_locations_count = 0
        spam_flag_count = 0
        avg_response_time = 0.0
        last_activity_days = 0

        # Spatial / temporal fields
        point_latitude = float(rpt.latitude)
        point_longitude = float(rpt.longitude)
        trust_weight = round(device_trust_score / 100.0, 3)

        # Time anomalies and flags
        now = datetime.utcnow()
        reported_at = rpt.reported_at or now
        time_since_incident = 0.0
        timestamp_anomaly = 1 if (now - reported_at).days * 24 > 72 else 0
        future_timestamp_flag = 1 if reported_at > now else 0

        # Basic text features
        text_sentiment_score = 0.0
        keyword_flag_count = 0

        # incident category & network & gps_location_type (best-effort)
        incident_category = getattr(rpt.incident_type, "type_name", "unknown") if getattr(rpt, "incident_type", None) else "unknown"
        gps_location_type = getattr(rpt, "gps_location_type", "Unknown") if hasattr(rpt, "gps_location_type") else "Unknown"
        network_type = "Mobile Data"
        priority_level = "Low"

        feature_vector = {
            # report-level
            "description_length": description_length,
            "has_evidence": has_evidence,
            "evidence_count": evidence_count,
            "image_quality_score": image_quality_score,
            "image_metadata_valid": int(image_metadata_valid),
            "time_since_incident": time_since_incident,
            "is_duplicate_media": int(is_duplicate_media),
            "gps_location_type": gps_location_type,
            "network_type": network_type,

            # location / ids
            "sector_id": getattr(rpt.village_location, "sector_id", 0) if hasattr(rpt, "village_location") else 0,
            "cell_id": getattr(rpt.village_location, "cell_id", 0) if hasattr(rpt, "village_location") else 0,
            "village_id": getattr(rpt.village_location, "village_id", 0) if hasattr(rpt, "village_location") else 0,

            # device-level
            "device_trust_score": device_trust_score,
            "total_reports_submitted": total_reports_submitted,
            "confirmed_reports": confirmed_reports,
            "rejected_reports": rejected_reports,
            "confirmation_rate": round(confirmation_rate, 3),
            "avg_response_time": avg_response_time,
            "reporting_frequency": reporting_frequency,
            "unique_locations_count": unique_locations_count,
            "spam_flag_count": spam_flag_count,
            "last_activity_days": last_activity_days,

            # spatial / clustering
            "point_latitude": point_latitude,
            "point_longitude": point_longitude,
            "trust_weight": trust_weight,

            # AI-assisted verification
            "gps_anomaly_flag": 1 if gps_accuracy > 200 else 0,
            "gps_speed_check": gps_speed_check,
            "timestamp_anomaly": int(timestamp_anomaly),
            "future_timestamp_flag": int(future_timestamp_flag),
            "image_blur_score": image_blur_score,
            "image_brightness": image_brightness,
            "perceptual_hash": perceptual_hash or "",
            "hash_similarity_score": hash_similarity_score,
            "metadata_gps_match": int(metadata_gps_match),
            "text_sentiment_score": text_sentiment_score,
            "keyword_flag_count": keyword_flag_count,

            # labels / priority (not set here)
            "priority_level": priority_level,
            "incident_category": incident_category,
        }

        # Persist into report.feature_vector and mark ai_ready
        rpt.feature_vector = feature_vector
        rpt.ai_ready = True
        rpt.features_extracted = datetime.utcnow()
        db.add(rpt)
        db.commit()

        return feature_vector
