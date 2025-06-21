from fastapi import FastAPI ,Request ,status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import logging
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.config.database import engine, Base
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware,
    CompressionMiddleware,
)
from app.core.dependencies import get_redis_client
from app.api.v1 import (
    auth,
    users,
    doctors,
    appointments,
    medications,
    chat,
    dashboard,
)

from app.utils.logger import setup_logging
from app.utils.validators import validation_exception_handler

# setup logging
setup_logging()
logger =logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # startup 
    logger.info("Starting Medical Platform API...")
    
    # create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize Redis connection
    redis_client = await get_redis_client()
    app.state.redis = redis_client
    
    logger.info("Application started complete")
    
    yield
    
    # shutdown
    logger.info("Shutting down Medical Platform API...")
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()
    logger.info("Shutting down Medical Platform API...")
    
# Create FastAPI application
app = FastAPI(
    title="medixai Platform API",
    description="Secure, scalable medical platform backend",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Custom Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(CompressionMiddleware)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": int(time.time())
        }
    )
    
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": int(time.time())
        }
    )

# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    }
    
@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check including dependencies"""
    checks = {
        "api": "healthy",
        "database": "checking",
        "redis": "checking",
        "timestamp": int(time.time())
    }
    
 # Check database connection
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = "unhealthy"
    
    # Check Redis connection
    try:
        redis_client = app.state.redis
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = "unhealthy"
    
    # Determine overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in checks.values() 
        if status != checks["timestamp"]
    ) else "unhealthy"
    
    checks["overall"] = overall_status
    
    return checks

# API Routes
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    doctors.router,
    prefix="/api/v1/doctors",
    tags=["Doctors"]
)

app.include_router(
    appointments.router,
    prefix="/api/v1/appointments",
    tags=["Appointments"]
)

app.include_router(
    medications.router,
    prefix="/api/v1/medications",
    tags=["Medications"]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["Chat"]
)

app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Medical Platform API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Contact administrator",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )