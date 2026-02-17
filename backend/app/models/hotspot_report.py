"""hotspot_reports — Hotspot Membership (join table)."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class HotspotReport(Base):
    __tablename__ = "hotspot_reports"

    hotspot_id = Column(Integer, ForeignKey("hotspots.hotspot_id", ondelete="CASCADE"), primary_key=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    hotspot = relationship("Hotspot", back_populates="hotspot_reports")
    report = relationship("Report")
