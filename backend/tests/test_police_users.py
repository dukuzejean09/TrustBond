"""Tests for police user endpoints."""


class TestListPoliceUsers:
    """GET /api/v1/police-users/"""

    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/police-users/")
        assert response.status_code in (401, 403)

    def test_list_returns_users(self, client, auth_headers, admin_user):
        response = client.get("/api/v1/police-users/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(u["email"] == "admin@trustbond.rw" for u in data)

    def test_list_filter_by_role(self, client, auth_headers, admin_user, officer_user):
        response = client.get(
            "/api/v1/police-users/?role=officer",
            headers=auth_headers,
        )
        data = response.json()
        assert all(u["role"] == "officer" for u in data)

    def test_list_filter_by_active(self, client, auth_headers, admin_user):
        response = client.get(
            "/api/v1/police-users/?is_active=true",
            headers=auth_headers,
        )
        data = response.json()
        assert all(u["is_active"] for u in data)


class TestCreatePoliceUser:
    """POST /api/v1/police-users/"""

    def test_admin_creates_officer(self, client, auth_headers):
        response = client.post("/api/v1/police-users/", json={
            "first_name": "Jean",
            "last_name": "Baptiste",
            "email": "jean@trustbond.rw",
            "password": "secure123",
            "badge_number": "JB-001",
            "role": "officer",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Jean"
        assert data["role"] == "officer"
        assert "password" not in data  # Password must not be returned

    def test_officer_cannot_create(self, client, officer_headers):
        response = client.post("/api/v1/police-users/", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@trustbond.rw",
            "password": "test123",
            "role": "officer",
        }, headers=officer_headers)
        assert response.status_code == 403

    def test_duplicate_email_rejected(self, client, auth_headers, admin_user):
        response = client.post("/api/v1/police-users/", json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "admin@trustbond.rw",  # Already exists
            "password": "test123",
            "role": "officer",
        }, headers=auth_headers)
        assert response.status_code == 409

    def test_duplicate_badge_rejected(self, client, auth_headers, admin_user):
        response = client.post("/api/v1/police-users/", json={
            "first_name": "Dup",
            "last_name": "Badge",
            "email": "dupbadge@trustbond.rw",
            "password": "test123",
            "badge_number": "ADM-001",  # Already exists
            "role": "officer",
        }, headers=auth_headers)
        assert response.status_code == 409


class TestGetPoliceUser:
    """GET /api/v1/police-users/{id}"""

    def test_get_existing_user(self, client, auth_headers, admin_user):
        response = client.get(
            f"/api/v1/police-users/{admin_user.police_user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["email"] == "admin@trustbond.rw"

    def test_get_nonexistent_user(self, client, auth_headers):
        response = client.get(
            "/api/v1/police-users/9999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdatePoliceUser:
    """PATCH /api/v1/police-users/{id}"""

    def test_admin_can_update(self, client, auth_headers, officer_user):
        response = client.patch(
            f"/api/v1/police-users/{officer_user.police_user_id}",
            json={"phone_number": "+250788000001"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["phone_number"] == "+250788000001"

    def test_toggle_is_active(self, client, auth_headers, officer_user):
        response = client.patch(
            f"/api/v1/police-users/{officer_user.police_user_id}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_officer_cannot_update(self, client, officer_headers, admin_user):
        response = client.patch(
            f"/api/v1/police-users/{admin_user.police_user_id}",
            json={"phone_number": "+250788999999"},
            headers=officer_headers,
        )
        assert response.status_code == 403
