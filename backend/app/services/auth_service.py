"""
Authentication Service

This module handles all authentication-related functionality including:
- User registration and login
- JWT token generation and validation
- Two-factor authentication
- Session management
- Password reset and email verification
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import jwt
import pyotp
import argon2
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from uuid import UUID

from app.models.user import User, UserSession
from app.schemas.auth import UserCreate, UserLogin
from app.core.security import (
    verify_password,
    get_password_hash,
    create_jwt_token,
    verify_jwt_token
)
from app.config.settings import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)
ph = argon2.PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM
)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user exists
        existing_user = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role
        )
        
        # Generate email verification token
        user.email_verification_token = create_jwt_token(
            {"email": user.email},
            expires_delta=timedelta(hours=24)
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Send verification email (implement in notification service)
        # await self.notification_service.send_verification_email(user)
        
        return user
    
    async def login_user(
        self,
        login_data: UserLogin,
        ip_address: str,
        user_agent: str
    ) -> Tuple[User, str, str]:
        """Authenticate user and create session"""
        user = await self.get_user_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.password_hash):
            await self._handle_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account locked until {user.account_locked_until}"
            )
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        
        # Generate tokens
        access_token = create_jwt_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_jwt_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            device_info={},  # Add device detection
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        self.db.add(session)
        await self.db.commit()
        
        return user, access_token, refresh_token
    
    async def verify_2fa(self, user_id: UUID, token: str) -> bool:
        """Verify 2FA token"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.two_fa_secret:
            return False
        
        totp = pyotp.TOTP(user.two_fa_secret)
        return totp.verify(token)
    
    async def setup_2fa(self, user_id: UUID) -> str:
        """Setup 2FA for user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate secret
        secret = pyotp.random_base32()
        user.two_fa_secret = secret
        user.two_fa_enabled = True
        
        await self.db.commit()
        
        # Return provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.APP_NAME
        )
    
    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """Generate new access token using refresh token"""
        try:
            payload = verify_jwt_token(refresh_token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Verify session exists and is active
            session = await self.db.execute(
                select(UserSession)
                .where(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True
                )
            )
            session = session.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            
            # Generate new tokens
            new_access_token = create_jwt_token(
                data={"sub": user_id},
                expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            new_refresh_token = create_jwt_token(
                data={"sub": user_id},
                expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
            )
            
            # Update session
            session.session_token = new_access_token
            session.refresh_token = new_refresh_token
            session.last_activity = datetime.utcnow()
            await self.db.commit()
            
            return new_access_token, new_refresh_token
            
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def logout_user(self, user_id: UUID, session_token: str) -> None:
        """Logout user and invalidate session"""
        session = await self.db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.session_token == session_token
            )
        )
        session = session.scalar_one_or_none()
        if session:
            session.is_active = False
            await self.db.commit()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _handle_failed_login(self, user: Optional[User]) -> None:
        """Handle failed login attempt"""
        if not user:
            return
        
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.account_locked_until = datetime.utcnow() + timedelta(
                seconds=settings.LOGIN_ATTEMPT_WINDOW
            )
        
        await self.db.commit()
