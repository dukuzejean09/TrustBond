from sqlalchemy import Column, SmallInteger, Integer, DateTime, ForeignKey, Numeric, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class IncidentGroup(Base):
    __tablename__ = "incident_groups"

    group_id = Column(UUID(as_uuid=True), primary_key=True)
    incident_type_id = Column(SmallInteger, ForeignKey("incident_types.incident_type_id"), nullable=False)
    center_lat = Column(Numeric(10, 7), nullable=False)
    center_long = Column(Numeric(10, 7), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    report_count = Column(Integer, nullable=False)
    distinct_device_count = Column(Integer, nullable=False, default=1)
    radius_meters = Column(Numeric(8, 2), nullable=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    grouping_method = Column(String(50), nullable=False, default="ai_auto_grouped")
    metadata_json = Column("metadata", JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incident_type = relationship("IncidentType", backref="incident_groups")
    reports = relationship("Report", back_populates="incident_group")
    case = relationship("Case", back_populates="incident_group", uselist=False)

    @property
    def case_id(self):
        return self.case.case_id if self.case is not None else None

    @property
    def case_number(self):
        return self.case.case_number if self.case is not None else None
