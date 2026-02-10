"""Device service — registration, trust score calculation."""

from sqlalchemy.orm import Session
from app.models.device import Device


class DeviceService:
    """Business logic for devices table."""

    @staticmethod
    def get_or_create(db: Session, device_hash: str) -> Device:
        """Find existing device by hash or create new one."""
        # TODO: implement
        pass

    @staticmethod
    def recalculate_trust(db: Session, device_id) -> float:
        """
        Recalculate device_trust_score based on:
        - trusted_reports / total_reports
        - flagged_reports / total_reports
        """
        # TODO: implement trust formula
        pass
