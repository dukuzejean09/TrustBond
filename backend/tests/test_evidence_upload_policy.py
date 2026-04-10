import pytest
from fastapi import HTTPException

from app.api.v1.reports import _enforce_evidence_size_limit, _resolve_evidence_type


def test_resolve_evidence_type_image_by_content_type() -> None:
    is_image, is_audio, file_type = _resolve_evidence_type(
        filename="sample.bin",
        content_type="image/jpeg",
    )
    assert is_image is True
    assert is_audio is False
    assert file_type == "photo"


def test_resolve_evidence_type_audio_by_extension() -> None:
    is_image, is_audio, file_type = _resolve_evidence_type(
        filename="voice_note.m4a",
        content_type="application/octet-stream",
    )
    assert is_image is False
    assert is_audio is True
    assert file_type == "audio"


def test_resolve_evidence_type_rejects_unknown_extension() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _resolve_evidence_type(filename="payload.exe", content_type="application/octet-stream")

    assert exc_info.value.status_code == 400


def test_enforce_evidence_size_limit_allows_small_payload() -> None:
    _enforce_evidence_size_limit(b"abc")


def test_enforce_evidence_size_limit_blocks_large_payload(monkeypatch) -> None:
    from app.api.v1 import reports as reports_module

    monkeypatch.setattr(reports_module.settings, "evidence_max_upload_mb", 1)

    oversized = b"x" * (1024 * 1024 + 1)
    with pytest.raises(HTTPException) as exc_info:
        _enforce_evidence_size_limit(oversized)

    assert exc_info.value.status_code == 413
