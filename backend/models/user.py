# =====================================================================
# GREEN-FINANCE — USER.PY (MODEL)
# Purpose: Defines the SQLAlchemy ORM schema for the "users" table.
#          Includes RBAC role, account status, security flags, and audit timestamps.
# =====================================================================

from backend.db.base import Base
from sqlalchemy import Column, String, DateTime, Boolean, Integer, func
import uuid


class User(Base):
    __tablename__ = "users"

    # UUID Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    # Identifiers
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    bank_id = Column(String(50), unique=True, nullable=True, index=True)

    # Role & Security Invariants
    role = Column(String(30), nullable=False, default="CUSTOMER")
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE, SUSPENDED, DISABLED
    is_boss_admin = Column(Boolean, nullable=False, default=False)

    # Brute Force Protection & Lockout
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)

    # MFA Configuration
    mfa_secret = Column(String(64), nullable=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
