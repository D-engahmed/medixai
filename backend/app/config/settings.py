"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field, ConfigDict
from typing import List, Optional, Dict, Union
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Medical Platform API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    SECRET_KEY: str
    ALLOWED_HOSTS: Union[List[str], str] = Field(default="localhost,127.0.0.1")
    CORS_ORIGINS: Union[List[str], str] = Field(default="")
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    
    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    SQLALCHEMY_DATABASE_URI: str = ""
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_URI: str = ""
    
    # Elasticsearch
    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: int
    ELASTICSEARCH_URI: str = ""
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str
    SMTP_USER: str
    SMTP_PASSWORD: str
    
    # External APIs
    STRIPE_API_KEY: str
    SENDGRID_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    GOOGLE_MAPS_API_KEY: str
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    
    # Monitoring
    SENTRY_DSN: str
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    HEALTH_CHECK_PATH: str = "/health"
    
    # Chat Model
    CHAT_MODEL_ENDPOINT: str
    GENERAL_CHAT_MODEL_ENDPOINT: str
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Database
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis
    REDIS_DB: int = 0
    REDIS_POOL_SIZE: int = 20
    
    # JWT Configuration
    JWT_ISSUER: str = "medical-platform"
    JWT_AUDIENCE: str = "medical-platform-users"
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 1
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    RATE_LIMIT_AUTH_REQUESTS: int = 5
    RATE_LIMIT_AUTH_WINDOW: int = 300  # 5 minutes
    
    # Email Configuration
    EMAIL_FROM: str = "noreply@medical-platform.com"
    EMAIL_FROM_NAME: str = "Medical Platform"
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: Union[List[str], str] = Field(default="image/jpeg,image/png,image/gif,application/pdf,text/plain")
    UPLOAD_PATH: str = "uploads"
    
    # External APIs
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Machine Learning Models
    ML_MODELS_PATH: str = "ml_models"
    BIOMEDX2_MODEL_PATH: Optional[str] = None
    GENERAL_CHAT_MODEL_PATH: Optional[str] = None
    ML_MODEL_DEVICE: str = "cpu"
    ML_MODEL_BATCH_SIZE: int = 32
    
    # Cloud Storage
    CLOUD_STORAGE_PROVIDER: str = "aws"  # or "gcp", "azure", "minio"
    GCP_PROJECT_ID: Optional[str] = None
    GCP_BUCKET_NAME: Optional[str] = None
    
    # Elasticsearch
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    ELASTICSEARCH_INDEX_PREFIX: str = "medical"
    
    # Monitoring and Telemetry
    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    LOGGING_LEVEL: str = "INFO"
    
    # Security Enhancements
    ENABLE_WAF: bool = True
    WAF_RULES: Union[Dict[str, bool], str] = Field(default="sql_injection:True,xss:True,csrf:True,rate_limiting:True,ip_blacklisting:True")
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_WINDOW: int = 900  # 15 minutes
    PASSWORD_HISTORY_SIZE: int = 5
    SESSION_IDLE_TIMEOUT: int = 1800  # 30 minutes
    
    # Notifications
    NOTIFICATION_CHANNELS: Union[List[str], str] = Field(default="email,sms,push")
    NOTIFICATION_BATCH_SIZE: int = 100
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    NOTIFICATION_RETRY_DELAY: int = 300  # 5 minutes
    
    # Compliance
    ENABLE_HIPAA_COMPLIANCE: bool = True
    ENABLE_GDPR_COMPLIANCE: bool = True
    DATA_RETENTION_DAYS: int = 2555  # 7 years
    AUDIT_LOG_RETENTION_DAYS: int = 2555
    PHI_FIELDS: Union[List[str], str] = Field(default="name,email,phone,address,date_of_birth,medical_history,prescription_details,diagnosis")
    
    # Chat System
    CHAT_MESSAGE_MAX_LENGTH: int = 4096
    CHAT_HISTORY_LIMIT: int = 100
    CHAT_AUTO_ESCALATION_THRESHOLD: float = 0.85
    CHAT_RESPONSE_TIMEOUT: int = 30  # seconds
    
    # Geo Search
    GEO_SEARCH_RADIUS_KM: float = 50.0
    GEO_SEARCH_MAX_RESULTS: int = 100
    
    # Payment Processing
    PAYMENT_PROVIDERS: Union[List[str], str] = Field(default="stripe,paypal")
    CURRENCY: str = "USD"
    TAX_RATE: float = 0.0
    MINIMUM_ORDER_AMOUNT: float = 0.50

    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse ALLOWED_HOSTS from string or list"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return ["localhost", "127.0.0.1"]
            # Split by comma and strip whitespace
            return [host.strip() for host in v.split(',') if host.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["localhost", "127.0.0.1"]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from string or list"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return []
            # Split by comma and strip whitespace
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
            # Validate URLs
            validated_origins = []
            for origin in origins:
                try:
                    # Basic URL validation
                    if origin.startswith(('http://', 'https://')):
                        validated_origins.append(origin)
                    else:
                        # Add protocol if missing
                        validated_origins.append(f"http://{origin}")
                except Exception:
                    continue
            return validated_origins
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        else:
            return []

    @field_validator('WAF_RULES', mode='before')
    @classmethod
    def parse_waf_rules(cls, v):
        """Parse WAF_RULES from string or dict"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return {
                    "sql_injection": True,
                    "xss": True,
                    "csrf": True,
                    "rate_limiting": True,
                    "ip_blacklisting": True
                }
            # Parse key:value pairs
            rules = {}
            for rule_pair in v.split(','):
                if ':' in rule_pair:
                    key, value = rule_pair.split(':', 1)
                    key = key.strip()
                    value = value.strip().lower()
                    rules[key] = value in ('true', '1', 'yes', 'on')
            return rules
        elif isinstance(v, dict):
            return v
        else:
            return {
                "sql_injection": True,
                "xss": True,
                "csrf": True,
                "rate_limiting": True,
                "ip_blacklisting": True
            }

    @field_validator('ALLOWED_FILE_TYPES', mode='before')
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parse ALLOWED_FILE_TYPES from string or list"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return ["image/jpeg", "image/png", "image/gif", "application/pdf", "text/plain"]
            # Split by comma and strip whitespace
            return [file_type.strip() for file_type in v.split(',') if file_type.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["image/jpeg", "image/png", "image/gif", "application/pdf", "text/plain"]

    @field_validator('NOTIFICATION_CHANNELS', mode='before')
    @classmethod
    def parse_notification_channels(cls, v):
        """Parse NOTIFICATION_CHANNELS from string or list"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return ["email", "sms", "push"]
            # Split by comma and strip whitespace
            return [channel.strip() for channel in v.split(',') if channel.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["email", "sms", "push"]

    @field_validator('PAYMENT_PROVIDERS', mode='before')
    @classmethod
    def parse_payment_providers(cls, v):
        """Parse PAYMENT_PROVIDERS from string or list"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return ["stripe", "paypal"]
            # Split by comma and strip whitespace
            return [provider.strip() for provider in v.split(',') if provider.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["stripe", "paypal"]

    @field_validator('PHI_FIELDS', mode='before')
    @classmethod
    def parse_phi_fields(cls, v):
        """Parse PHI_FIELDS from string or list"""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return ["name", "email", "phone", "address", "date_of_birth", 
                       "medical_history", "prescription_details", "diagnosis"]
            # Split by comma and strip whitespace
            return [field.strip() for field in v.split(',') if field.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["name", "email", "phone", "address", "date_of_birth", 
                   "medical_history", "prescription_details", "diagnosis"]

    # Computed properties for database URIs
    @property
    def database_url(self) -> str:
        """Generate database URL from components"""
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Generate Redis URL from components"""
        if self.REDIS_URI:
            return self.REDIS_URI
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def elasticsearch_url(self) -> str:
        """Generate Elasticsearch URL from components"""
        if self.ELASTICSEARCH_URI:
            return self.ELASTICSEARCH_URI
        if self.ELASTICSEARCH_USERNAME and self.ELASTICSEARCH_PASSWORD:
            return f"http://{self.ELASTICSEARCH_USERNAME}:{self.ELASTICSEARCH_PASSWORD}@{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"
        return f"http://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOGGING_LEVEL: str = "DEBUG"
    RELOAD: bool = True


class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOGGING_LEVEL: str = "WARNING"
    RELOAD: bool = False


class TestingSettings(Settings):
    """Testing environment settings"""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_medical_db"
    REDIS_URI: str = "redis://localhost:6379/15"


# Factory function to get settings
def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()