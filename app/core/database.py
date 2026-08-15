from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Production-grade connection pool settings
_pool_kwargs = {}
if not settings.DATABASE_URL.startswith("sqlite"):
    _pool_kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,   # detect stale connections automatically
        "pool_recycle": 1800,    # recycle connections every 30 minutes
    }

engine = create_engine(settings.DATABASE_URL, **_pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
