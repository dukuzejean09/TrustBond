"""Tests for authentication endpoints."""


class TestLogin:
    """POST /api/v1/auth/login"""

    def test_login_success(self, client, admin_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, admin_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "wrong",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@trustbond.rw",
            "password": "test",
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, client, db, admin_user):
        admin_user.is_active = False
        db.commit()
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "admin123",
        })
        assert response.status_code == 403

    def test_login_updates_last_login(self, client, db, admin_user):
        assert admin_user.last_login_at is None
        client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "admin123",
        })
        db.refresh(admin_user)
        assert admin_user.last_login_at is not None


class TestTokenRefresh:
    """POST /api/v1/auth/refresh"""

    def test_refresh_success(self, client, auth_headers):
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_no_token(self, client):
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code in (401, 403)


class TestAuthProtection:
    """Verify endpoints require authentication."""

    def test_reports_requires_auth(self, client):
        response = client.get("/api/v1/reports/")
        assert response.status_code in (401, 403)

    def test_police_users_requires_auth(self, client):
        response = client.get("/api/v1/police-users/")
        assert response.status_code in (401, 403)
