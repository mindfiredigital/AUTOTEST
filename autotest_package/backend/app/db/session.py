import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

DATABASE_URL = os.getenv("DATABASE_URL")  # mysql+pymysql://root:...@autotest_mysql:3306/AutoTestDB

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
