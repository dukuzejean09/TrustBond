"""hotspots — Risk Clusters."""

from sqlalchemy import Column, Integer, DECIMAL, TIMESTAMP, Enum, text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Hotspot(Base):
    __tablename__ = "hotspots"

    hotspot_id = Column(Integer, primary_key=True, autoincrement=True)
    center_lat = Column(DECIMAL(10, 7), nullable=False)
    center_long = Column(DECIMAL(10, 7), nullable=False)
    radius_meters = Column(DECIMAL(8, 2))
    incident_count = Column(Integer, nullable=False, server_default=text("0"))
    risk_level = Column(Enum("low", "medium", "high", name="risk_level_enum"), nullable=False)
    time_window_hours = Column(Integer)
    detected_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    # Relationships
    hotspot_reports = relationship("HotspotReport", back_populates="hotspot")
