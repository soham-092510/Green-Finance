# =====================================================================
# ECO MONITOR — TRANSACTION.PY (MODEL)
# Purpose: Defines the SQLAlchemy ORM schema for the "transactions" table.
#          A Transaction is a header grouping multiple balanced LedgerEntries.
# =====================================================================

# Import Base from db setup
from backend.db.base import Base

# Import SQLAlchemy column types
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy import func
import uuid


class Transaction(Base):
    # Map class to database table name
    __tablename__ = "transactions"

    # UUID Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    # General description of the Transaction
    description = Column(String(255), nullable=False)

    # Banking Entities & Value
    sender_bank_id = Column(String(50), nullable=True, index=True)
    recipient_bank_id = Column(String(50), nullable=True, index=True)
    amount = Column(Float, nullable=True, default=0.0)
    currency = Column(String(10), nullable=False, default="INR")
    status = Column(String(20), nullable=False, default="COMPLETED")

    # Energy & Carbon Attribution (Kepler Telemetry)
    energy_joules = Column(Float, nullable=False, default=0.0)
    carbon_grams = Column(Float, nullable=False, default=0.0)
    fidelity_percent = Column(Float, nullable=False, default=95.0)

    # Cryptographic Audit Hash (SHA-256)
    audit_hash = Column(String(64), nullable=True)

    # Timestamp of the transaction
    created_at = Column(DateTime, nullable=False, default=func.now())
