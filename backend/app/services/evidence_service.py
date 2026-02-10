"""Evidence service — Cloudinary upload, metadata storage."""

from sqlalchemy.orm import Session


class EvidenceService:
    """Business logic for evidence_files table."""

    @staticmethod
    def upload_evidence(db: Session, report_id: str, file, metadata: dict):
        """Upload file to Cloudinary, store URL and metadata in evidence_files."""
        # TODO: implement Cloudinary integration
        pass

    @staticmethod
    def get_evidence_for_report(db: Session, report_id: str):
        """Retrieve all evidence files for a report."""
        # TODO: implement
        pass
