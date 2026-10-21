# =====================================================================
# GREEN-FINANCE — DATABASE.PY (DATABASE INITIALIZATION)
# Purpose: Builds SQL database tables and initializes schema metadata.
# =====================================================================

from backend.db.base import Base
from backend.db.connection import engine
from backend.middleware.logger import logger


def init_db() -> None:
    """Creates all tables from models and seeds initial demonstration data."""
    # Ensure all models are imported so their tables are in Base.metadata
    from backend.models import (
        user, account, transaction, ledger_entry, 
        carbon_record, carbon_credit, credit, accuracy, 
        sustainability, session, rbac, idempotency
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema tables successfully verified/created.")

    # Auto-migrate any missing columns on existing SQLite databases
    from sqlalchemy import text
    with engine.connect() as conn:
        for col, col_type in [
            ("service", "VARCHAR(64) DEFAULT 'payment-service'"),
            ("transaction_type", "VARCHAR(64) DEFAULT 'TRANSFER'"),
            ("energy_joules", "FLOAT DEFAULT 0.69"),
            ("carbon_grams", "FLOAT DEFAULT 0.00014"),
            ("fidelity_percent", "FLOAT DEFAULT 96.0"),
            ("prev_audit_hash", "VARCHAR(64) DEFAULT '0000000000000000000000000000000000000000000000000000000000000000'"),
            ("audit_hash", "VARCHAR(64) DEFAULT 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE transactions ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass

        for col, col_type in [
            ("status", "VARCHAR(20) DEFAULT 'ACTIVE'"),
            ("is_boss_admin", "BOOLEAN DEFAULT 0"),
            ("failed_login_attempts", "INTEGER DEFAULT 0"),
            ("locked_until", "DATETIME"),
            ("mfa_secret", "VARCHAR(64)"),
            ("mfa_enabled", "BOOLEAN DEFAULT 0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass

    # Automatically seed the database on startup
    from backend.db.session import SessionLocal
    from backend.db.seed import seed_database
    from backend.services.rbac_service import init_rbac_system
    db = SessionLocal()
    try:
        init_rbac_system(db)
        seed_database(db)
    except Exception as e:
        logger.error(f"Database seeding notice: {str(e)}")
    finally:
        db.close()