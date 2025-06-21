"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timedelta

from app.core.security import rate_limit
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenPayload,
    TwoFactorSetup,
    TwoFactorVerify
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=Dict[str, Any])
@rate_limit(requests=5, window=300, key_prefix="register")
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Register a new user"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.register_user(user_data)
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "email": user.email,
            "requires_verification": True
        }
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
@rate_limit(requests=5, window=300, key_prefix="login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Login user and return tokens"""
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.login_user(
            UserLogin(
                email=form_data.username,
                password=form_data.password
            ),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        
        response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
        # If 2FA is enabled, mark token as requiring 2FA verification
        if user.two_fa_enabled:
            response["requires_2fa"] = True
        
        return response
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Get new access token using refresh token"""
    try:
        auth_service = AuthService(db)
        access_token, new_refresh_token = await auth_service.refresh_token(refresh_token)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Logout user and invalidate session"""
    try:
        auth_service = AuthService(db)
        await auth_service.logout_user(current_user.id, token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TwoFactorSetup:
    """Setup 2FA for user"""
    try:
        auth_service = AuthService(db)
        provisioning_uri = await auth_service.setup_2fa(current_user.id)
        return {
            "provisioning_uri": provisioning_uri,
            "message": "2FA setup successful"
        }
    except Exception as e:
        logger.error(f"2FA setup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA setup failed"
        )

@router.post("/2fa/verify", response_model=Token)
async def verify_2fa(
    verification_data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Verify 2FA token and complete login"""
    try:
        auth_service = AuthService(db)
        is_valid = await auth_service.verify_2fa(
            current_user.id,
            verification_data.token
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA token"
            )
        
        # Generate new tokens after 2FA verification
        access_token = create_jwt_token(
            data={"sub": str(current_user.id), "2fa_verified": True},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_jwt_token(
            data={"sub": str(current_user.id), "2fa_verified": True},
            expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"2FA verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA verification failed"
        )

@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Verify user's email address"""
    try:
        auth_service = AuthService(db)
        await auth_service.verify_email(token)
        return {"message": "Email verified successfully"}
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

@router.post("/reset-password/request")
@rate_limit(requests=3, window=300, key_prefix="reset_password")
async def request_password_reset(
    email: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Request password reset"""
    try:
        auth_service = AuthService(db)
        await auth_service.request_password_reset(email)
        return {"message": "Password reset instructions sent"}
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}")
        # Return success even if email doesn't exist (security)
        return {"message": "Password reset instructions sent"}

@router.post("/reset-password/{token}")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Reset password using reset token"""
    try:
        auth_service = AuthService(db)
        await auth_service.reset_password(token, new_password)
        return {"message": "Password reset successful"}
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
