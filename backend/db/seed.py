# =====================================================================
# ECO MONITOR — SEED.PY (SEEDER)
# Purpose: Seeds the database with default Scope 1, 2, 3 emission factors,
#          creates a demo user with pre-configured double-entry accounts,
#          and generates mock ledger transactions and carbon credits.
# =====================================================================

# Import Session from SQLAlchemy ORM
from sqlalchemy.orm import Session

# Import models
from backend.models.user import User
from backend.models.account import Account
from backend.models.carbon_record import EmissionFactor, CarbonRecord
from backend.models.carbon_credit import CarbonCredit
from backend.models.transaction import Transaction
from backend.models.ledger_entry import LedgerEntry
from backend.models.credit import CreditRetirement

# Import security hash function
from backend.core.security import hash_password

# Import DB session creator
from backend.db.session import SessionLocal

# Import logging
from backend.middleware.logger import logger

# Import datetime
from datetime import datetime, timedelta

# Import uuid
import uuid


def seed_database(db: Session) -> None:
    # Main seeder execution routine
    # WHY:
    # - Sets up default values for emission factor lookups
    # - Sets up a demo account preloaded with data so the UI has immediate, beautiful charts
    logger.info("Initializing database seeding...")

    # ------------------ 1. Seed Emission Factors ------------------
    # WHY:
    # - Standard conversion factors for carbon math (Scope 1, 2, 3)
    factors = [
        {"activity_type": "transport", "factor": 0.24, "unit": "km"},       # Scope 1 (Direct Fuel)
        {"activity_type": "energy", "factor": 0.38, "unit": "kWh"},         # Scope 2 (Indirect Electricity)
        {"activity_type": "manufacturing", "factor": 1.50, "unit": "USD"},  # Scope 3 (Supply Chain Spend)
        {"activity_type": "agriculture", "factor": 2.10, "unit": "kg"},     # Scope 3 (Food Supply)
        {"activity_type": "other", "factor": 0.50, "unit": "unit"}
    ]

    for f in factors:
        existing = db.query(EmissionFactor).filter(
            EmissionFactor.activity_type == f["activity_type"]
        ).first()
        if not existing:
            db.add(EmissionFactor(**f))
            logger.info(f"Seeded Emission Factor: {f['activity_type']}")
    db.commit()

    # ------------------ 2. Seed Demo User ------------------
    # WHY:
    # - Provides a ready-to-use profile to login with immediately (demo_user / password123)
    demo_username = "demo_user"
    user = db.query(User).filter(User.username == demo_username).first()
    if not user:
        user = User(
            name="Demo User",
            username=demo_username,
            email="demo@ecomonitor.dev",
            hashed_password=hash_password("password123"),
            role="INVESTOR"
        )
        db.add(user)
        db.flush()  # Assures user.id UUID is generated
        logger.info("Seeded Demo User: demo_user")
        
        # Create user accounts
        # WHY:
        # - Establish asset, liability and equity accounts for the demo user
        asset_account = Account(
            user_id=user.id,
            name="carbon_asset",
            type="asset",
            balance=500.0  # Pre-seed with some assets
        )
        liability_account = Account(
            user_id=user.id,
            name="carbon_liability",
            type="liability",
            balance=150.0  # Pre-seed with some liabilities
        )
        db.add(asset_account)
        db.add(liability_account)
        db.flush()
        
        # ------------------ 3. Seed System Account ------------------
        # WHY:
        # - Balancing system registry account to absorb credit issuance entries
        system_issuance = Account(
            id="system_issuance_id",
            user_id="system",
            name="issuance",
            type="liability",
            balance=10000000.0
        )
        db.add(system_issuance)
        db.flush()
        
        # ------------------ 4. Seed Carbon Record History ------------------
        # WHY:
        # - Populates the carbon tracker table with historic entries (Scope 1 and Scope 2)
        records = [
            {"activity_type": "energy", "amount": 100.0, "description": "Offices electrical billing", "created_at": datetime.utcnow() - timedelta(days=15)},
            {"activity_type": "transport", "amount": 50.0, "description": "Executive flights", "created_at": datetime.utcnow() - timedelta(days=5)}
        ]
        for r in records:
            # We seed direct carbon records
            # Note: 100 kWh * 0.38 factor = 38 kg, 50 km * 0.24 factor = 12 kg. Total emissions = 50 kg CO2.
            # Let's write the amount calculated or raw metric.
            record_amount = r["amount"] * (0.38 if r["activity_type"] == "energy" else 0.24)
            db.add(CarbonRecord(
                user_id=user.id,
                activity_type=r["activity_type"],
                amount=record_amount,
                description=r["description"],
                created_at=r["created_at"]
            ))
            
        # ------------------ 5. Seed Carbon Credits ------------------
        # WHY:
        # - Pre-populates carbon credit listings (solar, wind) in active state
        c1 = CarbonCredit(
            user_id=user.id,
            credit_type="solar",
            amount=300.0,
            source="Gujarat Solar Clean Energy Project",
            vintage_year=2025,
            serial_number="GF-2025-SOL-A8B9C0D1",
            status="active"
        )
        c2 = CarbonCredit(
            user_id=user.id,
            credit_type="wind",
            amount=200.0,
            source="Tamil Nadu Wind Power Farm",
            vintage_year=2026,
            serial_number="GF-2026-WIN-E2F3G4H5",
            status="active"
        )
        db.add(c1)
        db.add(c2)
        db.flush()
        
        # ------------------ 6. Seed Double-Entry Ledger Transactions ------------------
        # WHY:
        # - Ensures the ledger journal is filled out with balanced entries representing
        #   minting, logging emissions, and buying offsets.
        
        # Transaction 1: Minting Credits
        # - Debit: User Asset Account (+ 500)
        # - Credit: System Issuance Account (- 500)
        t1 = Transaction(description="Initial Carbon Credit Issuance", created_at=datetime.utcnow() - timedelta(days=20))
        db.add(t1)
        db.flush()
        db.add(LedgerEntry(transaction_id=t1.id, account_id=asset_account.id, type="debit", amount=500.0, running_balance=500.0))
        db.add(LedgerEntry(transaction_id=t1.id, account_id=system_issuance.id, type="credit", amount=500.0, running_balance=9999500.0))
        
        # Transaction 2: Emissions logged (creates liability)
        # - Credit: User Liability Account (+ 150)
        # - Debit: Offset Equity / System Account (we represent this simply by updating running balances)
        t2 = Transaction(description="Logged Carbon Emissions (Energy & Transport)", created_at=datetime.utcnow() - timedelta(days=10))
        db.add(t2)
        db.flush()
        db.add(LedgerEntry(transaction_id=t2.id, account_id=liability_account.id, type="credit", amount=150.0, running_balance=150.0))
        # Balancing system entry
        db.add(LedgerEntry(transaction_id=t2.id, account_id=system_issuance.id, type="debit", amount=150.0, running_balance=9999650.0))
        
        logger.info("Preloaded ledger logs and carbon assets seeded.")
        
    # ------------------ 7. Seed Banking User (Soham Gaikwad - HDFC9999) ------------------
    soham = db.query(User).filter(User.username == "soham_gaikwad").first()
    if not soham:
        soham = User(
            name="Soham Gaikwad",
            username="soham_gaikwad",
            email="soham@greenfinance.dev",
            bank_id="HDFC9999",
            hashed_password=hash_password("password123"),
            role="ADMIN"
        )
        db.add(soham)
        db.flush()
        
        # Checking account with ₹50,000 balance
        db.add(Account(
            user_id=soham.id,
            name="cash_wallet",
            type="asset",
            balance=50000.0
        ))
        logger.info("Seeded primary user Soham Gaikwad (HDFC9999) with ₹50,000 cash balance.")

    # ------------------ 8. Seed Recipient Banks ------------------
    banks_to_seed = [
        {"username": "bank_mah123", "name": "Bank of Maharashtra", "bank_id": "MAH123", "balance": 10000.0},
        {"username": "bank_idf892", "name": "IDFC First Bank", "bank_id": "IDF892", "balance": 15000.0},
        {"username": "bank_sbin456", "name": "State Bank of India", "bank_id": "SBIN456", "balance": 25000.0},
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
            db.add(Account(
                user_id=u_bank.id,
                name="cash_wallet",
                type="asset",
                balance=b["balance"]
            ))
            logger.info(f"Seeded bank: {b['name']} ({b['bank_id']}) with ₹{b['balance']}")

    # ------------------ 9. Seed Accuracy Baseline & Validation Run ------------------
    from backend.models.accuracy import BaselineProfile, ValidationRun
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
        logger.info("Seeded default locked BaselineProfile and 95% Fidelity ValidationRun.")

    db.commit()
    logger.info("Database seeding successfully completed!")


if __name__ == "__main__":
    # Allow execution directly as a python script
    db_session = SessionLocal()
    try:
        seed_database(db_session)
    finally:
        db_session.close()
