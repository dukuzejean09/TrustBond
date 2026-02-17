"""incident_groups — Duplicate Incident Grouping."""

import uuid
from sqlalchemy import Column, SmallInteger, Integer, DECIMAL, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class IncidentGroup(Base):
    __tablename__ = "incident_groups"

    group_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    incident_type_id = Column(SmallInteger, ForeignKey("incident_types.incident_type_id"), nullable=False)
    center_lat = Column(DECIMAL(10, 7))
    center_long = Column(DECIMAL(10, 7))
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    report_count = Column(Integer, nullable=False, server_default=text("0"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # Relationships
    incident_type = relationship("IncidentType", back_populates="incident_groups")
