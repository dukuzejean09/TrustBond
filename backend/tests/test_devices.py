"""Tests for device endpoints."""


class TestDeviceRegister:
    """POST /api/v1/devices/register"""

    def test_register_new_device(self, client):
        response = client.post("/api/v1/devices/register", json={
            "device_hash": "sha256_test_hash_abc123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["device_hash"] == "sha256_test_hash_abc123"
        assert data["total_reports"] == 0
        assert data["trusted_reports"] == 0
        assert data["flagged_reports"] == 0
        assert float(data["device_trust_score"]) == 50.00

    def test_register_existing_device_returns_same(self, client):
        # First registration
        r1 = client.post("/api/v1/devices/register", json={
            "device_hash": "duplicate_hash",
        })
        assert r1.status_code == 201
        id1 = r1.json()["device_id"]

        # Second registration same hash
        r2 = client.post("/api/v1/devices/register", json={
            "device_hash": "duplicate_hash",
        })
        # Should succeed (idempotent) and return same device
        assert r2.status_code == 201
        assert r2.json()["device_id"] == id1


class TestDeviceGet:
    """GET /api/v1/devices/{device_hash}"""

    def test_get_existing_device(self, client, sample_device):
        response = client.get(f"/api/v1/devices/{sample_device.device_hash}")
        assert response.status_code == 200
        assert response.json()["device_hash"] == sample_device.device_hash

    def test_get_nonexistent_device(self, client):
        response = client.get("/api/v1/devices/nonexistent_hash")
        assert response.status_code == 404
