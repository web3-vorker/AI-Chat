import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from backend.auth.services.service import AuthService
from backend.auth.schemas.user import UserCredentials
from backend.auth.models.user import UserModel
from backend.auth.security.password import hash_password


@pytest.mark.asyncio
async def test_register_success(test_session):
    service = AuthService(test_session)
    credentials = UserCredentials(email="test@example.com", password="password123")
    
    result = await service.register(credentials)
    
    assert result["message"] == "✅ User created"


@pytest.mark.asyncio
async def test_register_duplicate_email(test_session):
    service = AuthService(test_session)
    credentials = UserCredentials(email="test@example.com", password="password123")
    
    await service.register(credentials)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.register(credentials)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User with this email already exists"


@pytest.mark.asyncio
async def test_login_success(test_session):
    service = AuthService(test_session)
    credentials = UserCredentials(email="test@example.com", password="password123")
    
    await service.register(credentials)
    
    response = MagicMock()
    result = await service.login(credentials, response)
    
    assert "access_token" in result
    assert len(result["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(test_session):
    service = AuthService(test_session)
    register_creds = UserCredentials(email="test@example.com", password="password123")
    await service.register(register_creds)
    
    login_creds = UserCredentials(email="test@example.com", password="wrongpassword")
    response = MagicMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await service.login(login_creds, response)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_nonexistent_user(test_session):
    service = AuthService(test_session)
    credentials = UserCredentials(email="nonexistent@example.com", password="password123")
    response = MagicMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await service.login(credentials, response)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_current_user_success(test_session):
    service = AuthService(test_session)
    
    user = UserModel(email="test@example.com", password_hash=hash_password("password123"))
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    token = MagicMock()
    token.sub = str(user.id)
    
    result = await service.get_current_user(token)
    
    assert result.email == "test@example.com"
    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_not_found(test_session):
    service = AuthService(test_session)
    
    token = MagicMock()
    token.sub = "999"
    
    with pytest.raises(HTTPException) as exc_info:
        await service.get_current_user(token)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"
