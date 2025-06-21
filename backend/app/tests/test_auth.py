"""
Authentication tests
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Dict

from app.core.security import verify_password
from app.models.user import UserRole

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient, test_data: Dict):
    """Test user registration"""
    response = await client.post("/api/v1/auth/register", json=test_data["user"])
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == test_data["user"]["email"]
    assert data["role"] == UserRole.PATIENT
    assert "id" in data
    assert "password" not in data

async def test_register_doctor(client: AsyncClient, test_data: Dict):
    """Test doctor registration"""
    response = await client.post("/api/v1/auth/register", json=test_data["doctor"])
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == test_data["doctor"]["email"]
    assert data["role"] == UserRole.DOCTOR
    assert "license_number" in data
    assert "password" not in data

async def test_register_duplicate_email(client: AsyncClient, test_data: Dict):
    """Test registration with duplicate email"""
    # First registration
    await client.post("/api/v1/auth/register", json=test_data["user"])
    
    # Second registration with same email
    response = await client.post("/api/v1/auth/register", json=test_data["user"])
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already registered" in response.json()["detail"].lower()

async def test_login_user(client: AsyncClient, test_data: Dict):
    """Test user login"""
    # Register user first
    await client.post("/api/v1/auth/register", json=test_data["user"])
    
    # Login
    response = await client.post("/api/v1/auth/login", data={
        "username": test_data["user"]["email"],
        "password": test_data["user"]["password"]
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

async def test_login_wrong_password(client: AsyncClient, test_data: Dict):
    """Test login with wrong password"""
    # Register user first
    await client.post("/api/v1/auth/register", json=test_data["user"])
    
    # Login with wrong password
    response = await client.post("/api/v1/auth/login", data={
        "username": test_data["user"]["email"],
        "password": "wrong_password"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect email or password" in response.json()["detail"].lower()

async def test_refresh_token(client: AsyncClient, test_data: Dict):
    """Test token refresh"""
    # Register and login user first
    await client.post("/api/v1/auth/register", json=test_data["user"])
    login_response = await client.post("/api/v1/auth/login", data={
        "username": test_data["user"]["email"],
        "password": test_data["user"]["password"]
    })
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_refresh_invalid_token(client: AsyncClient):
    """Test refresh with invalid token"""
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid_token"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid refresh token" in response.json()["detail"].lower()

async def test_logout(client: AsyncClient, auth_headers: Dict):
    """Test user logout"""
    response = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

async def test_logout_invalid_token(client: AsyncClient):
    """Test logout with invalid token"""
    response = await client.post("/api/v1/auth/logout", headers={
        "Authorization": "Bearer invalid_token"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_verify_email(client: AsyncClient, test_data: Dict):
    """Test email verification"""
    # Register user first
    register_response = await client.post("/api/v1/auth/register", json=test_data["user"])
    user_id = register_response.json()["id"]
    
    # Get verification token
    response = await client.post(f"/api/v1/auth/verify-email/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["verification_token"]
    
    # Verify email
    response = await client.post("/api/v1/auth/verify-email", json={
        "token": token
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email_verified"] is True

async def test_verify_email_invalid_token(client: AsyncClient):
    """Test email verification with invalid token"""
    response = await client.post("/api/v1/auth/verify-email", json={
        "token": "invalid_token"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid verification token" in response.json()["detail"].lower()

async def test_reset_password_request(client: AsyncClient, test_data: Dict):
    """Test password reset request"""
    # Register user first
    await client.post("/api/v1/auth/register", json=test_data["user"])
    
    # Request password reset
    response = await client.post("/api/v1/auth/reset-password-request", json={
        "email": test_data["user"]["email"]
    })
    assert response.status_code == status.HTTP_200_OK

async def test_reset_password(client: AsyncClient, test_data: Dict):
    """Test password reset"""
    # Register user first
    await client.post("/api/v1/auth/register", json=test_data["user"])
    
    # Request password reset
    response = await client.post("/api/v1/auth/reset-password-request", json={
        "email": test_data["user"]["email"]
    })
    token = response.json()["reset_token"]
    
    # Reset password
    new_password = "NewTest@123"
    response = await client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": new_password
    })
    assert response.status_code == status.HTTP_200_OK
    
    # Try login with new password
    response = await client.post("/api/v1/auth/login", data={
        "username": test_data["user"]["email"],
        "password": new_password
    })
    assert response.status_code == status.HTTP_200_OK

async def test_change_password(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test password change"""
    new_password = "NewTest@123"
    response = await client.post("/api/v1/auth/change-password", 
        headers=auth_headers,
        json={
            "current_password": test_data["user"]["password"],
            "new_password": new_password
        }
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Try login with new password
    response = await client.post("/api/v1/auth/login", data={
        "username": test_data["user"]["email"],
        "password": new_password
    })
    assert response.status_code == status.HTTP_200_OK

async def test_setup_2fa(client: AsyncClient, doctor_auth_headers: Dict):
    """Test 2FA setup"""
    # Get 2FA setup data
    response = await client.post("/api/v1/auth/2fa/setup", headers=doctor_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "secret" in data
    assert "qr_code" in data
    
    # Verify 2FA setup
    response = await client.post("/api/v1/auth/2fa/verify", 
        headers=doctor_auth_headers,
        json={"code": "123456"}  # This is a mock code
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["two_fa_enabled"] is True

async def test_login_with_2fa(client: AsyncClient, test_data: Dict):
    """Test login with 2FA"""
    # Register doctor first
    await client.post("/api/v1/auth/register", json=test_data["doctor"])
    
    # First step login
    response = await client.post("/api/v1/auth/login", data={
        "username": test_data["doctor"]["email"],
        "password": test_data["doctor"]["password"]
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "two_fa_required" in data
    assert data["two_fa_required"] is True
    
    # Second step login with 2FA code
    response = await client.post("/api/v1/auth/2fa/login", json={
        "email": test_data["doctor"]["email"],
        "code": "123456"  # This is a mock code
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
