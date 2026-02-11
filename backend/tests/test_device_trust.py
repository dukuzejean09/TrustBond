"""Tests for device trust score calculation."""

from decimal import Decimal
from app.services.device_service import DeviceService


class TestDeviceTrustRecalculation:
    """Verify trust score formula works correctly."""

    def test_initial_trust_score(self, sample_device):
        assert sample_device.device_trust_score == Decimal("50.00")

    def test_trust_increases_with_confirmed_reviews(self, db, sample_device):
        sample_device.total_reports = 5
        sample_device.trusted_reports = 4
        sample_device.flagged_reports = 0
        db.commit()

        score = DeviceService.recalculate_trust(db, sample_device.device_id)
        # base(50) + trusted(4/5 * 30 = 24) - flagged(0) + consistency(10) = 84
        assert score == Decimal("84.00")

    def test_trust_decreases_with_flagged_reports(self, db, sample_device):
        sample_device.total_reports = 5
        sample_device.trusted_reports = 1
        sample_device.flagged_reports = 4
        db.commit()

        score = DeviceService.recalculate_trust(db, sample_device.device_id)
        # base(50) + trusted(1/5 * 30 = 6) - flagged(4/5 * 40 = 32) + consistency(0) = 24
        assert score == Decimal("24.00")

    def test_trust_clamped_to_zero(self, db, sample_device):
        sample_device.total_reports = 5
        sample_device.trusted_reports = 0
        sample_device.flagged_reports = 5
        db.commit()

        score = DeviceService.recalculate_trust(db, sample_device.device_id)
        # base(50) + trusted(0) - flagged(5/5 * 40 = 40) + consistency(0) = 10
        assert score == Decimal("10.00")

    def test_trust_with_zero_reports(self, db, sample_device):
        score = DeviceService.recalculate_trust(db, sample_device.device_id)
        assert score == Decimal("50.00")

    def test_increment_trusted(self, db, sample_device):
        assert sample_device.trusted_reports == 0
        DeviceService.increment_trusted(db, sample_device.device_id)
        db.refresh(sample_device)
        assert sample_device.trusted_reports == 1

    def test_increment_flagged(self, db, sample_device):
        assert sample_device.flagged_reports == 0
        DeviceService.increment_flagged(db, sample_device.device_id)
        db.refresh(sample_device)
        assert sample_device.flagged_reports == 1

    def test_increment_total(self, db, sample_device):
        assert sample_device.total_reports == 0
        DeviceService.increment_total(db, sample_device.device_id)
        db.refresh(sample_device)
        assert sample_device.total_reports == 1
