import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base  
from unittest.mock import MagicMock
from app.config.security import security_service

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_security():
    security_service.hash_password = MagicMock(return_value="hashed_pw")
    security_service.verify_password = MagicMock(return_value=True)
    security_service.create_access_token = MagicMock(return_value="access_token_jwt")
    security_service.create_refresh_token = MagicMock(return_value="refresh_token_jwt")
    security_service.decode_token = MagicMock(return_value={
        "sub": "test@example.com",
        "user_id": 1,
        "role_id": 1,
        "type": "refresh"
    })
