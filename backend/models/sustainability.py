# =====================================================================
# GREEN-FINANCE / ECO-MONITOR — SUSTAINABILITY.PY (MODELS)
# Purpose: Defines SQLAlchemy ORM schemas for sustainability analytics:
#          - CarbonFactor: Grid emission factors (CEA India, etc.)
#          - SustainabilityGoal: Institutional ESG targets and progress
#          - Alert: Dynamic threshold alerts (Basel III / RBI aligned)
#          - Recommendation: Explainable rule-based optimization actions
#          - CarbonMeasurement: Workload-window energy and carbon allocation
# =====================================================================

from backend.db.base import Base
from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, Text
from sqlalchemy import func
import uuid


class CarbonFactor(Base):
    """
    Regional electricity grid carbon intensity factors (gCO2/kWh).
    References official governmental sources such as the Central Electricity Authority (CEA) of India.
    """
    __tablename__ = "carbon_factors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    region = Column(String(100), nullable=False, default="India (National Grid)")
    year = Column(Integer, nullable=False, default=2024)
    factor_gco2_per_kwh = Column(Float, nullable=False, default=713.0)
    unit = Column(String(20), nullable=False, default="gCO2/kWh")
    source = Column(String(255), nullable=False, default="Central Electricity Authority (CEA) CO2 Baseline Database v20.0 (2024)")
    effective_date = Column(String(20), nullable=False, default="2024-01-01")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())


class SustainabilityGoal(Base):
    """
    Institutional sustainability targets and progress tracking.
    """
    __tablename__ = "sustainability_goals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(150), nullable=False)
    goal_type = Column(String(50), nullable=False)  # 'co2_per_tx', 'monthly_co2', 'energy_per_tx'
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False, default=0.0)
    unit = Column(String(30), nullable=False)       # 'gCO2/tx', 'kg CO2', 'J/tx'
    period = Column(String(50), nullable=False, default="Monthly")
    status = Column(String(30), nullable=False, default="ON_TRACK")  # 'ACHIEVED', 'ON_TRACK', 'AT_RISK', 'BREACHED'
    created_at = Column(DateTime, nullable=False, default=func.now())


class Alert(Base):
    """
    Dynamic risk alerts triggered when emissions, energy, or drift exceed statistical baselines.
    """
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    alert_type = Column(String(80), nullable=False)  # 'CARBON_INTENSITY_SPIKE', 'ENERGY_WORKLOAD_SURGE', 'SERVICE_DRIFT'
    severity = Column(String(20), nullable=False, default="WARNING")  # 'CRITICAL', 'WARNING', 'INFO'
    service = Column(String(60), nullable=False, default="payment-service")
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False, default="J/tx")
    status = Column(String(20), nullable=False, default="ACTIVE")  # 'ACTIVE', 'RESOLVED', 'DISMISSED'
    message = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())


class Recommendation(Base):
    """
    Explainable, rule-based sustainability optimization actions.
    """
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    issue = Column(String(150), nullable=False)
    detected_value = Column(String(80), nullable=False)
    baseline_threshold = Column(String(80), nullable=False)
    recommendation = Column(Text, nullable=False)
    expected_benefit = Column(String(150), nullable=False)
    service = Column(String(60), nullable=False, default="payment-service")
    status = Column(String(20), nullable=False, default="OPEN")  # 'OPEN', 'IMPLEMENTED', 'DISMISSED'
    created_at = Column(DateTime, nullable=False, default=func.now())


class CarbonMeasurement(Base):
    """
    Time-window aggregated workload energy and carbon footprint calculations.
    """
    __tablename__ = "carbon_measurements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    measurement_window_start = Column(DateTime, nullable=False)
    measurement_window_end = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False, default=300)
    total_energy_kwh = Column(Float, nullable=False, default=0.0)
    total_energy_joules = Column(Float, nullable=False, default=0.0)
    transaction_count = Column(Integer, nullable=False, default=0)
    carbon_factor = Column(Float, nullable=False, default=713.0)
    estimated_co2_grams = Column(Float, nullable=False, default=0.0)
    estimated_co2_per_tx_grams = Column(Float, nullable=False, default=0.0)
    service = Column(String(60), nullable=False, default="payment-service")
    created_at = Column(DateTime, nullable=False, default=func.now())
