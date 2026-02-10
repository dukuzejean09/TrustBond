"""Hashing utility — SHA-256 device fingerprint generation."""

import hashlib


def generate_device_hash(device_attributes: dict) -> str:
    """
    Generate a non-reversible SHA-256 hash from device attributes.
    Used as pseudonymous device identifier (devices.device_hash).
    """
    raw = "|".join(str(v) for v in sorted(device_attributes.values()))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
