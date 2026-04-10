from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RouteRateLimitMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RouteRateLimitMiddleware,
        report_create_per_minute=2,
        evidence_upload_per_minute=2,
        report_confirm_per_minute=2,
    )

    @app.post("/api/v1/reports")
    async def create_report() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/reports/{report_id}/evidence")
    async def upload_evidence(report_id: str) -> dict[str, str]:
        return {"status": report_id}

    @app.post("/api/v1/reports/{report_id}/confirm")
    async def confirm_report(report_id: str) -> dict[str, str]:
        return {"status": report_id}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_rate_limit_applies_to_report_create() -> None:
    app = _build_app()
    client = TestClient(app)

    assert client.post("/api/v1/reports").status_code == 200
    assert client.post("/api/v1/reports").status_code == 200

    blocked = client.post("/api/v1/reports")
    assert blocked.status_code == 429
    assert blocked.json()["rule"] == "report_create"


def test_rate_limit_applies_to_evidence_route() -> None:
    app = _build_app()
    client = TestClient(app)

    assert client.post("/api/v1/reports/abc/evidence").status_code == 200
    assert client.post("/api/v1/reports/abc/evidence").status_code == 200

    blocked = client.post("/api/v1/reports/abc/evidence")
    assert blocked.status_code == 429
    assert blocked.json()["rule"] == "evidence_upload"


def test_non_targeted_routes_not_rate_limited() -> None:
    app = _build_app()
    client = TestClient(app)

    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
