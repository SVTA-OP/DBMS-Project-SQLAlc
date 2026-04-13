"""
ICPS – Insurance Claim Processing System
database.py  –  Engine, Session, and Declarative Base
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Engine ────────────────────────────────────────────────────────────────────
# SQLite for local testing; swap the URL for PostgreSQL in production:
#   postgresql+psycopg2://user:pass@localhost:5432/icps_db
DATABASE_URL = "sqlite:///./icps.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,           # set True to see generated SQL
    future=True,
    # SQLite requires this pragma to honour FOREIGN KEY constraints
    connect_args={"check_same_thread": False},
)

# Enable FK enforcement for every new SQLite connection
from sqlalchemy import event as sa_event

@sa_event.listens_for(engine, "connect")
def _set_sqlite_fk_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Session factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


# ── Declarative base ───────────────────────────────────────────────────────────
Base = declarative_base()


# ── Convenience helper ─────────────────────────────────────────────────────────
def get_db():
    """Yield a session and close it when done (use as a context manager)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
