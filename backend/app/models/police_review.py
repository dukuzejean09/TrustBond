"""police_reviews — Ground Truth Decisions."""

import uuid
from sqlalchemy import Column, Text, Boolean, DECIMAL, TIMESTAMP, Enum, ForeignKey, Integer, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PoliceReview(Base):
    __tablename__ = "police_reviews"

    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    police_user_id = Column(Integer, ForeignKey("police_users.police_user_id"), nullable=False)
    decision = Column(Enum("confirmed", "rejected", "investigation", name="review_decision_enum"), nullable=False)
    review_note = Column(Text)
    reviewed_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    ground_truth_label = Column(Enum("real", "fake", name="ground_truth_enum"))
    confidence_level = Column(DECIMAL(5, 2))
    used_for_training = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (
        Index("idx_review_report", "report_id"),
    )

    # Relationships
    report = relationship("Report", back_populates="police_reviews")
    police_user = relationship("PoliceUser", back_populates="reviews")
