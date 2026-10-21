# =====================================================================
# GREEN-FINANCE — CONNECTION.PY (DATABASE ENGINE INITIALIZATION)
# Purpose: Establishes dialect-specific database connections with:
#          - SQLite WAL mode, foreign keys enforcement, busy timeout (concurrency)
#          - PostgreSQL connection pooling with pre-ping validation
# =====================================================================

from sqlalchemy import create_engine, event
from backend.core.config import settings

if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )

    # Enforce SQLite foreign keys, WAL journal mode, and busy timeout on every connection
    @event.listens_for(engine, "connect")
    def configure_sqlite_connection(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.close()

else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
