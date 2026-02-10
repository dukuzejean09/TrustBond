"""incident_types — Incident Categories."""

from sqlalchemy import Column, SmallInteger, String, Text, DECIMAL, Boolean, TIMESTAMP, text
from sqlalchemy.orm import relationship
from app.core.database import Base


class IncidentType(Base):
    __tablename__ = "incident_types"

    incident_type_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    type_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    severity_weight = Column(DECIMAL(3, 2), nullable=False, server_default=text("1.00"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # Relationships
    reports = relationship("Report", back_populates="incident_type")
    incident_groups = relationship("IncidentGroup", back_populates="incident_type")
