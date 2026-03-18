from __future__ import annotations

import argparse

from sqlalchemy.orm import joinedload, selectinload

from app.database import SessionLocal
from app.models.report import Report
from app.models.device import Device
from app.models.ml_prediction import MLPrediction
from app.core.credibility_model import score_report_credibility


def run(force: bool = False) -> None:
    db = SessionLocal()
    try:
        reports = (
            db.query(Report)
            .options(
                joinedload(Report.device),
                selectinload(Report.evidence_files),
                selectinload(Report.ml_predictions),
            )
            .all()
        )

        reviewed = 0
        skipped = 0

        for report in reports:
            already_reviewed = any((p.is_final is True) for p in (report.ml_predictions or []))
            if already_reviewed and not force:
                skipped += 1
                continue

            device = report.device or db.query(Device).filter(Device.device_id == report.device_id).first()
            if not device:
                skipped += 1
                continue

            evidence_count = len(report.evidence_files or [])
            score_report_credibility(db, report, device, evidence_count)
            reviewed += 1

        db.commit()
        print(f"ML review complete. reviewed={reviewed}, skipped={skipped}, total={len(reports)}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill ML review for reports")
    parser.add_argument("--force", action="store_true", help="Re-score all reports even if they already have a final prediction")
    args = parser.parse_args()
    run(force=args.force)
