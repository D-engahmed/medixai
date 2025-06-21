"""
Tests for user management functionality
"""
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session
import json
from datetime import datetime, timedelta

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService
from app.utils.encryption import hash_password

@pytest.mark.asyncio
class TestUserManagement:
    """Test cases for user management"""

    async def test_create_user(self, app: FastAPI, client: AsyncClient, db: Session):
        """Test user creation"""
        user_data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "PATIENT",
            "phone": "+1234567890"
        }

        response = await client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert data["role"] == user_data["role"]
        assert "id" in data
        assert "password" not in data

        # Verify user in database
        db_user = db.query(User).filter(User.email == user_data["email"]).first()
        assert db_user is not None
        assert db_user.email == user_data["email"]
        assert db_user.role == UserRole.PATIENT

    async def test_create_user_duplicate_email(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session
    ):
        """Test creating user with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "PATIENT"
        }

        # Create first user
        response = await client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 201

        # Try to create second user with same email
        response = await client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()

    async def test_get_user(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test getting user details"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/v1/users/{test_user.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert "password" not in data

    async def test_update_user(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test updating user details"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+9876543210",
            "preferences": {"theme": "dark", "notifications": {"email": True, "sms": False}}
        }

        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["phone"] == update_data["phone"]
        assert data["preferences"] == update_data["preferences"]

        # Verify updates in database
        db.refresh(test_user)
        assert test_user.first_name == update_data["first_name"]
        assert test_user.last_name == update_data["last_name"]
        assert test_user.phone == update_data["phone"]
        assert test_user.preferences == update_data["preferences"]

    async def test_delete_user(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test user deletion"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(f"/api/v1/users/{test_user.id}", headers=headers)
        assert response.status_code == 200

        # Verify user is marked as inactive in database
        db.refresh(test_user)
        assert not test_user.is_active

    async def test_change_password(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test password change"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "oldpassword",
            "new_password": "NewStrongPass123!"
        }

        response = await client.post(
            f"/api/v1/users/{test_user.id}/change-password",
            headers=headers,
            json=password_data
        )
        assert response.status_code == 200

        # Verify password is updated in database
        db.refresh(test_user)
        assert test_user.verify_password(password_data["new_password"])

    async def test_update_preferences(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test updating user preferences"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        preferences = {
            "theme": "light",
            "language": "ar",
            "notifications": {
                "email": True,
                "sms": True,
                "push": False
            },
            "timezone": "UTC+3"
        }

        response = await client.put(
            f"/api/v1/users/{test_user.id}/preferences",
            headers=headers,
            json=preferences
        )
        assert response.status_code == 200
        data = response.json()

        assert data["preferences"] == preferences

        # Verify preferences are updated in database
        db.refresh(test_user)
        assert test_user.preferences == preferences

    async def test_get_user_activity(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test getting user activity history"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/users/{test_user.id}/activity",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "activities" in data
        assert isinstance(data["activities"], list)

    @pytest.mark.parametrize("invalid_data", [
        {"email": "invalid-email"},
        {"email": "test@example.com", "password": "short"},
        {"email": "test@example.com", "password": "StrongPass123!", "role": "INVALID"},
        {}
    ])
    async def test_create_user_validation(
        self,
        app: FastAPI,
        client: AsyncClient,
        invalid_data: dict
    ):
        """Test user creation with invalid data"""
        response = await client.post("/api/v1/users/", json=invalid_data)
        assert response.status_code in [400, 422]

    async def test_user_search(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        admin_user: User
    ):
        """Test searching users"""
        token = create_access_token(admin_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Create test users
        users = [
            User(
                email=f"user{i}@example.com",
                password_hash=hash_password("password"),
                first_name=f"User{i}",
                last_name="Test",
                role=UserRole.PATIENT
            )
            for i in range(5)
        ]
        for user in users:
            db.add(user)
        db.commit()

        # Test search by email
        response = await client.get(
            "/api/v1/users/search?email=user",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 5

        # Test search by name
        response = await client.get(
            "/api/v1/users/search?name=User1",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1

        # Test pagination
        response = await client.get(
            "/api/v1/users/search?limit=2&offset=0",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2

    async def test_user_sessions(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test user session management"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Get active sessions
        response = await client.get(
            f"/api/v1/users/{test_user.id}/sessions",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data

        # Terminate specific session
        if data["sessions"]:
            session_id = data["sessions"][0]["id"]
            response = await client.delete(
                f"/api/v1/users/{test_user.id}/sessions/{session_id}",
                headers=headers
            )
            assert response.status_code == 200

        # Terminate all sessions
        response = await client.delete(
            f"/api/v1/users/{test_user.id}/sessions",
            headers=headers
        )
        assert response.status_code == 200

    async def test_user_notifications(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test user notification settings"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        notification_settings = {
            "email": True,
            "sms": False,
            "push": True,
            "types": {
                "appointment_reminder": True,
                "prescription_refill": True,
                "chat_message": False
            }
        }

        response = await client.put(
            f"/api/v1/users/{test_user.id}/notifications",
            headers=headers,
            json=notification_settings
        )
        assert response.status_code == 200
        data = response.json()

        assert data["preferences"]["notifications"] == notification_settings

        # Verify settings are updated in database
        db.refresh(test_user)
        assert test_user.preferences.get("notifications") == notification_settings

    @pytest.mark.parametrize("role", [UserRole.PATIENT, UserRole.DOCTOR])
    async def test_create_user_with_role(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        role: UserRole
    ):
        """Test creating users with different roles"""
        user_data = {
            "email": f"{role.lower()}@example.com",
            "password": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": role.value
        }

        if role == UserRole.DOCTOR:
            user_data.update({
                "license_number": "MD123456",
                "specialization": "General Medicine",
                "years_experience": 5
            })

        response = await client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 201
        data = response.json()

        assert data["role"] == role.value
        if role == UserRole.DOCTOR:
            assert "doctor" in data
            assert data["doctor"]["license_number"] == user_data["license_number"]

    async def test_user_profile_image(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Session,
        test_user: User
    ):
        """Test user profile image upload and update"""
        token = create_access_token(test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Create test image file
        files = {
            "file": ("test.jpg", b"test image content", "image/jpeg")
        }

        response = await client.post(
            f"/api/v1/users/{test_user.id}/profile-image",
            headers=headers,
            files=files
        )
        assert response.status_code == 200
        data = response.json()

        assert "image_url" in data
        assert data["image_url"].endswith(".jpg")

        # Verify image URL is updated in database
        db.refresh(test_user)
        assert test_user.profile_image_url == data["image_url"]

        # Delete profile image
        response = await client.delete(
            f"/api/v1/users/{test_user.id}/profile-image",
            headers=headers
        )
        assert response.status_code == 200

        # Verify image URL is removed from database
        db.refresh(test_user)
        assert test_user.profile_image_url is None
