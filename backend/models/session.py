# =====================================================================
# GREEN-FINANCE — SESSION.PY (MODEL)
# Purpose: Defines the SQLAlchemy ORM schema for the "auth_sessions" table.
#          Enables immediate session revocation on logout, privilege change,
#          or administrative suspension.
# =====================================================================

from backend.db.base import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func
import uuid


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_jti = Column(String(64), unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(100), nullable=True)
