"""Database setup: engine, session factory, and `get_db` dependency.

Creates the SQLAlchemy `engine` and `SessionLocal` factory used
throughout the application. Export `get_db()` as a small dependency
helper that yields a session and ensures it is closed.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.setting import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

# Session factory to be used by request handlers / services
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_db():
    """Yield a database session and close it when finished.

    Intended for use as a FastAPI dependency: `Depends(get_db)`.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
