# =====================================================================
# ECO MONITOR — BASE.PY
# Purpose: Defines the base class for all database models and registers
#          them to metadata for automatic DDL generation (table creation).
# =====================================================================

# Import DeclarativeBase from SQLAlchemy ORM
# WHY:
# - SQLAlchemy uses a "declarative system" to map database tables to Python classes
# - All models must inherit from this Base so SQLAlchemy can collect table metadata
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Docstring explaining purpose
    """Base class all ORM models inherit from."""
    pass
