"""
Core Security Module
Handles authentication, password hashing, JWT tokens, and 2FA
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64
from passlib.context import CryptContext
from passlib.hash import argon2
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import logging
from cryptography.fernet import Fernet
from app.config.settings import get_settings

from app.config.settings import settings
from app.models.user import User, UserSession

logger = logging.getLogger(__name__)

# Password context
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=settings.ARGON2_TIME_COST,
    argon2__memory_cost=settings.ARGON2_MEMORY_COST,
    argon2__parallelism=settings.ARGON2_PARALLELISM,
)

# Data encryption key
encryption_key = Fernet.generate_key()
fernet = Fernet(encryption_key)

class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using Argon2"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password meets security requirements"""
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "access"
        })
        
        return jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "refresh"
        })
        
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def is_token_expired(payload: Dict[str, Any]) -> bool:
        """Check if token is expired"""
        exp = payload.get("exp")
        if not exp:
            return True
        return datetime.utcnow().timestamp() > exp

class TwoFactorAuth:
    """Two-Factor Authentication management"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate new 2FA secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(email: str, secret: str) -> str:
        """Generate QR code for 2FA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=settings.APP_NAME
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

class SessionManager:
    """User session management"""
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: str,
        device_info: Dict[str, Any],
        ip_address: str,
        user_agent: str
    ) -> UserSession:
        """Create new user session"""
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(
                minutes=settings.SESSION_TIMEOUT
            )
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_token: str
    ) -> Optional[UserSession]:
        """Get active session by token"""
        query = select(UserSession).where(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def invalidate_session(
        db: AsyncSession,
        session_token: str
    ) -> bool:
        """Invalidate user session"""
        query = select(UserSession).where(
            UserSession.session_token == session_token
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            session.is_active = False
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions"""
        from sqlalchemy import update
        
        query = update(UserSession).where(
            UserSession.expires_at < datetime.utcnow()
        ).values(is_active=False)
        
        result = await db.execute(query)
        await db.commit()
        
        return result.rowcount

class EncryptionManager:
    """Data encryption utilities"""
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        """Encrypt sensitive data using AES-256-GCM"""
        return fernet.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return fernet.decrypt(encrypted_data.encode()).decode()

class SecurityAudit:
    """Security audit and logging"""
    
    @staticmethod
    async def log_security_event(
        db: AsyncSession,
        user_id: Optional[str],
        event_type: str,
        details: Dict[str, Any],
        ip_address: str,
        user_agent: str
    ):
        """Log security-related events"""
        from app.models.user import AuditLog
        
        audit_log = AuditLog(
            user_id=user_id,
            action=event_type,
            resource_type="security",
            details={
                **details,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high" if event_type in [
                    "failed_login", "account_locked", "suspicious_activity"
                ] else "medium"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        await db.commit()
        
        # Log to application logger as well
        logger.warning(f"Security event: {event_type} for user {user_id}")

# Security utilities
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)

def constant_time_compare(a: str, b: str) -> bool:
    """Constant time string comparison to prevent timing attacks"""
    return secrets.compare_digest(a, b)

# Rate limiting helpers
async def is_rate_limited(
    redis_client,
    key: str,
    limit: int,
    window: int
) -> bool:
    """Check if action is rate limited"""
    current_count = await redis_client.get(key)
    
    if current_count is None:
        await redis_client.setex(key, window, 1)
        return False
    
    if int(current_count) >= limit:
        return True
    
    await redis_client.incr(key)
    return False

# New functions from the code block
def get_password_hash(password: str) -> str:
    """Generate password hash using Argon2"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using Argon2"""
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT token with claims"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        return payload
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data using Fernet (AES-128)"""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using Fernet (AES-128)"""
    return fernet.decrypt(encrypted_data.encode()).decode()

def generate_random_key(length: int = 32) -> str:
    """Generate cryptographically secure random key"""
    return secrets.token_urlsafe(length)

# Rate limiting decorator
from functools import wraps
from fastapi import HTTPException, Request
from redis import Redis
import time

redis_client = Redis.from_url(settings.REDIS_URL)

def rate_limit(
    requests: int = 100,
    window: int = 3600,
    key_prefix: str = "ratelimit"
):
    """Rate limiting decorator using Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get client IP
            client_ip = request.client.host
            key = f"{key_prefix}:{client_ip}"
            
            # Check rate limit
            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, window, 1)
            else:
                if int(current) >= requests:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests"
                    )
                redis_client.incr(key)
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# WAF rules
def check_sql_injection(value: str) -> bool:
    """Check for SQL injection patterns"""
    sql_patterns = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP",
        "UNION", "OR '1'='1", "OR 1=1"
    ]
    return any(pattern.lower() in value.lower() for pattern in sql_patterns)

def check_xss(value: str) -> bool:
    """Check for XSS patterns"""
    xss_patterns = [
        "<script>", "</script>", "javascript:", "onerror=",
        "onload=", "eval(", "alert("
    ]
    return any(pattern.lower() in value.lower() for pattern in xss_patterns)

def sanitize_input(value: str) -> str:
    """Sanitize input to prevent XSS"""
    import html
    return html.escape(value)

# CSRF Protection
from fastapi import Cookie, Header
from starlette.middleware.base import BaseHTTPMiddleware
import hmac

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_token = request.headers.get("X-CSRF-Token")
            csrf_cookie = request.cookies.get("csrf_token")
            
            if not csrf_token or not csrf_cookie:
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing"
                )
            
            if not hmac.compare_digest(csrf_token, csrf_cookie):
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token invalid"
                )
        
        response = await call_next(request)
        return response