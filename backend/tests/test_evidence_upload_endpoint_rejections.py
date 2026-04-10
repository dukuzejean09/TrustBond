from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1 import reports as reports_api

from tests.evidence_upload_test_helpers import FakeDB, base_report, build_client


def test_upload_evidence_returns_413_when_file_too_large(monkeypatch) -> None:
    report_id = uuid4()
    device_id = uuid4()
    fake_db = FakeDB(base_report(report_id, device_id))
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 1)

    oversized = b"x" * (1024 * 1024 + 1)
    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(device_id), "is_live_capture": "false"},
        files={"file": ("clip.mp4", oversized, "video/mp4")},
    )

    assert response.status_code == 413
    assert "max upload size" in response.json().get("detail", "").lower()


def test_upload_evidence_returns_400_for_unsupported_format(monkeypatch) -> None:
    report_id = uuid4()
    device_id = uuid4()
    fake_db = FakeDB(base_report(report_id, device_id))
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 5)

    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(device_id), "is_live_capture": "false"},
        files={"file": ("payload.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "unsupported evidence format" in response.json().get("detail", "").lower()


def test_upload_evidence_returns_409_for_duplicate_hash(monkeypatch) -> None:
    report_id = uuid4()
    device_id = uuid4()

    content = b"duplicate-video-content"
    existing = SimpleNamespace(
        evidence_id=uuid4(),
        perceptual_hash=sha256(content).hexdigest(),
    )

    fake_db = FakeDB(base_report(report_id, device_id), duplicate_rows=[existing])
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 5)
    monkeypatch.setattr(reports_api, "_log_blocked_attempt", lambda *args, **kwargs: None)

    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(device_id), "is_live_capture": "false"},
        files={"file": ("clip.mp4", content, "video/mp4")},
    )

    assert response.status_code == 409
    assert "reused" in response.json().get("detail", "").lower()


def test_upload_evidence_returns_404_when_report_missing(monkeypatch) -> None:
    report_id = uuid4()
    device_id = uuid4()
    fake_db = FakeDB(report=None)
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 5)

    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(device_id), "is_live_capture": "false"},
        files={"file": ("clip.mp4", b"ok", "video/mp4")},
    )

    assert response.status_code == 404
    assert "report not found" in response.json().get("detail", "").lower()


def test_upload_evidence_returns_403_for_device_mismatch(monkeypatch) -> None:
    report_id = uuid4()
    report_owner_device_id = uuid4()
    another_device_id = uuid4()
    fake_db = FakeDB(base_report(report_id, report_owner_device_id))
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 5)

    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(another_device_id), "is_live_capture": "false"},
        files={"file": ("clip.mp4", b"ok", "video/mp4")},
    )

    assert response.status_code == 403
    assert "own report" in response.json().get("detail", "").lower()


def test_upload_evidence_returns_400_when_window_expired(monkeypatch) -> None:
    report_id = uuid4()
    device_id = uuid4()
    report = base_report(report_id, device_id)
    report.reported_at = datetime.now(timezone.utc) - timedelta(hours=80)
    fake_db = FakeDB(report)
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 5)
    monkeypatch.setattr(reports_api.settings, "evidence_add_window_hours", 72)

    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(device_id), "is_live_capture": "false"},
        files={"file": ("clip.mp4", b"ok", "video/mp4")},
    )

    assert response.status_code == 400
    assert "within 72 hours" in response.json().get("detail", "").lower()
