"""Device service — registration, trust score calculation."""

from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.device import Device


class DeviceService:
    """Business logic for devices table."""

    @staticmethod
    def get_or_create(db: Session, device_hash: str) -> Device:
        """Find existing device by hash or create new one."""
        device = db.query(Device).filter(Device.device_hash == device_hash).first()
        if device:
            return device
        device = Device(device_hash=device_hash)
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def get_by_hash(db: Session, device_hash: str):
        """Retrieve device by its SHA-256 hash."""
        return db.query(Device).filter(Device.device_hash == device_hash).first()

    @staticmethod
    def increment_total(db: Session, device_id) -> None:
        """Increment total_reports counter after a new report."""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device:
            device.total_reports += 1
            db.commit()

    @staticmethod
    def increment_trusted(db: Session, device_id) -> None:
        """Increment trusted_reports counter after a confirmed review."""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device:
            device.trusted_reports += 1
            db.commit()

    @staticmethod
    def increment_flagged(db: Session, device_id) -> None:
        """Increment flagged_reports counter after a rejected review."""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device:
            device.flagged_reports += 1
            db.commit()

    @staticmethod
    def recalculate_trust(db: Session, device_id) -> Decimal:
        """
        Recalculate device_trust_score using the formula:
          score = base + (trusted_ratio × w1) - (flagged_ratio × w2) + (consistency × w3)
        Clamped to [0, 100].
        """
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device or device.total_reports == 0:
            return Decimal("50.00")

        base  = Decimal("50.00")
        w1    = Decimal("30.00")   # trusted reward
        w2    = Decimal("40.00")   # flagged penalty
        w3    = Decimal("10.00")   # consistency bonus

        total   = Decimal(device.total_reports)
        trusted = Decimal(device.trusted_reports) / total
        flagged = Decimal(device.flagged_reports) / total

        # Consistency bonus if ≥5 reports and <20 % flagged
        consistency = (
            Decimal("1.0")
            if device.total_reports >= 5 and flagged < Decimal("0.2")
            else Decimal("0.0")
        )

        score = base + (trusted * w1) - (flagged * w2) + (consistency * w3)
        score = max(Decimal("0.00"), min(Decimal("100.00"), score.quantize(Decimal("0.01"))))

        device.device_trust_score = score
        db.commit()
        db.refresh(device)
        return score
