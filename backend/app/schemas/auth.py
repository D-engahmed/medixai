"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from app.models.user import UserRole

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)

class UserCreate(UserBase):
    """User registration schema"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str
    requires_2fa: Optional[bool] = False

class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: str
    exp: int
    iat: int
    iss: str
    aud: str
    two_fa_verified: Optional[bool] = False

class TwoFactorSetup(BaseModel):
    """2FA setup response schema"""
    provisioning_uri: str
    message: str

class TwoFactorVerify(BaseModel):
    """2FA verification schema"""
    token: str = Field(..., min_length=6, max_length=6)

class PasswordReset(BaseModel):
    """Password reset schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserResponse(UserBase):
    """User response schema"""
    id: str
    role: UserRole
    is_active: bool
    email_verified: bool
    two_fa_enabled: bool
    preferences: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True
