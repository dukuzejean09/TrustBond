"""Evidence endpoints — upload and retrieve report evidence files."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/reports/{report_id}/upload")
async def upload_evidence(report_id: str):
    """Upload evidence to Cloudinary, store metadata in evidence_files table."""
    # TODO: Cloudinary upload, store file_url, file_type, media GPS, is_live_capture
    pass


@router.get("/reports/{report_id}")
async def get_report_evidence(report_id: str):
    """Retrieve all evidence files for a report."""
    # TODO: query evidence_files by report_id
    pass
