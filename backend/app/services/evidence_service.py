"""Evidence service — Cloudinary upload, metadata storage."""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.models.evidence_file import EvidenceFile
from app.utils.cloudinary import upload_file


class EvidenceService:
    """Business logic for evidence_files table."""

    @staticmethod
    def upload_evidence(
        db: Session,
        report_id: UUID,
        file,
        metadata: dict,
    ) -> EvidenceFile:
        """Upload file to Cloudinary, store URL and metadata in evidence_files."""
        file_type = metadata.get("file_type", "photo")
        cloud_result = upload_file(file, file_type=file_type)

        evidence = EvidenceFile(
            report_id=report_id,
            file_url=cloud_result["url"],
            file_type=file_type,
            media_latitude=metadata.get("media_latitude"),
            media_longitude=metadata.get("media_longitude"),
            captured_at=metadata.get("captured_at"),
            is_live_capture=metadata.get("is_live_capture", False),
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    @staticmethod
    def get_evidence_for_report(db: Session, report_id: UUID) -> List[EvidenceFile]:
        """Retrieve all evidence files for a report."""
        return (
            db.query(EvidenceFile)
            .filter(EvidenceFile.report_id == report_id)
            .order_by(EvidenceFile.uploaded_at)
            .all()
        )
