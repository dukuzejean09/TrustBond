from sqlalchemy import Column, Integer, SmallInteger, String, Text, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(UUID(as_uuid=True), primary_key=True)
    case_number = Column(String(20), unique=True)
    status = Column(String(20), nullable=False, default="open")
    priority = Column(String(20), nullable=False, default="medium")
    title = Column(String(200))
    description = Column(Text)
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    incident_type_id = Column(SmallInteger, ForeignKey("incident_types.incident_type_id"))
    assigned_to_id = Column(Integer, ForeignKey("police_users.police_user_id"))
    created_by = Column(Integer, ForeignKey("police_users.police_user_id"))
    report_count = Column(Integer, default=0)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    outcome = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Station this case belongs to (primary organisational anchor)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=True)
    incident_group_id = Column(UUID(as_uuid=True), ForeignKey("incident_groups.group_id", ondelete="SET NULL"), nullable=True)
    device_count = Column(Integer, nullable=False, default=1)
    auto_created = Column(Boolean, nullable=False, default=False)
    source = Column(String(30), nullable=False, default="manual")
    auto_group_confidence = Column(Numeric(5, 2), nullable=True)

    location = relationship("Location", backref="cases")
    incident_type = relationship("IncidentType", backref="cases")
    assigned_to = relationship("PoliceUser", foreign_keys=[assigned_to_id])
    created_by_user = relationship("PoliceUser", foreign_keys=[created_by])
    station = relationship("Station", backref="cases", foreign_keys=[station_id])
    incident_group = relationship("IncidentGroup", back_populates="case")


class CaseReport(Base):
    __tablename__ = "case_reports"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.case_id", ondelete="CASCADE"), primary_key=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case", backref="case_reports")
    report = relationship("Report", backref="case_reports")


class CaseHistory(Base):
    """Audit log for all changes to a case — created automatically by the system."""
    __tablename__ = "case_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False)
    # e.g. created | report_added | report_removed | status_changed
    #       officer_assigned | priority_changed | note_added
    action = Column(String(50), nullable=False)
    details = Column(JSONB, nullable=True)
    # NULL means the action was performed by the system (auto-case logic)
    performed_by = Column(Integer, ForeignKey("police_users.police_user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case", backref="history")
    performed_by_user = relationship("PoliceUser", foreign_keys=[performed_by])
