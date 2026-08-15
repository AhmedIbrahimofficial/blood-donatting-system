"""
Shared pytest fixtures for the full test suite.

Auth is now Google OAuth (no OTP/Redis dependency).
Provides:
- An in-memory SQLite engine (StaticPool) visible to all test modules.
- DB dependency override applied once at import time.
"""
import os
# Disable rate limiting and Sentry during tests
os.environ["ENVIRONMENT"] = "test"
os.environ["SENTRY_DSN"] = ""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# ---------------------------------------------------------------------------
# Shared SQLite in-memory engine
# ---------------------------------------------------------------------------

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Apply DB override once at import time
# ---------------------------------------------------------------------------

app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Autouse fixture — reset DB before every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    """Drop and recreate all tables before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
