import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "✅ User created"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    response = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "invalid-email", "password": "password123"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "short"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "my_access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
