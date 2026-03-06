"""
app/services/incident_type_importer.py

Loads incident types from a JSON file and upserts them into the database.
Called automatically at application startup via lifespan event.

JSON file location (default): data/incident_types.json
Override with env var: INCIDENT_TYPES_JSON_PATH
"""
from __future__ import annotations

import json
import logging
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.incident_type import IncidentType

logger = logging.getLogger(__name__)

# ── Resolve the JSON path ──────────────────────────────────────────────────────
# Default: <project_root>/data/incident_types.json
# Can be overridden by setting INCIDENT_TYPES_JSON_PATH in your .env / environment.
_DEFAULT_JSON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "incident_types.json"


def _resolve_json_path() -> Path:
    """Return the JSON file path, preferring the env-var override."""
    import os
    env_path = os.getenv("INCIDENT_TYPES_JSON_PATH")
    return Path(env_path) if env_path else _DEFAULT_JSON_PATH


# ── Core import logic ─────────────────────────────────────────────────────────

def import_incident_types(db: Session, json_path: Path | None = None) -> dict[str, int]:
    """
    Read incident types from *json_path* and upsert them into the database.

    Upsert logic:
      - If a row with the same ``type_name`` exists → update description,
        severity_weight, and is_active.
      - If it does not exist → insert it.

    Returns a summary dict: {"inserted": int, "updated": int, "errors": int}
    """
    path = json_path or _resolve_json_path()

    if not path.exists():
        logger.warning("Incident types JSON not found at %s – skipping import.", path)
        return {"inserted": 0, "updated": 0, "errors": 0}

    try:
        raw = path.read_text(encoding="utf-8")
        records: list[dict] = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to read incident types JSON at %s: %s", path, exc)
        return {"inserted": 0, "updated": 0, "errors": 1}

    if not isinstance(records, list):
        logger.error("incident_types.json must contain a JSON array at the top level.")
        return {"inserted": 0, "updated": 0, "errors": 1}

    inserted = updated = errors = 0

    for record in records:
        try:
            type_name = record["type_name"].strip()
        except (KeyError, AttributeError):
            logger.warning("Skipping record missing 'type_name': %s", record)
            errors += 1
            continue

        try:
            severity_weight = Decimal(str(record.get("severity_weight", "1.00")))
        except Exception:
            logger.warning("Invalid severity_weight for '%s', defaulting to 1.00", type_name)
            severity_weight = Decimal("1.00")

        # PostgreSQL upsert on the unique type_name column
        stmt = (
            pg_insert(IncidentType)
            .values(
                type_name=type_name,
                description=record.get("description"),
                severity_weight=severity_weight,
                is_active=record.get("is_active", True),
            )
            .on_conflict_do_update(
                index_elements=["type_name"],
                set_={
                    "description": record.get("description"),
                    "severity_weight": severity_weight,
                    "is_active": record.get("is_active", True),
                },
            )
        )

        try:
            result = db.execute(stmt)
            # rowcount == 1 on insert, == 1 on update (PostgreSQL always returns 1 for upsert)
            # Use result.inserted_primary_key to distinguish: None means update occurred.
            if result.inserted_primary_key:
                inserted += 1
            else:
                updated += 1
        except Exception as exc:
            logger.error("DB error upserting incident type '%s': %s", type_name, exc)
            db.rollback()
            errors += 1
            continue

    db.commit()
    logger.info(
        "Incident types import complete – inserted=%d, updated=%d, errors=%d",
        inserted, updated, errors,
    )
    return {"inserted": inserted, "updated": updated, "errors": errors}