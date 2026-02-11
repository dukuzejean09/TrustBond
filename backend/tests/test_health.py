"""Smoke test — verify the app starts and health check works."""


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project"] == "TrustBond"


def test_openapi_available(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()
