"""ml_predictions — Machine Learning Outputs."""

import uuid
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, TIMESTAMP, Enum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    trust_score = Column(DECIMAL(5, 2))
    prediction_label = Column(Enum("likely_real", "suspicious", "fake", name="prediction_label_enum"))
    model_version = Column(String(50))
    evaluated_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    confidence = Column(DECIMAL(5, 2))
    explanation = Column(JSONB)
    processing_time = Column(Integer)  # milliseconds
    model_type = Column(String(50))  # random_forest / anomaly / vision
    is_final = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (
        Index("idx_ml_report", "report_id"),
        Index("idx_ml_final", "is_final"),
    )

    # Relationships
    report = relationship("Report", back_populates="ml_predictions")
