from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_context import get_request_id
from app.middleware.request_id import REQUEST_ID_HEADER, RequestIdMiddleware


def test_request_id_is_generated_and_exposed_in_response_header() -> None:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/echo")
    async def echo() -> dict[str, str | None]:
        return {"request_id": get_request_id()}

    client = TestClient(app)
    response = client.get("/echo")

    assert response.status_code == 200
    generated_request_id = response.headers.get(REQUEST_ID_HEADER)
    assert generated_request_id
    assert response.json()["request_id"] == generated_request_id


def test_request_id_header_is_preserved_when_provided() -> None:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/echo")
    async def echo() -> dict[str, str | None]:
        return {"request_id": get_request_id()}

    client = TestClient(app)
    response = client.get("/echo", headers={REQUEST_ID_HEADER: "manual-request-id-123"})

    assert response.status_code == 200
    assert response.headers.get(REQUEST_ID_HEADER) == "manual-request-id-123"
    assert response.json()["request_id"] == "manual-request-id-123"
