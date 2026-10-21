# =====================================================================
# GREEN-FINANCE — IDEMPOTENCY.PY (IDEMPOTENCY KEY MODEL)
# Purpose: Prevents duplicate banking transfers and double-spending across
#          network retries and client reconnections.
# =====================================================================

import uuid
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, func
from backend.db.base import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    response_code = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
