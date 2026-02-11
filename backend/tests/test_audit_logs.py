"""Tests for audit logging across all state-changing endpoints."""


class TestAuditLogging:
    """Verify audit_logs entries are created for state-changing calls."""

    def test_login_creates_audit_log(self, client, db, admin_user):
        from app.models.audit_log import AuditLog

        client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "admin123",
        })
        logs = db.query(AuditLog).filter(AuditLog.action_type == "login").all()
        assert len(logs) >= 1
        assert logs[0].entity_type == "police_user"

    def test_failed_login_creates_audit_log(self, client, db, admin_user):
        from app.models.audit_log import AuditLog

        client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "wrong",
        })
        logs = db.query(AuditLog).filter(
            AuditLog.action_type == "login_failed",
        ).all()
        assert len(logs) >= 1
        assert logs[0].success is False

    def test_create_report_audited(self, client, db, sample_incident_type):
        from app.models.audit_log import AuditLog

        client.post("/api/v1/reports/", json={
            "device_hash": "audit_test_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        logs = db.query(AuditLog).filter(
            AuditLog.action_type == "create",
            AuditLog.entity_type == "report",
        ).all()
        assert len(logs) >= 1

    def test_update_report_audited(self, client, db, auth_headers, sample_incident_type):
        from app.models.audit_log import AuditLog

        create_resp = client.post("/api/v1/reports/", json={
            "device_hash": "audit_update_hash",
            "incident_type_id": sample_incident_type.incident_type_id,
            "latitude": "-1.5000000",
            "longitude": "29.6000000",
        })
        report_id = create_resp.json()["report_id"]

        client.patch(
            f"/api/v1/reports/{report_id}",
            json={"is_flagged": True},
            headers=auth_headers,
        )
        logs = db.query(AuditLog).filter(
            AuditLog.action_type == "update",
            AuditLog.entity_type == "report",
        ).all()
        assert len(logs) >= 1

    def test_create_incident_type_audited(self, client, db, auth_headers):
        from app.models.audit_log import AuditLog

        client.post(
            "/api/v1/incident-types/",
            json={"type_name": "Audit Test Type"},
            headers=auth_headers,
        )
        logs = db.query(AuditLog).filter(
            AuditLog.entity_type == "incident_type",
        ).all()
        assert len(logs) >= 1

    def test_create_police_user_audited(self, client, db, auth_headers):
        from app.models.audit_log import AuditLog

        client.post("/api/v1/police-users/", json={
            "first_name": "Audit",
            "last_name": "Test",
            "email": "audit@trustbond.rw",
            "password": "test123",
            "role": "officer",
        }, headers=auth_headers)
        logs = db.query(AuditLog).filter(
            AuditLog.entity_type == "police_user",
            AuditLog.action_type == "create",
        ).all()
        assert len(logs) >= 1


class TestAuditLogsEndpoint:
    """GET /api/v1/audit-logs/"""

    def test_admin_can_view(self, client, db, auth_headers, admin_user):
        # Create some audit entries by performing actions
        client.post("/api/v1/auth/login", json={
            "email": "admin@trustbond.rw",
            "password": "admin123",
        })
        response = client.get("/api/v1/audit-logs/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_officer_cannot_view(self, client, officer_headers):
        response = client.get("/api/v1/audit-logs/", headers=officer_headers)
        assert response.status_code == 403

    def test_filter_by_action_type(self, client, db, auth_headers, admin_user):
        from app.services.audit_service import AuditService
        AuditService.log(
            db,
            actor_type="system",
            actor_id=None,
            action_type="test_action",
            entity_type="test",
            entity_id="1",
        )
        response = client.get(
            "/api/v1/audit-logs/?action_type=test_action",
            headers=auth_headers,
        )
        data = response.json()
        assert all(log["action_type"] == "test_action" for log in data)
