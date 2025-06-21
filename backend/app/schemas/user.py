"""
User Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, constr, validator, Field
from uuid import UUID

from app.models.user import UserRole, Gender

class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    first_name: constr(min_length=1, max_length=100)
    last_name: constr(min_length=1, max_length=100)
    role: UserRole

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: constr(min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('كلمات المرور غير متطابقة')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    remember_me: bool = False

class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    is_active: bool
    email_verified: bool
    two_fa_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    class Config:
        orm_mode = True

class PatientBase(BaseModel):
    """Base schema for patient data"""
    date_of_birth: Optional[date]
    gender: Optional[Gender]
    phone: Optional[constr(regex=r'^\+?[1-9]\d{1,14}$')]
    address: Optional[Dict[str, str]]
    medical_history: Optional[Dict[str, Any]]
    allergies: Optional[List[str]]
    current_medications: Optional[List[str]]
    emergency_contact: Optional[Dict[str, str]]
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    preferred_language: str = "ar"
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "email": True,
        "sms": True,
        "push": True
    })

class PatientCreate(PatientBase):
    """Schema for creating a new patient"""
    user: UserCreate

class PatientUpdate(PatientBase):
    """Schema for updating patient data"""
    pass

class PatientResponse(PatientBase):
    """Schema for patient response"""
    id: UUID
    user: UserResponse
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True

class DoctorBase(BaseModel):
    """Base schema for doctor data"""
    license_number: constr(min_length=5, max_length=50)
    specialization: str
    years_experience: int = Field(ge=0)
    consultation_fee: Decimal = Field(ge=0)
    phone: constr(regex=r'^\+?[1-9]\d{1,14}$')
    address: Dict[str, str]
    bio: Optional[str]
    qualifications: List[Dict[str, str]]
    languages_spoken: List[str] = Field(default_factory=lambda: ["ar", "en"])
    availability_hours: Dict[str, List[Dict[str, str]]]
    timezone: str = "Asia/Riyadh"
    accepts_new_patients: bool = True
    online_consultation_enabled: bool = True

class DoctorCreate(DoctorBase):
    """Schema for creating a new doctor"""
    user: UserCreate

class DoctorUpdate(DoctorBase):
    """Schema for updating doctor data"""
    pass

class DoctorResponse(DoctorBase):
    """Schema for doctor response"""
    id: UUID
    user: UserResponse
    verified: bool
    verification_date: Optional[datetime]
    rating: float
    total_reviews: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseModel):
    """Schema for token payload"""
    sub: UUID
    role: UserRole
    exp: int
    jti: str

class PasswordReset(BaseModel):
    """Schema for password reset"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: constr(min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('كلمات المرور غير متطابقة')
        return v

class TwoFactorSetup(BaseModel):
    """Schema for 2FA setup"""
    password: str
    code: constr(regex=r'^\d{6}$')

class TwoFactorVerify(BaseModel):
    """Schema for 2FA verification"""
    code: constr(regex=r'^\d{6}$')
