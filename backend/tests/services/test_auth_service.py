from app.services.auth_service import auth_service
from app.models.role import Role
from app.schemas.auth_schema import RegisterRequest
from fastapi import HTTPException
import pytest
from fastapi import HTTPException
from app.models.user import User
from starlette.responses import Response
from app.schemas.auth_schema import LoginRequest
from starlette.requests import Request

def test_register_success(db_session, mock_security):
    db_session.add(Role(id=1, type="user"))
    db_session.commit()

    req = RegisterRequest(
        firstname="Lokanatham",
        lastname="Latesh",
        email="lokanathamlatesh@gmail.com",
        password="123456",
        username="lokanathaml"
    )

    result = auth_service.register(req, db_session)

    assert result.email == "lokanathamlatesh@gmail.com"
    assert result.role == "user"

def test_register_email_exists(db_session, mock_security):
    db_session.add(Role(id=1, type="user"))
    db_session.add(User(email="lokanathamlatesh@gmail.com", username="old", password="pw", role_id=1))
    db_session.commit()

    req = RegisterRequest(
        firstname="Lokanatham", lastname="Latesh",
        email="lokanathamlatesh@gmail.com",
        password="123456",
        username="lokanathaml"
    )

    with pytest.raises(HTTPException) as e:
        auth_service.register(req, db_session)

    assert e.value.status_code == 400

def test_register_username_exists(db_session, mock_security):
    db_session.add(Role(id=1, type="user"))
    db_session.add(User(email="old@mail.com", username="Lokanatham", password="pw", role_id=1))
    db_session.commit()

    req = RegisterRequest(
        firstname="Lokanatham", lastname="Latesh",
        email="new@mail.com",
        password="123456",
        username="Lokanatham"
    )

    with pytest.raises(HTTPException):
        auth_service.register(req, db_session)

def test_register_missing_role(db_session, mock_security):
    req = RegisterRequest(
        firstname="Lokanatham", lastname="Latesh",
        email="lokanathamlatesh@gmail.com",
        password="123456",
        username="Lokanatham"
    )

    with pytest.raises(HTTPException) as e:
        auth_service.register(req, db_session)

    assert e.value.status_code == 500

def test_login_success(db_session, mock_security):
    role = Role(id=1, type="user")
    user = User(id=1, email="lokanathamlatesh@gmail.com", username="Lokanatham", name="Lokanatham Latesh",
                password="hashed_pw", role_id=1)

    db_session.add(role)
    db_session.add(user)
    db_session.commit()

    req = LoginRequest(email="lokanathamlatesh@gmail.com", password="123456")
    response = Response()

    result = auth_service.login(response, req, db_session)

    assert result.email == "lokanathamlatesh@gmail.com"
    assert "access_token" in response.headers.get("set-cookie")


def test_login_user_not_found(db_session, mock_security):
    req = LoginRequest(email="notfound@mail.com", password="123")
    response = Response()

    with pytest.raises(HTTPException):
        auth_service.login(response, req, db_session)

def test_refresh_success(db_session, mock_security):
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    request.cookies["refresh_token"] = "refresh_token_jwt"
    response = Response()
    result = auth_service.refresh(request, response)

    assert result["message"] == "Access token refreshed"

def test_refresh_missing_token():
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    response = Response()

    with pytest.raises(HTTPException):
        auth_service.refresh(request, response)

def test_logout():
    response = Response()
    result = auth_service.logout(response)

    assert result["message"] == "Logged out successfully"
    cookies = response.headers.getlist("set-cookie")
    assert any("access_token=" in c and "Max-Age=0" in c for c in cookies)
    assert any("refresh_token=" in c and "Max-Age=0" in c for c in cookies)

