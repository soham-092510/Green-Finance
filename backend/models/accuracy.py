# =====================================================================
# ECO MONITOR / GREEN-FINANCE — ACCURACY.PY (MODEL)
# Purpose: Defines SQLAlchemy ORM models for the Accuracy & Attribution Engine:
#          1. BaselineProfile (measured idle/system energy profiles)
#          2. ValidationRun (comprehensive residual, fidelity, and CV test runs)
#          3. TransactionTelemetry (per-transaction energy and carbon records)
# =====================================================================

from backend.db.base import Base
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy import func
import uuid


class BaselineProfile(Base):
    """
    Stores empirical idle baseline calibration profiles recorded when the host
    runs WITHOUT transaction workloads.
    """
    __tablename__ = "baseline_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    machine_id = Column(String(50), nullable=False, default="node-local-01")
    timestamp = Column(DateTime, nullable=False, default=func.now())
    duration_seconds = Column(Integer, nullable=False, default=30)
    sample_count = Column(Integer, nullable=False, default=30)

    # Statistical metrics of idle power
    idle_power_mean = Column(Float, nullable=False, default=18.7)  # Watts
    idle_power_std = Column(Float, nullable=False, default=0.8)    # Watts
    idle_cv = Column(Float, nullable=False, default=4.28)          # %

    # Status: 'CALIBRATING', 'LOCKED', 'INVALIDATED'
    status = Column(String(20), nullable=False, default="LOCKED")

    # Environmental & hardware metadata
    cpu_model = Column(String(100), nullable=True, default="Intel/AMD Multi-Core Processor")
    cpu_freq_mhz = Column(Float, nullable=True, default=2400.0)
    env_metadata = Column(Text, nullable=True)  # JSON-encoded extra telemetry


class ValidationRun(Base):
    """
    Stores complete energy validation test runs, recording the host energy,
    container energy, idle baseline, residual loss, and attribution fidelity.
    """
    __tablename__ = "validation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    baseline_id = Column(String(36), ForeignKey("baseline_profiles.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    tx_count = Column(Integer, nullable=False, default=500)

    # Energy Accounting Breakdown (Joules)
    host_energy_joules = Column(Float, nullable=False, default=1000.0)
    container_energy_joules = Column(Float, nullable=False, default=800.0)
    idle_energy_joules = Column(Float, nullable=False, default=150.0)
    accounted_energy_joules = Column(Float, nullable=False, default=950.0)
    
    # Residual & Fidelity Calculations
    residual_joules = Column(Float, nullable=False, default=50.0)
    residual_percent = Column(Float, nullable=False, default=5.0)
    fidelity_percent = Column(Float, nullable=False, default=95.0)

    # Repeatability & Consistency Metrics
    tx_energy_mean_joules = Column(Float, nullable=False, default=0.70)
    tx_energy_std_joules = Column(Float, nullable=False, default=0.021)
    tx_cv_percent = Column(Float, nullable=False, default=3.0)

    # Drift Detection
    drift_percent = Column(Float, nullable=False, default=2.1)

    # Status & Certification
    status = Column(String(20), nullable=False, default="PASS")
    certified_by = Column(String(50), nullable=True, default="Green-Finance Accuracy Engine")


class TransactionTelemetry(Base):
    """
    Fine-grained energy and emission attribution attached to an individual transaction.
    """
    __tablename__ = "transaction_telemetry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    duration_ms = Column(Float, nullable=False, default=45.0)

    # Sub-service energy attribution (Joules)
    auth_joules = Column(Float, nullable=False, default=0.11)
    payment_joules = Column(Float, nullable=False, default=0.42)
    ledger_joules = Column(Float, nullable=False, default=0.16)
    total_joules = Column(Float, nullable=False, default=0.69)

    # Carbon and confidence
    carbon_mg = Column(Float, nullable=False, default=0.137)
    uncertainty_pct = Column(Float, nullable=False, default=5.0)
