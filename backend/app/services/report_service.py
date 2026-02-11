"""Report service — submission, filtering, status updates."""

from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional

from app.models.report import Report


class ReportService:
    """Business logic for reports table."""

    @staticmethod
    def create_report(db: Session, device_id, data: dict) -> Report:
        """Create report record."""
        report = Report(
            device_id=device_id,
            incident_type_id=data["incident_type_id"],
            description=data.get("description"),
            latitude=data["latitude"],
            longitude=data["longitude"],
            gps_accuracy=data.get("gps_accuracy"),
            motion_level=data.get("motion_level"),
            movement_speed=data.get("movement_speed"),
            was_stationary=data.get("was_stationary"),
            village_location_id=data.get("village_location_id"),
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def list_reports(
        db: Session,
        filters: dict,
        page: int = 1,
        per_page: int = 20,
    ):
        """Paginated, filtered report listing with eager-loaded relations."""
        query = db.query(Report).options(
            joinedload(Report.incident_type),
            joinedload(Report.device),
        )

        if filters.get("rule_status"):
            query = query.filter(Report.rule_status == filters["rule_status"])
        if filters.get("incident_type_id"):
            query = query.filter(Report.incident_type_id == filters["incident_type_id"])
        if filters.get("is_flagged") is not None:
            query = query.filter(Report.is_flagged == filters["is_flagged"])
        if filters.get("device_id"):
            query = query.filter(Report.device_id == filters["device_id"])
        if filters.get("start_date"):
            query = query.filter(Report.reported_at >= filters["start_date"])
        if filters.get("end_date"):
            query = query.filter(Report.reported_at <= filters["end_date"])

        total = query.count()
        reports = (
            query
            .order_by(Report.reported_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return reports, total

    @staticmethod
    def get_report_detail(db: Session, report_id: UUID) -> Optional[Report]:
        """Full report with evidence, predictions, reviews, assignments."""
        return (
            db.query(Report)
            .options(
                joinedload(Report.incident_type),
                joinedload(Report.device),
                joinedload(Report.evidence_files),
                joinedload(Report.ml_predictions),
                joinedload(Report.police_reviews),
                joinedload(Report.assignments),
            )
            .filter(Report.report_id == report_id)
            .first()
        )

    @staticmethod
    def update_report(db: Session, report_id: UUID, data: dict) -> Optional[Report]:
        """Partial update — typically rule_status, is_flagged."""
        report = db.query(Report).filter(Report.report_id == report_id).first()
        if not report:
            return None
        for key, value in data.items():
            if value is not None and hasattr(report, key):
                setattr(report, key, value)
        db.commit()
        db.refresh(report)
        return report
