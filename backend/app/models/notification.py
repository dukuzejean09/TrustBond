"""notifications — System Alerts."""

import uuid
from sqlalchemy import Column, Integer, String, CHAR, Text, Boolean, TIMESTAMP, Enum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    police_user_id = Column(Integer, ForeignKey("police_users.police_user_id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text)
    type = Column(
        Enum("report", "hotspot", "assignment", "system", name="notification_type_enum"),
        nullable=False,
    )
    related_entity_type = Column(String(50))
    related_entity_id = Column(CHAR(36))
    is_read = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_notif_user", "police_user_id"),
        Index("idx_notif_unread", "police_user_id", "is_read"),
    )

    # Relationships
    police_user = relationship("PoliceUser", back_populates="notifications")
