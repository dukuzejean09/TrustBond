from __future__ import annotations

import argparse
import json
import ssl
import uuid
import urllib.request
import urllib.parse


def run(base_url: str, insecure: bool = False) -> None:
    base = _normalize_base_url(base_url)

    # Register synthetic device
    hash_value = f"docker-e2e-ml-check-{uuid.uuid4().hex[:8]}"
    device = _json_request("POST", f"{base}/devices/register", {"device_hash": hash_value}, insecure=insecure)

    # Pick theft incident type if available
    all_types = _json_request("GET", f"{base}/incident-types/", insecure=insecure)
    theft = next(
        (t for t in all_types if "theft" in (t.get("type_name", "").lower())),
        all_types[0],
    )

    # Create report with intentionally contradictory description
    create_payload = {
        "device_id": device["device_id"],
        "incident_type_id": theft["incident_type_id"],
        "description": "A house is burning with visible flames and thick smoke.",
        "latitude": -1.4997,
        "longitude": 29.6351,
        "evidence_files": [],
        "context_tags": ["Night-time"],
        "app_version": "docker-e2e",
        "network_type": "wifi",
        "battery_level": 88,
    }
    report = _json_request("POST", f"{base}/reports/", create_payload, insecure=insecure)

    # Upload tiny PNG via multipart
    png = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000A49444154789C6360000000020001E221BC330000000049454E44AE426082"
    )
    fields = {
        "device_id": device["device_id"],
        "media_latitude": "-1.4997",
        "media_longitude": "29.6351",
        "is_live_capture": "true",
    }
    _multipart_request(
        f"{base}/reports/{report['report_id']}/evidence",
        fields,
        file_field_name="file",
        file_name="e2e.png",
        file_content=png,
        file_content_type="image/png",
        insecure=insecure,
    )

    # Fetch detail
    query = urllib.parse.urlencode({"device_id": device["device_id"]})
    detail = _json_request("GET", f"{base}/reports/{report['report_id']}?{query}", insecure=insecure)

    evidence_files = detail.get("evidence_files") or []

    out = {
        "runtime": "docker_container",
        "incident_type": theft.get("type_name"),
        "report_id": report.get("report_id"),
        "rule_status": detail.get("rule_status"),
        "is_flagged": detail.get("is_flagged"),
        "flag_reason": detail.get("flag_reason"),
        "evidence_count": len(evidence_files),
        "last_evidence_ai_quality": evidence_files[-1].get("ai_quality_label") if evidence_files else None,
        "trust_score": detail.get("trust_score"),
    }
    print(json.dumps(out, indent=2))


def _normalize_base_url(base_url: str) -> str:
    b = (base_url or "").strip().rstrip("/")
    if not b:
        b = "http://127.0.0.1:8000"
    if not b.endswith("/api/v1"):
        b = f"{b}/api/v1"
    return b


def _json_request(method: str, url: str, payload: dict | None = None, insecure: bool = False):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    context = None
    if insecure and url.lower().startswith("https://"):
        context = ssl._create_unverified_context()

    with urllib.request.urlopen(req, timeout=60, context=context) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def _multipart_request(
    url: str,
    fields: dict[str, str],
    file_field_name: str,
    file_name: str,
    file_content: bytes,
    file_content_type: str,
    insecure: bool = False,
) -> dict:
    boundary = f"----TrustBondBoundary{uuid.uuid4().hex}"
    parts: list[bytes] = []

    for key, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        parts.append(str(value).encode("utf-8"))
        parts.append(b"\r\n")

    parts.append(f"--{boundary}\r\n".encode("utf-8"))
    parts.append(
        (
            f'Content-Disposition: form-data; name="{file_field_name}"; '
            f'filename="{file_name}"\r\n'
        ).encode("utf-8")
    )
    parts.append(f"Content-Type: {file_content_type}\r\n\r\n".encode("utf-8"))
    parts.append(file_content)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(parts)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(url, method="POST", data=body, headers=headers)

    context = None
    if insecure and url.lower().startswith("https://"):
        context = ssl._create_unverified_context()

    with urllib.request.urlopen(req, timeout=60, context=context) as resp:
        response_body = resp.read().decode("utf-8")
        return json.loads(response_body) if response_body else {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-end report verification checker")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL, e.g. http://127.0.0.1:8000 or https://trustbond-backend.onrender.com",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for HTTPS requests (test use only).",
    )
    args = parser.parse_args()
    run(args.base_url, insecure=args.insecure)
