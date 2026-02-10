"""Report service — submission, filtering, status updates."""

from sqlalchemy.orm import Session


class ReportService:
    """Business logic for reports table."""

    @staticmethod
    def create_report(db: Session, data: dict) -> dict:
        """Create report, resolve village_location_id from GPS, trigger verification."""
        # TODO: implement
        pass

    @staticmethod
    def list_reports(db: Session, filters: dict, page: int, per_page: int):
        """Paginated, filtered report listing with joins."""
        # TODO: implement
        pass

    @staticmethod
    def get_report_detail(db: Session, report_id: str):
        """Full report with evidence, predictions, reviews, assignments."""
        # TODO: implement
        pass
