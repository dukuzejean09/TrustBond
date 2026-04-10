import hashlib

from app.api.v1.reports import _content_fingerprint


def test_content_fingerprint_has_size_and_short_hash_prefix() -> None:
    payload = b"example-evidence-payload"
    metrics = _content_fingerprint(payload)

    assert metrics["content_size_bytes"] == len(payload)
    assert len(metrics["content_sha256_prefix"]) == 12


def test_content_fingerprint_prefix_matches_sha256_digest() -> None:
    payload = b"abc123"
    metrics = _content_fingerprint(payload)

    expected_prefix = hashlib.sha256(payload).hexdigest()[:12]
    assert metrics["content_sha256_prefix"] == expected_prefix
