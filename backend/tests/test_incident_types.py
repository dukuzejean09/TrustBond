"""Tests for incident type endpoints."""


class TestListIncidentTypes:
    """GET /api/v1/incident-types/"""

    def test_list_active_only(self, client, sample_incident_type):
        response = client.get("/api/v1/incident-types/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type_name"] == "Theft"

    def test_list_includes_inactive(self, client, db, sample_incident_type):
        from app.models.incident_type import IncidentType
        inactive = IncidentType(type_name="Inactive", is_active=False)
        db.add(inactive)
        db.commit()

        # Default (active only)
        r1 = client.get("/api/v1/incident-types/")
        assert len(r1.json()) == 1

        # All including inactive
        r2 = client.get("/api/v1/incident-types/?active_only=false")
        assert len(r2.json()) == 2

    def test_list_empty(self, client):
        response = client.get("/api/v1/incident-types/")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateIncidentType:
    """POST /api/v1/incident-types/"""

    def test_admin_can_create(self, client, auth_headers):
        response = client.post(
            "/api/v1/incident-types/",
            json={"type_name": "Assault", "severity_weight": "3.00"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type_name"] == "Assault"
        assert float(data["severity_weight"]) == 3.00
        assert data["is_active"] is True

    def test_officer_cannot_create(self, client, officer_headers):
        response = client.post(
            "/api/v1/incident-types/",
            json={"type_name": "Fraud"},
            headers=officer_headers,
        )
        assert response.status_code == 403

    def test_duplicate_name_rejected(self, client, auth_headers, sample_incident_type):
        response = client.post(
            "/api/v1/incident-types/",
            json={"type_name": "Theft"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_no_auth_rejected(self, client):
        response = client.post(
            "/api/v1/incident-types/",
            json={"type_name": "Test"},
        )
        assert response.status_code in (401, 403)


class TestUpdateIncidentType:
    """PATCH /api/v1/incident-types/{id}"""

    def test_admin_can_update(self, client, auth_headers, sample_incident_type):
        response = client.patch(
            f"/api/v1/incident-types/{sample_incident_type.incident_type_id}",
            json={"severity_weight": "5.00"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert float(response.json()["severity_weight"]) == 5.00

    def test_toggle_active(self, client, auth_headers, sample_incident_type):
        response = client.patch(
            f"/api/v1/incident-types/{sample_incident_type.incident_type_id}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_nonexistent(self, client, auth_headers):
        response = client.patch(
            "/api/v1/incident-types/9999",
            json={"type_name": "Changed"},
            headers=auth_headers,
        )
        assert response.status_code == 404
