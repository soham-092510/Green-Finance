# =====================================================================
# ECO MONITOR / GREEN-FINANCE — SEED.PY (COMPREHENSIVE SEEDER)
# Purpose: Seeds database with:
#          - Scope 1, 2, 3 emission factors & CEA India Grid factors
#          - Demo users (Soham, Demo User, Alice, Bob) & Bank Accounts
#          - Recipient Institutional Banks (MAH, IDFC, SBI)
#          - Sustainability Goals, Alerts & Explainable Recommendations
#          - Realistic preloaded audited banking transactions
#          - Baseline Profiles and Validation Runs
# =====================================================================

import hashlib
import uuid
from datetime import datetime, timedelta
import random

from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.db.session import SessionLocal
from backend.middleware.logger import logger
from backend.models.account import Account
from backend.models.accuracy import BaselineProfile, ValidationRun, TransactionTelemetry
from backend.models.carbon_credit import CarbonCredit
from backend.models.carbon_record import EmissionFactor, CarbonRecord
from backend.models.credit import CreditRetirement
from backend.models.ledger_entry import LedgerEntry
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.models.sustainability import (
    CarbonFactor, SustainabilityGoal, Alert, Recommendation, CarbonMeasurement
)


def seed_database(db: Session) -> None:
    logger.info("Initializing comprehensive database seeding...")

    # ------------------ 1. Seed Generic Activity Factors ------------------
    activity_factors = [
        {"activity_type": "transport", "factor": 0.24, "unit": "km"},
        {"activity_type": "energy", "factor": 0.38, "unit": "kWh"},
        {"activity_type": "manufacturing", "factor": 1.50, "unit": "USD"},
        {"activity_type": "agriculture", "factor": 2.10, "unit": "kg"},
        {"activity_type": "other", "factor": 0.50, "unit": "unit"}
    ]
    for f in activity_factors:
        existing = db.query(EmissionFactor).filter(
            EmissionFactor.activity_type == f["activity_type"]
        ).first()
        if not existing:
            db.add(EmissionFactor(**f))

    # ------------------ 2. Seed CEA India Grid Carbon Factors ------------------
    grid_factors = [
        {
            "region": "India (National Grid)",
            "year": 2024,
            "factor_gco2_per_kwh": 713.0,
            "unit": "gCO2/kWh",
            "source": "Central Electricity Authority (CEA) CO2 Baseline Database v20.0 (2024)",
            "effective_date": "2024-01-01",
            "is_active": True
        },
        {
            "region": "India (National Grid)",
            "year": 2023,
            "factor_gco2_per_kwh": 727.0,
            "unit": "gCO2/kWh",
            "source": "Central Electricity Authority (CEA) CO2 Baseline Database v19.0 (2023)",
            "effective_date": "2023-01-01",
            "is_active": False
        },
        {
            "region": "India (National Grid)",
            "year": 2022,
            "factor_gco2_per_kwh": 827.0,
            "unit": "gCO2/kWh",
            "source": "Central Electricity Authority (CEA) CO2 Baseline Database v18.0 (2022)",
            "effective_date": "2022-01-01",
            "is_active": False
        },
        {
            "region": "Maharashtra State Grid",
            "year": 2024,
            "factor_gco2_per_kwh": 742.0,
            "unit": "gCO2/kWh",
            "source": "MERC State Electricity Analysis / CEA Regional Breakdown (2024)",
            "effective_date": "2024-01-01",
            "is_active": False
        },
        {
            "region": "Corporate Renewable PPA",
            "year": 2024,
            "factor_gco2_per_kwh": 120.0,
            "unit": "gCO2/kWh",
            "source": "Corporate Solar-Wind Hybrid PPA Verified Guarantee of Origin",
            "effective_date": "2024-01-01",
            "is_active": False
        }
    ]
    for gf in grid_factors:
        existing = db.query(CarbonFactor).filter(
            CarbonFactor.region == gf["region"],
            CarbonFactor.year == gf["year"]
        ).first()
        if not existing:
            db.add(CarbonFactor(**gf))
            logger.info(f"Seeded Grid Carbon Factor: {gf['region']} ({gf['year']}) -> {gf['factor_gco2_per_kwh']} g/kWh")

    # ------------------ 3. Seed Banking & Investor Users ------------------
    users_to_seed = [
        {
            "username": "soham_gaikwad",
            "name": "Soham Gaikwad",
            "email": "soham@greenfinance.dev",
            "bank_id": "HDFC9999",
            "balance": 50000.0,
            "role": "ADMIN",
            "password": "password123"
        },
        {
            "username": "demo_user",
            "name": "Demo User",
            "email": "demo@greenfinance.dev",
            "bank_id": "DEMO0001",
            "balance": 25000.0,
            "role": "INVESTOR",
            "password": "password123"
        },
        {
            "username": "alice_smith",
            "name": "Alice Smith",
            "email": "alice@greenfinance.dev",
            "bank_id": "ALICE101",
            "balance": 30000.0,
            "role": "USER",
            "password": "password123"
        },
        {
            "username": "bob_kumar",
            "name": "Bob Kumar",
            "email": "bob@greenfinance.dev",
            "bank_id": "BOB202",
            "balance": 15000.0,
            "role": "USER",
            "password": "password123"
        }
    ]

    user_map = {}
    for u in users_to_seed:
        db_user = db.query(User).filter(User.username == u["username"]).first()
        if not db_user:
            db_user = User(
                name=u["name"],
                username=u["username"],
                email=u["email"],
                bank_id=u["bank_id"],
                hashed_password=hash_password(u["password"]),
                role=u["role"]
            )
            db.add(db_user)
            db.flush()

            # Assign wallet
            wallet = Account(
                user_id=db_user.id,
                name="cash_wallet",
                type="asset",
                balance=u["balance"]
            )
            db.add(wallet)
            # Assign carbon accounts
            db.add(Account(user_id=db_user.id, name="carbon_asset", type="asset", balance=250.0))
            db.add(Account(user_id=db_user.id, name="carbon_liability", type="liability", balance=50.0))
            logger.info(f"Seeded User: {u['username']} ({u['bank_id']}) with ₹{u['balance']:,}")
        user_map[u["bank_id"]] = db_user

    # ------------------ 4. Seed Recipient Institutional Banks ------------------
    banks_to_seed = [
        {"username": "bank_mah123", "name": "Bank of Maharashtra", "bank_id": "MAH123", "balance": 100000.0},
        {"username": "bank_idf892", "name": "IDFC First Bank", "bank_id": "IDF892", "balance": 150000.0},
        {"username": "bank_sbin456", "name": "State Bank of India", "bank_id": "SBIN456", "balance": 250000.0},
    ]
    for b in banks_to_seed:
        existing_bank = db.query(User).filter(User.bank_id == b["bank_id"]).first()
        if not existing_bank:
            u_bank = User(
                name=b["name"],
                username=b["username"],
                email=f"{b['bank_id'].lower()}@banknet.in",
                bank_id=b["bank_id"],
                hashed_password=hash_password("bankpassword123"),
                role="BANK"
            )
            db.add(u_bank)
            db.flush()
            db.add(Account(user_id=u_bank.id, name="cash_wallet", type="asset", balance=b["balance"]))
            logger.info(f"Seeded Bank: {b['name']} ({b['bank_id']}) with ₹{b['balance']:,}")

    # ------------------ 5. Seed System Registry Account ------------------
    system_issuance = db.query(Account).filter(Account.id == "system_issuance_id").first()
    if not system_issuance:
        system_issuance = Account(
            id="system_issuance_id",
            user_id="system",
            name="issuance",
            type="liability",
            balance=10000000.0
        )
        db.add(system_issuance)
        db.flush()

    # ------------------ 6. Seed Sustainability Goals ------------------
    goals_to_seed = [
        {
            "title": "Computational Carbon per Transaction",
            "goal_type": "co2_per_tx",
            "target_value": 0.20,
            "current_value": 0.16,
            "unit": "gCO2/tx",
            "period": "Continuous SLA",
            "status": "ACHIEVED"
        },
        {
            "title": "Monthly Scope 2 Processing Emissions",
            "goal_type": "monthly_co2",
            "target_value": 50.0,
            "current_value": 32.4,
            "unit": "kg CO2",
            "period": "October 2026",
            "status": "ON_TRACK"
        },
        {
            "title": "Payment Workload Energy Efficiency",
            "goal_type": "energy_per_tx",
            "target_value": 0.80,
            "current_value": 0.69,
            "unit": "J/tx",
            "period": "Continuous SLA",
            "status": "ACHIEVED"
        }
    ]
    for g in goals_to_seed:
        existing = db.query(SustainabilityGoal).filter(SustainabilityGoal.goal_type == g["goal_type"]).first()
        if not existing:
            db.add(SustainabilityGoal(**g))
            logger.info(f"Seeded Sustainability Goal: {g['title']}")

    # ------------------ 7. Seed Dynamic Alerts ------------------
    alerts_to_seed = [
        {
            "alert_type": "SERVICE_EFFICIENCY_DRIFT",
            "severity": "WARNING",
            "service": "payment-service",
            "value": 0.82,
            "threshold": 0.75,
            "unit": "J/tx",
            "status": "ACTIVE",
            "message": "Payment Service energy intensity +17.1% above calibrated baseline.",
            "details": "Triggered by multi-window persistence (N=4 consecutive windows > 0.75 J/tx). Baseline idle = 18.7W."
        },
        {
            "alert_type": "WORKLOAD_SURGE_RESOLVED",
            "severity": "INFO",
            "service": "fraud-service",
            "value": 0.44,
            "threshold": 0.50,
            "unit": "J/tx",
            "status": "RESOLVED",
            "message": "Fraud Service cryptographic evaluation surge stabilized below threshold.",
            "details": "Workload normalized after temporary concurrent UPI batch settlement."
        }
    ]
    for a in alerts_to_seed:
        existing = db.query(Alert).filter(Alert.alert_type == a["alert_type"]).first()
        if not existing:
            db.add(Alert(**a))

    # ------------------ 8. Seed Recommendations ------------------
    recs_to_seed = [
        {
            "issue": "Payment Service higher energy share vs Auth Service",
            "detected_value": "0.45 J / tx (65% of workload)",
            "baseline_threshold": "0.35 J / tx (50% target)",
            "recommendation": "Profile payment-service JSON serialization and batch double-entry database flushes to reduce CPU cycles.",
            "expected_benefit": "~14% reduction in computational energy per transaction",
            "service": "payment-service",
            "status": "OPEN"
        },
        {
            "issue": "High peak-hour grid carbon intensity",
            "detected_value": "713 gCO2/kWh (India National Grid)",
            "baseline_threshold": "600 gCO2/kWh target",
            "recommendation": "Schedule non-urgent batch reconciliation and payroll transfers during lower-carbon off-peak windows.",
            "expected_benefit": "~8% to 12% reduction in Scope 2 operational carbon footprint",
            "service": "ledger-service",
            "status": "OPEN"
        },
        {
            "issue": "Redundant JWT verification queries on auth-service",
            "detected_value": "42ms latency, 0.12 J/tx",
            "baseline_threshold": "25ms latency, 0.08 J/tx",
            "recommendation": "Implement fast in-memory LRU token signature caching for active customer sessions.",
            "expected_benefit": "~35% latency improvement and ~4% energy savings",
            "service": "auth-service",
            "status": "IMPLEMENTED"
        }
    ]
    for r in recs_to_seed:
        existing = db.query(Recommendation).filter(Recommendation.issue == r["issue"]).first()
        if not existing:
            db.add(Recommendation(**r))

    # ------------------ 9. Seed Accuracy Baseline & Validation Run ------------------
    base_profile = db.query(BaselineProfile).filter(BaselineProfile.id == "BASE-DEFAULT-001").first()
    if not base_profile:
        base_profile = BaselineProfile(
            id="BASE-DEFAULT-001",
            machine_id="node-local-01",
            duration_seconds=300,
            sample_count=300,
            idle_power_mean=18.7,
            idle_power_std=0.8,
            idle_cv=4.28,
            status="LOCKED",
            cpu_model="Intel/AMD Multi-Core Architecture",
            cpu_freq_mhz=2400.0,
            env_metadata='{"os": "Windows/Linux Kernel", "kepler_version": "v0.7.2", "prometheus": "v2.45.0"}'
        )
        db.add(base_profile)
        db.flush()

        val_run = ValidationRun(
            id="VAL-RUN-001",
            baseline_id="BASE-DEFAULT-001",
            tx_count=500,
            host_energy_joules=1000.0,
            container_energy_joules=800.0,
            idle_energy_joules=150.0,
            accounted_energy_joules=950.0,
            residual_joules=50.0,
            residual_percent=5.0,
            fidelity_percent=95.0,
            tx_energy_mean_joules=0.70,
            tx_energy_std_joules=0.021,
            tx_cv_percent=3.0,
            drift_percent=2.1,
            status="PASS"
        )
        db.add(val_run)

    # ------------------ 10. Seed Realistic Audited Transactions ------------------
    sample_txns = [
        {
            "id": "TXN-8F9201",
            "sender": "HDFC9999",
            "recipient": "MAH123",
            "amount": 5000.0,
            "type": "UPI_TRANSFER",
            "desc": "Inter-bank fund settlement: Vendor supply invoice",
            "energy_j": 0.684,
            "minutes_ago": 12
        },
        {
            "id": "TXN-8F9202",
            "sender": "HDFC9999",
            "recipient": "IDF892",
            "amount": 12500.0,
            "type": "IMPS",
            "desc": "Inter-bank fund settlement: Cloud server infrastructure",
            "energy_j": 0.712,
            "minutes_ago": 28
        },
        {
            "id": "TXN-8F9203",
            "sender": "ALICE101",
            "recipient": "SBIN456",
            "amount": 3200.0,
            "type": "UPI_TRANSFER",
            "desc": "Peer-to-peer mobile transfer",
            "energy_j": 0.655,
            "minutes_ago": 45
        },
        {
            "id": "TXN-8F9204",
            "sender": "BOB202",
            "recipient": "HDFC9999",
            "amount": 7800.0,
            "type": "NEFT",
            "desc": "Contract payment settlement",
            "energy_j": 0.745,
            "minutes_ago": 62
        },
        {
            "id": "TXN-8F9205",
            "sender": "DEMO0001",
            "recipient": "MAH123",
            "amount": 1500.0,
            "type": "UPI_TRANSFER",
            "desc": "Retail utility bill payment",
            "energy_j": 0.672,
            "minutes_ago": 90
        },
        {
            "id": "TXN-8F9206",
            "sender": "HDFC9999",
            "recipient": "SBIN456",
            "amount": 25000.0,
            "type": "RTGS",
            "desc": "Institutional treasury transfer",
            "energy_j": 0.795,
            "minutes_ago": 120
        }
    ]

    for st in sample_txns:
        existing = db.query(Transaction).filter(Transaction.id == st["id"]).first()
        if not existing:
            created_dt = datetime.now() - timedelta(minutes=st["minutes_ago"])
            carbon_grams = round((st["energy_j"] / 3600000.0) * 713.0, 6)
            audit_raw = f"{st['id']}:{st['sender']}:{st['recipient']}:{st['amount']}:{st['energy_j']}:{created_dt}"
            audit_hash = hashlib.sha256(audit_raw.encode("utf-8")).hexdigest()

            txn = Transaction(
                id=st["id"],
                description=st["desc"],
                sender_bank_id=st["sender"],
                recipient_bank_id=st["recipient"],
                amount=st["amount"],
                currency="INR",
                status="COMPLETED",
                service="payment-service",
                transaction_type=st["type"],
                energy_joules=st["energy_j"],
                carbon_grams=carbon_grams,
                fidelity_percent=96.2,
                audit_hash=audit_hash,
                created_at=created_dt
            )
            db.add(txn)

            telemetry = TransactionTelemetry(
                transaction_id=st["id"],
                duration_ms=round(random.uniform(95.0, 160.0), 1),
                auth_joules=round(st["energy_j"] * 0.15, 4),
                payment_joules=round(st["energy_j"] * 0.60, 4),
                ledger_joules=round(st["energy_j"] * 0.25, 4),
                total_joules=st["energy_j"],
                carbon_mg=round(carbon_grams * 1000.0, 3),
                uncertainty_pct=4.8
            )
            db.add(telemetry)

    db.commit()
    logger.info("Database seeding successfully completed with full demo data!")


if __name__ == "__main__":
    db_session = SessionLocal()
    try:
        seed_database(db_session)
    finally:
        db_session.close()
