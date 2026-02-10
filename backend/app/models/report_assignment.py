"""report_assignments — Case Handling Workflow."""

import uuid
from sqlalchemy import Column, Integer, TIMESTAMP, Enum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReportAssignment(Base):
    __tablename__ = "report_assignments"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    police_user_id = Column(Integer, ForeignKey("police_users.police_user_id"), nullable=False)
    status = Column(
        Enum("assigned", "investigating", "resolved", "closed", name="assignment_status_enum"),
        nullable=False,
        server_default=text("'assigned'"),
    )
    priority = Column(
        Enum("low", "medium", "high", "urgent", name="assignment_priority_enum"),
        nullable=False,
        server_default=text("'medium'"),
    )
    assigned_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    completed_at = Column(TIMESTAMP)

    __table_args__ = (
        Index("idx_assign_report", "report_id"),
        Index("idx_assign_officer", "police_user_id"),
        Index("idx_assign_status", "status"),
    )

    # Relationships
    report = relationship("Report", back_populates="assignments")
    police_user = relationship("PoliceUser", back_populates="assignments")
