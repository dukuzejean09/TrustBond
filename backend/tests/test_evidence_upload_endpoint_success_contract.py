from __future__ import annotations

from uuid import uuid4

from app.api.v1 import reports as reports_api

from tests.evidence_upload_test_helpers import FakeDB, base_report, build_client


def test_upload_evidence_returns_200_on_valid_upload(monkeypatch) -> None:
    report_id = uuid4()
    device_id = uuid4()
    fake_db = FakeDB(base_report(report_id, device_id))
    client = build_client(fake_db)

    monkeypatch.setattr(reports_api.settings, "evidence_max_upload_mb", 5)
    monkeypatch.setattr(reports_api, "_CLOUDINARY_ENABLED", True)
    monkeypatch.setattr(
        reports_api.cloudinary.uploader,
        "upload",
        lambda *args, **kwargs: {"secure_url": "https://example.com/evidence/file.mp4"},
    )
    monkeypatch.setattr(
        reports_api,
        "_auto_group_and_persist_verified_report",
        lambda *args, **kwargs: None,
    )

    async def _noop_broadcast(*args, **kwargs):
        return None

    monkeypatch.setattr(reports_api.manager, "broadcast", _noop_broadcast)

    import app.core.report_priority as report_priority

    monkeypatch.setattr(
        report_priority,
        "apply_ai_enhanced_rules",
        lambda *args, **kwargs: ("passed", False, None),
    )
    monkeypatch.setattr(
        report_priority,
        "calculate_report_priority",
        lambda *args, **kwargs: "medium",
    )

    response = client.post(
        f"/api/v1/reports/{report_id}/evidence",
        data={"device_id": str(device_id), "is_live_capture": "false"},
        files={"file": ("clip.mp4", b"valid-video", "video/mp4")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "evidence_id" in payload
    assert payload.get("file_url", "").startswith("https://example.com/evidence/")
