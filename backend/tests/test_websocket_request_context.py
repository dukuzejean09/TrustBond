import asyncio
import json

from app.core.request_context import reset_request_id, set_request_id
from app.core.websocket import ConnectionManager


class _FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send_text(self, payload: str) -> None:
        self.messages.append(payload)


def test_broadcast_includes_request_id_from_context() -> None:
    manager = ConnectionManager()
    ws = _FakeWebSocket()
    manager.active_connections.append(ws)

    token = set_request_id("rid-123")
    try:
        asyncio.run(manager.broadcast({"type": "refresh_data", "entity": "report"}))
    finally:
        reset_request_id(token)

    assert len(ws.messages) == 1
    payload = json.loads(ws.messages[0])
    assert payload["request_id"] == "rid-123"
    assert payload["entity"] == "report"


def test_broadcast_preserves_existing_request_id() -> None:
    manager = ConnectionManager()
    ws = _FakeWebSocket()
    manager.active_connections.append(ws)

    token = set_request_id("rid-context")
    try:
        asyncio.run(
            manager.broadcast(
                {"type": "refresh_data", "entity": "hotspot", "request_id": "rid-payload"}
            )
        )
    finally:
        reset_request_id(token)

    payload = json.loads(ws.messages[0])
    assert payload["request_id"] == "rid-payload"
