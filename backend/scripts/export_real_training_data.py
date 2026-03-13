"""
Export real-world labeled reports from the database into a CSV that matches
the exact schema expected by `musanze/train_report_credibility_model.py`.

Ground truth is derived from police verification:
    - verification_status = 'verified'  → ground_truth_label = 'real'
    - verification_status = 'rejected'  → ground_truth_label = 'fake'
    - Other statuses are excluded (not yet labeled).

Usage:
    cd backend
    python -m scripts.export_real_training_data            # default output
    python -m scripts.export_real_training_data --out data/real_training.csv
"""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, func as sa_func
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.report import Report
from app.models.device import Device
from app.models.evidence_file import EvidenceFile
from app.models.incident_type import IncidentType
from app.models.location import Location


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "musanze" / "real_training_data.csv"


# ── Column order must match generate_report_credibility_training.py ──
COLUMNS = [
    "latitude",
    "longitude",
    "sector",
    "cell",
    "village",
    "sector_id",
    "cell_id",
    "village_id",
    "incident_type_id",
    "incident_type_name",
    "gps_accuracy",
    "motion_level",
    "movement_speed",
    "was_stationary",
    "evidence_count",
    "has_live_capture",
    "time_of_day",
    "reported_at",
    "description_length",
    "network_type",
    "device_total_reports",
    "device_trusted_reports",
    "device_flagged_reports",
    "device_trust_score",
    "confirmation_rate",
    "spam_flag_count",
    "rule_status",
    "is_flagged",
    "gps_speed_check",
    "gps_anomaly_flag",
    "future_timestamp_flag",
    "ground_truth_label",
    "decision",
    "confidence_level",
    "used_for_training",
]


def _bucket_time_of_day(dt: datetime | None) -> str:
    if dt is None:
        return "day"
    hour = dt.hour
    if 0 <= hour < 6:
        return "night"
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "day"
    return "evening"


def _derive_ground_truth(report: Report) -> str | None:
    """
    Map police verification to a binary label.
    Returns None when the report has not been conclusively labeled.
    """
    vs = (report.verification_status or "").lower()
    status = (report.status or "").lower()

    if vs == "verified" or status == "verified":
        return "real"
    if vs == "rejected" or status == "rejected":
        return "fake"
    # Reports still pending / under_review → skip
    return None


def _derive_decision(report: Report, label: str) -> str:
    vs = (report.verification_status or "").lower()
    if vs == "verified":
        return "confirmed"
    if vs == "rejected":
        return "rejected"
    return "investigation"


def export(db: Session, output_path: Path) -> int:
    """Export labeled reports to CSV. Returns number of rows written."""

    # Eager-load related objects
    reports = (
        db.query(Report)
        .options(
            joinedload(Report.device),
            joinedload(Report.incident_type),
            joinedload(Report.village_location).joinedload(Location.parent).joinedload(Location.parent),
        )
        .all()
    )

    rows_written = 0
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()

        for report in reports:
            label = _derive_ground_truth(report)
            if label is None:
                continue  # not yet labeled by police

            device: Device | None = report.device
            if device is None:
                continue

            # Evidence count
            evidence_count = len(report.evidence_files) if report.evidence_files else 0

            # Location fields (from village_location → parent chain)
            village_loc = report.village_location
            village = village_loc.location_name if village_loc else None
            village_id = village_loc.location_id if village_loc else None

            cell_loc = village_loc.parent if village_loc else None
            cell = cell_loc.location_name if cell_loc else None
            cell_id = cell_loc.location_id if cell_loc else None

            sector_loc = cell_loc.parent if cell_loc else None
            sector = sector_loc.location_name if sector_loc else None
            sector_id = sector_loc.location_id if sector_loc else None

            # Incident type
            it = report.incident_type
            incident_type_name = it.type_name if it else None

            # Numeric field helpers
            lat = float(report.latitude) if report.latitude is not None else None
            lon = float(report.longitude) if report.longitude is not None else None
            gps_accuracy = float(report.gps_accuracy) if report.gps_accuracy is not None else None
            movement_speed = float(report.movement_speed) if report.movement_speed is not None else None
            was_stationary = int(report.was_stationary) if report.was_stationary is not None else 0

            reported_at = report.reported_at
            time_of_day = _bucket_time_of_day(reported_at)
            reported_at_str = reported_at.isoformat() if reported_at else None

            description_length = len(report.description or "")
            network_type = report.network_type or "mobile"

            # Device stats
            total_reports = device.total_reports or 0
            trusted_reports = device.trusted_reports or 0
            flagged_reports = device.flagged_reports or 0
            device_trust_score = float(device.device_trust_score) if device.device_trust_score is not None else 50.0

            confirmation_rate = trusted_reports / total_reports if total_reports > 0 else 0.0
            spam_flag_count = flagged_reports

            # Rule-engine features
            rule_status = report.rule_status or "pending"
            is_flagged = int(report.is_flagged) if report.is_flagged is not None else 0

            gps_speed_check = movement_speed * 3.6 if movement_speed is not None else 0.0
            gps_anomaly_flag = 1 if (gps_speed_check > 200 or (gps_accuracy is not None and gps_accuracy > 200)) else 0

            now = datetime.now(timezone.utc)
            future_timestamp_flag = 1 if (reported_at and reported_at > now) else 0

            has_live_capture = 1 if evidence_count > 0 else 0

            decision = _derive_decision(report, label)
            confidence_level = 0.9 if decision in ("confirmed", "rejected") else 0.6

            row = {
                "latitude": lat,
                "longitude": lon,
                "sector": sector,
                "cell": cell,
                "village": village,
                "sector_id": sector_id,
                "cell_id": cell_id,
                "village_id": village_id,
                "incident_type_id": report.incident_type_id,
                "incident_type_name": incident_type_name,
                "gps_accuracy": round(gps_accuracy, 2) if gps_accuracy else None,
                "motion_level": report.motion_level or "low",
                "movement_speed": round(movement_speed, 3) if movement_speed else 0.0,
                "was_stationary": was_stationary,
                "evidence_count": evidence_count,
                "has_live_capture": has_live_capture,
                "time_of_day": time_of_day,
                "reported_at": reported_at_str,
                "description_length": description_length,
                "network_type": network_type,
                "device_total_reports": total_reports,
                "device_trusted_reports": trusted_reports,
                "device_flagged_reports": flagged_reports,
                "device_trust_score": round(device_trust_score, 2),
                "confirmation_rate": round(confirmation_rate, 3),
                "spam_flag_count": spam_flag_count,
                "rule_status": rule_status,
                "is_flagged": is_flagged,
                "gps_speed_check": round(gps_speed_check, 2),
                "gps_anomaly_flag": gps_anomaly_flag,
                "future_timestamp_flag": future_timestamp_flag,
                "ground_truth_label": label,
                "decision": decision,
                "confidence_level": round(confidence_level, 3),
                "used_for_training": 1,
            }

            writer.writerow(row)
            rows_written += 1

    return rows_written


def main():
    parser = argparse.ArgumentParser(description="Export real labeled reports for ML training")
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUTPUT), help="Output CSV path")
    args = parser.parse_args()

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        count = export(db, output_path)
        print(f"Exported {count} labeled reports → {output_path}")
        if count < 200:
            print(
                f"\n⚠  Only {count} labeled reports found. "
                "You need at least 200–500 labeled reports for meaningful training.\n"
                "Options to collect more labels:\n"
                "  1. Have police officers verify/reject more reports in the dashboard\n"
                "  2. Mix real data with synthetic data (see --help)\n"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
