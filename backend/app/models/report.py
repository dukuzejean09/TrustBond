"""reports — Incident Reports (Raw Submissions)."""

import uuid
from sqlalchemy import (
    Column, String, Text, Integer, SmallInteger, Boolean, DECIMAL, TIMESTAMP, Enum, ForeignKey, Index, text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    incident_type_id = Column(SmallInteger, ForeignKey("incident_types.incident_type_id"), nullable=False)
    description = Column(Text)
    latitude = Column(DECIMAL(10, 7), nullable=False)
    longitude = Column(DECIMAL(10, 7), nullable=False)
    gps_accuracy = Column(DECIMAL(6, 2))
    motion_level = Column(Enum("low", "medium", "high", name="motion_level_enum"))
    movement_speed = Column(DECIMAL(6, 2))
    was_stationary = Column(Boolean)
    village_location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=True)
    reported_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    rule_status = Column(Enum("passed", "flagged", "rejected", name="rule_status_enum"), nullable=False, server_default=text("'passed'"))
    is_flagged = Column(Boolean, nullable=False, server_default=text("false"))
    feature_vector = Column(JSONB, nullable=True)
    ai_ready = Column(Boolean, nullable=False, server_default=text("false"))
    features_extracted = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index("idx_reports_device", "device_id"),
        Index("idx_reports_type", "incident_type_id"),
        Index("idx_reports_reported", "reported_at"),
        Index("idx_reports_rule", "rule_status"),
        Index("idx_reports_ai_ready", "ai_ready"),
    )

    # Relationships
    device = relationship("Device", back_populates="reports")
    incident_type = relationship("IncidentType", back_populates="reports")
    village_location = relationship("Location", back_populates="reports")
    evidence_files = relationship("EvidenceFile", back_populates="report")
    ml_predictions = relationship("MLPrediction", back_populates="report")
    police_reviews = relationship("PoliceReview", back_populates="report")
    assignments = relationship("ReportAssignment", back_populates="report")
