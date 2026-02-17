"""audit_logs — Security & Accountability."""

from sqlalchemy import Column, BigInteger, Integer, String, CHAR, Boolean, TIMESTAMP, Enum, Index, text
from sqlalchemy.dialects.postgresql import JSON
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    actor_type = Column(Enum("system", "police_user", name="actor_type_enum"), nullable=False)
    actor_id = Column(Integer)
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(CHAR(36))
    action_details = Column(JSON)
    ip_address = Column(String(45))
    success = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_audit_actor", "actor_type", "actor_id"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_time", "created_at"),
    )
