from uuid import uuid4

from sqlalchemy import Column, SmallInteger, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class IncidentGroup(Base):
    __tablename__ = "incident_groups"

    group_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_type_id = Column(SmallInteger, ForeignKey("incident_types.incident_type_id"), nullable=False)
    center_lat = Column(Numeric(10, 7), nullable=False)
    center_long = Column(Numeric(10, 7), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    report_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship("Report", back_populates="incident_group")

    @property
    def report_ids(self):
        return [report.report_id for report in getattr(self, "reports", []) or []]

    @property
    def duration_minutes(self):
        if self.start_time is None or self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() // 60)
