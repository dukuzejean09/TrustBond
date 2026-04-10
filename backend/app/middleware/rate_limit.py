from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.audit import structured_log


WINDOW_SECONDS = 60.0


@dataclass
class _Rule:
    name: str
    path_pattern: re.Pattern[str]
    method: str
    limit_per_window: int


class RouteRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory fixed-window throttling for high-risk write routes."""

    def __init__(
        self,
        app,
        *,
        report_create_per_minute: int = 20,
        evidence_upload_per_minute: int = 30,
        report_confirm_per_minute: int = 40,
    ) -> None:
        super().__init__(app)
        self._rules = [
            _Rule(
                name="report_create",
                method="POST",
                path_pattern=re.compile(r"^/api/v1/reports/?$"),
                limit_per_window=max(1, int(report_create_per_minute)),
            ),
            _Rule(
                name="evidence_upload",
                method="POST",
                path_pattern=re.compile(r"^/api/v1/reports/[^/]+/evidence/?$"),
                limit_per_window=max(1, int(evidence_upload_per_minute)),
            ),
            _Rule(
                name="report_confirm",
                method="POST",
                path_pattern=re.compile(r"^/api/v1/reports/[^/]+/confirm/?$"),
                limit_per_window=max(1, int(report_confirm_per_minute)),
            ),
        ]
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def _match_rule(self, request: Request) -> _Rule | None:
        path = request.url.path
        method = request.method.upper()
        for rule in self._rules:
            if method == rule.method and rule.path_pattern.match(path):
                return rule
        return None

    def _client_key(self, request: Request, rule: _Rule) -> str:
        client_ip = request.client.host if request.client else "unknown"
        return f"{rule.name}:{client_ip}"

    def _consume(self, key: str, limit: int) -> tuple[bool, int, int]:
        now = monotonic()
        cutoff = now - WINDOW_SECONDS

        with self._lock:
            bucket = self._hits.get(key)
            if bucket is None:
                bucket = deque()
                self._hits[key] = bucket

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after_seconds = int(max(1, WINDOW_SECONDS - (now - bucket[0])))
                remaining = 0
                return False, remaining, retry_after_seconds

            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return True, remaining, 0

    async def dispatch(self, request: Request, call_next) -> Response:
        rule = self._match_rule(request)
        if rule is None:
            return await call_next(request)

        key = self._client_key(request, rule)
        allowed, remaining, retry_after = self._consume(key, rule.limit_per_window)
        if not allowed:
            structured_log(
                "rate_limit.blocked",
                "api",
                "blocked",
                rule=rule.name,
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else None,
                retry_after_seconds=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry shortly.",
                    "rule": rule.name,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule.limit_per_window),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rule.limit_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
