"""police_users — Police Accounts & Roles."""

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Enum, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from app.core.database import Base


class PoliceUser(Base):
    __tablename__ = "police_users"

    police_user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(150), nullable=False)
    middle_name = Column(String(150))
    last_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    badge_number = Column(String(50), unique=True)
    role = Column(Enum("admin", "supervisor", "officer", name="police_role_enum"), nullable=False)
    assigned_location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))
    last_login_at = Column(TIMESTAMP)

    __table_args__ = (
        Index("idx_police_email", "email"),
    )

    # Relationships
    assigned_location = relationship("Location", back_populates="assigned_officers")
    reviews = relationship("PoliceReview", back_populates="police_user")
    assignments = relationship("ReportAssignment", back_populates="police_user")
    notifications = relationship("Notification", back_populates="police_user")
