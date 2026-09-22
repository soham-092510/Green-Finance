# Import Base (the parent class of all ORM models)
# WHY:
# - Base contains metadata (all registered tables/models)
# - SQLAlchemy uses this to know which tables need to be created
from backend.db.base import Base


# Import the database engine (connection manager)
# WHY:
# - Engine is required to actually connect and execute operations on the database
# - Without engine, we cannot create tables
from backend.db.connection import engine


# Function to initialize the database
# WHY:
# - Encapsulates table creation logic in one place
# - Can be called when app starts (especially in development)
def init_db() -> None:

    # Docstring explaining purpose
    # WHY:
    # - Helps developers understand when and why to use this function
    # - Important note: only for development, NOT production
    """Creates all tables from models. Call once on startup (dev only — use Alembic in prod)."""

    # Ensure all models are imported so their tables are in Base.metadata
    from backend.models import user, account, transaction, ledger_entry, carbon_record, carbon_credit, credit, accuracy

    # Create all tables defined in models
    # WHY:
    # - Base.metadata contains all model definitions (User, Transaction, etc.)
    # - create_all() scans them and creates missing tables in the DB
    # - bind=engine tells SQLAlchemy which database to use
    Base.metadata.create_all(bind=engine)

    # Automatically seed the database on startup
    # WHY:
    # - Ensures default emission factors and demo portfolios are preloaded for immediate visualization
    from backend.db.session import SessionLocal
    from backend.db.seed import seed_database
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()