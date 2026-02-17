"""devices — Anonymous Reporter Devices."""

import uuid
from sqlalchemy import Column, String, Integer, DECIMAL, TIMESTAMP, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    device_hash = Column(String(255), unique=True, nullable=False)
    first_seen_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    total_reports = Column(Integer, nullable=False, server_default=text("0"))
    trusted_reports = Column(Integer, nullable=False, server_default=text("0"))
    flagged_reports = Column(Integer, nullable=False, server_default=text("0"))
    device_trust_score = Column(DECIMAL(5, 2), nullable=False, server_default=text("50.00"))

    __table_args__ = (
        Index("idx_devices_hash", "device_hash"),
    )

    # Relationships
    reports = relationship("Report", back_populates="device")
