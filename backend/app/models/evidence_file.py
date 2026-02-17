"""evidence_files — Report Evidence."""

import uuid
from sqlalchemy import Column, String, Boolean, DECIMAL, TIMESTAMP, Enum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    evidence_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(Enum("photo", "video", name="file_type_enum"), nullable=False)
    media_latitude = Column(DECIMAL(10, 7))
    media_longitude = Column(DECIMAL(10, 7))
    captured_at = Column(TIMESTAMP)
    is_live_capture = Column(Boolean, nullable=False, server_default=text("false"))
    uploaded_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    perceptual_hash = Column(String(128))
    blur_score = Column(DECIMAL(6, 3))
    tamper_score = Column(DECIMAL(6, 3))
    ai_quality_label = Column(Enum("good", "poor", "suspicious", name="ai_quality_label_enum"))
    ai_checked_at = Column(TIMESTAMP)

    __table_args__ = (
        Index("idx_evidence_report", "report_id"),
        Index("idx_evidence_phash", "perceptual_hash"),
    )

    # Relationships
    report = relationship("Report", back_populates="evidence_files")
