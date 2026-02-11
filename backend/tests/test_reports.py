"""Tests for report endpoints."""

from decimal import Decimal


class TestCreateReport:
    """POST /api/v1/reports/"""

    def test_create_report_new_device(self, client, sample_incident_type):
        response = client.post("/api/v1/reports/", json={
            "device_hash": "new_device_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "description": "Suspicious activity near the market",
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
            "gps_accuracy": "10.50",
            "motion_level": "low",
            "movement_speed": "0.50",
            "was_stationary": True,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["incident_type_id"] == sample_incident_type.incident_type_id
        assert data["rule_status"] == "passed"
        assert data["is_flagged"] is False
        assert data["ai_ready"] is False

    def test_create_report_existing_device(self, client, sample_incident_type, sample_device):
        response = client.post("/api/v1/reports/", json={
            "device_hash": sample_device.device_hash,
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5100000",
            "longitude": "29.6100000",
        })
        assert response.status_code == 201

    def test_create_report_increments_device_total(self, client, db, sample_incident_type, sample_device):
        assert sample_device.total_reports == 0
        client.post("/api/v1/reports/", json={
            "device_hash": sample_device.device_hash,
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        db.refresh(sample_device)
        assert sample_device.total_reports == 1

    def test_create_report_missing_required_fields(self, client, sample_incident_type):
        response = client.post("/api/v1/reports/", json={
            "device_hash": "hash",
            # missing incident_type_id, latitude, longitude
        })
        assert response.status_code == 422


class TestListReports:
    """GET /api/v1/reports/"""

    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/reports/")
        assert response.status_code in (401, 403)

    def test_list_empty(self, client, auth_headers):
        response = client.get("/api/v1/reports/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["reports"] == []

    def test_list_with_reports(self, client, auth_headers, sample_incident_type):
        # Create a report first
        client.post("/api/v1/reports/", json={
            "device_hash": "list_test_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        response = client.get("/api/v1/reports/", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert len(data["reports"]) == 1

    def test_list_filter_by_rule_status(self, client, auth_headers, sample_incident_type):
        client.post("/api/v1/reports/", json={
            "device_hash": "filter_test_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        # Filter for flagged — should be empty
        response = client.get(
            "/api/v1/reports/?rule_status=flagged",
            headers=auth_headers,
        )
        assert response.json()["total"] == 0

    def test_list_pagination(self, client, auth_headers, sample_incident_type):
        # Create 3 reports
        for i in range(3):
            client.post("/api/v1/reports/", json={
                "device_hash": f"paginate_{i}",
                "incident_type_id": sample_incident_type.incident_type_id,
                "latitude": "-1.5000000",
                "longitude": "29.6000000",
            })
        response = client.get(
            "/api/v1/reports/?page=1&per_page=2",
            headers=auth_headers,
        )
        data = response.json()
        assert data["total"] == 3
        assert len(data["reports"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2


class TestGetReport:
    """GET /api/v1/reports/{id}"""

    def test_get_report_detail(self, client, auth_headers, sample_incident_type):
        create_resp = client.post("/api/v1/reports/", json={
            "device_hash": "detail_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        report_id = create_resp.json()["report_id"]

        response = client.get(
            f"/api/v1/reports/{report_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == report_id
        assert "evidence_files" in data
        assert "ml_predictions" in data
        assert "police_reviews" in data
        assert "assignments" in data
        assert "incident_type" in data
        assert "device" in data

    def test_get_nonexistent_report(self, client, auth_headers):
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/reports/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateReport:
    """PATCH /api/v1/reports/{id}"""

    def test_update_rule_status(self, client, auth_headers, sample_incident_type):
        create_resp = client.post("/api/v1/reports/", json={
            "device_hash": "update_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        report_id = create_resp.json()["report_id"]

        response = client.patch(
            f"/api/v1/reports/{report_id}",
            json={"rule_status": "flagged", "is_flagged": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["rule_status"] == "flagged"
        assert response.json()["is_flagged"] is True
