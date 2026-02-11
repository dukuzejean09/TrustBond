"""Test configuration — shared fixtures with in-memory SQLite DB.

Registers @compiles hooks so PostgreSQL-specific DDL (UUID, JSONB,
Geometry, gen_random_uuid, NOW()) is replaced by SQLite equivalents.
"""

import uuid
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text as sa_text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles

# ── Register SQLite compilation overrides BEFORE any model import ─────
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy import BigInteger, SmallInteger

# GeoAlchemy2 may not be installed in all CI environments
try:
    from geoalchemy2 import Geometry as GA2_Geometry

    @compiles(GA2_Geometry, "sqlite")
    def _compile_geometry_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(PG_JSON, "sqlite")
def _compile_pgjson_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"


@compiles(SmallInteger, "sqlite")
def _compile_smallint_sqlite(type_, compiler, **kw):
    return "INTEGER"


# Now safe to import models / app
from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.police_user import PoliceUser
from app.models.device import Device
from app.models.incident_type import IncidentType
from app.main import app  # noqa: triggers all model imports


# ── In-memory SQLite engine (reset per test) ─────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

    # Register no-op stubs for SpatiaLite functions so GeoAlchemy2 DDL
    # events succeed on plain SQLite (no SpatiaLite extension needed).
    # DDL functions should return 1 (success); data functions return None.
    _ddl_noop = lambda *a: 1
    _data_noop = lambda *a: None

    for fn_name in (
        "RecoverGeometryColumn",
        "DiscardGeometryColumn",
        "AddGeometryColumn",
        "CreateSpatialIndex",
        "DisableSpatialIndex",
        "CheckSpatialIndex",
        "UpdateLayerStatistics",
    ):
        dbapi_connection.create_function(fn_name, -1, _ddl_noop)

    for fn_name in (
        "AsEWKB",
        "GeomFromEWKB",
        "GeomFromEWKT",
        "ST_AsText",
        "ST_GeomFromText",
        "ST_GeomFromEWKT",
        "AsGeoJSON",
        "ST_AsEWKB",
        "ST_GeomFromEWKB",
    ):
        dbapi_connection.create_function(fn_name, -1, _data_noop)


# ── Patch server_defaults that only work on PostgreSQL ───────────────
_PG_DEFAULTS_STRIP = {"gen_random_uuid()"}
_ALREADY_PATCHED = False


def _patch_pg_server_defaults():
    """Strip / replace PG-only server_default expressions so CREATE TABLE
    succeeds on SQLite.  Runs once per process."""
    global _ALREADY_PATCHED
    if _ALREADY_PATCHED:
        return
    for table in Base.metadata.tables.values():
        for col in table.columns:
            sd = col.server_default
            if sd is None:
                continue
            try:
                sd_text = sd.arg.text if hasattr(sd.arg, "text") else str(sd.arg)
            except Exception:
                continue
            sd_lower = sd_text.strip().lower()
            if sd_lower in _PG_DEFAULTS_STRIP:
                col.server_default = None  # rely on Python default=uuid.uuid4
            elif sd_lower == "now()":
                sd.arg = sa_text("CURRENT_TIMESTAMP")
            elif sd_lower == "false":
                sd.arg = sa_text("0")
            elif sd_lower == "true":
                sd.arg = sa_text("1")
            # string-wrapped enums like 'passed' and numeric defaults are fine
    _ALREADY_PATCHED = True


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    _patch_pg_server_defaults()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the in-memory rate limiter between tests."""
    from app.main import _rate_store
    _rate_store.clear()
    yield
    _rate_store.clear()


@pytest.fixture
def db():
    """Yield a fresh DB session for a test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """FastAPI test client wired to the test DB session."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helper fixtures ──────────────────────────────────────────────────

@pytest.fixture
def admin_user(db) -> PoliceUser:
    """Create an admin police user in the test DB."""
    user = PoliceUser(
        first_name="Admin",
        last_name="User",
        email="admin@trustbond.rw",
        password_hash=hash_password("admin123"),
        badge_number="ADM-001",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def officer_user(db) -> PoliceUser:
    """Create a regular officer in the test DB."""
    user = PoliceUser(
        first_name="John",
        last_name="Officer",
        email="officer@trustbond.rw",
        password_hash=hash_password("officer123"),
        badge_number="OFF-001",
        role="officer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user) -> str:
    """JWT token for the admin user."""
    return create_access_token(
        data={"sub": str(admin_user.police_user_id), "role": admin_user.role}
    )


@pytest.fixture
def officer_token(officer_user) -> str:
    """JWT token for the regular officer."""
    return create_access_token(
        data={"sub": str(officer_user.police_user_id), "role": officer_user.role}
    )


@pytest.fixture
def auth_headers(admin_token) -> dict:
    """Authorization headers with admin JWT."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def officer_headers(officer_token) -> dict:
    """Authorization headers with officer JWT."""
    return {"Authorization": f"Bearer {officer_token}"}


@pytest.fixture
def sample_incident_type(db) -> IncidentType:
    """Create a sample incident type."""
    it = IncidentType(type_name="Theft", severity_weight=2.0, is_active=True)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


@pytest.fixture
def sample_device(db) -> Device:
    """Create a sample device."""
    d = Device(device_hash="abc123hash456")
    db.add(d)
    db.commit()
    db.refresh(d)
    return d
