"""Feature extraction — build feature_vector from report + device + evidence data."""

from sqlalchemy.orm import Session


class FeatureExtractor:
    """Extracts ML features from reports and stores in reports.feature_vector (JSONB)."""

    @staticmethod
    def extract(db: Session, report_id: str) -> dict:
        """
        Build feature vector from:
        - Report-level: description length, gps_accuracy, motion_level, movement_speed, was_stationary
        - Device-level: total_reports, trusted_reports, flagged_reports, device_trust_score
        - Evidence-level: blur_score, tamper_score, is_live_capture, ai_quality_label, evidence count
        - Temporal: time since incident, reporting frequency

        Stores result in reports.feature_vector, sets ai_ready=True, features_extracted=NOW()
        """
        # TODO: implement
        pass
