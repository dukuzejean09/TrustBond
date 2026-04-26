"""
Seed initial incident types.

Run:
  python scripts/seed_incident_types.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from decimal import Decimal
from typing import Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Ensure `backend/` is on PYTHONPATH so `import app` works even when executing
# `python scripts/seed_incident_types.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.models.incident_type import IncidentType


DEFAULT_INCIDENT_TYPES: list[dict] = [
    {
        "type_name": "Theft (Ubujura)",
        "description": "Stealing of property such as a phone, money, livestock, or other personal belongings.",
        "severity_weight": Decimal("1.20"),
    },
    {
        "type_name": "Assault (Gukomeretsa)",
        "description": "Physical attack or violence against a person causing bodily harm or injury.",
        "severity_weight": Decimal("1.60"),
    },
    {
        "type_name": "Vandalism (Gusambura Umutungo)",
        "description": "Deliberate damage or destruction of public or private property.",
        "severity_weight": Decimal("1.10"),
    },
    {
        "type_name": "Suspicious Activity (Ibikorwa Biteye Inkeke)",
        "description": "Unusual or suspicious behavior, movement, or presence that may indicate a threat.",
        "severity_weight": Decimal("1.00"),
    },
    {
        "type_name": "Domestic Violence (Ihohoterwa mu Muryango)",
        "description": "Physical, emotional, or psychological abuse or threats occurring within a household or family.",
        "severity_weight": Decimal("1.70"),
    },
    {
        "type_name": "Drug Activity (Ibiyobyabwenge)",
        "description": "Suspected illegal selling, distribution, or use of narcotics or controlled substances.",
        "severity_weight": Decimal("1.40"),
    },
    {
        "type_name": "Fraud/Scam (Uburiganya)",
        "description": "Deception or trickery to unlawfully obtain money or property, including mobile money scams.",
        "severity_weight": Decimal("1.30"),
    },
    {
        "type_name": "Harassment (Gutoteza)",
        "description": "Repeated threats, intimidation, stalking, or unwanted aggressive behavior toward a person.",
        "severity_weight": Decimal("1.20"),
    },
    {
        "type_name": "Traffic Incident (Impanuka y'Umuhanda)",
        "description": "A road accident or traffic-related event that poses a safety risk to people or property.",
        "severity_weight": Decimal("1.00"),
    },
    {
        "type_name": "Sexual Assault (Ihohoterwa Rishingiye Ku Gitsina)",
        "description": "Any non-consensual sexual act or contact forced upon a person against their will.",
        "severity_weight": Decimal("1.80"),
    },
    {
        "type_name": "Robbery (Kunyaga)",
        "description": "Taking property from a person by force, threat, or use of a weapon.",
        "severity_weight": Decimal("1.70"),
    },
    {
        "type_name": "Homicide (Kwica)",
        "description": "The killing of a person or a life-threatening attack that results in death.",
        "severity_weight": Decimal("2.00"),
    },
    {
        "type_name": "Arson (Gutwika)",
        "description": "Deliberately setting fire to property, buildings, or land causing damage or danger.",
        "severity_weight": Decimal("1.60"),
    },
    {
        "type_name": "Kidnapping (Gutwara Ku Ngufu)",
        "description": "Unlawfully seizing or detaining a person against their will, often for ransom or coercion.",
        "severity_weight": Decimal("1.90"),
    },
]


def seed_incident_types(rows: Iterable[dict] = DEFAULT_INCIDENT_TYPES) -> tuple[int, int]:
    """
    Returns (inserted_count, skipped_count)
    """
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for row in rows:
            existing = db.execute(
                select(IncidentType).where(IncidentType.type_name == row["type_name"])
            ).scalar_one_or_none()
            if existing:
                skipped += 1
                continue
            db.add(
                IncidentType(
                    type_name=row["type_name"],
                    description=row.get("description"),
                    severity_weight=row.get("severity_weight", Decimal("1.00")),
                    is_active=True,
                )
            )
            inserted += 1
        db.commit()
        return inserted, skipped
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    inserted, skipped = seed_incident_types()
    print(f"Incident types seeded. Inserted={inserted}, Skipped(existing)={skipped}")
