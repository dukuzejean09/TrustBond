"""locations — Administrative Boundaries (Musanze)."""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Enum, ForeignKey, Index, text
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship
from app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    location_type = Column(Enum("sector", "cell", "village", name="location_type_enum"), nullable=False)
    location_name = Column(String(100), nullable=False)
    parent_location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=True)
    geometry = Column(Geometry("GEOMETRY", srid=4326, spatial_index=False), nullable=True)
    centroid_lat = Column(DECIMAL(10, 7))
    centroid_long = Column(DECIMAL(10, 7))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        Index("idx_locations_geo", "geometry", postgresql_using="gist"),
    )

    # Relationships
    parent = relationship("Location", remote_side=[location_id])
    reports = relationship("Report", back_populates="village_location")
    assigned_officers = relationship("PoliceUser", back_populates="assigned_location")
