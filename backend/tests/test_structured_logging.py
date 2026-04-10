import json
import logging

from app.core.audit import structured_log
from app.core.request_context import reset_request_id, set_request_id


def test_structured_log_includes_request_id_and_tags(caplog) -> None:
    token = set_request_id("req-abc-123")
    caplog.set_level(logging.INFO, logger="app.structured")

    payload = structured_log(
        "hotspot.recompute",
        "hotspot",
        "success",
        created=2,
        min_incidents=3,
    )

    reset_request_id(token)

    assert payload["request_id"] == "req-abc-123"
    assert payload["created"] == 2
    assert payload["min_incidents"] == 3

    parsed = json.loads(caplog.records[-1].message)
    assert parsed["request_id"] == "req-abc-123"
    assert parsed["action"] == "hotspot.recompute"
    assert parsed["entity"] == "hotspot"
    assert parsed["outcome"] == "success"
