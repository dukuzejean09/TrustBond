from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import reports as reports_api
from app.api.v1.reports import router
from app.database import get_db


class FakeQuery:
    def __init__(self, data):
        self._data = data

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def first(self):
        return self._data[0] if self._data else None

    def all(self):
        return list(self._data)

    def count(self):
        return len(self._data)


class FakeDB:
    def __init__(self, report, duplicate_rows=None):
        self._report = report
        self._duplicate_rows = duplicate_rows or []
        self._evidence_rows = []

    def query(self, model):
        if model is reports_api.Report:
            return FakeQuery([self._report] if self._report is not None else [])
        if model is reports_api.EvidenceFile:
            rows = list(self._duplicate_rows) + list(self._evidence_rows)
            return FakeQuery(rows)
        return FakeQuery([])

    def add(self, obj=None, *args, **kwargs):
        if obj is not None and isinstance(obj, reports_api.EvidenceFile):
            self._evidence_rows.append(obj)
        return None

    def commit(self):
        return None

    def rollback(self):
        return None

    def refresh(self, *args, **kwargs):
        return None


def build_client(fake_db: FakeDB) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: fake_db
    return TestClient(app)


def base_report(report_id: UUID, device_id: UUID):
    return SimpleNamespace(
        report_id=report_id,
        device_id=device_id,
        reported_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        device=SimpleNamespace(device_id=device_id, device_hash="hash-1"),
    )
